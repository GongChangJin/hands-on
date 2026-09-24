"""Human-readable evaluation report."""

from __future__ import annotations

from typing import Any

from .models import EvaluationRecord


def _pct(value: float | None) -> str:
    return "N/A" if value is None else f"{value:.1%}"


def _money(value: float | None) -> str:
    return "N/A" if value is None else f"${value:.6f}"


def _ms(value: float | None) -> str:
    return "N/A" if value is None else f"{value:,.1f}ms"


def evaluation_report(summary: dict[str, Any], records: list[EvaluationRecord], classifier_name: str) -> str:
    quality = summary["quality"]
    cost = summary["cost"]
    latency = summary["latency"]
    lines = [
        "# Hybrid LLM router evaluation",
        "",
        f"- classifier: `{classifier_name}` (used only for incomplete signals)",
        f"- routing accuracy: {summary['route_matches']}/{summary['tasks']} ({summary['routing_accuracy']:.1%})",
        f"- model / agent accuracy: {summary['model_accuracy']:.1%} / {summary['agent_accuracy']:.1%}",
        f"- strategy: {summary['strategies']}; classifier calls: {summary['classifier_calls']}",
        f"- projected quality: {_pct(quality['router_mean'])} vs all-frontier {_pct(quality['all_frontier_mean'])} (coverage {_pct(quality['coverage'])})",
        f"- projected cost: {_money(cost['router_total_usd'])} vs all-frontier {_money(cost['all_frontier_total_usd'])} (savings {_pct(cost['savings_rate'])}, coverage {_pct(cost['coverage'])})",
        f"- routing + model cost: {_money(cost['routing_and_model_total_usd'])} vs all-frontier model {_money(cost['all_frontier_model_total_usd'])} (savings {_pct(cost['routing_and_model_savings_rate'])})",
        f"- projected latency p50/p95: {_ms(latency['router_p50_ms'])} / {_ms(latency['router_p95_ms'])}",
        f"- all-frontier latency p50/p95: {_ms(latency['all_frontier_p50_ms'])} / {_ms(latency['all_frontier_p95_ms'])}",
        "",
        "| task | strategy | model | agents | confidence | match | classifier ms | projected cost | projected latency |",
        "| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for record in records:
        classifier_latency = float(record.metadata["classifier_latency_ms"])
        lines.append(
            f"| {record.task_id} | {record.route.strategy} | {record.route.selected_model.value} | "
            f"{', '.join(agent.value for agent in record.route.selected_agents) or '-'} | {record.route.confidence:.2f} | "
            f"{str(record.route_match).lower()} | {classifier_latency:.1f} | {_money(record.projected_cost_usd)} | "
            f"{_ms(record.projected_latency_ms)} |"
        )
    lines.extend(["", "## Limits", ""])
    lines.extend(f"- {item}" for item in summary["limitations"])
    return "\n".join(lines) + "\n"
