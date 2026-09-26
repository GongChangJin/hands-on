"""Human-readable report rendering."""

from __future__ import annotations


def render_report(summary: dict, handoffs: list[dict]) -> str:
    metrics = summary["fixture"]
    lines = [
        "# Cybersecurity Agent evaluation",
        "",
        f"- Run: `{summary['run_id']}`",
        f"- Decision: **{metrics['decision']}**",
        f"- Detection: {metrics['detected_expected']}/{metrics['expected_total']} ({metrics['detection_rate']:.0%})",
        f"- Remediation: {metrics['remediated_expected']}/{metrics['detected_expected']} ({metrics['remediation_rate']:.0%})",
        f"- False positives: {metrics['false_positives']}",
        f"- Regression/security tests after remediation: {'pass' if metrics['all_tests_after'] else 'fail'}",
        f"- Isolation probes: {summary['isolation']['passed']}/{summary['isolation']['total']}",
        "",
        "## Coding Agent handoff review",
        "",
        "| Task | Decision | Findings | Tests |",
        "| --- | --- | ---: | --- |",
    ]
    for item in handoffs:
        lines.append(
            f"| `{item['task_id']}` | {item['decision']} | {item['finding_count']} | "
            f"{'pass' if item['tests_passed'] else 'fail'} |"
        )
    lines.extend([
        "",
        "## Limits",
        "",
        "- The rule set is intentionally scoped to SQL injection, path traversal, and hardcoded secrets in Python.",
        "- Deterministic reference fixes and replay patches validate the gate and evidence chain; they do not measure live LLM generation quality.",
        "- Dependency and dynamic application security scanning remain outside this experiment.",
        "",
    ])
    return "\n".join(lines)
