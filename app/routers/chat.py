"""对话路由 — 多智能体协同流程（Supervisor → Workers → Reviewer）

完整 pipeline:
  supervisor(意图识别) → profile(画像) → retrieve → worker(生成) → reviewer(审核) → 返回

支持两种模式:
  - /chat/send: 同步模式，等待全部 Agent 执行完毕返回
  - /chat/stream: SSE 流式模式，实时推送每个 Agent 的状态变更
"""
import json
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..services.profile_manager import get_profile, update_profile_from_conversation
from ..services.retriever import retrieve
from ..utils.jwt_handler import get_current_user
from agents.graph import agent_graph
from agents.state import AgentState

logger = logging.getLogger(__name__)
router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    course: str = "computer_organization"
    chapter: Optional[str] = None


# ── 工厂函数 ──

def _load_profile(db: Session, user_id: int) -> dict | None:
    try:
        p = get_profile(db, user_id=user_id)
        return p.model_dump() if p else None
    except Exception as e:
        logger.warning("加载画像失败: %s", e)
        return None


def _make_initial_state(req: ChatRequest, user_id: int, profile: dict | None, chunks: list[dict]) -> AgentState:
    return {
        "user_id": str(user_id),
        "message": req.message,
        "chapter": req.chapter,
        "profile": profile,
        "retrieved_chunks": chunks,
        "task_type": None,
        "agent_sequence": [],
        "current_agent": None,
        "generated_resources": [],
        "mindmap_data": None,
        "quiz_data": None,
        "code_data": None,
        "video_script": None,
        "review_passed": None,
        "review_notes": [],
        "learning_path": [],
        "completed_nodes": [],
        "execution_log": [],
        "step_index": 0,
        "total_steps": 0,
        "next_step": "supervisor",
        "error": None,
        "llm_errors": [],
    }


def _sse(event: str, data: dict) -> str:
    payload = json.dumps(data, ensure_ascii=False)
    return f"event: {event}\ndata: {payload}\n\n"


# ── 同步模式 ──

@router.post("/chat/send", summary="发送消息（多智能体同步模式）")
async def send_message(
    req: ChatRequest,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """运行完整多智能体流程，返回所有生成资源 + 审核结果"""
    uid = user["user_id"]
    existing_profile = _load_profile(db, uid)

    chunks: list[dict] = []
    try:
        chunks = retrieve(req.message, top_k=5, course_id=req.course)
    except Exception as e:
        logger.warning("知识库检索失败: %s", e)

    initial_state = _make_initial_state(req, uid, existing_profile, chunks)

    try:
        result = agent_graph.invoke(initial_state)
    except Exception as e:
        logger.exception("多智能体流程执行失败")
        raise HTTPException(status_code=500, detail=f"Agent 流程失败: {str(e)}")

    if result.get("profile"):
        try:
            update_profile_from_conversation(db, user_id=uid, message=req.message)
        except Exception:
            pass

    return {
        "code": 200,
        "message": "success",
        "data": {
            "task_type": result.get("task_type"),
            "agent_sequence": result.get("agent_sequence", []),
            "resources": result.get("generated_resources", []),
            "mindmap": result.get("mindmap_data"),
            "quiz": result.get("quiz_data"),
            "code": result.get("code_data"),
            "video_script": result.get("video_script"),
            "learning_path": result.get("learning_path", []),
            "review": {
                "passed": result.get("review_passed"),
                "notes": result.get("review_notes", []),
            },
            "execution_log": result.get("execution_log", []),
            "step_index": result.get("step_index", 0),
            "total_steps": result.get("total_steps", 0),
            "retrieved_chunks": [
                {"id": c["id"], "title": c.get("title", "")}
                for c in result.get("retrieved_chunks", [])
            ],
            "error": result.get("error"),
            "llm_errors": result.get("llm_errors", []),
        },
    }


# ── SSE 流式模式 ──

@router.post("/chat/stream", summary="发送消息（多智能体流式模式）")
async def send_message_stream(
    req: ChatRequest,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """流式 SSE: 实时推送每个 Agent 节点的运行状态和最终结果"""

    async def generate():
        uid = user["user_id"]
        existing_profile = _load_profile(db, uid)

        chunks: list[dict] = []
        try:
            chunks = retrieve(req.message, top_k=5, course_id=req.course)
            yield _sse("agent_status", {
                "agent": "Retriever", "status": "done",
                "message": f"检索到 {len(chunks)} 个相关片段",
                "chunks": [c["id"] for c in chunks],
            })
        except Exception as e:
            yield _sse("agent_status", {
                "agent": "Retriever", "status": "error",
                "message": f"检索失败: {e}",
            })

        initial_state = _make_initial_state(req, uid, existing_profile, chunks)
        final_state = None

        try:
            for step_output in agent_graph.stream(initial_state):
                node_name = list(step_output.keys())[0]
                node_state = step_output[node_name]

                yield _sse("agent_status", {
                    "agent": node_name,
                    "status": "running",
                    "next_step": node_state.get("next_step", "end"),
                    "task_type": node_state.get("task_type"),
                    "agent_sequence": node_state.get("agent_sequence", []),
                })

                if node_name == "reviewer":
                    yield _sse("review", {
                        "passed": node_state.get("review_passed"),
                        "notes": node_state.get("review_notes", []),
                    })

                if node_name == "doc":
                    for r in node_state.get("generated_resources", []):
                        if r.get("type") == "doc":
                            yield _sse("content", {
                                "type": "doc",
                                "title": r.get("title"),
                                "content": r.get("content"),
                            })

                final_state = node_state

        except Exception:
            logger.exception("Agent 流式执行异常")
            yield _sse("error", {"message": "Agent 流程执行失败，请重试"})
            return

        if final_state:
            yield _sse("done", {
                "message": "处理完成",
                "task_type": final_state.get("task_type"),
                "resources": [
                    {"type": r.get("type"), "title": r.get("title")}
                    for r in final_state.get("generated_resources", [])
                ],
                "review_passed": final_state.get("review_passed"),
                "review_notes": final_state.get("review_notes", []),
                "llm_errors": final_state.get("llm_errors", []),
                "retrieved_chunks": [
                    c["id"] for c in final_state.get("retrieved_chunks", [])
                ],
            })

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
