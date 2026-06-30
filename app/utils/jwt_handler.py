"""JWT 签发与验证"""
from datetime import datetime, timedelta

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt

from ..config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

security = HTTPBearer()
DEMO_TOKEN = "demo-token"
DEMO_USER_ID = 1
DEMO_USERNAME = "demo_user"


def create_access_token(user_id: int, username: str) -> str:
    """签发 JWT，payload 含 user_id + username"""
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "username": username,
        "exp": expire,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str) -> dict | None:
    """验证 JWT，返回 payload dict（含 sub/user_id, username），失败返回 None"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("sub") is None:
            return None
        return payload
    except JWTError:
        return None


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    FastAPI 依赖：从 Authorization header 提取并验证 JWT，
    返回 {"user_id": int, "username": str}，鉴权失败抛 401。
    用法: user = Depends(get_current_user)
    """
    if credentials.credentials == DEMO_TOKEN:
        return {
            "user_id": DEMO_USER_ID,
            "username": DEMO_USERNAME,
        }

    payload = verify_token(credentials.credentials)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的访问令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {
        "user_id": int(payload["sub"]),
        "username": payload.get("username", ""),
    }
