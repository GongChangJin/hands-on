"""Versioned multimodal prompt with bounded, compact context."""

from __future__ import annotations

import json
from typing import Any


PROMPT_VERSION = "v2"

SYSTEM_PROMPT = """You analyze synthetic application UI screenshots for test evaluation.
Return one JSON object only. Use exactly these error types: layout_break, element_clipping,
invalid_state, error_message, accessibility_issue. Severity is none, low, medium, high,
or critical. Report only evidence visible in the image or explicitly stated in the compact
context. Use descriptive regions, never pixel coordinates. Do not infer hidden facts or a
CSS/root cause. Express uncertainty honestly and give a concrete UI fix. For a normal screen,
return an empty errors array and overall_severity none.

Classification rules:
- layout_break: layout geometry overlaps, collides, overflows the viewport, or compresses columns.
- element_clipping: meaningful text or a control is visibly cut off by its container or viewport.
- invalid_state: the UI shows contradictory, impossible, or unusable state.
- error_message: visible copy explicitly reports failure, timeout, invalid input, or another error.
- accessibility_issue: direct visual or compact-context evidence shows an accessibility barrier.
Report every independently supported type. Do not add accessibility_issue merely because a layout
looks crowded. A clipped error message is both element_clipping and error_message; a filled field
that is marked required is both invalid_state and error_message.

Severity calibration: critical is reserved for financial, destructive, security, or system-wide
risk; high means a primary task is blocked or seriously impaired; medium means material but
recoverable friction or ambiguity; low means minor friction with a viable workaround. Use the
overall severity of the most severe supported finding. Copy concrete visible or contextual wording
into evidence claims so the finding is auditable.

Required shape:
{"summary":"...","overall_severity":"...","errors":[{"error_type":"...","severity":"...","evidence":[{"region":"...","claim":"..."}],"uncertainty":"...","suggested_fix":"..."}]}"""


def build_prompt(condition: str, context: dict[str, Any] | None) -> str:
    if condition == "image-only":
        return f"{SYSTEM_PROMPT}\n\nInput condition: image-only. Analyze the attached screenshot."
    if condition not in {"image-with-context", "adaptive-context"} or context is None:
        raise ValueError(f"지원하지 않거나 불완전한 입력 조건입니다: {condition}")
    compact = {
        "user_description": context["user_description"],
        "dom_summary": context["dom_summary"],
        "accessibility_snapshot": context["accessibility_snapshot"],
    }
    return (
        f"{SYSTEM_PROMPT}\n\nInput condition: {condition}. Analyze the attached screenshot "
        "using this compact context only:\n"
        + json.dumps(compact, ensure_ascii=False, separators=(",", ":"))
    )
