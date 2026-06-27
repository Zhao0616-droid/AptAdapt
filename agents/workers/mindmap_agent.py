"""MindMap Agent — 基于知识库片段和学生画像，调用 LLM 生成 Mermaid 思维导图"""
import json
import logging
from ..state import AgentState
from ..utils import advance_agent

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """你是思维导图生成智能体。请根据提供的课程知识库片段和学生画像，生成 Mermaid mindmap 格式的思维导图。

要求：
1. 根节点为知识点名称
2. 二级节点为主要子主题（3-5 个）
3. 三级节点为关键细节或要点
4. 对学生的薄弱点增加标记（可在节点文本中标注 ★重点）
5. 层级控制在 3 层以内，保持清晰

输出格式（严格 Mermaid mindmap 语法，不要额外 Markdown 包装）：
mindmap
  root((知识点名称))
    子知识点1
      细节1
      细节2
    子知识点2
      细节1
      细节2
"""


def mindmap_node(state: AgentState) -> AgentState:
    """调用 LLM 生成思维导图"""
    message = state.get("message", "")
    profile = state.get("profile", {})
    chunks = state.get("retrieved_chunks", [])

    prompt = _build_prompt(message, profile, chunks)

    try:
        from app.llm_client import SparkLLM
        llm = SparkLLM()
        raw = llm.chat(prompt).strip()
        # 清理可能的 markdown 代码块包装
        if raw.startswith("```"):
            lines = raw.split("\n")
            raw = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
        mindmap = raw
    except Exception as e:
        logger.error("MindMap Agent LLM 调用失败: %s", e)
        mindmap = _fallback_mindmap(message, chunks)

    state["mindmap_data"] = mindmap

    resources = state.get("generated_resources", [])
    resources.append({"type": "mindmap", "title": _derive_title(message, chunks), "content": mindmap})
    state["generated_resources"] = resources
    return advance_agent(state)


def _build_prompt(message: str, profile: dict | None, chunks: list[dict]) -> str:
    parts = [SYSTEM_PROMPT]
    if profile:
        parts.append(f"\n学生画像:\n{json.dumps(profile, ensure_ascii=False, indent=2)}")
    if chunks:
        parts.append("\n知识库片段:")
        for c in chunks:
            parts.append(f"- [{c.get('id')}] {c.get('title')}: {c.get('content', '')[:200]}")
    parts.append(f"\n请为以下知识点生成思维导图: {message}")
    return "\n".join(parts)


def _derive_title(message: str, chunks: list[dict]) -> str:
    if chunks and chunks[0].get("title"):
        return f"{chunks[0]['title']} 思维导图"
    return f"{message} 思维导图"


def _fallback_mindmap(message: str, chunks: list[dict]) -> str:
    """LLM 不可用时的降级导图"""
    titles = [c.get("title", message) for c in chunks[:3]] or [message]
    lines = ["mindmap", f"  root(({titles[0]}))"]
    for t in titles[1:]:
        lines.append(f"    {t}")
    return "\n".join(lines)
