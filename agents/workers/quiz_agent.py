"""Quiz Agent — 基于知识点和学生画像，调用 LLM 生成练习题"""
import json
import logging
import re
from ..state import AgentState
from ..utils import advance_agent

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """你是《计算机组成原理》练习题生成智能体。请根据提供的知识库片段、难度等级和学生薄弱点，生成针对性练习题。

题目类型: choice（选择题）/ true_false（判断题）/ short_answer（简答题）

要求：
1. 题目必须基于知识库片段内容，不得编造
2. 针对薄弱点生成更多题目（2-3 题）
3. 每道题必须有详细解析，说明为什么对/错
4. 难度分为 easy / medium / hard，根据学生水平调整

输出格式（严格 JSON，不要额外文字）：
{
  "type": "choice",
  "question": "题目内容",
  "options": ["A. 选项1", "B. 选项2", "C. 选项3", "D. 选项4"],
  "answer": 0,
  "explanation": "详细的解析说明，解释正确选项和错误选项的原因",
  "difficulty": "medium",
  "knowledge_point": "知识点名称"
}
"""


def quiz_node(state: AgentState) -> AgentState:
    """调用 LLM 生成练习题"""
    message = state.get("message", "")
    profile = state.get("profile", {})
    chunks = state.get("retrieved_chunks", [])

    prompt = _build_prompt(message, profile, chunks)

    try:
        from app.llm_client import SparkLLM
        llm = SparkLLM()
        raw = llm.chat(prompt).strip()
        quiz = _parse_quiz_response(raw, message, chunks)
    except Exception as e:
        logger.error("Quiz Agent LLM 调用失败: %s", e)
        quiz = _fallback_quiz(message, chunks)

    state["quiz_data"] = quiz

    resources = state.get("generated_resources", [])
    resources.append({
        "type": "quiz",
        "title": f"{quiz.get('knowledge_point', message)} 练习题",
        "content": quiz,
    })
    state["generated_resources"] = resources
    return advance_agent(state)


def _build_prompt(message: str, profile: dict | None, chunks: list[dict]) -> str:
    parts = [SYSTEM_PROMPT]
    if profile:
        parts.append(f"\n学生画像:\n{json.dumps(profile, ensure_ascii=False, indent=2)}")
        if profile.get("weak_points"):
            parts.append(f"薄弱点（需重点出题）: {', '.join(profile['weak_points'])}")
    if chunks:
        parts.append("\n知识库片段（出题依据）:")
        for c in chunks:
            parts.append(f"- [{c.get('id')}] {c.get('title')}: {c.get('content', '')[:300]}")
    parts.append(f"\n请根据以上信息，为以下知识点生成一道练习题: {message}")
    return "\n".join(parts)


def _parse_quiz_response(raw: str, message: str, chunks: list[dict]) -> dict:
    raw = _strip_code_fence(raw.strip())
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        data = json.loads(match.group()) if match else {}
    return _normalize_quiz(data, message, chunks)


def _strip_code_fence(raw: str) -> str:
    if not raw.startswith("```"):
        return raw
    lines = raw.split("\n")
    return "\n".join(lines[1:-1] if lines and lines[-1].strip() == "```" else lines[1:])


def _normalize_quiz(data, message: str, chunks: list[dict]) -> dict:
    if isinstance(data, list):
        data = data[0] if data else {}
    if not isinstance(data, dict):
        data = {}

    fallback = _fallback_quiz(message, chunks)
    options = data.get("options")
    if not isinstance(options, list) or not options:
        options = fallback["options"]

    return {
        "type": data.get("type") or fallback["type"],
        "question": data.get("question") or fallback["question"],
        "options": options,
        "answer": data.get("answer", fallback["answer"]),
        "explanation": data.get("explanation") or fallback["explanation"],
        "difficulty": data.get("difficulty") or fallback["difficulty"],
        "knowledge_point": data.get("knowledge_point") or fallback["knowledge_point"],
    }


def _fallback_quiz(message: str, chunks: list[dict]) -> dict:
    """LLM 不可用时的降级题目"""
    title = chunks[0].get("title", message) if chunks else message
    return {
        "type": "choice",
        "question": f"关于「{title}」，以下说法正确的是？",
        "options": ["A. (请连接 AI 服务获取真实题目)", "B. 暂不可用", "C. 离线模式", "D. 请重试"],
        "answer": 0,
        "explanation": "当前 LLM 服务不可用，请稍后重试获取真实题目和解析。",
        "difficulty": "medium",
        "knowledge_point": title,
    }
