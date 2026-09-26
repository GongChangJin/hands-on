"""Metric and common-contract record construction."""

from __future__ import annotations

from .contracts import validate
from .models import ExpectedFinding, Finding, SecurityEvaluation, ToolExecution


def evaluate_fixture(
    expected: list[ExpectedFinding],
    before: list[Finding],
    after: list[Finding],
    functional_before: bool,
    security_before_failed: bool,
    all_after: bool,
    isolation_probes: list[dict],
    minimum_detection_rate: float,
    minimum_remediation_rate: float,
    clean_controls: int,
) -> SecurityEvaluation:
    expected_ids = {item.id for item in expected}
    detected = {item.expected_id for item in before if item.expected_id}
    residual = {item.expected_id for item in after if item.expected_id}
    false_positives = sum(item.expected_id is None for item in before)
    detection_rate = len(detected) / len(expected_ids) if expected_ids else 1.0
    remediated = detected - residual
    remediation_rate = len(remediated) / len(detected) if detected else 0.0
    isolation_ok = all(item["passed"] for item in isolation_probes)
    approved = all((
        detection_rate >= minimum_detection_rate,
        remediation_rate >= minimum_remediation_rate,
        not residual,
        functional_before,
        security_before_failed,
        all_after,
        isolation_ok,
    ))
    risks = [
        "Custom rules cover the three fixture categories, not every security weakness.",
        "Reference fixes validate the deterministic security gate, not live model remediation quality.",
    ]
    return SecurityEvaluation(
        detected_expected=len(detected),
        expected_total=len(expected_ids),
        detection_rate=detection_rate,
        residual_expected=len(residual),
        remediated_expected=len(remediated),
        remediation_rate=remediation_rate,
        false_positives=false_positives,
        clean_controls=clean_controls,
        functional_tests_before=functional_before,
        security_tests_before_failed=security_before_failed,
        all_tests_after=all_after,
        decision="approve" if approved else "block",
        remaining_risks=risks,
        metadata={"isolation_probes_passed": sum(item["passed"] for item in isolation_probes)},
    )


def tool_trace(task_id: str, execution: ToolExecution, input_summary: str) -> dict:
    tail = (execution.stdout or execution.stderr).strip().replace("\n", " ")[-400:]
    value = {
        "task_id": task_id,
        "tool_name": execution.tool,
        "input_summary": input_summary,
        "result_summary": f"exit={execution.exit_code}; {tail}",
        "duration_ms": execution.duration_ms,
        "error": None if execution.exit_code in {0, 1} and not execution.timed_out else f"exit_{execution.exit_code}",
        "metadata": {"timed_out": execution.timed_out, "container_args": execution.container_args},
    }
    validate("tool-trace", value)
    return value


def validate_records(name: str, rows: list[dict]) -> list[dict]:
    for row in rows:
        validate(name, row)
    return rows
