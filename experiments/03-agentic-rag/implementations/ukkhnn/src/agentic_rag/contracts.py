"""Validation helpers for the repository-level shared contracts."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


CONTRACT_NAMES = (
    "task-request",
    "agent-result",
    "tool-trace",
    "evaluation-record",
)


@lru_cache(maxsize=1)
def contracts_dir() -> Path:
    for parent in Path(__file__).resolve().parents:
        candidate = parent / "common" / "contracts"
        if candidate.is_dir():
            return candidate
    raise RuntimeError("common/contracts 디렉터리를 찾을 수 없습니다.")


@lru_cache(maxsize=None)
def contract_validator(contract_name: str) -> Draft202012Validator:
    if contract_name not in CONTRACT_NAMES:
        raise ValueError(f"알 수 없는 공통 계약입니다: {contract_name}")
    with (contracts_dir() / f"{contract_name}.schema.json").open(encoding="utf-8") as file:
        return Draft202012Validator(json.load(file))


def validate_contract(contract_name: str, value: dict[str, Any]) -> None:
    contract_validator(contract_name).validate(value)
