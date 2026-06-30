"""Profile Agent: extract and update student profile from conversation."""
import json
import re

from ..state import AgentState
from ..utils import advance_agent, record_llm_error

SYSTEM_PROMPT = """你是学生画像抽取智能体。请从学生的自然语言描述中提取以下维度，并只输出严格 JSON：

- major: 专业背景
- grade: 年级
- course_goal: 学习目标
- knowledge_base: 前置课程掌握程度，使用对象
- weak_points: 薄弱知识点列表
- learning_preference: 学习偏好列表，如图解、例题、代码示例
- pace: 学习节奏
- resource_preference: 偏好的资源类型列表

示例：
{
  "major": "计算机科学与技术",
  "grade": "大二",
  "course_goal": "两周内掌握 Cache、流水线和中断",
  "knowledge_base": {"digital_logic": "中等", "assembly": "较弱"},
  "weak_points": ["Cache映射方式", "流水线冲突"],
  "learning_preference": ["图解", "例题", "代码示例"],
  "pace": "每天1小时",
  "resource_preference": ["思维导图", "练习题"]
}
"""


def profile_node(state: AgentState) -> AgentState:
    """Extract a profile with LLM, then fall back to a default demo profile."""
    message = state.get("message", "")

    try:
        profile = _extract_with_llm(message) if message else None
    except Exception as e:
        record_llm_error(state, "Profile Agent", e)
        profile = None

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
        "course_goal": "掌握课程核心知识",
        "knowledge_base": {"digital_logic": "中等", "assembly": "较弱", "computer_architecture": "入门"},
        "weak_points": ["Cache映射方式", "流水线冲突"],
        "learning_preference": ["图解", "例题", "代码示例"],
        "pace": "每天1小时",
        "resource_preference": ["思维导图", "练习题"],
    }


def _extract_with_llm(message: str) -> dict | None:
    """Call LLM to extract student profile JSON."""
    from app.llm_client import SparkLLM

    llm = SparkLLM()
    prompt = f"{SYSTEM_PROMPT}\n\n学生自述：{message}\n\n只输出 JSON："
    raw = llm.chat(prompt).strip()
    raw = _strip_code_fence(raw)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        data = json.loads(match.group()) if match else {}
    return data if isinstance(data, dict) and data else None


def _strip_code_fence(raw: str) -> str:
    if not raw.startswith("```"):
        return raw
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    return raw
