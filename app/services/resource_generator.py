"""资源生成服务 — 按资源类型调用 LLM 生成个性化内容"""
import json
import re
import os
import logging
from typing import Optional

from ..llm_client import SparkLLM
from ..schemas import ResourceItem, ReviewResult, StudentProfile

# prompt 模板目录
PROMPT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "agents", "prompts")
logger = logging.getLogger(__name__)
LAST_LLM_ERRORS: list[str] = []


def _load_prompt(name: str) -> str:
    path = os.path.join(PROMPT_DIR, name)
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return ""


def _call_llm(prompt: str) -> str:
    llm = SparkLLM()
    return llm.chat(prompt)


def _safe_call_llm(prompt: str, fallback: str) -> str:
    try:
        content = _call_llm(prompt)
        return content.strip() or fallback
    except Exception as e:
        logger.error("LLM call failed: %s", e)
        LAST_LLM_ERRORS.append(str(e))
        return fallback


def _profile_to_json(profile: Optional[StudentProfile]) -> str:
    if not profile:
        return "{}"
    return json.dumps(profile.model_dump(), ensure_ascii=False, indent=2)


def _render_prompt(template: str, values: dict) -> str:
    rendered = template
    for key, value in values.items():
        rendered = rendered.replace("{" + key + "}", str(value))
    return rendered


def _parse_json(raw: str) -> dict:
    """从 LLM 返回中提取 JSON"""
    raw = raw.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        return json.loads(m.group()) if m else {}


def _normalize_quiz_set(raw_data, knowledge_point: str) -> dict:
    if isinstance(raw_data, list):
        raw_questions = raw_data
        title = f"{knowledge_point} 巩固练习"
    elif isinstance(raw_data, dict) and isinstance(raw_data.get("questions"), list):
        raw_questions = raw_data.get("questions") or []
        title = raw_data.get("title") or f"{knowledge_point} 巩固练习"
    elif isinstance(raw_data, dict):
        raw_questions = [raw_data]
        title = raw_data.get("title") or f"{knowledge_point} 巩固练习"
    else:
        raw_questions = []
        title = f"{knowledge_point} 巩固练习"

    questions = []
    for index, item in enumerate(raw_questions[:6], start=1):
        if not isinstance(item, dict):
            continue
        question_type = item.get("type") or "choice"
        if question_type == "short_answer":
            continue
        options = item.get("options")
        if not isinstance(options, list) or not options:
            options = ["正确", "错误"] if question_type == "true_false" else []
        questions.append({
            "id": item.get("id") or f"{knowledge_point}_{index}",
            "type": question_type,
            "question": item.get("question") or f"关于{knowledge_point}的第 {index} 题",
            "options": options,
            "answer": item.get("answer", 0),
            "explanation": item.get("explanation") or "请结合讲解文档复盘本题涉及的关键概念。",
            "difficulty": item.get("difficulty") or "medium",
            "knowledge_point": item.get("knowledge_point") or knowledge_point,
        })

    if len(questions) < 3:
        questions.extend(_fallback_quiz_questions(knowledge_point)[len(questions):])

    return {
        "title": title,
        "knowledge_point": knowledge_point,
        "questions": questions,
    }


def _fallback_quiz_questions(knowledge_point: str) -> list[dict]:
    return [
        {
            "id": f"{knowledge_point}_fallback_1",
            "type": "choice",
            "question": f"下列关于{knowledge_point}的说法，正确的是？",
            "options": ["它只需要死记结论", "它需要结合地址映射/执行过程理解", "它和性能无关", "它不属于计算机组成原理"],
            "answer": 1,
            "explanation": f"{knowledge_point}需要结合结构、过程和典型例题理解，不能只背结论。",
            "difficulty": "easy",
            "knowledge_point": knowledge_point,
        },
        {
            "id": f"{knowledge_point}_fallback_2",
            "type": "choice",
            "question": f"学习{knowledge_point}时，最有效的复盘方式是哪一种？",
            "options": ["只看答案", "用一个具体例子手算或推演", "跳过错题", "只记英文缩写"],
            "answer": 1,
            "explanation": "计算机组成原理的核心知识点通常需要通过具体例子推演，才能暴露薄弱环节。",
            "difficulty": "medium",
            "knowledge_point": knowledge_point,
        },
        {
            "id": f"{knowledge_point}_fallback_3",
            "type": "choice",
            "question": f"如果你在{knowledge_point}上连续做错题，系统应该优先做什么？",
            "options": ["降低该知识点掌握度并加入薄弱点", "直接标记为已掌握", "删除学习记录", "跳到无关课程"],
            "answer": 0,
            "explanation": "连续做错说明该知识点掌握度不足，应进入薄弱点并触发后续补强资源。",
            "difficulty": "medium",
            "knowledge_point": knowledge_point,
        },
    ]


