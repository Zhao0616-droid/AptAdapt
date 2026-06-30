"""Check XFYUN chat configuration is driven by env and points to Spark Ultra-32K."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
llm_source = (ROOT / "app" / "llm_client.py").read_text(encoding="utf-8")
config_source = (ROOT / "app" / "config.py").read_text(encoding="utf-8")
env_source = (ROOT / ".env").read_text(encoding="utf-8")


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


assert_true("XFYUN_CHAT_HOST" in config_source, "config should expose XFYUN_CHAT_HOST.")
assert_true("XFYUN_CHAT_PATH" in config_source, "config should expose XFYUN_CHAT_PATH.")
assert_true("XFYUN_CHAT_DOMAIN" in config_source, "config should expose XFYUN_CHAT_DOMAIN.")
assert_true("self.domain = XFYUN_CHAT_DOMAIN" in llm_source, "LLM client should use configured chat domain.")
assert_true('"domain": self.domain' in llm_source, "LLM payload should use configured chat domain.")
assert_true('self.Path = XFYUN_CHAT_PATH' in llm_source, "LLM client should use configured chat path.")
assert_true('"/v3.5/chat"' not in llm_source, "LLM client should not hard-code old v3.5 path.")
assert_true('"generalv3.5"' not in llm_source, "LLM client should not hard-code old generalv3.5 domain.")
assert_true("XFYUN_CHAT_PATH=/v4.0/chat" in env_source, ".env should point to Spark Ultra-32K websocket path.")
assert_true("XFYUN_CHAT_DOMAIN=4.0Ultra" in env_source, ".env should use Spark Ultra-32K domain.")

print("XFYUN chat config uses Spark Ultra-32K from environment.")
