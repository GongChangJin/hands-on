"""Aggregate and export benchmark results."""

from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean
from typing import Any


def percentile(values: list[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    rank = (len(ordered) - 1) * fraction
    lower = math.floor(rank)
    upper = math.ceil(rank)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (rank - lower)


def summarize(
    records: list[dict[str, Any]],
    *,
    implementation_id: str,
    adapter: str,
    model: str,
    repetitions: int,
    environment: dict[str, Any],
) -> dict[str, Any]:
    total = len(records)
    successes = sum(record["task_success"] for record in records)
    schema_passes = sum(bool(record["metadata"].get("schema_pass")) for record in records)
    latencies = [float(record["latency_ms"]) for record in records]
    first_tokens = [float(record["metadata"]["first_token_latency_ms"]) for record in records if record["metadata"].get("first_token_latency_ms") is not None]
    throughputs = [float(record["metadata"]["generation_tokens_per_second"]) for record in records if record["metadata"].get("generation_tokens_per_second") is not None]
    failure_types = Counter(record["failure_type"] for record in records if record["failure_type"])
    category_totals: dict[str, int] = defaultdict(int)
    category_successes: dict[str, int] = defaultdict(int)
    for record in records:
        category = str(record["metadata"].get("category", "unknown"))
        category_totals[category] += 1
        category_successes[category] += int(record["task_success"])
    costs = [float(record["cost"]) for record in records if record["cost"] is not None]
    usage_keys = ("requests", "input_tokens", "output_tokens", "total_tokens")
    return {
        "implementation_id": implementation_id,
        "adapter": adapter,
        "model": model,
        "repetitions": repetitions,
        "runs": total,
        "successful_runs": successes,
        "success_rate": successes / total if total else 0.0,
        "schema_passes": schema_passes,
        "schema_pass_rate": schema_passes / total if total else 0.0,
        "latency_p50_ms": percentile(latencies, 0.50),
        "latency_p95_ms": percentile(latencies, 0.95),
        "first_token_p50_ms": percentile(first_tokens, 0.50),
        "first_token_p95_ms": percentile(first_tokens, 0.95),
        "generation_tokens_per_second_mean": mean(throughputs) if throughputs else None,
        "usage": {key: sum(int(record["usage"].get(key, 0)) for record in records) for key in usage_keys},
        "estimated_cost_usd": sum(costs) if costs else None,
        "cost_coverage": len(costs) / total if total else 0.0,
        "safety_violation_count": sum(len(record["safety_violations"]) for record in records),
        "failure_types": dict(sorted(failure_types.items())),
        "categories": {
            category: {
                "runs": category_totals[category],
                "successful_runs": category_successes[category],
                "success_rate": category_successes[category] / category_totals[category],
            }
            for category in sorted(category_totals)
        },
        "environment": environment,
    }


def _number(value: float | None, suffix: str = "") -> str:
    return "N/A" if value is None else f"{value:,.1f}{suffix}"


def report_markdown(summary: dict[str, Any], records: list[dict[str, Any]]) -> str:
    cost = summary["estimated_cost_usd"]
    cost_text = "N/A" if cost is None else f"${cost:.6f}"
    lines = [
        f"# {summary['model']} benchmark",
        "",
        f"- adapter: `{summary['adapter']}`",
        f"- success: {summary['successful_runs']}/{summary['runs']} ({summary['success_rate']:.1%})",
        f"- JSON schema: {summary['schema_passes']}/{summary['runs']} ({summary['schema_pass_rate']:.1%})",
        f"- total latency p50/p95: {_number(summary['latency_p50_ms'], 'ms')} / {_number(summary['latency_p95_ms'], 'ms')}",
        f"- first token p50/p95: {_number(summary['first_token_p50_ms'], 'ms')} / {_number(summary['first_token_p95_ms'], 'ms')}",
        f"- generation: {_number(summary['generation_tokens_per_second_mean'], ' tokens/s')}",
        f"- measured request cost: {cost_text} ({summary['cost_coverage']:.0%} coverage)",
        f"- safety violations: {summary['safety_violation_count']}",
        "",
        "| task | repetition | success | schema | latency ms | first token ms | tokens/s | failure |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for record in records:
        metadata = record["metadata"]
        lines.append(
            f"| {record['task_id']} | {metadata['repetition']} | {str(record['task_success']).lower()} | "
            f"{str(metadata['schema_pass']).lower()} | {record['latency_ms']:.0f} | "
            f"{_number(metadata.get('first_token_latency_ms'))} | "
            f"{_number(metadata.get('generation_tokens_per_second'))} | {record['failure_type'] or '-'} |"
        )
    return "\n".join(lines) + "\n"


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records), encoding="utf-8")


def export_results(
    output_dir: Path,
    *,
    summary: dict[str, Any],
    agent_results: list[dict[str, Any]],
    tool_traces: list[dict[str, Any]],
    evaluation_records: list[dict[str, Any]],
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(output_dir / "agent-results.jsonl", agent_results)
    write_jsonl(output_dir / "tool-traces.jsonl", tool_traces)
    write_jsonl(output_dir / "records.jsonl", evaluation_records)
    (output_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report_path = output_dir / "report.md"
    report_path.write_text(report_markdown(summary, evaluation_records), encoding="utf-8")
    return report_path


def comparison_markdown(summaries: list[dict[str, Any]]) -> str:
    lines = [
        "# Local and API LLM comparison",
        "",
        "| adapter / model | success | JSON schema | p50 | p95 | first token p50 | tokens/s | model memory | request cost |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for summary in summaries:
        environment = summary.get("environment", {})
        model_info = environment.get("model", {})
        memory = model_info.get("accelerator_memory_bytes")
        memory_text = "N/A" if memory is None else f"{memory / 1024 ** 3:.2f} GiB"
        cost = summary.get("estimated_cost_usd")
        cost_text = "N/A" if cost is None else f"${cost:.6f}"
        lines.append(
            f"| {summary['adapter']} / `{summary['model']}` | {summary['success_rate']:.1%} | "
            f"{summary['schema_pass_rate']:.1%} | {_number(summary.get('latency_p50_ms'), 'ms')} | "
            f"{_number(summary.get('latency_p95_ms'), 'ms')} | {_number(summary.get('first_token_p50_ms'), 'ms')} | "
            f"{_number(summary.get('generation_tokens_per_second_mean'))} | {memory_text} | {cost_text} |"
        )
    lines.extend([
        "",
        "`success` requires both a valid schema and an exact deterministic answer. Local request cost is recorded as $0; hardware and electricity are not estimated.",
        "",
    ])
    return "\n".join(lines)
