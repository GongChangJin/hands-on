"""Validation helpers for repository-level shared contracts."""

from __future__ import annotations

import json
from functools import lru_cache
from typing import Any

from jsonschema import Draft202012Validator

from .paths import contracts_dir


CONTRACT_NAMES = {
    "task-request",
    "agent-result",
    "tool-trace",
    "evaluation-record",
}


@lru_cache(maxsize=None)
def contract_validator(name: str) -> Draft202012Validator:
    if name not in CONTRACT_NAMES:
        raise ValueError(f"알 수 없는 공통 계약입니다: {name}")
    path = contracts_dir() / f"{name}.schema.json"
    return Draft202012Validator(json.loads(path.read_text(encoding="utf-8")))


def validate_contract(name: str, value: dict[str, Any]) -> None:
    contract_validator(name).validate(value)


def validate_output(schema: dict[str, Any], value: Any) -> list[str]:
    errors = sorted(Draft202012Validator(schema).iter_errors(value), key=lambda item: list(item.path))
    return [error.message for error in errors]
