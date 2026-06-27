"""Check that resource generation returns usable fallback resources when LLM calls fail."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.schemas import StudentProfile
from app.services import resource_generator


def fail_llm(_: str) -> str:
    raise TimeoutError("simulated llm timeout")


resource_generator._call_llm = fail_llm

profile = StudentProfile(
    major="计算机科学与技术",
    grade="大二",
    course_goal="补齐计算机组成原理薄弱点",
    weak_points=["Cache 映射方式"],
    learning_preference=["图解", "例题"],
)

resources, review = resource_generator.generate_resources(
    knowledge_point="Cache 映射方式",
    resource_types=["doc", "mindmap", "quiz", "code", "video_script"],
    profile=profile,
    chunks=[],
)

expected_types = ["doc", "mindmap", "quiz", "code", "video_script"]
actual_types = [item.type for item in resources]

assert actual_types == expected_types, actual_types
assert all(item.content for item in resources)
assert review.notes

print("Resource generation fallback returns usable resources.")
