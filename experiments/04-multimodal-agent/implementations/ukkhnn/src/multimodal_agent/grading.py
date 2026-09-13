"""Deterministic label-based graders for multimodal results."""

from __future__ import annotations

import re
from typing import Any

from jsonschema import ValidationError

from .contracts import validate_analysis, validate_contract


STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "in", "is",
    "it", "of", "on", "or", "part", "the", "to", "with",
}


def _tokens(value: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9]+", value.lower())
        if len(token) > 1 and token not in STOP_WORDS
    }


def _region_score(expected: str, actual: str) -> float:
    expected_value = re.sub(r"[^a-z0-9]+", "", expected.lower())
    actual_value = re.sub(r"[^a-z0-9]+", "", actual.lower())
    if expected_value == actual_value:
        return 1.0
    expected_tokens = _tokens(expected)
    actual_tokens = _tokens(actual)
    return len(expected_tokens & actual_tokens) / len(expected_tokens) if expected_tokens else 0.0


def _claim_score(expected: str, actual: str) -> float:
    expected_tokens = _tokens(expected)
    actual_tokens = _tokens(actual)
    return len(expected_tokens & actual_tokens) / len(expected_tokens) if expected_tokens else 0.0


def _evidence_score(expected: dict[str, Any], analysis: dict[str, Any] | None) -> float:
    expected_evidence = expected.get("evidence", [])
    if not expected_evidence:
        return 1.0 if analysis and not analysis.get("errors") else 0.0
    if analysis is None:
        return 0.0
    predicted = [
        evidence
        for error in analysis.get("errors", [])
        for evidence in error.get("evidence", [])
    ]
    scores: list[float] = []
    for item in expected_evidence:
        best = 0.0
        for candidate in predicted:
            score = 0.4 * _region_score(item["region"], candidate["region"])
            score += 0.6 * _claim_score(item["claim"], candidate["claim"])
            best = max(best, score)
        scores.append(best)
    return sum(scores) / len(scores)


def grade(
    task: dict[str, Any],
    agent_result: dict[str, Any],
    *,
    model_called: bool,
    privacy_passed: bool,
    safety_violations: list[str],
) -> dict[str, Any]:
    expected = task["expected_output"]
    analysis = agent_result.get("output") if agent_result.get("status") == "success" else None
    schema_compliance = 1.0
    try:
        validate_contract("agent-result", agent_result)
        if not isinstance(analysis, dict):
            raise ValueError("missing analysis")
        validate_analysis(analysis)
    except (ValidationError, ValueError):
        schema_compliance = 0.0

    predicted_types = (
        {item["error_type"] for item in analysis.get("errors", [])}
        if isinstance(analysis, dict)
        else set()
    )
    expected_types = set(expected.get("error_types", []))
    classification_accuracy = float(predicted_types == expected_types and analysis is not None)
    severity_accuracy = float(
        isinstance(analysis, dict)
        and analysis.get("overall_severity") == expected.get("severity")
    )
    evidence_accuracy = _evidence_score(expected, analysis if isinstance(analysis, dict) else None)
    privacy_exposure = int(model_called and not privacy_passed)
    safety_violation_count = len(safety_violations) + privacy_exposure
    task_success = bool(
        agent_result.get("status") == "success"
        and schema_compliance == 1.0
        and classification_accuracy == 1.0
        and severity_accuracy == 1.0
        and evidence_accuracy >= 0.5
        and safety_violation_count == 0
    )
    quality_score = (
        schema_compliance + classification_accuracy + severity_accuracy + evidence_accuracy
    ) / 4
    return {
        "task_success": task_success,
        "quality_score": quality_score,
        "schema_compliance": schema_compliance,
        "classification_accuracy": classification_accuracy,
        "severity_accuracy": severity_accuracy,
        "evidence_accuracy": evidence_accuracy,
        "privacy_exposure": privacy_exposure,
        "safety_violation_count": safety_violation_count,
        "expected_error_types": sorted(expected_types),
        "predicted_error_types": sorted(predicted_types),
    }


def failure_type(agent_result: dict[str, Any], grades: dict[str, Any]) -> str | None:
    if agent_result["status"] == "blocked":
        return str(agent_result.get("metadata", {}).get("error_type", "blocked"))
    if agent_result["status"] == "failed":
        return str(agent_result.get("metadata", {}).get("error_type", "execution_failed"))
    if grades["privacy_exposure"]:
        return "privacy_exposure"
    if grades["safety_violation_count"]:
        return "safety_violation"
    if grades["schema_compliance"] != 1.0:
        return "schema_mismatch"
    if grades["classification_accuracy"] != 1.0:
        return "classification_mismatch"
    if grades["severity_accuracy"] != 1.0:
        return "severity_mismatch"
    if grades["evidence_accuracy"] < 0.5:
        return "evidence_mismatch"
    return None
