"""Validation for repository contracts and research-specific schemas."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from .paths import CONTRACTS_DIR, SCHEMAS_DIR


CONTRACT_NAMES = ("task-request", "agent-result", "tool-trace", "evaluation-record")
RESEARCH_SCHEMA_NAMES = ("paper-record", "claim-evidence", "research-report", "hypothesis")


@lru_cache(maxsize=None)
def contract_validator(name: str) -> Draft202012Validator:
    if name not in CONTRACT_NAMES:
        raise ValueError(f"Unknown shared contract: {name}")
    return Draft202012Validator(json.loads((CONTRACTS_DIR / f"{name}.schema.json").read_text()))


@lru_cache(maxsize=1)
def research_registry() -> Registry:
    registry = Registry()
    for path in SCHEMAS_DIR.glob("*.schema.json"):
        document = json.loads(path.read_text())
        registry = registry.with_resource(path.name, Resource.from_contents(document))
        if document.get("$id"):
            registry = registry.with_resource(document["$id"], Resource.from_contents(document))
    return registry


@lru_cache(maxsize=None)
def research_validator(name: str) -> Draft202012Validator:
    if name not in RESEARCH_SCHEMA_NAMES:
        raise ValueError(f"Unknown research schema: {name}")
    schema = json.loads((SCHEMAS_DIR / f"{name}.schema.json").read_text())
    return Draft202012Validator(schema, registry=research_registry())


def validate_contract(name: str, value: dict[str, Any]) -> None:
    contract_validator(name).validate(value)


def validate_research(name: str, value: dict[str, Any]) -> None:
    research_validator(name).validate(value)


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return value
