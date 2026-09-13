"""Strict model JSON parsing with no silent repair of invalid output."""

from __future__ import annotations

import json
from typing import Any

from jsonschema import ValidationError

from .contracts import validate_analysis


class OutputParseError(ValueError):
    pass


def parse_analysis(content: str) -> dict[str, Any]:
    value = content.strip()
    if value.startswith("```json") and value.endswith("```"):
        value = value[7:-3].strip()
    elif value.startswith("```") and value.endswith("```"):
        value = value[3:-3].strip()
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        raise OutputParseError(f"모델 JSON parsing 실패: {exc.msg}") from exc
    if not isinstance(parsed, dict):
        raise OutputParseError("모델 결과는 JSON object여야 합니다.")
    try:
        validate_analysis(parsed)
    except (ValidationError, ValueError) as exc:
        raise OutputParseError(f"모델 결과 schema 불일치: {exc.message if isinstance(exc, ValidationError) else exc}") from exc
    return parsed
