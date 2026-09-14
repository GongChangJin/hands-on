"""Validation helpers for the four shared hands-on contracts."""

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
    """Find the repository-level common/contracts directory."""

    for parent in Path(__file__).resolve().parents:
        candidate = parent / "common" / "contracts"
        if candidate.is_dir():
            return candidate
    raise RuntimeError("common/contracts 디렉터리를 찾을 수 없습니다.")


@lru_cache(maxsize=None)
def contract_validator(contract_name: str) -> Draft202012Validator:
    if contract_name not in CONTRACT_NAMES:
        raise ValueError(f"알 수 없는 공통 계약입니다: {contract_name}")
    schema_path = contracts_dir() / f"{contract_name}.schema.json"
    with schema_path.open(encoding="utf-8") as schema_file:
        schema = json.load(schema_file)
    return Draft202012Validator(schema)


def validate_contract(contract_name: str, value: dict[str, Any]) -> None:
    """Raise jsonschema.ValidationError when a shared contract is invalid."""

    contract_validator(contract_name).validate(value)


def task_request_from_example(example: dict[str, Any]) -> dict[str, Any]:
    """Adapt one Phoenix dataset example to the shared TaskRequest contract."""

    expected = example["output"]
    task = {
        "task_id": example["metadata"]["case_id"],
        "task_type": "evaluation",
        "input": example["input"],
        "constraints": {
            "allowed_tools": expected["required_tools"],
            "forbidden_actions": ["도구 결과 추측", "허용되지 않은 도구 호출"],
            "max_steps": 8,
            "max_tool_calls": len(expected["required_tools"]),
        },
        "expected_output": expected,
        "metadata": example["metadata"],
    }
    validate_contract("task-request", task)
    return task
