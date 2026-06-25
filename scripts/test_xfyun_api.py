"""测试讯飞 API 密钥是否有效"""
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

# 测试 Chat API
print("\n[1] 测试 Chat API ...")
try:
    llm = SparkLLM()
    resp = llm.chat("你好")
    print(f"  Chat API 成功，返回: {resp[:50]}...")
except Exception as e:
    print(f"  Chat API 失败: {e}")

# 测试 Embedding API
print("\n[2] 测试 Embedding API ...")
try:
    client = EmbeddingClient()
    vec = client.embed_single("计算机组成原理")
    print(f"  Embedding API 成功，向量维度: {len(vec)}")
except Exception as e:
    print(f"  Embedding API 失败: {e}")

print("\n" + "=" * 50)
print("如果 Embedding API 失败但 Chat API 成功，说明密钥没错，")
print("但 Embedding API 没有开通权限或服务未授权。")
print("=" * 50)
