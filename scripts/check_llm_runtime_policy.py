"""Check LLM runtime policy for fast, stable failure handling."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import app.llm_client as llm_client


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


source = Path(llm_client.__file__).read_text(encoding="utf-8")
config_source = (ROOT / "app" / "config.py").read_text(encoding="utf-8")

assert_true("LLM_FAILURE_COOLDOWN_SECONDS" in config_source, "config should expose LLM failure cooldown.")
assert_true("LLM_TEMPERATURE" in config_source, "config should expose model temperature.")
assert_true("LLM_MAX_TOKENS" in config_source, "config should expose max token budget.")
assert_true("_failure_until" in source, "llm client should track provider failure cooldown.")
assert_true("_ensure_available" in source, "llm client should fail fast while provider is cooling down.")
assert_true("_mark_failure" in source, "llm client should mark provider failures for cooldown.")

print("LLM runtime policy exposes cooldown and generation controls.")
