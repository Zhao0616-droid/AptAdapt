"""Reviewer Agent — 调用 LLM + 规则双层审核，确保生成内容质量

审核流程:
  1. LLM 语义审核（主路径）— 事实性 · 安全性 · 完整性 · 个性化 · 引用
  2. 规则审核（降级路径）— LLM 不可用时使用
  3. 幻觉检测 — 逐句比对知识库，标记无依据的陈述
"""
import json
import re
import logging
from .state import AgentState
from .utils import advance_agent

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """你是 AptAdapt 内容审核专家。请严格审核以下教学资源的质量。

审核维度（每个维度单独评分，1-5分）：
1. **事实性**：内容是否与提供的知识库片段一致？有无编造的知识点或数据？
2. **安全性**：内容是否包含敏感、违规、偏见或不当信息？
3. **完整性**：是否覆盖学生问题的核心要点？有无遗漏关键概念？
4. **个性化**：是否回应学生的薄弱点和学习偏好？（1分=完全未个性化，5分=精准回应）
5. **引用规范**：是否标注知识库来源？引用是否准确？

审核结论：
- passed=true: 所有维度 ≥3 分，可直接交付
- passed=false: 任一维度 <3 分，需修改

输出格式（严格 JSON，不要额外文字）：
{
  "passed": true,
  "scores": {"factuality": 5, "safety": 5, "completeness": 4, "personalization": 3, "citation": 3},
  "issues": [{"dimension": "factuality", "severity": "high", "detail": "具体问题描述"}],
  "suggestions": ["修改建议1", "修改建议2"],
  "hallucinations": [{"claim": "原文中的可疑陈述", "reason": "知识库中未找到依据"}],
  "referenced_chunks": ["chunk_id_1"],
  "summary": "一句话审核总结"
}
"""


def reviewer_node(state: AgentState) -> AgentState:
    """审核所有生成资源，LLM 审核失败自动降级为规则审核"""
    resources = state.get("generated_resources", [])
    retrieved = state.get("retrieved_chunks", [])

    if not resources:
        state["review_passed"] = False
        state["review_notes"] = ["未生成任何资源"]
        return advance_agent(state)

    try:
        from app.config import REVIEWER_USE_LLM
    except Exception:
        REVIEWER_USE_LLM = False

    review = _review_with_llm(resources, retrieved) if REVIEWER_USE_LLM else None

    rule_review = _rule_based_review(resources, retrieved)
    if review is None:
        review = rule_review
    else:
        # 合并 LLM 和规则审核结果
        review["issues"].extend(rule_review.get("issues", []))
        review["suggestions"].extend(rule_review.get("suggestions", []))
        if rule_review.get("issues"):
            review["passed"] = False

    state["review_passed"] = review.get("passed", False)
    notes = _format_notes(review)
    for error in state.get("llm_errors", []):
        notes.insert(0, f"[大模型调用失败] {error}")
    state["review_notes"] = notes
    return advance_agent(state)


# ── LLM 审核 ──

def _review_with_llm(resources: list[dict], chunks: list[dict]) -> dict | None:
    """调用 LLM 进行语义级深度审核"""
    try:
        from app.llm_client import SparkLLM

        resource_texts = []
        for i, r in enumerate(resources):
            content = r.get("content", "")
            if isinstance(content, dict):
                content = json.dumps(content, ensure_ascii=False)
            resource_texts.append(
                f"### 资源{i+1} [{r.get('type')}] {r.get('title', '')}\n{str(content)[:800]}"
            )

        chunk_texts = []
        for c in chunks:
            chunk_texts.append(
                f"- [{c.get('id')}] {c.get('title')}: {c.get('content', '')[:300]}"
            )

        prompt = f"""{SYSTEM_PROMPT}

## 知识库参考（事实依据）
{chr(10).join(chunk_texts) if chunk_texts else '未检索到知识库'}

## 待审核资源
{chr(10).join(resource_texts)}

请严格审核，输出 JSON："""

        llm = SparkLLM()
        raw = llm.chat(prompt).strip()
        if raw.startswith("```"):
            lines = raw.split("\n")
            raw = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
        return json.loads(raw)

    except Exception as e:
        logger.warning("Reviewer LLM 审核失败，降级规则审核: %s", e)
        return None


# ── 规则审核 ──

