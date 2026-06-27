"""Check profile prompt rendering and agent fallback behavior for malformed LLM JSON."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agents.workers import code_agent
from agents.workers import quiz_agent
from app.services import profile_manager
from app.schemas import StudentProfile


def check_profile_prompt_handles_json_examples():
    prompt = profile_manager._render_extraction_prompt("我是大二学生，数字逻辑基础一般。")
    assert "数字逻辑" in prompt
    assert "我是大二学生" in prompt


def check_code_agent_keeps_malformed_model_output():
    raw = '{"language":"verilog","source":"module cache;\nendmodule","explanation":"demo"}'
    parsed = code_agent._parse_code_response(raw, "Cache 映射方式", [])
    assert parsed["language"] == "verilog"
    assert "module cache" in parsed["source"]


def check_quiz_agent_accepts_list_output():
    raw = '[{"type":"choice","question":"Cache 直接映射的特点是？","options":["A. 固定映射","B. 任意映射"],"answer":0,"explanation":"直接映射位置固定。","difficulty":"medium","knowledge_point":"Cache 映射"}]'
    parsed = quiz_agent._parse_quiz_response(raw, "Cache 映射", [])
    assert parsed["knowledge_point"] == "Cache 映射"
    assert parsed["question"]


def check_profile_serialization_is_json():
    profile_json = profile_manager._profile_to_json(StudentProfile(major="计算机", weak_points=["Cache 映射"]))
    assert '"major"' in profile_json
    assert "Cache 映射" in profile_json


check_profile_prompt_handles_json_examples()
check_code_agent_keeps_malformed_model_output()
check_quiz_agent_accepts_list_output()
check_profile_serialization_is_json()
print("Agent resilience checks passed.")
