"""学习效果评估路由：返回学生掌握度、学习进度和薄弱点建议。"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..schemas import StudentProfile
from ..services.profile_manager import get_profile
from ..utils.jwt_handler import get_current_user

router = APIRouter(prefix="/evaluation", tags=["学习评估"])


class MasteryItem(BaseModel):
    knowledge_point: str
    mastery: float
    status: str  # untested / weak / normal / strong


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
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """根据画像中的 mastery 和 weak_points 生成学习效果评估数据。"""
    uid = user["user_id"]
    profile = get_profile(db, uid) or StudentProfile()

    mastery_dict = profile.mastery or {}
    weak_points = profile.weak_points or []

    mastery_list = []
    measured_mastery_items = []
    strong_points = []

    for kp, score in mastery_dict.items():
      score = float(score or 0)
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
      measured_mastery_items.append(score)

    for kp in weak_points:
        if kp not in mastery_dict:
            mastery_list.append(MasteryItem(
                knowledge_point=kp,
                mastery=0.0,
                status="untested",
            ))

    if measured_mastery_items:
        overall = round(sum(measured_mastery_items) / len(measured_mastery_items), 2)
    else:
        overall = 0.0

    progress = [
        ProgressItem(date="2026-06-20", completed=2, total=24),
        ProgressItem(date="2026-06-21", completed=5, total=24),
        ProgressItem(date="2026-06-22", completed=8, total=24),
        ProgressItem(date="2026-06-23", completed=10, total=24),
        ProgressItem(date="2026-06-24", completed=12, total=24),
    ]

    untested_points = [kp for kp in weak_points if kp not in mastery_dict]
    if untested_points:
        suggestion = f"以下薄弱点尚未测评：{', '.join(untested_points)}。建议先完成对应练习题，再根据正确率更新掌握度。"
    elif weak_points:
        suggestion = f"建议优先巩固薄弱点：{', '.join(weak_points)}。可结合思维导图和代码案例针对性学习。"
    elif overall >= 0.8:
        suggestion = "整体掌握良好，建议进入综合复习和进阶练习阶段。"
    else:
        suggestion = "继续保持学习节奏，多完成练习题以提升掌握度。"

    return EvaluationResponse(
        user_id=str(uid),
        overall_mastery=overall,
        weak_points=weak_points,
        strong_points=strong_points,
        mastery_list=mastery_list,
        progress=progress,
        suggestion=suggestion,
    )
