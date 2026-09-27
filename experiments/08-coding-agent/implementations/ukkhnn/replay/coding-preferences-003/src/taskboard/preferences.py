"""Preference merging."""

from copy import deepcopy
from typing import Any


def merge_preferences(defaults: dict[str, Any], overrides: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge preferences without sharing mutable input values."""

    merged = deepcopy(defaults)
    for key, value in overrides.items():
        if isinstance(merged.get(key), dict) and isinstance(value, dict):
            merged[key] = merge_preferences(merged[key], value)
        else:
            merged[key] = deepcopy(value)
    return merged
