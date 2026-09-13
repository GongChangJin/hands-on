"""One traced workflow from TaskRequest through deterministic evaluation."""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

from .contracts import validate_contract
from .grading import failure_type, grade
from .observability import span
from .parsing import OutputParseError, parse_analysis
from .paths import CONTEXT_DIR, PROJECT_DIR
from .preprocessing import ImageSafetyError, preprocess_image
from .privacy import scan_texts
from .provider import ProviderFailure
from .prompts import PROMPT_VERSION, build_prompt
from .types import RunOutcome, Usage, VisionGateway


def _tool_trace(
    task_id: str,
    tool_name: str,
    *,
    input_summary: str,
    result_summary: str,
    duration_ms: float,
    error: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    value = {
        "task_id": task_id,
        "tool_name": tool_name,
        "input_summary": input_summary,
        "result_summary": result_summary,
        "duration_ms": max(0.0, duration_ms),
        "error": error,
        "metadata": metadata or {},
    }
    validate_contract("tool-trace", value)
    return value


def _failed_result(task_id: str, *, status: str, error_type: str, message: str) -> dict[str, Any]:
    result = {
        "task_id": task_id,
        "status": status,
        "output": None,
        "evidence": [],
        "actions": [],
        "limitations": [message],
        "metadata": {"error_type": error_type},
    }
    validate_contract("agent-result", result)
    return result


def _success_result(
    task_id: str,
    analysis: dict[str, Any],
    *,
    condition: str,
    model: str,
    image_hash: str,
) -> dict[str, Any]:
    evidence = [
        {"source": "synthetic_ui_image", "location": item["region"], "claim": item["claim"]}
        for error in analysis["errors"]
        for item in error["evidence"]
    ]
    result = {
        "task_id": task_id,
        "status": "success",
        "output": analysis,
        "evidence": evidence,
        "actions": [item["suggested_fix"] for item in analysis["errors"]],
        "limitations": [item["uncertainty"] for item in analysis["errors"]],
        "metadata": {
            "provider": "deepseek",
            "model": model,
            "condition": condition,
            "image_sha256": image_hash,
            "prompt_version": PROMPT_VERSION,
        },
    }
    validate_contract("agent-result", result)
    return result


def _load_context(path_value: str | None) -> dict[str, Any] | None:
    if path_value is None:
        return None
    candidate = Path(path_value)
    if not candidate.is_absolute():
        candidate = PROJECT_DIR / candidate
    if candidate.is_symlink():
        raise ImageSafetyError("context_symlink_rejected", "symlink context는 허용하지 않습니다.")
    try:
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(CONTEXT_DIR.resolve(strict=True))
    except (FileNotFoundError, ValueError) as exc:
        raise ImageSafetyError("invalid_context_path", "허용된 context 파일이 아닙니다.") from exc
    value = json.loads(resolved.read_text(encoding="utf-8"))
    required = {"fixture_id", "user_description", "dom_summary", "accessibility_snapshot"}
    if not isinstance(value, dict) or not required.issubset(value):
        raise ImageSafetyError("invalid_context", "context schema가 올바르지 않습니다.")
    return value


class MultimodalAgent:
    def __init__(self, gateway: VisionGateway) -> None:
        self.gateway = gateway

    async def run(self, task: dict[str, Any]) -> RunOutcome:
        validate_contract("task-request", task)
        task_id = task["task_id"]
        if task["task_type"] != "vision" or not isinstance(task["input"], dict):
            raise ValueError("멀티모달 Agent는 object input의 vision TaskRequest만 처리합니다.")
        condition = str(task["input"].get("condition"))
        image_value = str(task["input"].get("image_path", ""))
        image_path = Path(image_value)
        if not image_path.is_absolute():
            image_path = PROJECT_DIR / image_path

        started = time.perf_counter()
        traces: list[dict[str, Any]] = []
        usage = Usage()
        cost_usd: float | None = None
        pricing_tier: str | None = None
        model_called = False
        privacy_passed = False
        safety_violations: list[str] = []
        agent_result: dict[str, Any]

        with span(
            "multimodal.workflow",
            task_id=task_id,
            condition=condition,
            provider="deepseek",
            model=self.gateway.model_name,
            project="04-multimodal-agent",
            protocol_provider="openai-compatible",
            actual_endpoint_provider="deepseek",
        ) as workflow_span:
            step_started = time.perf_counter()
            try:
                with span("image.preprocess", task_id=task_id, condition=condition):
                    prepared = preprocess_image(image_path)
            except ImageSafetyError as exc:
                duration = (time.perf_counter() - step_started) * 1000
                traces.append(
                    _tool_trace(
                        task_id,
                        "image_preprocessor",
                        input_summary="candidate fixture image",
                        result_summary="blocked before model call",
                        duration_ms=duration,
                        error=exc.code,
                    )
                )
                agent_result = _failed_result(task_id, status="blocked", error_type=exc.code, message=str(exc))
            else:
                duration = (time.perf_counter() - step_started) * 1000
                traces.append(
                    _tool_trace(
                        task_id,
                        "image_preprocessor",
                        input_summary=f"fixture {prepared.relative_path}",
                        result_summary="validated and normalized to metadata-free PNG",
                        duration_ms=duration,
                        metadata={
                            "file_path": prepared.relative_path,
                            "image_sha256": prepared.sha256,
                            "width": prepared.width,
                            "height": prepared.height,
                            "mime_type": "image/png",
                            "source_bytes": prepared.source_bytes,
                            "normalized_bytes": len(prepared.png_bytes),
                            "metadata_removed_count": len(prepared.metadata_removed),
                        },
                    )
                )

                step_started = time.perf_counter()
                try:
                    context = _load_context(task["input"].get("context_path"))
                except (ImageSafetyError, json.JSONDecodeError) as exc:
                    code = exc.code if isinstance(exc, ImageSafetyError) else "invalid_context_json"
                    duration = (time.perf_counter() - step_started) * 1000
                    traces.append(
                        _tool_trace(
                            task_id,
                            "privacy_scanner",
                            input_summary="fixture text manifest and compact context",
                            result_summary="blocked before model call",
                            duration_ms=duration,
                            error=code,
                        )
                    )
                    agent_result = _failed_result(task_id, status="blocked", error_type=code, message="context를 안전하게 검증할 수 없습니다.")
                else:
                    scan_values = [
                        ("image_manifest", str(value))
                        for value in prepared.label.get("visible_text", [])
                    ]
                    if context is not None:
                        scan_values.extend((f"context.{key}", str(value)) for key, value in context.items())
                    with span(
                        "privacy.scan",
                        task_id=task_id,
                        image_sha256=prepared.sha256,
                        scanned_value_count=len(scan_values),
                    ):
                        findings = scan_texts(scan_values)
                    duration = (time.perf_counter() - step_started) * 1000
                    privacy_passed = not findings
                    traces.append(
                        _tool_trace(
                            task_id,
                            "privacy_scanner",
                            input_summary="integrity-bound visible text and compact context",
                            result_summary="passed" if privacy_passed else "blocked before model call",
                            duration_ms=duration,
                            error=None if privacy_passed else "privacy_pattern_detected",
                            metadata={
                                "finding_count": len(findings),
                                "finding_types": sorted({finding.kind for finding in findings}),
                                "image_sha256": prepared.sha256,
                            },
                        )
                    )
                    if findings:
                        agent_result = _failed_result(
                            task_id,
                            status="blocked",
                            error_type="privacy_pattern_detected",
                            message="개인정보 또는 비밀 형태 문자열이 탐지되어 모델 호출을 차단했습니다.",
                        )
                    else:
                        prompt = build_prompt(condition, context)
                        step_started = time.perf_counter()
                        try:
                            with span(
                                "deepseek.vision",
                                task_id=task_id,
                                condition=condition,
                                provider="deepseek",
                                protocol_provider="openai-compatible",
                                actual_endpoint="api.deepseek.com",
                                model=self.gateway.model_name,
                                file_path=prepared.relative_path,
                                image_sha256=prepared.sha256,
                                width=prepared.width,
                                height=prepared.height,
                                mime_type="image/png",
                                prompt_version=PROMPT_VERSION,
                                context_sha256=(hashlib.sha256(json.dumps(context, sort_keys=True).encode()).hexdigest() if context else "none"),
                            ) as model_span:
                                model_called = True
                                raw = await self.gateway.analyze(image=prepared, prompt=prompt)
                                model_span.set_attributes(
                                    {
                                        "llm.token_count.input": raw.usage.input_tokens,
                                        "llm.token_count.output": raw.usage.output_tokens,
                                        "llm.token_count.total": raw.usage.total_tokens,
                                        "llm.cost_usd": raw.cost_usd,
                                        "llm.latency_ms": raw.latency_ms,
                                    }
                                )
                        except ProviderFailure as exc:
                            duration = (time.perf_counter() - step_started) * 1000
                            traces.append(
                                _tool_trace(
                                    task_id,
                                    "deepseek_vision",
                                    input_summary=f"sanitized PNG, {condition}",
                                    result_summary="provider call failed and was preserved",
                                    duration_ms=duration,
                                    error=exc.kind,
                                    metadata={"provider": "deepseek", "model": self.gateway.model_name, "endpoint": "api.deepseek.com"},
                                )
                            )
                            agent_result = _failed_result(task_id, status="failed", error_type=exc.kind, message=str(exc))
                        except Exception as exc:  # provider fakes and unexpected SDK failures are still preserved
                            duration = (time.perf_counter() - step_started) * 1000
                            error_type = f"provider_exception:{type(exc).__name__}"
                            traces.append(
                                _tool_trace(
                                    task_id,
                                    "deepseek_vision",
                                    input_summary=f"sanitized PNG, {condition}",
                                    result_summary="unexpected provider failure preserved",
                                    duration_ms=duration,
                                    error=error_type,
                                )
                            )
                            agent_result = _failed_result(task_id, status="failed", error_type=error_type, message="예상하지 못한 model provider 오류가 발생했습니다.")
                        else:
                            usage = raw.usage
                            cost_usd = raw.cost_usd
                            pricing_tier = raw.pricing_tier
                            traces.append(
                                _tool_trace(
                                    task_id,
                                    "deepseek_vision",
                                    input_summary=f"sanitized PNG, {condition}",
                                    result_summary="structured response received",
                                    duration_ms=raw.latency_ms,
                                    metadata={
                                        "provider": "deepseek",
                                        "protocol_provider": "openai-compatible",
                                        "endpoint": "api.deepseek.com",
                                        "model": raw.model,
                                        "input_tokens": usage.input_tokens,
                                        "output_tokens": usage.output_tokens,
                                        "cached_input_tokens": usage.cached_input_tokens,
                                        "total_tokens": usage.total_tokens,
                                        "cost_usd": cost_usd,
                                        "pricing_tier": pricing_tier,
                                    },
                                )
                            )
                            step_started = time.perf_counter()
                            try:
                                with span("output.parse", task_id=task_id, model=raw.model):
                                    analysis = parse_analysis(raw.content)
                            except OutputParseError as exc:
                                duration = (time.perf_counter() - step_started) * 1000
                                traces.append(
                                    _tool_trace(
                                        task_id,
                                        "output_parser",
                                        input_summary="model response text (not retained)",
                                        result_summary="invalid model output preserved as failure",
                                        duration_ms=duration,
                                        error="output_parse_error",
                                    )
                                )
                                agent_result = _failed_result(task_id, status="failed", error_type="output_parse_error", message=str(exc))
                            else:
                                duration = (time.perf_counter() - step_started) * 1000
                                traces.append(
                                    _tool_trace(
                                        task_id,
                                        "output_parser",
                                        input_summary="model response text (not retained)",
                                        result_summary="valid multimodal analysis",
                                        duration_ms=duration,
                                    )
                                )
                                agent_result = _success_result(
                                    task_id,
                                    analysis,
                                    condition=condition,
                                    model=raw.model,
                                    image_hash=prepared.sha256,
                                )

            grading_started = time.perf_counter()
            with span("evaluation.deterministic", task_id=task_id, grader="fixed-label-v1"):
                grades = grade(
                    task,
                    agent_result,
                    model_called=model_called,
                    privacy_passed=privacy_passed,
                    safety_violations=safety_violations,
                )
            traces.append(
                _tool_trace(
                    task_id,
                    "deterministic_grader",
                    input_summary="AgentResult and fixed expected label",
                    result_summary="pass" if grades["task_success"] else "failure preserved",
                    duration_ms=(time.perf_counter() - grading_started) * 1000,
                    metadata={
                        "classification_accuracy": grades["classification_accuracy"],
                        "schema_compliance": grades["schema_compliance"],
                        "evidence_accuracy": grades["evidence_accuracy"],
                        "privacy_exposure": grades["privacy_exposure"],
                        "safety_violation_count": grades["safety_violation_count"],
                    },
                )
            )
            total_latency = (time.perf_counter() - started) * 1000
            failure = failure_type(agent_result, grades)
            record = {
                "task_id": task_id,
                "implementation_id": f"ukkhnn:deepseek:{self.gateway.model_name}:{condition}",
                "task_success": grades["task_success"],
                "quality_score": grades["quality_score"],
                "tool_accuracy": grades["classification_accuracy"],
                "latency_ms": total_latency,
                "usage": usage.as_dict(),
                "cost": cost_usd,
                "safety_violations": safety_violations,
                "failure_type": failure,
                "metadata": {
                    "condition": condition,
                    "provider": "deepseek",
                    "protocol_provider": "openai-compatible",
                    "actual_endpoint_provider": "deepseek",
                    "endpoint": "api.deepseek.com",
                    "model": self.gateway.model_name,
                    "pricing_tier": pricing_tier,
                    "cost_basis": "provider-reported tokens and published rates" if cost_usd is not None else None,
                    "model_called": model_called,
                    "privacy_passed": privacy_passed,
                    "graders": grades,
                    "agent_result": agent_result,
                    "tool_traces": traces,
                },
            }
            validate_contract("evaluation-record", record)
            workflow_span.set_attributes(
                {
                    "workflow.latency_ms": total_latency,
                    "workflow.task_success": grades["task_success"],
                    "workflow.failure_type": failure or "none",
                    "workflow.model_called": model_called,
                    "workflow.privacy_passed": privacy_passed,
                }
            )
        return RunOutcome(
            agent_result=agent_result,
            tool_traces=traces,
            evaluation_record=record,
            usage=usage,
            cost_usd=cost_usd,
        )
