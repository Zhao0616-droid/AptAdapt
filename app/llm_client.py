"""LLM client facade.

The project historically called this class SparkLLM. Keep that public name so
existing agents do not need to know which provider is configured underneath.
"""
import base64
import hashlib
import hmac
import json
import ssl
import time
from typing import Generator
from urllib.parse import urlencode

import requests
import websocket

from .config import (
    LLM_PROVIDER,
    OPENAI_API_KEY,
    OPENAI_BASE_URL,
    OPENAI_MODEL,
    LLM_TIMEOUT_SECONDS,
    LLM_FAILURE_COOLDOWN_SECONDS,
    LLM_TEMPERATURE,
    LLM_MAX_TOKENS,
    XFYUN_APPID,
    XFYUN_API_KEY,
    XFYUN_API_SECRET,
    XFYUN_CHAT_HOST,
    XFYUN_CHAT_PATH,
    XFYUN_CHAT_DOMAIN,
)

SYSTEM_PROMPT = "你是一个专业的计算机课程助教，请用通俗易懂的语言回答学生的问题。"

_failure_until: dict[str, float] = {}


class LLMProviderError(RuntimeError):
    """Raised when the configured LLM provider returns an explicit failure."""


class SparkLLM:
    """Unified LLM client used by all agents.

    Provider selection:
    - LLM_PROVIDER=openai_compatible: OpenAI-compatible chat completions API.
    - LLM_PROVIDER=xfyun: XFYUN Spark WebSocket API.
    """

    def __init__(self):
        self.provider = LLM_PROVIDER
        self.openai_api_key = OPENAI_API_KEY
        self.openai_base_url = OPENAI_BASE_URL.rstrip("/")
        self.openai_model = OPENAI_MODEL
        self.timeout = LLM_TIMEOUT_SECONDS
        self.failure_cooldown = LLM_FAILURE_COOLDOWN_SECONDS
        self.temperature = LLM_TEMPERATURE
        self.max_tokens = LLM_MAX_TOKENS

        self.APPID = XFYUN_APPID
        self.API_KEY = XFYUN_API_KEY
        self.API_SECRET = XFYUN_API_SECRET
        self.Host = XFYUN_CHAT_HOST
        self.Path = XFYUN_CHAT_PATH
        self.domain = XFYUN_CHAT_DOMAIN
        self.URL = f"wss://{self.Host}{self.Path}"

    def chat(self, message: str) -> str:
        """Return one complete response."""
        self._ensure_available()
        if self.provider == "openai_compatible":
            return self._with_failure_tracking(self._chat_openai_compatible, message)
        return self._with_failure_tracking(self._chat_xfyun, message)

    def chat_stream(self, message: str) -> Generator[str, None, None]:
        """Yield response chunks."""
        try:
            self._ensure_available()
        except Exception as e:
            yield f"[错误] {e}"
            return
        if self.provider == "openai_compatible":
            yield from self._chat_stream_openai_compatible(message)
            return
        yield from self._chat_stream_xfyun(message)

    def _ensure_available(self) -> None:
        until = _failure_until.get(self.provider, 0)
        remaining = int(until - time.time())
        if remaining > 0:
            raise LLMProviderError(f"{self.provider} is cooling down after a recent failure; retry in {remaining}s")

    def _mark_failure(self) -> None:
        if self.failure_cooldown > 0:
            _failure_until[self.provider] = time.time() + self.failure_cooldown

    def _with_failure_tracking(self, fn, message: str) -> str:
        try:
            return fn(message)
        except Exception:
            self._mark_failure()
            raise

    def _chat_openai_compatible(self, message: str) -> str:
        url = f"{self.openai_base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.openai_api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.openai_model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": message},
            ],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        resp = requests.post(url, headers=headers, json=payload, timeout=self.timeout)
        resp.raise_for_status()
        data = resp.json()
        content = data["choices"][0]["message"]["content"]
        if not content.strip():
            raise LLMProviderError("OpenAI-compatible provider returned empty response")
        return content

    def _chat_stream_openai_compatible(self, message: str) -> Generator[str, None, None]:
        url = f"{self.openai_base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.openai_api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.openai_model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": message},
            ],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stream": True,
        }
        emitted = False
        try:
            with requests.post(url, headers=headers, json=payload, stream=True, timeout=self.timeout) as resp:
                resp.raise_for_status()
                for raw_line in resp.iter_lines(decode_unicode=True):
                    if not raw_line or not raw_line.startswith("data:"):
                        continue
                    line = raw_line.removeprefix("data:").strip()
                    if line == "[DONE]":
                        break
                    try:
                        data = json.loads(line)
                        delta = data["choices"][0].get("delta", {})
                        content = delta.get("content")
                        if content:
                            emitted = True
                            yield content
                    except Exception:
                        continue
        except Exception as e:
            self._mark_failure()
            yield f"[错误] {e}"
            emitted = True
        if not emitted:
            yield "[错误] OpenAI-compatible provider returned empty response"

    def _build_url(self) -> str:
        now = time.time()
        date = time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime(now))

        signature_origin = f"host: {self.Host}\ndate: {date}\nGET {self.Path} HTTP/1.1"
        signature_sha = hmac.new(
            self.API_SECRET.encode("utf-8"),
            signature_origin.encode("utf-8"),
            hashlib.sha256,
        ).digest()
        signature = base64.b64encode(signature_sha).decode()

        authorization_origin = (
            f'api_key="{self.API_KEY}", '
            f'algorithm="hmac-sha256", '
            f'headers="host date request-line", '
            f'signature="{signature}"'
        )
        authorization = base64.b64encode(authorization_origin.encode("utf-8")).decode()

        params = {"authorization": authorization, "date": date, "host": self.Host}
        return self.URL + "?" + urlencode(params)

    def _build_payload(self, message: str) -> dict:
        return {
            "header": {"app_id": self.APPID, "uid": "user_123"},
            "parameter": {
                "chat": {
                    "domain": self.domain,
                    "temperature": self.temperature,
                    "max_tokens": self.max_tokens,
                }
            },
            "payload": {
                "message": {
                    "text": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": message},
                    ]
                }
            },
        }

    def _validate_xfyun_frame(self, res: dict) -> None:
        header = res.get("header", {})
        code = header.get("code")
        if code not in (0, None):
            message = header.get("message") or "unknown error"
            sid = header.get("sid")
            sid_text = f", sid={sid}" if sid else ""
            raise LLMProviderError(f"XFYUN error {code}: {message}{sid_text}")

    def _chat_xfyun(self, message: str) -> str:
        url = self._build_url()
        ws = websocket.create_connection(
            url,
            timeout=self.timeout,
            sslopt={"cert_reqs": ssl.CERT_NONE},
        )
        ws.send(json.dumps(self._build_payload(message), ensure_ascii=False))

        full_response = ""
        try:
            while True:
                res = json.loads(ws.recv())
                self._validate_xfyun_frame(res)
                choices = res.get("payload", {}).get("choices", {})
                text = choices.get("text", [])
                if text and "content" in text[0]:
                    full_response += text[0]["content"]
                if res.get("header", {}).get("status") == 2:
                    break
        finally:
            ws.close()

        if not full_response.strip():
            raise LLMProviderError("XFYUN returned empty response")
        return full_response

    def _chat_stream_xfyun(self, message: str) -> Generator[str, None, None]:
        url = self._build_url()
        ws = websocket.create_connection(
            url,
            timeout=self.timeout,
            sslopt={"cert_reqs": ssl.CERT_NONE},
        )
        ws.send(json.dumps(self._build_payload(message), ensure_ascii=False))

        emitted = False
        try:
            while True:
                res = json.loads(ws.recv())
                self._validate_xfyun_frame(res)
                choices = res.get("payload", {}).get("choices", {})
                text = choices.get("text", [])
                if text and "content" in text[0]:
                    emitted = True
                    yield text[0]["content"]
                if res.get("header", {}).get("status") == 2:
                    break
        except Exception as e:
            self._mark_failure()
            yield f"[错误] {e}"
            emitted = True
        finally:
            ws.close()

        if not emitted:
            yield "[错误] XFYUN returned empty response"
