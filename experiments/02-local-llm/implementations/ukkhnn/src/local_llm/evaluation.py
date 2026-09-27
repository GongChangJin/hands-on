"""Deterministic parsing and grading."""

from __future__ import annotations

import json
import math
import re
from typing import Any

from .contracts import validate_contract, validate_output
from .types import GenerationResponse


SECRET_PATTERNS = (
    re.compile(r"(?:UPSTAGE|OPENAI|DEEPSEEK)_API_KEY\s*=\s*\S+", re.IGNORECASE),
    re.compile(r"\bsk-[A-Za-z0-9_-]{12,}\b"),
    re.compile(r"BEGIN (?:RSA |EC )?PRIVATE KEY"),
)


def parse_json_object(text: str) -> tuple[dict[str, Any] | None, str | None]:
    try:
        value = json.loads(text)
    except json.JSONDecodeError as error:
        return None, f"invalid_json:{error.msg}"
    if not isinstance(value, dict):
        return None, "invalid_json:top_level_must_be_object"
    return value, None


def _normalize(value: Any) -> Any:
    if isinstance(value, str):
        return " ".join(value.strip().casefold().split())
    if isinstance(value, list):
        return [_normalize(item) for item in value]
    if isinstance(value, dict):
        return {key: _normalize(item) for key, item in sorted(value.items())}
    if isinstance(value, float) and math.isfinite(value) and value.is_integer():
        return int(value)
    return value


def exact_answer_match(actual: Any, expected: Any) -> bool:
    return _normalize(actual) == _normalize(expected)


def find_safety_violations(text: str) -> list[str]:
    return [f"secret_pattern:{index}" for index, pattern in enumerate(SECRET_PATTERNS, start=1) if pattern.search(text)]


def build_run_records(
    task: dict[str, Any],
    response: GenerationResponse,
    *,
    implementation_id: str,
    adapter_name: str,
    repetition: int,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    parsed, parse_error = parse_json_object(response.text) if not response.error else (None, None)
    expected = task["expected_output"]
    schema_errors = validate_output(expected["response_schema"], parsed) if parsed is not None else []
    schema_pass = parsed is not None and not schema_errors
    answer_match = schema_pass and exact_answer_match(parsed.get("answer"), expected["expected_answer"])
    safety_violations = find_safety_violations(response.text)
    task_success = bool(answer_match and not response.error and not safety_violations)
    if response.error:
        failure_type = "adapter_error"
    elif parse_error:
        failure_type = "json_parse_error"
    elif schema_errors:
        failure_type = "schema_error"
    elif safety_violations:
        failure_type = "safety_violation"
    elif not answer_match:
        failure_type = "answer_mismatch"
    else:
        failure_type = None

    agent_result = {
        "task_id": task["task_id"],
        "status": "success" if task_success else "failed",
        "output": parsed if parsed is not None else response.text,
        "evidence": [],
        "actions": [f"{adapter_name}.generate"],
        "limitations": [failure_type] if failure_type else [],
        "metadata": {
            "model": response.model,
            "repetition": repetition,
            "schema_pass": schema_pass,
            "answer_match": answer_match,
            "raw_response": response.text,
            "adapter_error": response.error,
        },
    }
    tool_trace = {
        "task_id": task["task_id"],
        "tool_name": f"llm.{adapter_name}.generate",
        "input_summary": f"category={task.get('metadata', {}).get('category', 'unknown')}",
        "result_summary": "success" if response.error is None else "failed",
        "duration_ms": response.total_latency_ms,
        "error": response.error,
        "metadata": {
            "model": response.model,
            "first_token_latency_ms": response.first_token_latency_ms,
            "prompt_tokens": response.prompt_tokens,
            "output_tokens": response.output_tokens,
            "generation_tokens_per_second": response.generation_tokens_per_second,
            "load_duration_ms": response.load_duration_ms,
            "prompt_eval_duration_ms": response.prompt_eval_duration_ms,
            "generation_duration_ms": response.generation_duration_ms,
            **response.metadata,
        },
    }
    evaluation_record = {
        "task_id": task["task_id"],
        "implementation_id": implementation_id,
        "task_success": task_success,
        "quality_score": 1.0 if answer_match else 0.0,
        "tool_accuracy": 1.0,
        "latency_ms": response.total_latency_ms,
        "usage": {
            "requests": 1,
            "input_tokens": response.prompt_tokens,
            "output_tokens": response.output_tokens,
            "total_tokens": response.prompt_tokens + response.output_tokens,
        },
        "cost": response.cost_usd,
        "safety_violations": safety_violations,
        "failure_type": failure_type,
        "metadata": {
            "category": task.get("metadata", {}).get("category"),
            "adapter": adapter_name,
            "model": response.model,
            "repetition": repetition,
            "schema_pass": schema_pass,
            "answer_match": answer_match,
            "first_token_latency_ms": response.first_token_latency_ms,
            "generation_tokens_per_second": response.generation_tokens_per_second,
        },
    }
    for name, record in (
        ("agent-result", agent_result),
        ("tool-trace", tool_trace),
        ("evaluation-record", evaluation_record),
    ):
        validate_contract(name, record)
    return agent_result, tool_trace, evaluation_record
