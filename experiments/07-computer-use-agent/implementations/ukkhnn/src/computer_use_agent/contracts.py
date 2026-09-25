"""Validation for the repository shared contracts."""

from __future__ import annotations

import json
from functools import lru_cache

from jsonschema import Draft202012Validator

from .io import repo_root


@lru_cache(maxsize=None)
def validator(name: str) -> Draft202012Validator:
    path = repo_root() / "common" / "contracts" / f"{name}.schema.json"
    return Draft202012Validator(json.loads(path.read_text(encoding="utf-8")))


def validate(name: str, value: dict) -> None:
    validator(name).validate(value)
