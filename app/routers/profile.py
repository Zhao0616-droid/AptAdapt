"""画像路由 — 获取与更新学生画像"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas import StudentProfile, ProfileResponse, ProfileUpdateRequest
from ..services.profile_manager import get_profile, save_profile, extract_profile_from_text
from ..utils.jwt_handler import get_current_user

router = APIRouter(prefix="/profile", tags=["画像"])


@router.get("/get", response_model=ProfileResponse, summary="获取学生画像")
async def get_student_profile(
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """根据当前登录用户获取学生画像，未生成时返回空画像"""
    uid = user["user_id"]
    profile = get_profile(db, uid)
    if profile is None:
        return ProfileResponse(
            user_id=str(uid),
            profile=StudentProfile(),
        )
    return ProfileResponse(user_id=str(uid), profile=profile)


@router.post("/update", response_model=ProfileResponse, summary="手动更新学生画像")
async def update_student_profile(
    req: ProfileUpdateRequest,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """手动覆盖学生画像"""
    uid = user["user_id"]
    row = save_profile(db, uid, req.profile)
    return ProfileResponse(
        user_id=str(uid),
        profile=req.profile,
        updated_at=row.updated_at,
    )


@router.post("/extract", response_model=ProfileResponse, summary="从对话文本抽取画像")
async def extract_profile_from_conversation(
    text: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """输入一段文本，由大模型抽取画像并保存"""
    uid = user["user_id"]
    try:
        profile = extract_profile_from_text(text)
        row = save_profile(db, uid, profile)
        return ProfileResponse(
            user_id=str(uid),
            profile=profile,
            updated_at=row.updated_at,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"画像抽取失败: {str(e)}")
