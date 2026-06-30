"""LangGraph 多智能体编排图 — Supervisor → Workers → Reviewer

流程:
  START → supervisor → [条件路由] → worker_1 → worker_2 → ... → reviewer → END

每个 worker 执行时自动记录执行日志、更新进度索引。
条件边 route_map 根据 next_step 将执行流路由到对应 worker 或 END。
"""
import logging
import time
from langgraph.graph import StateGraph, END
from .state import AgentState
from .supervisor import supervisor_node, route_to_worker
from .workers.profile_agent import profile_node
from .workers.doc_agent import doc_node
from .workers.mindmap_agent import mindmap_node
from .workers.quiz_agent import quiz_node
from .workers.code_agent import code_node
from .workers.video_script_agent import video_script_node
from .reviewer import reviewer_node
from .planner import planner_node

logger = logging.getLogger(__name__)

def _retrieve_node(state: AgentState) -> AgentState:
    """知识库检索节点 — 检查 chunks 是否已有数据，空则实时检索"""
    from .utils import advance_agent

    chunks = state.get("retrieved_chunks", [])
    if not chunks:
        try:
            from app.services.retriever import retrieve
            message = state.get("message", "")
            chunks = retrieve(message, top_k=5)
            state["retrieved_chunks"] = chunks
            logger.info("Retrieve: 检索到 %d 个片段", len(chunks))
        except Exception as e:
            logger.warning("Retrieve: 检索失败 %s", e)
    return advance_agent(state)


WORKER_MAP = {
    "retrieve": "retrieve",
    "profile": "profile",
    "doc": "doc",
    "mindmap": "mindmap",
    "quiz": "quiz",
    "code": "code",
    "video_script": "video_script",
    "reviewer": "reviewer",
    "planner": "planner",
}

_ROUTE_OPTIONS = {**WORKER_MAP, "end": END}


# ── 节点包装：执行追踪 + 错误边界 ──

def _wrap_node(name: str, fn):
    """包装每个节点：自动记录执行日志、track progress、加错误边界"""
    def wrapper(state: AgentState) -> AgentState:
        start = time.time()
        seq = state.get("agent_sequence", [])

        # 更新进度
        state["step_index"] = seq.index(name) + 1 if name in seq else state.get("step_index", 0)
        state["total_steps"] = len(seq)

        try:
            result = fn(state)
            duration_ms = int((time.time() - start) * 1000)
            _log(state, name, "done", duration_ms)
            return result
        except Exception as e:
            duration_ms = int((time.time() - start) * 1000)
            logger.exception("[%s] 执行失败: %s", name, e)
            _log(state, name, "error", duration_ms, str(e))
            state["error"] = str(e)
            state["next_step"] = "end"
            return state
    return wrapper


def _log(state: AgentState, node: str, status: str, duration_ms: int, error: str = ""):
    log = state.get("execution_log", [])
    log.append({
        "node": node,
        "status": status,
        "timestamp": time.strftime("%H:%M:%S"),
        "duration_ms": duration_ms,
        "error": error,
    })
    state["execution_log"] = log


# ── 图构建 ──

def _build_graph() -> StateGraph:
    workflow = StateGraph(AgentState)

    workflow.add_node("supervisor", _wrap_node("supervisor", supervisor_node))
    workflow.add_node("retrieve", _wrap_node("retrieve", _retrieve_node))
    workflow.add_node("profile", _wrap_node("profile", profile_node))
    workflow.add_node("doc", _wrap_node("doc", doc_node))
    workflow.add_node("mindmap", _wrap_node("mindmap", mindmap_node))
    workflow.add_node("quiz", _wrap_node("quiz", quiz_node))
    workflow.add_node("code", _wrap_node("code", code_node))
    workflow.add_node("video_script", _wrap_node("video_script", video_script_node))
    workflow.add_node("reviewer", _wrap_node("reviewer", reviewer_node))
    workflow.add_node("planner", _wrap_node("planner", planner_node))

    workflow.set_entry_point("supervisor")

    workflow.add_conditional_edges("supervisor", route_to_worker, _ROUTE_OPTIONS)

    for node_name in WORKER_MAP:
        workflow.add_conditional_edges(node_name, route_to_worker, _ROUTE_OPTIONS)

    return workflow


agent_graph = _build_graph().compile()


# ── 便捷入口 ──

def run_agent_flow(user_id: str, message: str, chapter: str | None = None,
                    profile: dict | None = None, chunks: list[dict] | None = None) -> AgentState:
    """同步运行完整多智能体流程"""
    initial_state: AgentState = {
        "user_id": user_id, "message": message, "chapter": chapter,
        "profile": profile,
        "retrieved_chunks": chunks or [],
        "task_type": None, "agent_sequence": [], "current_agent": None,
        "generated_resources": [], "mindmap_data": None, "quiz_data": None,
        "code_data": None, "video_script": None,
        "review_passed": None, "review_notes": [], "learning_path": [], "completed_nodes": [],
        "execution_log": [], "step_index": 0, "total_steps": 0,
        "next_step": "supervisor", "error": None, "llm_errors": [],
    }
    logger.info("Agent 流程启动: user=%s msg=%s", user_id, message[:50])
    result = agent_graph.invoke(initial_state)
    logger.info("Agent 流程完成: resources=%d steps=%d",
                len(result.get("generated_resources", [])),
                len(result.get("execution_log", [])))
    return result


def run_agent_flow_stream(user_id: str, message: str, chapter: str | None = None,
                          profile: dict | None = None, chunks: list[dict] | None = None):
    """流式入口：逐步 yield 每个节点的执行状态，配合 SSE 使用"""
    initial_state: AgentState = {
        "user_id": user_id, "message": message, "chapter": chapter,
        "profile": profile,
        "retrieved_chunks": chunks or [],
        "task_type": None, "agent_sequence": [], "current_agent": None,
        "generated_resources": [], "mindmap_data": None, "quiz_data": None,
        "code_data": None, "video_script": None,
        "review_passed": None, "review_notes": [], "learning_path": [], "completed_nodes": [],
        "execution_log": [], "step_index": 0, "total_steps": 0,
        "next_step": "supervisor", "error": None, "llm_errors": [],
    }

    for step_output in agent_graph.stream(initial_state):
        node_name = list(step_output.keys())[0]
        node_state = step_output[node_name]

        yield {
            "event": "agent_status",
            "agent": node_name,
            "status": "running",
            "next_step": node_state.get("next_step", "end"),
            "task_type": node_state.get("task_type"),
            "agent_sequence": node_state.get("agent_sequence", []),
            "step_index": node_state.get("step_index", 0),
            "total_steps": node_state.get("total_steps", 0),
            "error": node_state.get("error"),
        }

    # 注意：stream 已消费初始状态，最终状态 = 最后 yield 的 node_state
    # 如需完整 final_state，可通过执行日志重建
