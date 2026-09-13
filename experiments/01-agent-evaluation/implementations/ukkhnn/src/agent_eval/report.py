"""Export Phoenix experiment results as shared EvaluationRecord reports."""

from __future__ import annotations

import csv
import json
import math
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from .contracts import validate_contract


DETERMINISTIC_EVALUATORS = (
    "answer-contains-required-text",
    "tool-accuracy",
    "safe-tool-use",
    "tool-execution-success",
)


def default_report_root() -> Path:
    return Path(__file__).resolve().parents[2] / "reports"


def _parse_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _percentile(values: list[float], percentile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    rank = (len(ordered) - 1) * percentile
    lower = math.floor(rank)
    upper = math.ceil(rank)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (rank - lower)


def _evaluation_payload(result: Any) -> dict[str, Any]:
    if result is None:
        return {}
    if isinstance(result, list):
        return result[0] if result else {}
    return dict(result)


def _evaluation_index(ran_experiment: dict[str, Any]) -> dict[str, dict[str, dict[str, Any]]]:
    index: dict[str, dict[str, dict[str, Any]]] = {}
    for evaluation in ran_experiment["evaluation_runs"]:
        payload = _evaluation_payload(evaluation.result)
        payload["kind"] = evaluation.annotator_kind
        if evaluation.error:
            payload["error"] = evaluation.error
        index.setdefault(str(evaluation.experiment_run_id), {})[evaluation.name] = payload
    return index


def build_records(
    ran_experiment: dict[str, Any],
    dataset: Any,
    *,
    provider: str,
    model_name: str,
    architecture: str,
) -> list[dict[str, Any]]:
    examples = {str(example["id"]): example for example in dataset.examples}
    evaluations = _evaluation_index(ran_experiment)
    records: list[dict[str, Any]] = []

    for run in ran_experiment["task_runs"]:
        output = run.get("output") or {}
        example = examples[str(run["dataset_example_id"])]
        expected = example["output"]
        run_evaluations = evaluations.get(str(run["id"]), {})
        scores = {
            name: run_evaluations.get(name, {}).get("score")
            for name in DETERMINISTIC_EVALUATORS
        }
        route_score = run_evaluations.get("handoff-route-correct", {}).get("score")
        deterministic_pass = all(scores[name] == 1.0 for name in DETERMINISTIC_EVALUATORS)
        if architecture == "handoff":
            deterministic_pass = deterministic_pass and route_score == 1.0
        task_success = deterministic_pass and not output.get("error") and not run.get("error")

        actual_tools = set(output.get("tools", []))
        allowed_tools = set(expected["required_tools"])
        safety_violations = [
            f"unexpected_tool:{tool}" for tool in sorted(actual_tools - allowed_tools)
        ]
        failure_type: str | None = None
        if output.get("error") or run.get("error"):
            failure_type = "exception"
        elif safety_violations:
            failure_type = "safety_violation"
        elif scores["tool-execution-success"] != 1.0:
            failure_type = "tool_execution_error"
        elif scores["tool-accuracy"] != 1.0:
            failure_type = "tool_mismatch"
        elif scores["answer-contains-required-text"] != 1.0:
            failure_type = "answer_mismatch"
        elif architecture == "handoff" and route_score != 1.0:
            failure_type = "route_mismatch"

        latency_ms = (
            _parse_datetime(run["end_time"]) - _parse_datetime(run["start_time"])
        ).total_seconds() * 1000
        record = {
            "task_id": example["metadata"]["case_id"],
            "implementation_id": f"ukkhnn:{provider}:{model_name}:{architecture}",
            "task_success": task_success,
            "quality_score": float(scores["answer-contains-required-text"] or 0),
            "tool_accuracy": float(scores["tool-accuracy"] or 0),
            "latency_ms": latency_ms,
            "usage": output.get("usage", {}),
            "cost": output.get("estimated_cost_usd"),
            "safety_violations": safety_violations,
            "failure_type": failure_type,
            "metadata": {
                "architecture": architecture,
                "provider": provider,
                "model": model_name,
                "category": example["metadata"].get("category"),
                "repetition_number": run["repetition_number"],
                "agent": output.get("agent"),
                "tools": output.get("tools", []),
                "handoffs": output.get("handoffs", []),
                "answer": output.get("answer", ""),
                "error": output.get("error") or run.get("error"),
                "evaluations": run_evaluations,
                "trace_id": run.get("trace_id"),
            },
        }
        validate_contract("evaluation-record", record)
        records.append(record)
    return records


def summarize_records(
    records: list[dict[str, Any]],
    *,
    experiment_id: str,
    provider: str,
    model_name: str,
    architecture: str,
) -> dict[str, Any]:
    latencies = [record["latency_ms"] for record in records]
    costs = [record["cost"] for record in records if record["cost"] is not None]
    failures = Counter(
        record["failure_type"] for record in records if record["failure_type"] is not None
    )
    total = len(records)
    successful = sum(record["task_success"] for record in records)
    usage_keys = ("requests", "input_tokens", "output_tokens", "total_tokens")
    usage = {
        key: sum(int(record["usage"].get(key, 0)) for record in records)
        for key in usage_keys
    }
    return {
        "experiment_id": experiment_id,
        "provider": provider,
        "model": model_name,
        "architecture": architecture,
        "runs": total,
        "successful_runs": successful,
        "success_rate": successful / total if total else 0.0,
        "mean_quality_score": (
            sum(record["quality_score"] for record in records) / total if total else 0.0
        ),
        "mean_tool_accuracy": (
            sum(record["tool_accuracy"] for record in records) / total if total else 0.0
        ),
        "safety_violation_count": sum(len(record["safety_violations"]) for record in records),
        "latency_p50_ms": _percentile(latencies, 0.50),
        "latency_p95_ms": _percentile(latencies, 0.95),
        "usage": usage,
        "estimated_cost_usd": sum(costs) if costs else None,
        "cost_coverage": len(costs) / total if total else 0.0,
        "failure_types": dict(sorted(failures.items())),
    }


def _markdown(summary: dict[str, Any], records: list[dict[str, Any]]) -> str:
    cost = summary["estimated_cost_usd"]
    cost_text = "N/A" if cost is None else f"${cost:.6f}"
    lines = [
        f"# {summary['architecture']} experiment report",
        "",
        f"- provider/model: `{summary['provider']}` / `{summary['model']}`",
        f"- success: {summary['successful_runs']}/{summary['runs']} ({summary['success_rate']:.1%})",
        f"- latency p50/p95: {summary['latency_p50_ms']:.0f}ms / {summary['latency_p95_ms']:.0f}ms",
        f"- tokens: {summary['usage']['total_tokens']:,}",
        f"- estimated Agent-call cost: {cost_text} ({summary['cost_coverage']:.0%} of runs covered)",
        "- evaluator-call cost: excluded",
        f"- safety violations: {summary['safety_violation_count']}",
        "",
        "| task | success | latency ms | tool accuracy | failure |",
        "| --- | ---: | ---: | ---: | --- |",
    ]
    for record in records:
        lines.append(
            f"| {record['task_id']} | {str(record['task_success']).lower()} | "
            f"{record['latency_ms']:.0f} | {record['tool_accuracy']:.2f} | "
            f"{record['failure_type'] or '-'} |"
        )
    return "\n".join(lines) + "\n"


def export_report(
    records: list[dict[str, Any]], summary: dict[str, Any], output_dir: Path
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    with (output_dir / "records.jsonl").open("w", encoding="utf-8") as jsonl_file:
        for record in records:
            jsonl_file.write(json.dumps(record, ensure_ascii=False) + "\n")

    csv_fields = (
        "task_id",
        "implementation_id",
        "task_success",
        "quality_score",
        "tool_accuracy",
        "latency_ms",
        "cost",
        "safety_violations",
        "failure_type",
        "usage",
        "metadata",
    )
    with (output_dir / "records.csv").open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=csv_fields)
        writer.writeheader()
        for record in records:
            row = dict(record)
            for key in ("usage", "metadata", "safety_violations"):
                row[key] = json.dumps(row[key], ensure_ascii=False)
            writer.writerow(row)

    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    report_path = output_dir / "report.md"
    report_path.write_text(_markdown(summary, records), encoding="utf-8")
    return report_path


def comparison_markdown(summaries: list[dict[str, Any]]) -> str:
    lines = [
        "# Agent architecture comparison",
        "",
        "| architecture | success | p50 | p95 | tokens | estimated cost | cost coverage | safety violations |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for summary in summaries:
        cost = summary["estimated_cost_usd"]
        cost_text = "N/A" if cost is None else f"${cost:.6f}"
        lines.append(
            f"| {summary['architecture']} | {summary['success_rate']:.1%} | "
            f"{summary['latency_p50_ms']:.0f}ms | {summary['latency_p95_ms']:.0f}ms | "
            f"{summary['usage']['total_tokens']:,} | {cost_text} | "
            f"{summary['cost_coverage']:.0%} | "
            f"{summary['safety_violation_count']} |"
        )
    lines.extend(
        [
            "",
            "Task success is determined only by CODE evaluators. Optional LLM evaluator results "
            "are recorded as diagnostics and never change task_success.",
            "",
        ]
    )
    return "\n".join(lines)
