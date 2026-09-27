"""Repository paths and JSON loading helpers."""

from __future__ import annotations

import json
from pathlib import Path

from .models import BrowserPolicy, ComputerTask


def implementation_dir() -> Path:
    return Path(__file__).resolve().parents[2]


def experiment_dir() -> Path:
    return implementation_dir().parents[1]


def repo_root() -> Path:
    return implementation_dir().parents[3]


def shared_dir() -> Path:
    return experiment_dir() / "shared"


def load_policy(path: Path | None = None) -> BrowserPolicy:
    target = path or shared_dir() / "policy.json"
    return BrowserPolicy.model_validate_json(target.read_text(encoding="utf-8"))


def load_tasks(path: Path | None = None) -> list[ComputerTask]:
    target = path or shared_dir() / "tasks.jsonl"
    tasks: list[ComputerTask] = []
    for line_number, line in enumerate(target.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            tasks.append(ComputerTask.model_validate_json(line))
        except Exception as error:
            raise ValueError(f"{target}:{line_number}: {error}") from error
    ids = [task.task_id for task in tasks]
    if len(ids) != len(set(ids)):
        raise ValueError("task_id must be unique")
    return tasks


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_jsonl(path: Path, values: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(value, ensure_ascii=False) + "\n" for value in values), encoding="utf-8")
