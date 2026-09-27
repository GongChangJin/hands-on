"""Stable repository paths used by integration adapters."""

from __future__ import annotations

from pathlib import Path


INTEGRATION_DIR = Path(__file__).resolve().parents[2]
REPO_ROOT = INTEGRATION_DIR.parent
CONTRACTS_DIR = REPO_ROOT / "common" / "contracts"
EXPERIMENTS_DIR = REPO_ROOT / "experiments"


def implementation(number: str, slug: str) -> Path:
    return EXPERIMENTS_DIR / f"{number}-{slug}" / "implementations" / "ukkhnn"
