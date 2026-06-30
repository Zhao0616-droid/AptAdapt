"""Check that LLM client surfaces provider errors instead of returning empty success."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import app.llm_client as llm_client
from app.llm_client import SparkLLM


class FakeWebSocket:
    def __init__(self, frames):
        self.frames = list(frames)
        self.sent_payload = None
        self.closed = False

    def send(self, payload):
        self.sent_payload = payload

    def recv(self):
        if not self.frames:
            raise RuntimeError("no more frames")
        return json.dumps(self.frames.pop(0), ensure_ascii=False)

    def close(self):
        self.closed = True


def run_case(name, frames, expected_text):
    original_create_connection = llm_client.websocket.create_connection
    fake_ws = FakeWebSocket(frames)
    llm_client.websocket.create_connection = lambda *args, **kwargs: fake_ws
    llm_client._failure_until.clear()
    try:
        try:
            SparkLLM().chat("ping")
        except RuntimeError as exc:
            message = str(exc)
            if expected_text not in message:
                raise AssertionError(f"{name}: expected {expected_text!r} in {message!r}")
            print(f"[pass] {name}: {message}")
            return
        raise AssertionError(f"{name}: expected RuntimeError, got success")
    finally:
        llm_client.websocket.create_connection = original_create_connection
        llm_client._failure_until.clear()


def main():
    run_case(
        "xfyun error code",
        [{"header": {"code": 11200, "message": "AppIdNoAuthError", "status": 2}}],
        "11200",
    )
    run_case(
        "xfyun empty final response",
        [{"header": {"code": 0, "message": "success", "status": 2}}],
        "empty response",
    )


if __name__ == "__main__":
    main()
