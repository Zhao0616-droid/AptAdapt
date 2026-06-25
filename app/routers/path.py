"""学习路径路由 — 基于知识点 DAG 和学生画像生成个性化路径"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Optional

from ..database import get_db
from ..schemas import StudentProfile
from ..services.profile_manager import get_profile
from agents.planner import load_dag, topological_sort

router = APIRouter(prefix="/path", tags=["学习路径"])


class PathNode(BaseModel):
    id: str
    title: str
    difficulty: Optional[str] = None
    chapter: Optional[int] = None
    priority: str = "normal"
    note: Optional[str] = None


class PathResponse(BaseModel):
    user_id: str
    course: str
    path: List[PathNode]
    weak_points: List[str]


@router.get("/get", response_model=PathResponse, summary="获取个性化学习路径")
async def get_learning_path(
    user_id: str = "demo_user",
    course: str = "computer_organization",
    db: Session = Depends(get_db),
):
    """
    根据学生画像中的 weak_points，结合知识点 DAG 的拓扑排序，
    生成薄弱点优先的个性化学习路径。
    """
    # 1. 查询画像
    uid = 1 if user_id == "demo_user" else int(user_id) if user_id.isdigit() else 1
    profile = get_profile(db, uid)
    weak_points = profile.weak_points if profile else []

    # 2. 加载 DAG 并拓扑排序
    try:
        dag = load_dag()
        raw_path = topological_sort(dag, weak_points)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"路径规划失败: {str(e)}")

    # 3. 包装成响应格式
    path = []
    for node in raw_path:
        nid = node.get("id", "")
        title = node.get("title", "")
        is_weak = nid in weak_points or title in weak_points
        path.append(PathNode(
            id=nid,
            title=title,
            difficulty=node.get("difficulty"),
            chapter=node.get("chapter"),
            priority="high" if is_weak else "normal",
            note="薄弱点，建议重点学习" if is_weak else None,
        ))

    return PathResponse(
        user_id=user_id,
        course=course,
        path=path,
        weak_points=weak_points,
    )
