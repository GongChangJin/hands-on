"""Repository paths and JSON helpers."""

from __future__ import annotations

import json
from pathlib import Path

from .models import ExpectedFinding, SecurityPolicy


def implementation_dir() -> Path:
    return Path(__file__).resolve().parents[2]


def experiment_dir() -> Path:
    return implementation_dir().parents[1]


def repo_root() -> Path:
    return implementation_dir().parents[3]


def shared_dir() -> Path:
    return experiment_dir() / "shared"


def load_policy(path: Path | None = None) -> SecurityPolicy:
    target = path or shared_dir() / "policy.json"
    return SecurityPolicy.model_validate_json(target.read_text(encoding="utf-8"))


def load_expected() -> tuple[list[ExpectedFinding], list[dict]]:
    payload = json.loads((shared_dir() / "expected-findings.json").read_text(encoding="utf-8"))
    return [ExpectedFinding.model_validate(item) for item in payload["vulnerabilities"]], payload["clean_controls"]


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_jsonl(path: Path, values: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(value, ensure_ascii=False) + "\n" for value in values), encoding="utf-8")
