"""Validate the four repository contracts and the multimodal model payload."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from .paths import REPOSITORY_DIR


CONTRACT_NAMES = ("task-request", "agent-result", "tool-trace", "evaluation-record")
ERROR_TYPES = ("layout_break", "element_clipping", "invalid_state", "error_message", "accessibility_issue")
SEVERITIES = ("none", "low", "medium", "high", "critical")

ANALYSIS_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "additionalProperties": False,
    "required": ["summary", "overall_severity", "errors"],
    "properties": {
        "summary": {"type": "string", "minLength": 1, "maxLength": 600},
        "overall_severity": {"type": "string", "enum": list(SEVERITIES)},
        "errors": {
            "type": "array",
            "maxItems": 8,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["error_type", "severity", "evidence", "uncertainty", "suggested_fix"],
                "properties": {
                    "error_type": {"type": "string", "enum": list(ERROR_TYPES)},
                    "severity": {"type": "string", "enum": list(SEVERITIES[1:])},
                    "evidence": {
                        "type": "array",
                        "minItems": 1,
                        "maxItems": 4,
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": ["region", "claim"],
                            "properties": {
                                "region": {"type": "string", "minLength": 1, "maxLength": 160},
                                "claim": {"type": "string", "minLength": 1, "maxLength": 500},
                            },
                        },
                    },
                    "uncertainty": {"type": "string", "minLength": 1, "maxLength": 500},
                    "suggested_fix": {"type": "string", "minLength": 1, "maxLength": 500},
                },
            },
        },
    },
}


@lru_cache(maxsize=None)
def contract_validator(name: str) -> Draft202012Validator:
    if name not in CONTRACT_NAMES:
        raise ValueError(f"알 수 없는 공통 계약입니다: {name}")
    path = REPOSITORY_DIR / "common" / "contracts" / f"{name}.schema.json"
    return Draft202012Validator(json.loads(path.read_text(encoding="utf-8")))


def validate_contract(name: str, value: dict[str, Any]) -> None:
    contract_validator(name).validate(value)


def validate_analysis(value: dict[str, Any]) -> None:
    Draft202012Validator(ANALYSIS_SCHEMA).validate(value)
    if not value["errors"] and value["overall_severity"] != "none":
        raise ValueError("정상 화면의 overall_severity는 none이어야 합니다.")
    if value["errors"] and value["overall_severity"] == "none":
        raise ValueError("오류가 있으면 overall_severity는 none일 수 없습니다.")
