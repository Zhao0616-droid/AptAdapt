"""Code Agent — 基于知识点和学生画像，调用 LLM 生成 Verilog/汇编/伪代码案例"""
import json
import logging
from ..state import AgentState
from ..utils import advance_agent

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """你是《计算机组成原理》代码案例生成智能体。请根据知识点和学生画像，生成代码示例并附带逐行解释。

支持的代码类型：
- verilog: Verilog HDL 硬件描述
- assembly: MIPS/ARM/x86 汇编
- pseudocode: 伪代码 / C-like 描述
- circuit: 电路描述（门级/寄存器级）

要求：
1. 代码必须与知识点紧密相关
2. 附带逐行或逐段解释
3. 根据学生画像中的偏好的资源类型选择语言
4. 代码简洁可运行（或在仿真环境可验证）

输出格式（严格 JSON，不要额外文字）：
{
  "language": "verilog",
  "source": "完整的代码内容",
  "explanation": "逐行/逐段解释，使用 Markdown 格式"
}
"""


def code_node(state: AgentState) -> AgentState:
    """调用 LLM 生成代码案例"""
    message = state.get("message", "")
    profile = state.get("profile", {})
    chunks = state.get("retrieved_chunks", [])

    prompt = _build_prompt(message, profile, chunks)

    try:
        from app.llm_client import SparkLLM
        llm = SparkLLM()
        raw = llm.chat(prompt).strip()
        if raw.startswith("```"):
            lines = raw.split("\n")
            raw = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
        code = json.loads(raw)
    except Exception as e:
        logger.error("Code Agent LLM 调用失败: %s", e)
        code = _fallback_code(message, chunks)

    state["code_data"] = code

    resources = state.get("generated_resources", [])
    resources.append({
        "type": "code",
        "title": f"{code.get('language', 'verilog').upper()} 代码示例",
        "content": code,
    })
    state["generated_resources"] = resources
    return advance_agent(state)


def _build_prompt(message: str, profile: dict | None, chunks: list[dict]) -> str:
    parts = [SYSTEM_PROMPT]
    if profile:
        parts.append(f"\n学生画像:\n{json.dumps(profile, ensure_ascii=False, indent=2)}")
    if chunks:
        parts.append("\n知识库片段:")
        for c in chunks:
            parts.append(f"- [{c.get('id')}] {c.get('title')}: {c.get('content', '')[:300]}")
    parts.append(f"\n请为以下知识点生成代码案例: {message}")
    return "\n".join(parts)


def _fallback_code(message: str, chunks: list[dict]) -> dict:
    """LLM 不可用时的降级代码"""
    title = chunks[0].get("title", message) if chunks else message
    return {
        "language": "verilog",
        "source": f"// {title} — 代码示例（离线模式）\n// 请连接 AI 服务获取完整代码\nmodule example;\n  // TODO\nendmodule",
        "explanation": "当前 LLM 服务不可用，请稍后重试获取完整代码案例和逐行解释。",
    }