def _rule_based_review(resources: list[dict], chunks: list[dict]) -> dict:
    """基于规则的审核 + 简易幻觉检测"""
    issues: list[dict] = []
    suggestions: list[str] = []
    hallucinations: list[dict] = []

    # 1. 知识库可用性检查
    if not chunks:
        issues.append({
            "dimension": "factuality",
            "severity": "high",
            "detail": "未检索到知识库片段，无法验证内容事实性",
        })
        suggestions.append("建议先通过检索获取相关知识点，再重新生成内容")

    # 2. 逐资源检查
    for r in resources:
        rtype = r.get("type", "")
        content = r.get("content", "")
        if isinstance(content, dict):
            content = json.dumps(content, ensure_ascii=False)
        content = str(content)
        title = r.get("title", rtype)

        # 内容长度检查
        if len(content) < 80:
            issues.append({
                "dimension": "completeness",
                "severity": "medium",
                "detail": f"[{title}] 内容过短（{len(content)}字符），可能不完整",
            })
            suggestions.append(f"建议扩展 [{title}] 的内容，增加细节和例题")

        # 引用检查（Markdown doc 类型）
        if rtype == "doc" and "[来源:" not in content and "[来源" not in content:
            suggestions.append(f"[{title}] 建议标注知识库引用来源，格式: [来源: chunk_id]")

        # 简易幻觉检测：检查 content 中是否有与所有 chunks 无关的陌生概念
        if chunks:
            fake_claims = _detect_hallucinations(content, chunks)
            hallucinations.extend(fake_claims)

    # 3. 跨资源一致性（同类资源数量异常检查）
    types = [r.get("type") for r in resources]
    if len(types) > 1 and len(set(types)) < len(types):
        suggestions.append("存在同类重复资源，建议去重")

    passed = len([i for i in issues if i.get("severity") == "high"]) == 0

    return {
        "passed": passed,
        "scores": {},
        "issues": issues,
        "suggestions": suggestions,
        "hallucinations": hallucinations,
        "referenced_chunks": [c.get("id", "") for c in chunks],
        "summary": f"规则审核: {len(resources)}个资源, {len(issues)}个问题, {'通过' if passed else '需修改'}",
    }


def _detect_hallucinations(content: str, chunks: list[dict]) -> list[dict]:
    """
    简易幻觉检测：从内容中提取中文短句，比对是否出现在任一知识库片段中。
    未命中任意 chunk 的陈述标记为潜在幻觉。

    注意：这是启发式检测，不能替代 LLM 语义审核。
    """
    if not chunks:
        return []

    # 合并所有知识库文本
    all_chunk_text = " ".join(c.get("content", "") for c in chunks)

    # 按句号/分号拆分内容
    sentences = re.split(r"[。；\n]", content)
    suspicious = []
    for sent in sentences:
        sent = sent.strip()
        # 跳过过短或纯标点的句子
        if len(sent) < 8 or re.match(r"^[#\-\*\s\[\]\(\)>]+$", sent):
            continue
        # 跳过包含来源标注的句子
        if "[来源" in sent or "[source" in sent.lower():
            continue
        # 检查是否在知识库中出现
        if sent not in all_chunk_text:
            suspicious.append({
                "claim": sent[:100],
                "reason": "未在知识库中找到匹配依据",
            })

    return suspicious[:5]  # 最多 5 条


def _format_notes(review: dict) -> list[str]:
    """将审核结果格式化为前端可展示的 notes 列表"""
    notes: list[str] = []

    if review.get("summary"):
        notes.append(f"[审核结论] {review['summary']}")

    scores = review.get("scores", {})
    if scores:
        dim_names = {
            "factuality": "事实性", "safety": "安全性",
            "completeness": "完整性", "personalization": "个性化", "citation": "引用",
        }
        score_str = " | ".join(
            f"{dim_names.get(k, k)}: {v}/5" for k, v in scores.items()
        )
        notes.append(f"[评分] {score_str}")

    for issue in review.get("issues", []):
        sev = issue.get("severity", "medium")
        icon = "🔴" if sev == "high" else "🟡" if sev == "medium" else "🟢"
        notes.append(f"{icon} [{issue.get('dimension', '')}] {issue.get('detail', '')}")

    for sug in review.get("suggestions", []):
        notes.append(f"[建议] {sug}")

    for hal in review.get("hallucinations", []):
        notes.append(f"[疑似幻觉] {hal.get('claim', '')[:60]}... — {hal.get('reason', '')}")

    return notes
