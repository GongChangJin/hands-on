"""Load paired tasks and retain every evaluation outcome."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .contracts import validate_contract
from .reporting import export_results, summarize
from .workflow import MultimodalAgent


def load_tasks(path: Path, *, condition: str, limit: int | None = None) -> list[dict[str, Any]]:
    tasks = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
    selected = []
    for task in tasks:
        validate_contract("task-request", task)
        if task["input"].get("condition") == condition:
            selected.append(task)
    if limit is not None:
        if limit < 1:
            raise ValueError("--limit은 1 이상이어야 합니다.")
        selected = selected[:limit]
    if not selected:
        raise ValueError(f"{condition} 조건의 평가 task가 없습니다.")
    return selected


async def run_evaluation(
    agent: MultimodalAgent,
    tasks: list[dict[str, Any]],
    *,
    output: Path,
    condition: str,
) -> dict[str, Any]:
    records = []
    for task in tasks:
        outcome = await agent.run(task)
        records.append(outcome.evaluation_record)
    summary = summarize(records, condition=condition, model=agent.gateway.model_name)
    export_results(records, summary, output)
    return summary
