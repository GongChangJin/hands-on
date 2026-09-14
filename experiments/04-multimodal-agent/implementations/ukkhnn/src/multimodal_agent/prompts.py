"""Versioned multimodal prompt with bounded, compact context."""

from __future__ import annotations

import json
from typing import Any


PROMPT_VERSION = "v1"

SYSTEM_PROMPT = """You analyze synthetic application UI screenshots for test evaluation.
Return one JSON object only. Use exactly these error types: layout_break, element_clipping,
invalid_state, error_message, accessibility_issue. Severity is none, low, medium, high,
or critical. Report only evidence visible in the image or explicitly stated in the compact
context. Use descriptive regions, never pixel coordinates. Do not infer hidden facts or a
CSS/root cause. Express uncertainty honestly and give a concrete UI fix. For a normal screen,
return an empty errors array and overall_severity none.

Required shape:
{"summary":"...","overall_severity":"...","errors":[{"error_type":"...","severity":"...","evidence":[{"region":"...","claim":"..."}],"uncertainty":"...","suggested_fix":"..."}]}"""


def build_prompt(condition: str, context: dict[str, Any] | None) -> str:
    if condition == "image-only":
        return f"{SYSTEM_PROMPT}\n\nInput condition: image-only. Analyze the attached screenshot."
    if condition != "image-with-context" or context is None:
        raise ValueError(f"지원하지 않거나 불완전한 입력 조건입니다: {condition}")
    compact = {
        "user_description": context["user_description"],
        "dom_summary": context["dom_summary"],
        "accessibility_snapshot": context["accessibility_snapshot"],
    }
    return (
        f"{SYSTEM_PROMPT}\n\nInput condition: image-with-context. Analyze the attached screenshot "
        "using this compact context only:\n"
        + json.dumps(compact, ensure_ascii=False, separators=(",", ":"))
    )
