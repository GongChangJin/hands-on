"""Repository path and JSON loading helpers."""

from __future__ import annotations

import json
from pathlib import Path

from .models import DatasetCase, ProjectMetrics, RouterPolicy


def implementation_dir() -> Path:
    return Path(__file__).resolve().parents[2]


def experiment_dir() -> Path:
    return implementation_dir().parents[1]


def shared_dir() -> Path:
    return experiment_dir() / "shared"


def load_policy(path: Path | None = None) -> RouterPolicy:
    target = path or shared_dir() / "routing-policy.json"
    return RouterPolicy.model_validate_json(target.read_text(encoding="utf-8"))


def load_metrics(path: Path | None = None) -> ProjectMetrics:
    target = path or shared_dir() / "project-metrics.json"
    return ProjectMetrics.model_validate_json(target.read_text(encoding="utf-8"))


def load_dataset(path: Path | None = None) -> list[DatasetCase]:
    target = path or shared_dir() / "task-requests.jsonl"
    cases: list[DatasetCase] = []
    for line_number, line in enumerate(target.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            cases.append(DatasetCase.model_validate_json(line))
        except Exception as error:
            raise ValueError(f"{target}:{line_number}: {error}") from error
    ids = [case.task_id for case in cases]
    if len(ids) != len(set(ids)):
        raise ValueError("task_id must be unique")
    return cases


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")
