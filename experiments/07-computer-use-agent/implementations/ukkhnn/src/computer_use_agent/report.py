"""Markdown reports for condition and safety comparisons."""

from __future__ import annotations

from typing import Any

from .models import TaskRun


def condition_report(summary: dict[str, Any], runs: list[TaskRun]) -> str:
    lines = [
        f"# {summary['condition']} computer-use evaluation",
        "",
        f"- success: {summary['successful_tasks']}/{summary['tasks']} ({summary['success_rate']:.1%}; {summary['unique_tasks']} tasks × {summary['repetitions']} repetitions)",
        f"- average actions: {summary['average_actions']:.2f}",
        f"- latency p50/p95: {summary['latency_p50_ms']:.1f}ms / {summary['latency_p95_ms']:.1f}ms",
        f"- recovery: {summary['recovery_successes']}/{summary['recovery_cases']} ({summary['recovery_rate']:.1%})",
        f"- safety violations: {summary['safety_violation_count']}",
        f"- isolated contexts: {summary['isolated_contexts']}",
        "",
        "| task | repetition | success | actions | recoveries | latency ms | final value | failure |",
        "| --- | ---: | ---: | ---: | ---: | ---: | --- | --- |",
    ]
    for run in runs:
        lines.append(
            f"| {run.task_id} | {run.repetition} | {str(run.success).lower()} | {run.action_count} | {run.recovery_count} | "
            f"{run.latency_ms:.1f} | {run.final_value} | {run.failure_type or '-'} |"
        )
    return "\n".join(lines) + "\n"


def comparison_report(comparison: dict[str, Any]) -> str:
    dom = comparison["conditions"]["dom-accessibility"]
    adaptive = comparison["conditions"]["adaptive-screenshot"]
    safety = comparison["safety"]
    lines = [
        "# Computer-use condition comparison",
        "",
        "| condition | success | average actions | recovery | p50 | p95 | screenshot observations |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        f"| DOM/accessibility | {dom['success_rate']:.1%} | {dom['average_actions']:.2f} | {dom['recovery_rate']:.1%} | {dom['latency_p50_ms']:.1f}ms | {dom['latency_p95_ms']:.1f}ms | {dom['screenshot_observations']} |",
        f"| failure-triggered screenshot + accessibility fallback | {adaptive['success_rate']:.1%} | {adaptive['average_actions']:.2f} | {adaptive['recovery_rate']:.1%} | {adaptive['latency_p50_ms']:.1f}ms | {adaptive['latency_p95_ms']:.1f}ms | {adaptive['screenshot_observations']} |",
        "",
        f"Safety probes passed {safety['passed']}/{safety['scenarios']}; actual external navigations: {safety['actual_external_navigations']}.",
        "",
        "The adaptive condition records screenshot evidence only after an action error, then uses an accessible-name fallback. Routine steps retain the lower-overhead DOM/accessibility representation.",
    ]
    return "\n".join(lines) + "\n"
