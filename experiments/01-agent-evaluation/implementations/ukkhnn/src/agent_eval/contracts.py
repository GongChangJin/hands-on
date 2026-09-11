"""Load and validate the shared JSON contracts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


SCHEMA_FILES = {
    "task_request": "task-request.schema.json",
    "agent_result": "agent-result.schema.json",
    "tool_trace": "tool-trace.schema.json",
    "evaluation_record": "evaluation-record.schema.json",
}


class ContractError(ValueError):
    """Raised when a payload does not satisfy a shared contract."""


def discover_contracts_dir(start: Path | None = None) -> Path:
    """Find ``common/contracts`` by walking toward the repository root."""

    current = (start or Path(__file__)).resolve()
    for candidate in (current, *current.parents):
        contracts_dir = candidate / "common" / "contracts"
        if contracts_dir.is_dir():
            return contracts_dir
    raise FileNotFoundError("common/contracts 디렉터리를 찾을 수 없습니다.")


class ContractRegistry:
    """Validate dictionaries against the four shared JSON Schemas."""

    def __init__(self, contracts_dir: Path | None = None) -> None:
        self.contracts_dir = contracts_dir or discover_contracts_dir()
        self._validators: dict[str, Draft202012Validator] = {}

        for contract_name, filename in SCHEMA_FILES.items():
            schema_path = self.contracts_dir / filename
            with schema_path.open(encoding="utf-8") as schema_file:
                schema = json.load(schema_file)
            Draft202012Validator.check_schema(schema)
            self._validators[contract_name] = Draft202012Validator(schema)

    def validate(self, contract_name: str, payload: dict[str, Any]) -> None:
        """Raise ``ContractError`` with readable paths for every violation."""

        try:
            validator = self._validators[contract_name]
        except KeyError as exc:
            raise KeyError(f"알 수 없는 계약입니다: {contract_name}") from exc

        errors = sorted(validator.iter_errors(payload), key=lambda error: list(error.path))
        if not errors:
            return

        messages = []
        for error in errors:
            location = ".".join(str(part) for part in error.absolute_path) or "<root>"
            messages.append(f"{location}: {error.message}")
        raise ContractError(f"{contract_name} 검증 실패: " + "; ".join(messages))
