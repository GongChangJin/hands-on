"""Repository paths used by the implementation."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=1)
def hands_on_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "common" / "contracts").is_dir() and (parent / "experiments").is_dir():
            return parent
    raise RuntimeError("hands-on 저장소 루트를 찾을 수 없습니다.")


def contracts_dir() -> Path:
    return hands_on_root() / "common" / "contracts"


def shared_dir() -> Path:
    return hands_on_root() / "experiments" / "02-local-llm" / "shared"


def implementation_dir() -> Path:
    return Path(__file__).resolve().parents[2]
