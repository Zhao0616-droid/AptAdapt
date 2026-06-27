"""练习题路由 — 提交答案、判定正误、更新画像掌握度"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from ..database import get_db
from ..schemas import StudentProfile, ProfileResponse
from ..services.profile_manager import get_profile, save_profile
from ..utils.jwt_handler import get_current_user

router = APIRouter(prefix="/quiz", tags=["练习题"])


class QuizAnswer(BaseModel):
    question_id: Optional[str] = None
    knowledge_point: str
    question: str
    correct_answer: str  # 正确答案，如 "A" / "True"
    user_answer: str     # 学生答案
    difficulty: str = "medium"


class QuizSubmitRequest(BaseModel):
    answers: List[QuizAnswer]


class QuizResultItem(BaseModel):
    knowledge_point: str
    correct: bool
    user_answer: str
    correct_answer: str


class QuizSubmitResponse(BaseModel):
    user_id: str
    total: int
    correct_count: int
    accuracy: float
    results: List[QuizResultItem]
    updated_profile: StudentProfile


def _update_mastery(profile: StudentProfile, answers: List[QuizAnswer]) -> StudentProfile:
    """根据答题结果更新知识点掌握度 mastery"""
    if profile.mastery is None:
        profile.mastery = {}

    # 按知识点聚合答题
    grouped = {}
    for ans in answers:
        grouped.setdefault(ans.knowledge_point, []).append(
            ans.user_answer.strip().lower() == ans.correct_answer.strip().lower()
        )

    # 更新掌握度：简单用该知识点最近正确率
    for kp, results in grouped.items():
        accuracy = sum(results) / len(results)
        # 与历史掌握度做滑动平均（权重 0.6 历史 + 0.4 本次）
        old = profile.mastery.get(kp, 0.0)
        if isinstance(old, (int, float)):
            new_mastery = round(old * 0.6 + accuracy * 0.4, 2)
        else:
            new_mastery = round(accuracy, 2)
        profile.mastery[kp] = new_mastery

        # 根据掌握度调整 weak_points
        if new_mastery >= 0.8 and kp in profile.weak_points:
            profile.weak_points.remove(kp)
        elif new_mastery < 0.6 and kp not in profile.weak_points:
            profile.weak_points.append(kp)

    return profile


@router.post("/submit", response_model=QuizSubmitResponse, summary="提交练习题答案")
async def submit_quiz(
    req: QuizSubmitRequest,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """
    接收学生练习题作答，判定正误，更新画像中对应知识点的掌握度，
    并动态调整 weak_points。
    """
    if not req.answers:
        raise HTTPException(status_code=400, detail="answers 不能为空")

    uid = user["user_id"]
    profile = get_profile(db, uid) or StudentProfile()

    results = []
    for ans in req.answers:
        is_correct = ans.user_answer.strip().lower() == ans.correct_answer.strip().lower()
        results.append(QuizResultItem(
            knowledge_point=ans.knowledge_point,
            correct=is_correct,
            user_answer=ans.user_answer,
            correct_answer=ans.correct_answer,
        ))

    correct_count = sum(1 for r in results if r.correct)
    accuracy = round(correct_count / len(results), 2)

    # 更新掌握度
    updated_profile = _update_mastery(profile, req.answers)
    save_profile(db, uid, updated_profile)

    return QuizSubmitResponse(
        user_id=str(uid),
        total=len(results),
        correct_count=correct_count,
        accuracy=accuracy,
        results=results,
        updated_profile=updated_profile,
    )
