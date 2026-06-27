"""Supervisor Agent — 任务识别、路由分发、流程编排

支持两种模式：
- Keyword mode: 基于关键词快速匹配（无外部依赖，LLM 不可用时降级使用）
- LLM mode: 调用星火 API 做语义级意图识别（更准确）
"""
import json
import logging
from .state import AgentState
from .utils import next_in_sequence

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """你是 AptAdapt 系统的 Supervisor 智能体，负责识别学生意图并调度 Worker Agent。

你的职责：
1. 分析用户输入，判断任务类型
2. 决定需要调用哪些 Agent，以及调用顺序
3. 将任务分发给对应的 Worker Agent

可用的 Worker Agent：
- retrieve: 检索知识库片段（生成类任务前必须先 retrieve）
- profile: 抽取/更新学生画像
- doc: 生成讲解文档
- mindmap: 生成思维导图
- quiz: 生成练习题
- code: 生成代码案例
- video_script: 生成视频脚本
- path: 规划学习路径
- reviewer: 审核生成内容

Agent 调用规则：
- 第一次对话应先调用 profile 更新画像
- 生成类任务 (doc/mindmap/quiz/code/video_script) 之后必须调用 reviewer
- path 任务独立调用 planner
- 多资源生成按 doc → mindmap → quiz → code → video_script 顺序

输出格式（严格 JSON）：
{
  "task_type": "doc",
  "agent_sequence": ["profile", "doc", "reviewer"],
  "reasoning": "学生询问Cache映射方式，先更新画像，再生成讲解文档，最后审核"
}
"""

# ── 关键词路由表（LLM 不可用时的降级方案）──
KEYWORD_ROUTES = [
    (["我是", "专业", "基础", "学过", "薄弱", "目标", "大几", "大一", "大二", "大三", "大四"], ["profile"]),
    (["路径", "计划", "学习顺序", "规划", "先学", "后学"], ["planner"]),
    (["题目", "练习题", "测试", "做题", "出题", "考题"], ["profile", "retrieve", "quiz", "reviewer"]),
    (["导图", "思维导图", "脑图", "mindmap"], ["profile", "retrieve", "mindmap", "reviewer"]),
    (["代码", "verilog", "汇编", "Verilog", "写个", "实现"], ["profile", "retrieve", "code", "reviewer"]),
    (["视频", "脚本", "讲解视频", "录制"], ["profile", "retrieve", "video_script", "reviewer"]),
    (["全面", "所有", "全部", "整套", "完整"], ["profile", "retrieve", "doc", "mindmap", "quiz", "code", "reviewer"]),
]


def classify_by_keywords(message: str) -> tuple[str, list[str], str]:
    """关键词匹配：返回 (task_type, agent_sequence, reasoning)"""
    for keywords, sequence in KEYWORD_ROUTES:
        if any(kw in message for kw in keywords):
            task_type = sequence[0] if sequence[0] != "profile" else (sequence[1] if len(sequence) > 1 else "profile")
            reasoning = f"关键词匹配 → 路由到: {' → '.join(sequence)}"
            return task_type, sequence, reasoning

    # 默认：生成讲解文档
    return "doc", ["profile", "retrieve", "doc", "reviewer"], "默认路由 → 生成讲解文档"


def classify_by_llm(message: str) -> tuple[str, list[str], str]:
    """调用星火 LLM 做语义级意图识别，返回 (task_type, agent_sequence, reasoning)"""
    try:
        from app.llm_client import SparkLLM

        llm = SparkLLM()
        prompt = f"{SYSTEM_PROMPT}\n\n学生输入: {message}\n\n请分析并输出 JSON："
        raw = llm.chat(prompt)

        # 尝试从回复中提取 JSON
        raw = raw.strip()
        if raw.startswith("```"):
            # 去掉 markdown 代码块标记
            lines = raw.split("\n")
            raw = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

        result = json.loads(raw)
        task_type = result.get("task_type", "doc")
        agent_sequence = result.get("agent_sequence", ["profile", "doc", "reviewer"])
        reasoning = result.get("reasoning", "LLM 语义分析")
        return task_type, agent_sequence, reasoning

    except json.JSONDecodeError as e:
        logger.warning("Supervisor LLM 返回非 JSON，降级为关键词路由: %s", e)
    except Exception as e:
        logger.warning("Supervisor LLM 调用失败，降级为关键词路由: %s", e)

    return classify_by_keywords(message)


def route_to_worker(state: AgentState) -> str:
    """
    LangGraph 条件边函数：根据 next_step 决定路由到哪个 Worker。
    由 supervisor_node 设置 next_step 后，Graph 自动调用此函数执行分派。
    """
    step = state.get("next_step", "end")
    valid_agents = {"retrieve", "profile", "doc", "mindmap", "quiz", "code", "video_script", "reviewer", "planner"}

    if step in valid_agents:
        return step
    if step == "end":
        return "end"
    # unknown step → end
    logger.warning("未知的 next_step: %s，终止流程", step)
    return "end"


def supervisor_node(state: AgentState) -> AgentState:
    """
    Supervisor 入口节点：
    1. 分析用户消息，决定 task_type 和 agent_sequence
    2. 将序列首节点设为 current_agent / next_step
    3. 状态流入 LangGraph 条件边 → 对应 Worker
    """
    message = state.get("message", "")

    # 先尝试 LLM 分析，失败自动降级关键词
    task_type, agent_sequence, reasoning = classify_by_llm(message)

    logger.info("Supervisor: task=%s, seq=%s, reason=%s", task_type, agent_sequence, reasoning)

    state["task_type"] = task_type
    state["agent_sequence"] = agent_sequence
    state["current_agent"] = agent_sequence[0] if agent_sequence else None
    state["next_step"] = agent_sequence[0] if agent_sequence else "end"

    return state
