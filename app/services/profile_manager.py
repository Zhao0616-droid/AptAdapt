"""Student profile extraction, persistence, and merge helpers."""
import json
import re
from typing import Optional

from sqlalchemy.orm import Session

from ..llm_client import SparkLLM
from ..models import UserProfile
from ..schemas import StudentProfile

EXTRACTION_PROMPT = """请从以下学生对话中提取学习画像信息，并只输出严格 JSON，不要 Markdown 代码块。

画像维度：
- major: 专业背景
- grade: 年级
- course_goal: 学习目标
- knowledge_base: 前置课程掌握程度对象，如 {"数字逻辑": "中等"}
- weak_points: 薄弱知识点列表
- learning_preference: 学习偏好列表，如 ["图解", "例题", "代码示例"]
- pace: 学习节奏
- resource_preference: 偏好资源类型列表，如 ["思维导图", "练习题"]

学生对话：
__CONVERSATION__

只输出 JSON："""


def _render_extraction_prompt(text: str) -> str:
    return EXTRACTION_PROMPT.replace("__CONVERSATION__", text)


def _profile_to_json(profile: StudentProfile) -> str:
    return json.dumps(profile.model_dump(), ensure_ascii=False)


def extract_profile_from_text(text: str) -> StudentProfile:
    """Extract a student profile with LLM; return an empty profile on failure."""
    try:
        llm = SparkLLM()
        raw = llm.chat(_render_extraction_prompt(text)).strip()
        raw = _strip_code_fence(raw)
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            data = json.loads(match.group()) if match else {}
        return StudentProfile(**data)
    except Exception as e:
        print(f"[Profile] 画像抽取失败，返回空画像: {e}")
        return StudentProfile()


def _strip_code_fence(raw: str) -> str:
    if not raw.startswith("```"):
        return raw
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    return raw


def _normalize_tag_key(value: str) -> str:
    text = str(value or "").strip().lower()
    text = re.sub(r"[\s，,、/|｜;；:：()（）【】\[\]{}<>《》\"'“”‘’·.\-_]+", "", text)
    text = re.sub(r"(方式|知识点|核心|相关|学习|掌握|理解|生成)", "", text)
    return text


def _dedupe_similar_items(items: list) -> list[str]:
    result: list[str] = []
    keys: list[str] = []
    token_sets: list[set[str]] = []
    for item in items:
        text = str(item or "").strip()
        key = _normalize_tag_key(text)
        if not text or not key:
            continue
        tokens = _semantic_tokens(key)

        duplicate_index = next(
            (
                index
                for index, existing in enumerate(keys)
                if existing == key or existing in key or key in existing
                or _is_similar_token_set(tokens, token_sets[index])
            ),
            -1,
        )
        if duplicate_index >= 0:
            if len(text) < len(result[duplicate_index]):
                result[duplicate_index] = text
                keys[duplicate_index] = key
                token_sets[duplicate_index] = tokens
            continue

        result.append(text)
        keys.append(key)
        token_sets.append(tokens)
    return result


def _merge_similar_lists(old_items: list, new_items: list) -> list[str]:
    return _dedupe_similar_items([*old_items, *new_items])


def _semantic_tokens(key: str) -> set[str]:
    concepts = [
        "cache", "映射", "直接映射", "全相联", "组相联", "流水线", "冲突",
        "中断", "dma", "代码", "图解", "资源", "原理",
    ]
    tokens = {concept for concept in concepts if concept in key}
    return tokens or set(key)


def _is_similar_token_set(a: set[str], b: set[str]) -> bool:
    if not a or not b:
        return False
    intersection = a & b
    if len(intersection) < 2:
        return False
    return len(intersection) / min(len(a), len(b)) >= 0.66


def get_profile(db: Session, user_id: int) -> Optional[StudentProfile]:
    """Load a persisted student profile."""
    row = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    if row and row.profile_json:
        data = json.loads(row.profile_json)
        return StudentProfile(**data)
    return None


def save_profile(db: Session, user_id: int, profile: StudentProfile) -> UserProfile:
    """Create or update a persisted student profile."""
    row = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    profile_json = _profile_to_json(profile)

    if row:
        row.profile_json = profile_json
    else:
        row = UserProfile(user_id=user_id, profile_json=profile_json)
        db.add(row)

    db.commit()
    db.refresh(row)
    return row


def update_profile_from_conversation(db: Session, user_id: int, message: str) -> StudentProfile:
    """Extract profile from a message, merge it with existing data, and persist it."""
    new_profile = extract_profile_from_text(message)
    existing = get_profile(db, user_id)

    if existing:
        merged = existing.model_dump()
        new_data = new_profile.model_dump(exclude_unset=True, exclude_none=True)
        for key, value in new_data.items():
            if isinstance(value, list) and isinstance(merged.get(key), list):
                merged[key] = _merge_similar_lists(merged[key], value)
            elif value:
                merged[key] = value
        merged_profile = StudentProfile(**merged)
    else:
        merged_profile = new_profile

    save_profile(db, user_id, merged_profile)
    return merged_profile
