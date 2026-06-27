"""Check profile prompt rendering and agent fallback behavior for malformed LLM JSON."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agents.workers import code_agent
from app.services import profile_manager


def check_profile_prompt_handles_json_examples():
    prompt = profile_manager._render_extraction_prompt("我是大二学生，数字逻辑基础一般。")
    assert "数字逻辑" in prompt
    assert "我是大二学生" in prompt


def check_code_agent_keeps_malformed_model_output():
    raw = '{"language":"verilog","source":"module cache;\nendmodule","explanation":"demo"}'
    parsed = code_agent._parse_code_response(raw, "Cache 映射方式", [])
    assert parsed["language"] == "verilog"
    assert "module cache" in parsed["source"]


check_profile_prompt_handles_json_examples()
check_code_agent_keeps_malformed_model_output()
print("Agent resilience checks passed.")
