"""Deterministic graders and comparison-ready report export."""

from __future__ import annotations

import csv
import json
import re
import statistics
from pathlib import Path
from typing import Any, Awaitable, Callable

from .calculator import evaluate_arithmetic
from .contracts import validate_contract


AgentRunner = Callable[[dict[str, Any]], Awaitable[dict[str, Any]]]


def load_tasks(path: Path) -> list[dict[str, Any]]:
    tasks: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            if not line.strip():
                continue
            try:
                task = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_number} JSON 오류: {exc}") from exc
            validate_contract("task-request", task)
            tasks.append(task)
    if len(tasks) < 15:
        raise ValueError("평가 질문이 15개 이상 필요합니다.")
    return tasks


def _normalized(text: str) -> str:
    return re.sub(r"[\s,_]", "", text).lower()


def _tool_score(required: list[str], actual: list[str]) -> float:
    required_set = set(required)
    actual_set = set(actual)
    union = required_set | actual_set
    return 1.0 if not union else len(required_set & actual_set) / len(union)


def _expression_matches(expected: str, traces: list[dict[str, Any]]) -> bool:
    calculator_traces = [item for item in traces if item["tool_name"] == "calculator"]
    if not expected:
        return not calculator_traces
    if len(calculator_traces) != 1 or calculator_traces[0].get("error"):
        return False
    try:
        expected_value = float(evaluate_arithmetic(expected))
        actual_value = float(calculator_traces[0]["result_summary"])
    except (TypeError, ValueError, SyntaxError, ZeroDivisionError):
        return False
    return abs(expected_value - actual_value) <= 1e-9


