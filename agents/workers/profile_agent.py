"""Profile Agent — 从对话中抽取和更新学生画像"""
from ..state import AgentState
from ..utils import advance_agent

SYSTEM_PROMPT = """你是学生画像抽取智能体。请从学生的自然语言描述中提取以下维度的信息，输出结构化 JSON。

画像维度（至少 6 个）：
- major: 专业背景
- grade: 年级
- course_goal: 学习目标
- knowledge_base: 各前置课程掌握程度 (dict)
- weak_points: 薄弱知识点列表
- learning_preference: 学习偏好（图解/例题/代码等）
- pace: 学习节奏
- resource_preference: 偏好的资源类型

输出格式（严格 JSON，不要额外文字）：
{
  "major": "计算机科学与技术",
  "grade": "大二",
  "course_goal": "两周内掌握Cache、流水线和中断",
  "knowledge_base": {"digital_logic": "中等", "assembly": "较弱", "computer_architecture": "入门"},
  "weak_points": ["Cache映射方式", "流水线冲突"],
  "learning_preference": ["图解", "例题", "代码示例"],
  "pace": "每天1小时",
  "resource_preference": ["思维导图", "练习题"]
}
"""


def profile_node(state: AgentState) -> AgentState:
    """从用户消息中抽取/更新画像，优先使用 LLM 抽取，失败降级为默认画像"""
    message = state.get("message", "")

    profile = _extract_with_llm(message) if message else None
    if profile is None:
        profile = _default_profile()

    if state.get("profile"):
        existing = state["profile"]
        existing["weak_points"] = list(set(existing.get("weak_points", []) + profile.get("weak_points", [])))
        state["profile"] = existing
    else:
        state["profile"] = profile

    return advance_agent(state)


def _default_profile() -> dict:
    return {
        "major": "计算机科学与技术",
        "grade": "大二",
        "course_goal": "掌握《计算机组成原理》核心知识",
        "knowledge_base": {"digital_logic": "中等", "assembly": "较弱", "computer_architecture": "入门"},
        "weak_points": ["Cache映射方式", "流水线冲突"],
        "learning_preference": ["图解", "例题", "代码示例"],
        "pace": "每天1小时",
        "resource_preference": ["思维导图", "练习题"],
    }


def _extract_with_llm(message: str) -> dict | None:
    """调用星火 LLM 从用户消息中抽取画像 JSON"""
    try:
        from app.llm_client import SparkLLM
        import json
        llm = SparkLLM()
        prompt = f"{SYSTEM_PROMPT}\n\n学生自述: {message}\n\n请输出结构化 JSON："
        raw = llm.chat(prompt).strip()
        if raw.startswith("```"):
            lines = raw.split("\n")
            raw = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
        return json.loads(raw)
    except Exception:
        return None
