"""学习效果评估路由 — 返回学生掌握度、学习进度、薄弱点趋势"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Optional

from ..database import get_db
from ..schemas import StudentProfile
from ..services.profile_manager import get_profile

router = APIRouter(prefix="/evaluation", tags=["学习评估"])


class MasteryItem(BaseModel):
    knowledge_point: str
    mastery: float  # 0.0 ~ 1.0
    status: str     # weak / normal / strong


class ProgressItem(BaseModel):
    date: str
    completed: int
    total: int


class EvaluationResponse(BaseModel):
    user_id: str
    overall_mastery: float
    weak_points: List[str]
    strong_points: List[str]
    mastery_list: List[MasteryItem]
    progress: List[ProgressItem]
    suggestion: str


@router.get("/get", response_model=EvaluationResponse, summary="获取学习效果评估")
async def get_evaluation(
    user_id: str = "demo_user",
    db: Session = Depends(get_db),
):
    """
    根据学生画像中的 mastery 和 weak_points，生成学习效果评估数据。
    当前为基础实现，进度数据为 mock，后续可接入真实学习记录。
    """
    uid = 1 if user_id == "demo_user" else int(user_id) if user_id.isdigit() else 1
    profile = get_profile(db, uid) or StudentProfile()

    mastery_dict = profile.mastery or {}
    weak_points = profile.weak_points or []

    # 构造掌握度列表
    mastery_list = []
    strong_points = []
    for kp, score in mastery_dict.items():
        if score < 0.6:
            status = "weak"
        elif score < 0.85:
            status = "normal"
        else:
            status = "strong"
            strong_points.append(kp)
        mastery_list.append(MasteryItem(
            knowledge_point=kp,
            mastery=score,
            status=status,
        ))

    # 把 weak_points 中还没 mastery 的也补进去
    for kp in weak_points:
        if kp not in mastery_dict:
            mastery_list.append(MasteryItem(
                knowledge_point=kp,
                mastery=0.0,
                status="weak",
            ))

    # 计算总掌握度
    if mastery_list:
        overall = round(sum(m.mastery for m in mastery_list) / len(mastery_list), 2)
    else:
        overall = 0.0

    # Mock 学习进度（后续替换为真实记录）
    progress = [
        ProgressItem(date="2026-06-20", completed=2, total=24),
        ProgressItem(date="2026-06-21", completed=5, total=24),
        ProgressItem(date="2026-06-22", completed=8, total=24),
        ProgressItem(date="2026-06-23", completed=10, total=24),
        ProgressItem(date="2026-06-24", completed=12, total=24),
    ]

    # 生成学习建议
    if weak_points:
        suggestion = f"建议优先巩固薄弱点：{', '.join(weak_points)}。可结合思维导图和代码案例针对性学习。"
    elif overall >= 0.8:
        suggestion = "整体掌握良好，建议进入综合复习和进阶练习阶段。"
    else:
        suggestion = "继续保持学习节奏，多完成练习题以提升掌握度。"

    return EvaluationResponse(
        user_id=user_id,
        overall_mastery=overall,
        weak_points=weak_points,
        strong_points=strong_points,
        mastery_list=mastery_list,
        progress=progress,
        suggestion=suggestion,
    )
