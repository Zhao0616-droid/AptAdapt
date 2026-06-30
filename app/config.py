import os
from pathlib import Path

# 自动加载项目根目录的 .env 文件（如果存在）
from dotenv import load_dotenv

_ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_ENV_PATH)


# ── 讯飞开放平台 API 密钥 ──
XFYUN_APPID = os.getenv("XFYUN_APPID", "")
XFYUN_API_KEY = os.getenv("XFYUN_API_KEY", "")
XFYUN_API_SECRET = os.getenv("XFYUN_API_SECRET", "")
XFYUN_CHAT_HOST = os.getenv("XFYUN_CHAT_HOST", "spark-api.xf-yun.com")
XFYUN_CHAT_PATH = os.getenv("XFYUN_CHAT_PATH", "/v4.0/chat")
XFYUN_CHAT_DOMAIN = os.getenv("XFYUN_CHAT_DOMAIN", "4.0Ultra")

# ── LLM Provider 配置 ──
# openai_compatible: 使用 OpenAI 兼容接口；xfyun: 使用讯飞星火 WebSocket。
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "xfyun")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
LLM_TIMEOUT_SECONDS = int(os.getenv("LLM_TIMEOUT_SECONDS", "20"))
LLM_FAILURE_COOLDOWN_SECONDS = int(os.getenv("LLM_FAILURE_COOLDOWN_SECONDS", "45"))
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.35"))
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "1200"))
SUPERVISOR_USE_LLM = os.getenv("SUPERVISOR_USE_LLM", "0") == "1"
REVIEWER_USE_LLM = os.getenv("REVIEWER_USE_LLM", "0") == "1"

# ── 讯飞 Embedding API ──
EMBEDDING_HOST = os.getenv("XFYUN_EMBEDDING_HOST", "emb-cn-huabei-1.xf-yun.com")
EMBEDDING_PATH = os.getenv("XFYUN_EMBEDDING_PATH", "/v1/embeddings")
EMBEDDING_MODEL = os.getenv("XFYUN_EMBEDDING_MODEL", "paraformer-zh")

# ── 数据库 ──
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./aptadapt.db")

# ── JWT 配置 ──
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))


# ── 启动时校验关键配置 ──
def _check_required(name: str, value: str):
    if not value:
        raise RuntimeError(f"缺少必要的环境变量: {name}。请复制 .env.example 为 .env 并填写。")


if LLM_PROVIDER == "openai_compatible":
    _check_required("OPENAI_API_KEY", OPENAI_API_KEY)
    _check_required("OPENAI_BASE_URL", OPENAI_BASE_URL)
else:
    _check_required("XFYUN_APPID", XFYUN_APPID)
    _check_required("XFYUN_API_KEY", XFYUN_API_KEY)
    _check_required("XFYUN_API_SECRET", XFYUN_API_SECRET)
_check_required("JWT_SECRET_KEY", SECRET_KEY)