def grade_result(task: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    expected = task["expected_output"]
    output = str(result.get("output", ""))
    normalized_output = _normalized(output)
    content_ok = all(
        _normalized(str(term)) in normalized_output for term in expected.get("required_terms", [])
    )
    alternatives = expected.get("required_any", [])
    if alternatives:
        content_ok = content_ok and any(
            _normalized(str(term)) in normalized_output for term in alternatives
        )
    forbidden = [
        str(term)
        for term in expected.get("forbidden_terms", [])
        if _normalized(str(term)) in normalized_output
    ]
    content_ok = content_ok and not forbidden

    traces = list(result.get("metadata", {}).get("tool_traces", []))
    actual_tools = [trace["tool_name"] for trace in traces]
    required_tools = list(expected.get("required_tools", []))
    tool_score = _tool_score(required_tools, actual_tools)
    tool_errors = [trace for trace in traces if trace.get("error")]

    expected_sources = set(expected.get("expected_sources", []))
    evidence = result.get("evidence", [])
    actual_sources = {
        item.get("source") for item in evidence if item.get("source") != "calculator"
    }
    evidence_ok = expected_sources <= actual_sources
    if expected_sources:
        evidence_ok = evidence_ok and all(
            item.get("location")
            for item in evidence
            if item.get("source") in expected_sources
        )
    elif expected.get("category") == "no_answer":
        evidence_ok = not actual_sources

    calculation_ok = _expression_matches(str(expected.get("expected_expression", "")), traces)
    safety_violations = list(result.get("metadata", {}).get("safety_violations", []))
    safety_violations.extend(f"금지 문자열 포함: {term}" for term in forbidden)
    allowed_statuses = {"partial", "success"} if expected.get("category") == "no_answer" else {"success"}
    status_ok = result.get("status") in allowed_statuses
    task_success = all(
        [
            content_ok,
            evidence_ok,
            calculation_ok,
            tool_score == 1.0,
            not tool_errors,
            not safety_violations,
            status_ok,
        ]
    )
    components = {
        "content": float(content_ok),
        "evidence": float(evidence_ok),
        "calculation": float(calculation_ok),
        "tool": tool_score,
        "safety": float(not safety_violations),
        "status": float(status_ok),
    }
    failure_type = None
    if not task_success:
        failed_component = next(
            (name for name, score in components.items() if score < 1.0),
            None,
        )
        failure_type = "tool_error" if tool_errors else failed_component or "unknown"
    return {
        "task_id": task["task_id"],
        "implementation_id": result["metadata"]["implementation_id"],
        "task_success": task_success,
        "quality_score": sum(components.values()) / len(components),
        "tool_accuracy": tool_score,
        "latency_ms": float(result["metadata"]["latency_ms"]),
        "usage": result["metadata"]["usage"],
        "cost": result["metadata"].get("estimated_cost_usd"),
        "safety_violations": safety_violations,
        "failure_type": failure_type,
        "metadata": {
            "category": expected.get("category"),
            "provider": result["metadata"]["provider"],
            "model": result["metadata"]["model"],
            "components": components,
            "actual_tools": actual_tools,
            "expected_tools": required_tools,
            "actual_sources": sorted(str(item) for item in actual_sources),
            "expected_sources": sorted(expected_sources),
            "output": output,
            "limitations": result.get("limitations", []),
            "tool_traces": traces,
        },
    }


def summarize(records: list[dict[str, Any]]) -> dict[str, Any]:
    latencies = sorted(float(item["latency_ms"]) for item in records)

    def percentile(percent: float) -> float:
        if not latencies:
            return 0.0
        return latencies[round((len(latencies) - 1) * percent)]

    passed = sum(bool(item["task_success"]) for item in records)
    costs = [float(item["cost"]) for item in records if item.get("cost") is not None]
    by_category: dict[str, dict[str, int | float]] = {}
    for record in records:
        category = str(record["metadata"]["category"])
        bucket = by_category.setdefault(category, {"passed": 0, "total": 0})
        bucket["total"] = int(bucket["total"]) + 1
        bucket["passed"] = int(bucket["passed"]) + int(record["task_success"])
    for bucket in by_category.values():
        bucket["success_rate"] = int(bucket["passed"]) / int(bucket["total"])
    return {
        "total": len(records),
        "passed": passed,
        "failed": len(records) - passed,
        "success_rate": passed / len(records) if records else 0.0,
        "evidence_accuracy": statistics.mean(
            item["metadata"]["components"]["evidence"] for item in records
        ) if records else 0.0,
        "calculation_accuracy": statistics.mean(
            item["metadata"]["components"]["calculation"] for item in records
        ) if records else 0.0,
        "tool_accuracy": statistics.mean(item["tool_accuracy"] for item in records) if records else 0.0,
        "p50_latency_ms": percentile(0.50),
        "p95_latency_ms": percentile(0.95),
        "estimated_cost_usd": sum(costs) if costs else None,
        "safety_violations": sum(len(item["safety_violations"]) for item in records),
        "by_category": by_category,
        "failure_types": {
            failure: sum(item["failure_type"] == failure for item in records)
            for failure in sorted({item["failure_type"] for item in records if item["failure_type"]})
        },
    }


def _write_report(path: Path, summary: dict[str, Any], records: list[dict[str, Any]]) -> None:
    cost = summary["estimated_cost_usd"]
    cost_text = f"${cost:.6f}" if cost is not None else "N/A"
    lines = [
        "# Agentic RAG 평가 결과",
        "",
        "| 지표 | 결과 |",
        "| --- | ---: |",
        f"| 성공률 | {summary['success_rate']:.1%} ({summary['passed']}/{summary['total']}) |",
        f"| 근거 정확도 | {summary['evidence_accuracy']:.1%} |",
        f"| 계산 정확도 | {summary['calculation_accuracy']:.1%} |",
        f"| 도구 정확도 | {summary['tool_accuracy']:.1%} |",
        f"| p50 / p95 | {summary['p50_latency_ms']:.0f}ms / {summary['p95_latency_ms']:.0f}ms |",
        f"| 추정 API 비용 | {cost_text} |",
        f"| 안전 위반 | {summary['safety_violations']} |",
        "",
        "## 케이스",
        "",
        "| task | category | pass | tools | sources | failure |",
        "| --- | --- | ---: | --- | --- | --- |",
    ]
    for record in records:
        metadata = record["metadata"]
        lines.append(
            "| {task} | {category} | {passed} | {tools} | {sources} | {failure} |".format(
                task=record["task_id"],
                category=metadata["category"],
                passed="PASS" if record["task_success"] else "FAIL",
                tools=", ".join(metadata["actual_tools"]),
                sources=", ".join(metadata["actual_sources"]),
                failure=record["failure_type"] or "—",
            )
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def export_results(output_dir: Path, records: list[dict[str, Any]]) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = summarize(records)
    with (output_dir / "records.jsonl").open("w", encoding="utf-8") as file:
        for record in records:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")
    flat_rows = [
        {
            "task_id": item["task_id"],
            "category": item["metadata"]["category"],
            "task_success": item["task_success"],
            "quality_score": item["quality_score"],
            "tool_accuracy": item["tool_accuracy"],
            "latency_ms": item["latency_ms"],
            "cost": item["cost"],
            "failure_type": item["failure_type"],
        }
        for item in records
    ]
    with (output_dir / "records.csv").open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=list(flat_rows[0]) if flat_rows else [],
            lineterminator="\n",
        )
        if flat_rows:
            writer.writeheader()
            writer.writerows(flat_rows)
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    _write_report(output_dir / "report.md", summary, records)
    return summary


async def run_evaluation(
    run_agent: AgentRunner,
    tasks: list[dict[str, Any]],
    output_dir: Path,
) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    for task in tasks:
        result = await run_agent(task)
        record = grade_result(task, result)
        validate_contract("evaluation-record", record)
        records.append(record)
        verdict = "PASS" if record["task_success"] else "FAIL"
        print(f"[{len(records):02d}/{len(tasks):02d}] {task['task_id']}: {verdict}")
    return export_results(output_dir, records)
