"""JSONL, CSV, JSON, Markdown, and condition comparison reports."""

from __future__ import annotations

import csv
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any


def percentile(values: list[float], quantile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    rank = (len(ordered) - 1) * quantile
    lower, upper = math.floor(rank), math.ceil(rank)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (rank - lower)


def summarize(records: list[dict[str, Any]], *, condition: str, model: str) -> dict[str, Any]:
    total = len(records)
    graders = [record["metadata"]["graders"] for record in records]
    usage_keys = ("requests", "input_tokens", "output_tokens", "cached_input_tokens", "total_tokens")
    costs = [record["cost"] for record in records if record["cost"] is not None]
    failures = Counter(record["failure_type"] for record in records if record["failure_type"])
    representative = []
    for record in records:
        if not record["failure_type"]:
            continue
        grades = record["metadata"]["graders"]
        representative.append(
            {
                "task_id": record["task_id"],
                "failure_type": record["failure_type"],
                "expected_error_types": grades["expected_error_types"],
                "predicted_error_types": grades["predicted_error_types"],
            }
        )
        if len(representative) == 5:
            break
    mean = lambda key: (sum(float(item[key]) for item in graders) / total if total else 0.0)
    return {
        "experiment": "04-multimodal-agent",
        "implementation": "ukkhnn",
        "provider": "deepseek",
        "protocol_provider": "openai-compatible",
        "actual_endpoint_provider": "deepseek",
        "model": model,
        "condition": condition,
        "runs": total,
        "successful_runs": sum(record["task_success"] for record in records),
        "success_rate": sum(record["task_success"] for record in records) / total if total else 0.0,
        "classification_accuracy": mean("classification_accuracy"),
        "schema_compliance_rate": mean("schema_compliance"),
        "evidence_accuracy": mean("evidence_accuracy"),
        "severity_accuracy": mean("severity_accuracy"),
        "latency_p50_ms": percentile([record["latency_ms"] for record in records], 0.50),
        "latency_p95_ms": percentile([record["latency_ms"] for record in records], 0.95),
        "usage": {key: sum(int(record["usage"].get(key, 0)) for record in records) for key in usage_keys},
        "calculated_cost_usd": sum(costs) if costs else None,
        "cost_coverage": len(costs) / total if total else 0.0,
        "cost_basis": "provider-reported tokens and DeepSeek published peak/off-peak rates",
        "privacy_exposure_count": sum(int(item["privacy_exposure"]) for item in graders),
        "safety_violation_count": sum(int(item["safety_violation_count"]) for item in graders),
        "failure_types": dict(sorted(failures.items())),
        "representative_failures": representative,
    }


def _report(summary: dict[str, Any], records: list[dict[str, Any]]) -> str:
    cost = summary["calculated_cost_usd"]
    cost_text = "N/A" if cost is None else f"${cost:.6f}"
    lines = [
        f"# {summary['condition']} evaluation report",
        "",
        f"- provider/model: `deepseek` / `{summary['model']}`",
        f"- success: {summary['successful_runs']}/{summary['runs']} ({summary['success_rate']:.1%})",
        f"- classification/schema/evidence: {summary['classification_accuracy']:.1%} / {summary['schema_compliance_rate']:.1%} / {summary['evidence_accuracy']:.1%}",
        f"- latency p50/p95: {summary['latency_p50_ms']:.0f}ms / {summary['latency_p95_ms']:.0f}ms",
        f"- provider-reported tokens: {summary['usage']['total_tokens']:,}",
        f"- calculated model cost: {cost_text} ({summary['cost_coverage']:.0%} coverage)",
        f"- privacy exposures / safety violations: {summary['privacy_exposure_count']} / {summary['safety_violation_count']}",
        "",
        "Cost is calculated from provider-reported tokens and the published rate active at each call; it is not a billing invoice.",
        "Failed results are retained below and in records.jsonl/records.csv.",
        "",
        "| task | success | class | schema | evidence | latency ms | tokens | cost USD | failure |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for record in records:
        grades = record["metadata"]["graders"]
        record_cost = "N/A" if record["cost"] is None else f"{record['cost']:.8f}"
        lines.append(
            f"| {record['task_id']} | {str(record['task_success']).lower()} | "
            f"{grades['classification_accuracy']:.2f} | {grades['schema_compliance']:.2f} | "
            f"{grades['evidence_accuracy']:.2f} | {record['latency_ms']:.0f} | "
            f"{record['usage'].get('total_tokens', 0)} | {record_cost} | {record['failure_type'] or '-'} |"
        )
    return "\n".join(lines) + "\n"


def export_results(records: list[dict[str, Any]], summary: dict[str, Any], output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    with (output / "records.jsonl").open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    fields = (
        "task_id", "implementation_id", "task_success", "quality_score", "tool_accuracy",
        "latency_ms", "cost", "safety_violations", "failure_type", "usage", "metadata",
    )
    with (output / "records.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for record in records:
            row = dict(record)
            for key in ("safety_violations", "usage", "metadata"):
                row[key] = json.dumps(row[key], ensure_ascii=False, separators=(",", ":"))
            writer.writerow(row)
    (output / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output / "report.md").write_text(_report(summary, records), encoding="utf-8")


def _metric(summary: dict[str, Any], key: str) -> float:
    value = summary.get(key)
    return float(value) if value is not None else 0.0


def compare_results(first_dir: Path, second_dir: Path, output: Path) -> str:
    first = json.loads((first_dir / "summary.json").read_text(encoding="utf-8"))
    second = json.loads((second_dir / "summary.json").read_text(encoding="utf-8"))
    first_condition = str(first.get("condition") or "first")
    second_condition = str(second.get("condition") or "second")
    if first_condition == second_condition:
        raise ValueError("서로 다른 입력 조건의 결과를 비교해야 합니다.")
    rows = (
        ("success rate", "success_rate", ".1%"),
        ("classification accuracy", "classification_accuracy", ".1%"),
        ("schema compliance", "schema_compliance_rate", ".1%"),
        ("evidence accuracy", "evidence_accuracy", ".1%"),
        ("severity accuracy", "severity_accuracy", ".1%"),
        ("latency p50 ms", "latency_p50_ms", ".0f"),
        ("latency p95 ms", "latency_p95_ms", ".0f"),
        ("total tokens", "usage.total_tokens", ".0f"),
        ("calculated cost USD", "calculated_cost_usd", ".6f"),
        ("privacy exposures", "privacy_exposure_count", ".0f"),
        ("safety violations", "safety_violation_count", ".0f"),
    )
    def get(summary: dict[str, Any], key: str) -> float:
        if key.startswith("usage."):
            return float(summary["usage"].get(key.split(".", 1)[1], 0))
        return _metric(summary, key)

    lines = [
        "# DeepSeek input condition comparison",
        "",
        f"Model: `{first['model']}`; endpoint provider: `deepseek`; protocol: `openai-compatible`.",
        "",
        f"| metric | {first_condition} | {second_condition} | {second_condition} - {first_condition} |",
        "| --- | ---: | ---: | ---: |",
    ]
    for label, key, fmt in rows:
        a, b = get(first, key), get(second, key)
        lines.append(f"| {label} | {format(a, fmt)} | {format(b, fmt)} | {format(b - a, fmt)} |")
    lines.extend(
        [
            "",
            "## Retained failures",
            "",
            f"- {first_condition}: `{json.dumps(first['failure_types'], ensure_ascii=False)}`",
            f"- {second_condition}: `{json.dumps(second['failure_types'], ensure_ascii=False)}`",
            "",
            "Cost uses provider-reported token usage and the rate active at each call; cache hits and peak/off-peak timing mean the two totals are observational rather than a controlled price comparison. It is not a billing invoice.",
            "",
        ]
    )
    value = "\n".join(lines)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(value, encoding="utf-8")
    return value
