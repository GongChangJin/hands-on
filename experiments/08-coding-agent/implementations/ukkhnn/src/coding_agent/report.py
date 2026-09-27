"""Markdown report generation."""

from __future__ import annotations

from typing import Any

from .models import EvaluationRun


def evaluation_report(summary: dict[str, Any], runs: list[EvaluationRun]) -> str:
    lines = [
        "# Bounded coding-agent replay evaluation",
        "",
        f"- success: {summary['successful_tasks']}/{summary['tasks']} ({summary['success_rate']:.1%})",
        f"- held-out tests: {summary['held_out_test_pass_rate']:.1%}",
        f"- regression tests catch original bug: {summary['regression_test_catches_bug_rate']:.1%}",
        f"- scope pass: {summary['scope_pass_rate']:.1%}",
        f"- average attempts: {summary['average_attempts']:.2f}",
        f"- latency p50/p95: {summary['latency_p50_ms']:.1f}ms / {summary['latency_p95_ms']:.1f}ms",
        f"- provider tokens: {summary['input_tokens']} input / {summary['output_tokens']} output",
        f"- estimated API cost: ${summary['cost_usd']:.6f}",
        (
            "- safety violations / forbidden Git actions: "
            f"{summary['safety_violation_count']} / {summary['forbidden_git_actions']}"
        ),
        "",
        "| issue | success | attempts | public | regression | held-out | lint | catches bug | scope | cost | latency |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for run in runs:
        lines.append(
            f"| {run.task_id} | {str(run.success).lower()} | {run.attempts} | "
            f"{str(run.public_tests_passed).lower()} | {str(run.regression_tests_passed).lower()} | "
            f"{str(run.held_out_tests_passed).lower()} | {str(run.lint_passed).lower()} | "
            f"{str(run.regression_test_catches_bug).lower()} | {str(run.scope_passed).lower()} | "
            f"${run.cost_usd:.6f} | {run.latency_ms:.1f}ms |"
        )
    lines.extend(
        [
            "",
            (
                "Held-out tests were not available to the agent loop. Each regression test was also "
                "executed against the original buggy fixture and counted only when it failed there."
            ),
            "",
            (
                "This run uses frozen reference patches to validate the execution and evaluation "
                "control plane. It does not measure live model patch-generation quality."
            ),
        ]
    )
    return "\n".join(lines) + "\n"
