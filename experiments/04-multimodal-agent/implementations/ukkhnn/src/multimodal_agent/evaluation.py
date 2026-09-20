"""Load paired tasks and retain every evaluation outcome."""

from __future__ import annotations

import json
from copy import deepcopy
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


def load_adaptive_tasks(
    path: Path,
    *,
    limit: int | None = None,
) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    image_only = load_tasks(path, condition="image-only")
    with_context = load_tasks(path, condition="image-with-context")
    context_by_fixture = {
        task["expected_output"]["fixture_id"]: task for task in with_context
    }
    pairs = [
        (task, context_by_fixture[task["expected_output"]["fixture_id"]])
        for task in image_only
    ]
    if limit is not None:
        if limit < 1:
            raise ValueError("--limit은 1 이상이어야 합니다.")
        pairs = pairs[:limit]
    return pairs


def needs_context_retry(outcome: Any) -> bool:
    result = outcome.agent_result
    if result.get("status") != "success" or not isinstance(result.get("output"), dict):
        return True
    errors = result["output"].get("errors") or []
    if not errors:
        return True
    context_sensitive = {"accessibility_issue", "invalid_state"}
    return any(error.get("error_type") in context_sensitive for error in errors)


def _adaptive_record(first: Any, second: Any | None) -> dict[str, Any]:
    selected = second or first
    record = deepcopy(selected.evaluation_record)
    fixture_id = record["task_id"].split("-image-")[0]
    record["task_id"] = f"{fixture_id}-adaptive-context"
    record["implementation_id"] = record["implementation_id"].rsplit(":", 1)[0] + ":adaptive-context"
    metadata = record["metadata"]
    metadata["condition"] = "adaptive-context"
    metadata["adaptive"] = {
        "context_retried": second is not None,
        "selected_phase": "image-with-context" if second is not None else "image-only",
    }
    metadata["agent_result"]["task_id"] = record["task_id"]
    metadata["agent_result"]["metadata"]["condition"] = "adaptive-context"
    if second is not None:
        record["latency_ms"] = first.evaluation_record["latency_ms"] + second.evaluation_record["latency_ms"]
        record["usage"] = {
            key: int(first.evaluation_record["usage"].get(key, 0)) + int(second.evaluation_record["usage"].get(key, 0))
            for key in ("requests", "input_tokens", "output_tokens", "cached_input_tokens", "total_tokens")
        }
        first_cost = first.evaluation_record.get("cost")
        second_cost = second.evaluation_record.get("cost")
        record["cost"] = (
            float(first_cost or 0) + float(second_cost or 0)
            if first_cost is not None or second_cost is not None
            else None
        )
        record["safety_violations"] = list(
            dict.fromkeys(
                [
                    *first.evaluation_record.get("safety_violations", []),
                    *second.evaluation_record.get("safety_violations", []),
                ]
            )
        )
        metadata["tool_traces"] = [
            *first.evaluation_record["metadata"].get("tool_traces", []),
            *second.evaluation_record["metadata"].get("tool_traces", []),
        ]
    validate_contract("evaluation-record", record)
    return record


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


async def run_adaptive_evaluation(
    agent: MultimodalAgent,
    tasks: list[tuple[dict[str, Any], dict[str, Any]]],
    *,
    output: Path,
) -> dict[str, Any]:
    records = []
    for image_only_task, context_task in tasks:
        first = await agent.run(image_only_task)
        second = await agent.run(context_task) if needs_context_retry(first) else None
        records.append(_adaptive_record(first, second))
    summary = summarize(records, condition="adaptive-context", model=agent.gateway.model_name)
    summary["context_retry_count"] = sum(
        bool(record["metadata"]["adaptive"]["context_retried"]) for record in records
    )
    summary["context_retry_rate"] = summary["context_retry_count"] / len(records) if records else 0.0
    export_results(records, summary, output)
    return summary
