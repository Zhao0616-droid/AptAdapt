"""Doc Agent — 基于知识库片段和学生画像，调用 LLM 生成个性化讲解文档"""
import json
import logging
from ..state import AgentState
from ..utils import advance_agent

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """你是《计算机组成原理》课程高级讲师，请根据提供的课程知识库片段和学生画像，生成个性化 Markdown 讲解文档。

要求：
1. 内容必须基于提供的知识库片段，不得虚构知识点或数据
2. 根据学生画像中的 weak_points 和 learning_preference 调整讲解策略
3. 使用 Markdown 格式，结构清晰：标题 → 引入 → 核心概念 → 图解/类比 → 例题 → 要点总结
4. 对薄弱知识点增加图解说明和具体例题
5. 标注引用来源（知识库片段 ID），格式: [来源: chunk_id]
6. 语言通俗易懂，适当使用类比帮助理解

输出格式：直接输出 Markdown 文档，不需要 JSON 包装。
"""


def doc_node(state: AgentState) -> AgentState:
    """生成个性化讲解文档 —— 调用星火 LLM 基于检索片段和画像生成"""
    message = state.get("message", "")
    profile = state.get("profile", {})
    chunks = state.get("retrieved_chunks", [])

    # 如果还没有检索片段，尝试实时检索
    if not chunks and message:
        try:
            from app.services.retriever import retrieve
            chunks = retrieve(message, top_k=5)
            state["retrieved_chunks"] = chunks
        except Exception as e:
            logger.warning("Doc Agent 检索知识库失败: %s", e)

    prompt = _build_prompt(message, profile, chunks)

    try:
        from app.llm_client import SparkLLM
        llm = SparkLLM()
        content = llm.chat(prompt)
    except Exception as e:
        logger.error("Doc Agent LLM 调用失败: %s", e)
        content = _fallback_content(message, profile, chunks)

    doc = {
        "type": "doc",
        "title": _derive_title(message, profile, chunks),
        "content": content,
        "knowledge_point": message,
        "sources": [c.get("id", "") for c in chunks],
    }

    resources = state.get("generated_resources", [])
    resources.append(doc)
    state["generated_resources"] = resources
    return advance_agent(state)


def _build_prompt(message: str, profile: dict | None, chunks: list[dict]) -> str:
    parts = [SYSTEM_PROMPT]

    # 学生画像
    if profile:
        parts.append(f"\n## 学生画像\n{json.dumps(profile, ensure_ascii=False, indent=2)}")

    # 知识库片段
    if chunks:
        parts.append("\n## 课程知识库参考片段\n以下内容来自课程教材，请严格据此讲解，不得偏离：")
        for i, c in enumerate(chunks, 1):
            parts.append(
                f"\n### 片段 {i} [{c.get('id', 'unknown')}]\n"
                f"标题: {c.get('title', '')}\n"
                f"章节: {c.get('chapter', '')}\n"
                f"内容: {c.get('content', '')}"
            )
    else:
        parts.append("\n## 注意：未检索到知识库片段\n请基于你的知识讲解，但必须标注「依据不足」。")

    # 学生问题
    parts.append(f"\n## 学生问题\n{message}")
    parts.append("\n请生成个性化讲解文档（直接输出 Markdown）：")

    return "\n".join(parts)


def _derive_title(message: str, profile: dict | None, chunks: list[dict]) -> str:
    """从检索片段和用户消息中提取合适标题"""
    if chunks:
        titles = [c.get("title", "") for c in chunks if c.get("title")]
        if titles:
            return f"《计算机组成原理》— {titles[0]}"
    if profile and profile.get("weak_points"):
        for wp in profile["weak_points"]:
            if wp in message:
                return f"薄弱点攻克: {wp}"
    return f"《计算机组成原理》个性化讲解"


def _fallback_content(message: str, profile: dict | None, chunks: list[dict]) -> str:
    """LLM 不可用时的降级内容，基于检索片段拼装"""
    lines = ["## 个性化讲解（离线模式）\n", "> LLM 服务暂时不可用，以下为知识库片段摘要。\n"]

    if chunks:
        for c in chunks[:3]:
            lines.append(f"### {c.get('title', '知识点')}")
            lines.append(c.get("content", ""))
            lines.append(f"[来源: {c.get('id', '')}]\n")
    else:
        lines.append("当前无法获取知识库内容，请稍后重试。")

    weak_points = (profile or {}).get("weak_points", [])
    if weak_points:
        lines.append("### 你的薄弱点")
        for wp in weak_points:
            lines.append(f"- {wp}")

    return "\n".join(lines)
