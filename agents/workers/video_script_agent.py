"""VideoScript Agent — 基于知识点和学生偏好，调用 LLM 生成短视频讲解脚本"""
import json
import logging
from ..state import AgentState
from ..utils import advance_agent

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """你是教育短视频脚本生成智能体。请根据知识点和学生画像，生成 1-3 分钟的短视频讲解脚本。

要求：
1. 时长控制在 1-3 分钟（共 3-5 个分镜）
2. 每个分镜包含画面描述和旁白内容
3. 语言生动有趣，适合短视频平台
4. 根据学生的薄弱点重点展开
5. 结尾有知识点总结

输出格式（严格 Markdown，不要额外包装）：
## 视频标题
### 第 1 镜（XX 秒）
- 画面：画面描述
- 旁白：旁白内容
### 第 2 镜（XX 秒）
- 画面：...
- 旁白：...
"""


def video_script_node(state: AgentState) -> AgentState:
    """调用 LLM 生成视频脚本"""
    message = state.get("message", "")
    profile = state.get("profile", {})
    chunks = state.get("retrieved_chunks", [])

    prompt = _build_prompt(message, profile, chunks)

    try:
        from app.llm_client import SparkLLM
        llm = SparkLLM()
        script = llm.chat(prompt).strip()
    except Exception as e:
        logger.error("VideoScript Agent LLM 调用失败: %s", e)
        script = _fallback_script(message, chunks)

    state["video_script"] = script

    resources = state.get("generated_resources", [])
    resources.append({"type": "video_script", "title": _derive_title(message, chunks), "content": script})
    state["generated_resources"] = resources
    return advance_agent(state)


def _build_prompt(message: str, profile: dict | None, chunks: list[dict]) -> str:
    parts = [SYSTEM_PROMPT]
    if profile:
        parts.append(f"\n学生画像:\n{json.dumps(profile, ensure_ascii=False, indent=2)}")
        if profile.get("weak_points"):
            parts.append(f"薄弱点（需重点讲解）: {', '.join(profile['weak_points'])}")
        if profile.get("learning_preference"):
            parts.append(f"学习偏好: {', '.join(profile['learning_preference'])}")
    if chunks:
        parts.append("\n知识库片段（脚本素材）:")
        for c in chunks:
            parts.append(f"- [{c.get('id')}] {c.get('title')}: {c.get('content', '')[:300]}")
    parts.append(f"\n请为以下知识点生成短视频脚本: {message}")
    return "\n".join(parts)


def _derive_title(message: str, chunks: list[dict]) -> str:
    if chunks and chunks[0].get("title"):
        return f"{chunks[0]['title']} — 短视频脚本"
    return f"{message} — 短视频脚本"


def _fallback_script(message: str, chunks: list[dict]) -> str:
    """LLM 不可用时的降级脚本"""
    title = chunks[0].get("title", message) if chunks else message
    return f"""## {title} — 3 分钟讲解（离线模式）

> LLM 服务暂时不可用，以下为基础脚本框架。

### 第 1 镜（30 秒）
- 画面：课程标题卡片 + 知识点关键词动画
- 旁白：同学们好，今天我们来学习 {title}。

### 第 2 镜（60 秒）
- 画面：核心概念图解
- 旁白：（请连接 AI 服务获取完整旁白）

### 第 3 镜（30 秒）
- 画面：知识要点总结卡片
- 旁白：以上就是 {title} 的核心内容，同学们记得做练习题巩固哦。
"""
