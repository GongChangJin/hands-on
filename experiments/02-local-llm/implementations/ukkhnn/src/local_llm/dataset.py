"""Load and validate the fixed evaluation dataset."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

from .contracts import validate_contract
from .paths import shared_dir


def default_dataset_path() -> Path:
    return shared_dir() / "evals" / "tasks.jsonl"


def load_dataset(path: Path | None = None) -> list[dict[str, Any]]:
    source = path or default_dataset_path()
    tasks: list[dict[str, Any]] = []
    for line_number, line in enumerate(source.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            task = json.loads(line)
        except json.JSONDecodeError as error:
            raise ValueError(f"{source}:{line_number}: 잘못된 JSON") from error
        validate_contract("task-request", task)
        if task["task_type"] != "local_llm":
            raise ValueError(f"{task['task_id']}: task_type은 local_llm이어야 합니다.")
        tasks.append(task)
    ids = [task["task_id"] for task in tasks]
    if len(ids) != len(set(ids)):
        raise ValueError("평가 데이터에 중복 task_id가 있습니다.")
    return tasks


def iter_categories(tasks: Iterable[dict[str, Any]]) -> set[str]:
    return {str(task.get("metadata", {}).get("category", "unknown")) for task in tasks}
