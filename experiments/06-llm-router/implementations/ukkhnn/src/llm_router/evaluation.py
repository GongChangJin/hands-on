"""Replay evaluation against measured upstream project metrics."""

from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path
from statistics import mean
from typing import Any

from .models import AgentRoute, ClassifierResult, DataScope, DatasetCase, EvaluationRecord, LogicalModel, ProjectMetrics, TaskRequest
from .router import HybridRouter


def percentile(values: list[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    rank = (len(ordered) - 1) * fraction
    lower, upper = math.floor(rank), math.ceil(rank)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (rank - lower)


def _execution_projection(
    model: LogicalModel,
    agents: list[AgentRoute],
    metrics: ProjectMetrics,
) -> tuple[float | None, float | None, float | None]:
    model_metric = metrics.logical_models[model]
    agent_metrics = [metrics.agents[agent] for agent in agents]
    if any(item.quality_score is None for item in agent_metrics):
        quality = None
    else:
        quality = min([model_metric.quality_score, *[float(item.quality_score) for item in agent_metrics]])
    if any(item.request_cost_usd is None for item in agent_metrics):
        cost = None
    else:
        cost = model_metric.request_cost_usd + sum(float(item.request_cost_usd) for item in agent_metrics)
    if any(item.latency_p50_ms is None for item in agent_metrics):
        latency = None
    else:
        latency = max([model_metric.latency_p50_ms, *[float(item.latency_p50_ms) for item in agent_metrics]])
    return quality, cost, latency


def evaluate_case(case: DatasetCase, router: HybridRouter) -> EvaluationRecord:
    decision = router.route(case.request())
    projected_quality, projected_cost, projected_latency = _execution_projection(
        decision.selected_model, decision.selected_agents, router.metrics
    )
    baseline_quality, baseline_cost, baseline_latency = _execution_projection(
        LogicalModel.FRONTIER, decision.selected_agents, router.metrics
    )
    classifier_cost = decision.classifier.cost_usd if decision.classifier else 0.0
    classifier_latency = decision.classifier.latency_ms if decision.classifier else 0.0
    if projected_cost is not None:
        projected_cost += classifier_cost
    if projected_latency is not None:
        projected_latency += decision.latency_ms
    model_match = decision.selected_model in case.expected_models
    agent_match = set(decision.selected_agents) == set(case.expected_agents)
    return EvaluationRecord(
        task_id=case.task_id,
        route=decision,
        expected_models=case.expected_models,
        expected_agents=case.expected_agents,
        model_match=model_match,
        agent_match=agent_match,
        route_match=model_match and agent_match and not decision.blocked,
        projected_quality=projected_quality,
        baseline_quality=baseline_quality,
        projected_cost_usd=projected_cost,
        baseline_cost_usd=baseline_cost,
        projected_latency_ms=projected_latency,
        baseline_latency_ms=baseline_latency,
        metadata={
            "classifier_latency_ms": classifier_latency,
            "classifier_cost_usd": classifier_cost,
            "router_and_model_cost_usd": router.metrics.logical_models[decision.selected_model].request_cost_usd + classifier_cost,
            "all_frontier_model_cost_usd": router.metrics.logical_models[LogicalModel.FRONTIER].request_cost_usd,
            "projection_basis": "02-05 measured p50, quality, and calculated request costs",
        },
    )


def summarize(records: list[EvaluationRecord]) -> dict[str, Any]:
    total = len(records)
    comparable_quality = [record for record in records if record.projected_quality is not None and record.baseline_quality is not None]
    comparable_cost = [record for record in records if record.projected_cost_usd is not None and record.baseline_cost_usd is not None]
    comparable_latency = [record for record in records if record.projected_latency_ms is not None and record.baseline_latency_ms is not None]
    projected_quality = mean(float(record.projected_quality) for record in comparable_quality) if comparable_quality else None
    baseline_quality = mean(float(record.baseline_quality) for record in comparable_quality) if comparable_quality else None
    projected_cost = sum(float(record.projected_cost_usd) for record in comparable_cost) if comparable_cost else None
    baseline_cost = sum(float(record.baseline_cost_usd) for record in comparable_cost) if comparable_cost else None
    routing_and_model_cost = sum(float(record.metadata["router_and_model_cost_usd"]) for record in records)
    all_frontier_model_cost = sum(float(record.metadata["all_frontier_model_cost_usd"]) for record in records)
    projected_latencies = [float(record.projected_latency_ms) for record in comparable_latency]
    baseline_latencies = [float(record.baseline_latency_ms) for record in comparable_latency]
    strategies = Counter(record.route.strategy for record in records)
    return {
        "tasks": total,
        "route_matches": sum(record.route_match for record in records),
        "routing_accuracy": sum(record.route_match for record in records) / total if total else 0,
        "model_accuracy": sum(record.model_match for record in records) / total if total else 0,
        "agent_accuracy": sum(record.agent_match for record in records) / total if total else 0,
        "strategies": dict(sorted(strategies.items())),
        "classifier_calls": sum(record.route.classifier is not None for record in records),
        "fallbacks": sum(record.route.fallback for record in records),
        "quality": {
            "coverage": len(comparable_quality) / total if total else 0,
            "router_mean": projected_quality,
            "all_frontier_mean": baseline_quality,
            "absolute_gap": None if projected_quality is None or baseline_quality is None else baseline_quality - projected_quality,
            "within_five_percent": bool(
                projected_quality is not None
                and baseline_quality is not None
                and baseline_quality - projected_quality <= 0.05
            ),
        },
        "cost": {
            "coverage": len(comparable_cost) / total if total else 0,
            "router_total_usd": projected_cost,
            "all_frontier_total_usd": baseline_cost,
            "savings_rate": None if not baseline_cost else (baseline_cost - float(projected_cost)) / baseline_cost,
            "classifier_total_usd": sum(float(record.metadata["classifier_cost_usd"]) for record in records),
            "routing_and_model_total_usd": routing_and_model_cost,
            "all_frontier_model_total_usd": all_frontier_model_cost,
            "routing_and_model_savings_rate": (
                (all_frontier_model_cost - routing_and_model_cost) / all_frontier_model_cost
                if all_frontier_model_cost
                else None
            ),
        },
        "latency": {
            "coverage": len(comparable_latency) / total if total else 0,
            "router_p50_ms": percentile(projected_latencies, 0.50),
            "router_p95_ms": percentile(projected_latencies, 0.95),
            "all_frontier_p50_ms": percentile(baseline_latencies, 0.50),
            "all_frontier_p95_ms": percentile(baseline_latencies, 0.95),
        },
        "limitations": [
            "Execution quality, downstream latency, and downstream cost are replay projections from 02-05 rather than new task executions.",
            "Browser and coding projections are excluded because 07 and 08 have no measured metrics yet.",
            "Balanced and frontier currently map to the same measured Solar Pro 4 endpoint.",
        ],
    }


def run_evaluation(cases: list[DatasetCase], router: HybridRouter) -> tuple[list[EvaluationRecord], dict[str, Any]]:
    records = [evaluate_case(case, router) for case in cases]
    return records, summarize(records)


class _TimeoutClassifier:
    def classify(self, task: TaskRequest) -> ClassifierResult:
        raise TimeoutError("injected timeout")


class _FailingClassifier:
    def classify(self, task: TaskRequest) -> ClassifierResult:
        raise RuntimeError("injected provider failure")


class _InvalidClassifier:
    def classify(self, task: TaskRequest) -> ClassifierResult:
        raise ValueError("injected schema failure")


class _LowConfidenceClassifier:
    def classify(self, task: TaskRequest) -> ClassifierResult:
        return ClassifierResult(agents=[], confidence=0.2, reason="injected uncertainty")


def run_fallback_suite(policy, metrics) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    ambiguous = TaskRequest(
        task_id="fallback-probe",
        prompt="첨부한 화면에서 오류를 찾아줘.",
        modalities=["text", "image"],
        complexity="moderate",
        risk="medium",
        signals_complete=False,
    )
    rows: list[dict[str, Any]] = []
    for name, classifier, expected_reason in [
        ("timeout", _TimeoutClassifier(), "classifier_timeout"),
        ("provider_failure", _FailingClassifier(), "classifier_failure"),
        ("schema_failure", _InvalidClassifier(), "classifier_failure"),
        ("low_confidence", _LowConfidenceClassifier(), "classifier_low_confidence"),
    ]:
        decision = HybridRouter(policy, metrics, classifier=classifier).route(ambiguous.model_copy(update={"task_id": name}))
        rows.append({
            "scenario": name,
            "passed": decision.fallback and decision.fallback_reason == expected_reason and decision.actual_model is not None,
            "decision": decision.model_dump(mode="json"),
        })

    circuit_router = HybridRouter(policy, metrics, classifier=_FailingClassifier())
    circuit_router.route(ambiguous.model_copy(update={"task_id": "circuit-prime-1"}))
    circuit_router.route(ambiguous.model_copy(update={"task_id": "circuit-prime-2"}))
    circuit = circuit_router.route(ambiguous.model_copy(update={"task_id": "circuit-open"}))
    rows.append({
        "scenario": "circuit_open",
        "passed": circuit.fallback_reason == "classifier_circuit_open" and circuit.actual_model is not None,
        "decision": circuit.model_dump(mode="json"),
    })

    local_actual = metrics.logical_models[LogicalModel.LOCAL].actual_model
    local_only = TaskRequest(
        task_id="local-only-unavailable",
        prompt="기밀 인사 기록을 요약해줘.",
        data_scope="local_only",
        complexity="moderate",
        risk="high",
    )
    blocked = HybridRouter(policy, metrics, availability={local_actual: False}).route(local_only)
    rows.append({
        "scenario": "local_only_unavailable",
        "passed": blocked.blocked and blocked.actual_model is None and not blocked.fallback,
        "decision": blocked.model_dump(mode="json"),
    })

    private = local_only.model_copy(update={"task_id": "private-unavailable", "data_scope": DataScope.PRIVATE})
    recovered = HybridRouter(policy, metrics, availability={local_actual: False}).route(private)
    rows.append({
        "scenario": "private_model_unavailable",
        "passed": recovered.fallback and recovered.actual_model is not None and not recovered.blocked,
        "decision": recovered.model_dump(mode="json"),
    })
    passed = sum(bool(row["passed"]) for row in rows)
    return rows, {"scenarios": len(rows), "passed": passed, "pass_rate": passed / len(rows)}


def export_evaluation(output_dir: Path, records: list[EvaluationRecord], summary: dict[str, Any], report: str) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "records.jsonl").write_text(
        "".join(record.model_dump_json() + "\n" for record in records), encoding="utf-8"
    )
    (output_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output_dir / "report.md").write_text(report, encoding="utf-8")


def export_fallback(output_dir: Path, rows: list[dict[str, Any]], summary: dict[str, Any]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "fallback-results.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8"
    )
    (output_dir / "fallback-summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
