"""Check that repeated provider failures fail fast during cooldown."""
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import app.llm_client as llm_client
from app.llm_client import SparkLLM


class FakeWebSocket:
    def send(self, payload):
        pass

    def recv(self):
        return json.dumps({"header": {"code": 11200, "message": "AppIdNoAuthError", "status": 2}})

    def close(self):
        pass


original_create_connection = llm_client.websocket.create_connection
llm_client.websocket.create_connection = lambda *args, **kwargs: FakeWebSocket()
llm_client._failure_until.clear()

try:
    llm = SparkLLM()
    first_start = time.time()
    try:
        llm.chat("ping")
    except Exception as e:
        first_error = str(e)
    first_elapsed = time.time() - first_start

    second_start = time.time()
    try:
        llm.chat("ping")
    except Exception as e:
        second_error = str(e)
    second_elapsed = time.time() - second_start

    if "11200" not in first_error:
        raise AssertionError(f"expected provider error first, got {first_error}")
    if "cooling down" not in second_error:
        raise AssertionError(f"expected cooldown error second, got {second_error}")
    if second_elapsed > 0.05:
        raise AssertionError(f"cooldown should fail fast, took {second_elapsed:.3f}s")

    print(f"LLM cooldown works: first={first_elapsed:.3f}s second={second_elapsed:.3f}s")
finally:
    llm_client.websocket.create_connection = original_create_connection
    llm_client._failure_until.clear()
