"""Validation against the repository-wide contracts."""

from __future__ import annotations

import json
from functools import cache

from jsonschema import Draft202012Validator

from .io import repo_root


@cache
def validator(name: str) -> Draft202012Validator:
    path = repo_root() / "common" / "contracts" / f"{name}.schema.json"
    return Draft202012Validator(json.loads(path.read_text(encoding="utf-8")))


def validate(name: str, value: dict) -> None:
    validator(name).validate(value)