def _build_context(
    knowledge_point: str,
    profile: Optional[StudentProfile],
    chunks: list[dict],
) -> dict:
    """构造填充 prompt 模板的上下文变量"""
    chunks_text = "\n---\n".join(
        f"[{c['id']}] {c['title']}: {c['content']}" for c in chunks
    ) if chunks else "暂无匹配的知识库片段"

    return {
        "knowledge_point": knowledge_point,
        "profile": _profile_to_json(profile),
        "weak_points": json.dumps(profile.weak_points, ensure_ascii=False) if profile else "[]",
        "retrieved_chunks": chunks_text,
        "message": f"请生成关于「{knowledge_point}」的学习资源",
    }


# ── 各资源类型生成函数 ──

def generate_doc(knowledge_point: str, profile: Optional[StudentProfile],
                 chunks: list[dict]) -> ResourceItem:
    """生成个性化讲解文档 (Markdown)"""
    template = _load_prompt("doc_prompt.txt")
    ctx = _build_context(knowledge_point, profile, chunks)

    prompt = _render_prompt(template, {k: ctx.get(k, "") for k in ["profile", "retrieved_chunks", "message"]})
    fallback = f"## {knowledge_point}\n\n当前 AI 服务暂不可用，系统已生成基础讲解框架。请结合知识库片段复习核心概念、典型例题和易错点。"
    content = _safe_call_llm(prompt, fallback)

    return ResourceItem(
        type="doc",
        title=f"《{knowledge_point}》个性化讲解",
        content=content,
    )


def generate_mindmap(knowledge_point: str, profile: Optional[StudentProfile],
                     chunks: list[dict]) -> ResourceItem:
    """生成思维导图 (Mermaid 格式)"""
    prompt = f"""请为知识点「{knowledge_point}」生成 Mermaid mindmap 格式的思维导图。

参考知识库片段:
{_build_context(knowledge_point, profile, chunks)['retrieved_chunks']}

严格按以下格式输出，不要多余文字:
mindmap
  root(({knowledge_point}))
    子主题1
      细节1
      细节2
    子主题2
      细节1"""

    content = _safe_call_llm(prompt, f"mindmap\n  root(({knowledge_point}))\n    核心概念\n    关键原理\n    典型应用")
    # 如果 LLM 没按格式，做兜底
    if not content.strip().startswith("mindmap"):
        content = f"mindmap\n  root(({knowledge_point}))\n    核心概念\n    关键原理\n    典型应用"

    return ResourceItem(
        type="mindmap",
        title=f"{knowledge_point} 思维导图",
        content=content,
    )


def generate_quiz(knowledge_point: str, profile: Optional[StudentProfile],
                  chunks: list[dict]) -> ResourceItem:
    """生成练习题 (JSON)"""
    template = _load_prompt("quiz_prompt.txt")
    ctx = _build_context(knowledge_point, profile, chunks)

    prompt = _render_prompt(template, {k: ctx.get(k, "") for k in ["profile", "knowledge_point", "weak_points"]})
    raw = _safe_call_llm(prompt, "{}")
    quiz_data = _parse_json(raw)
    quiz_data = _normalize_quiz_set(quiz_data, knowledge_point)

    return ResourceItem(
        type="quiz",
        title=f"{knowledge_point} 练习集",
        content=json.dumps(quiz_data, ensure_ascii=False),
    )


