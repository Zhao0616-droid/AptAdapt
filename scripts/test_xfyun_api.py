"""Test whether the configured XFYUN credentials can access chat and embedding APIs."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import config
from app.llm_client import SparkLLM
from app.services.embedding_client import EmbeddingClient

print("=" * 50)
print("当前配置:")
print(f"  APPID: {config.XFYUN_APPID}")
print(f"  API_KEY: {config.XFYUN_API_KEY[:6]}...")
print(f"  API_SECRET: {config.XFYUN_API_SECRET[:6]}...")
print("=" * 50)

print("\n[1] 测试 Chat API ...")
try:
    llm = SparkLLM()
    resp = llm.chat("你好，请用一句话回答：1+1等于几？")
    print(f"  Chat API 成功，返回: {resp[:80]}...")
except Exception as e:
    print(f"  Chat API 失败: {e}")

print("\n[2] 测试 Embedding API ...")
try:
    client = EmbeddingClient()
    vec = client.embed_single("计算机组成原理")
    print(f"  Embedding API 成功，向量维度: {len(vec)}")
except Exception as e:
    print(f"  Embedding API 失败: {e}")

print("\n" + "=" * 50)
print("如果 Embedding 成功但 Chat 失败，一般说明密钥存在，但该 APPID 没有开通当前 Chat 模型权限。")
print(f"当前 Chat 配置: wss://{config.XFYUN_CHAT_HOST}{config.XFYUN_CHAT_PATH}, domain={config.XFYUN_CHAT_DOMAIN}")
print("=" * 50)
