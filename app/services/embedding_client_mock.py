"""本地 Mock Embedding —— 无需调用讯飞 API，用于开发/演示"""
import hashlib
import re
from typing import List
import numpy as np


class MockEmbeddingClient:
    """基于词袋哈希的本地 mock 嵌入，无需联网和 API 额度"""

    DIMENSION = 384

    def embed(self, texts: List[str]) -> List[List[float]]:
        return [self._hash_embed(t) for t in texts]

    def embed_single(self, text: str) -> List[float]:
        return self._hash_embed(text)

    def _hash_embed(self, text: str) -> List[float]:
        text = text.lower().strip()
        vec = np.zeros(self.DIMENSION, dtype=np.float32)

        # 简单分词（按字符 + 2-gram）
        tokens = list(text)
        for i in range(len(text) - 1):
            tokens.append(text[i:i + 2])

        for token in tokens:
            idx = int(hashlib.md5(token.encode()).hexdigest(), 16) % self.DIMENSION
            vec[idx] += 1.0

        # L2 归一化
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm

        return vec.tolist()


# 兼容 EmbeddingClient 的接口名
EmbeddingClient = MockEmbeddingClient