def generate_code(knowledge_point: str, profile: Optional[StudentProfile],
                  chunks: list[dict]) -> ResourceItem:
    """生成代码案例 (JSON)"""
    template = _load_prompt("code_prompt.txt")
    ctx = _build_context(knowledge_point, profile, chunks)

    prompt = _render_prompt(template, {k: ctx.get(k, "") for k in ["profile", "knowledge_point", "retrieved_chunks"]})
    raw = _safe_call_llm(prompt, "{}")
    code_data = _parse_json(raw)

    if not code_data.get("source"):
        code_data = {
            "language": "verilog",
            "source": "// 示例代码待生成\nmodule example;\nendmodule",
            "explanation": f"关于{knowledge_point}的代码示例。",
        }

    return ResourceItem(
        type="code",
        title=f"{knowledge_point} 代码案例",
        content=json.dumps(code_data, ensure_ascii=False),
    )


def generate_video_script(knowledge_point: str, profile: Optional[StudentProfile],
                          chunks: list[dict]) -> ResourceItem:
    """生成视频脚本 (Markdown)"""
    prompt = f"""请为知识点「{knowledge_point}」生成一段 1-3 分钟的短视频讲解脚本。

参考知识库:
{_build_context(knowledge_point, profile, chunks)['retrieved_chunks']}

输出 Markdown 格式:
## {knowledge_point} — 短视频讲解脚本
### 第 1 镜 (XX 秒)
- 画面: ...
- 旁白: ...
### 第 2 镜 (XX 秒)
- 画面: ...
- 旁白: ..."""

    fallback = f"## {knowledge_point} — 短视频讲解脚本\n\n### 第 1 镜\n- 画面: 知识点标题卡片\n- 旁白: 今天我们学习 {knowledge_point}。\n\n### 第 2 镜\n- 画面: 核心概念图解\n- 旁白: 请结合课程知识库理解关键原理。\n"
    content = _safe_call_llm(prompt, fallback)

    return ResourceItem(
        type="video_script",
        title=f"{knowledge_point} 视频脚本",
        content=content,
    )


# ── 资源类型 → 生成函数映射 ──

GENERATORS = {
    "doc": generate_doc,
    "mindmap": generate_mindmap,
    "quiz": generate_quiz,
    "code": generate_code,
    "video_script": generate_video_script,
}


def review_resources(resources: list[ResourceItem], chunks: list[dict]) -> ReviewResult:
    """用 Reviewer Agent 审核生成资源"""
    if not resources:
        return ReviewResult(passed=False, notes=["未生成任何资源"])

    template = _load_prompt("reviewer_prompt.txt")
    chunks_text = "\n".join(f"[{c['id']}] {c['title']}: {c['content'][:200]}..." for c in chunks)
    resources_text = "\n---\n".join(
        f"[{r.type}] {r.title}\n{r.content[:500]}" for r in resources
    )

    prompt = (
        template
        .replace("{generated_resources}", resources_text[:3000])
        .replace("{retrieved_chunks}", chunks_text[:2000])
    )

    try:
        raw = _safe_call_llm(prompt, "{}")
        result = _parse_json(raw)
    except Exception:
        result = {}

    passed = result.get("passed", True)
    notes = [
        f"已审核 {len(resources)} 个资源",
        f"引用知识片段: {[c['id'] for c in chunks]}",
    ]
    if result.get("issues"):
        notes.extend(result["issues"])
    if result.get("suggestions"):
        notes.extend(result["suggestions"])
    for error in LAST_LLM_ERRORS:
        notes.insert(0, f"大模型调用失败: {error}")

    return ReviewResult(passed=passed, notes=notes)


def generate_resources(
    knowledge_point: str,
    resource_types: list[str],
    profile: Optional[StudentProfile],
    chunks: list[dict],
    skip_review: bool = False,
) -> tuple[list[ResourceItem], ReviewResult]:
    """
    按指定类型生成个性化资源，完成后审核。

    Args:
        knowledge_point: 目标知识点
        resource_types: 资源类型列表
        profile: 学生画像
        chunks: RAG 检索结果
        skip_review: 是否跳过审核（加速调试）

    Returns:
        (resources, review)
    """
    resources: list[ResourceItem] = []
    LAST_LLM_ERRORS.clear()

    for rtype in resource_types:
        gen = GENERATORS.get(rtype)
        if gen is None:
            continue
        item = gen(knowledge_point, profile, chunks)
        resources.append(item)

    if skip_review:
        review = ReviewResult(
            passed=True,
            notes=[f"已生成 {len(resources)} 个资源（跳过审核）"],
        )
    else:
        review = review_resources(resources, chunks)

    return resources, review
