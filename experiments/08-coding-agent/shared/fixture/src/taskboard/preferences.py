"""Preference merging."""

from typing import Any


def merge_preferences(defaults: dict[str, Any], overrides: dict[str, Any]) -> dict[str, Any]:
    """Merge top-level preference values."""

    return {**defaults, **overrides}
