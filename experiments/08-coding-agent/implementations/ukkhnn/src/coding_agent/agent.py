"""Bounded issue-to-patch loop."""

from __future__ import annotations

import difflib
import time
from pathlib import Path

from .models import AgentRun, AttemptRecord, CodingIssue, CodingPolicy
from .policy import PolicyViolation, apply_proposal
from .provider import PatchProvider, ProviderFailure
from .runner import run_lint, run_tests


def changed_paths(base: Path, workspace: Path, allowed_paths: list[str]) -> list[str]:
    changed: list[str] = []
    for relative in allowed_paths:
        original = base / relative
        current = workspace / relative
        original_bytes = original.read_bytes() if original.exists() else None
        current_bytes = current.read_bytes() if current.exists() else None
        if original_bytes != current_bytes:
            changed.append(relative)
    return sorted(changed)


def unified_patch(base: Path, workspace: Path, paths: list[str]) -> str:
    chunks: list[str] = []
    for relative in paths:
        original = base / relative
        current = workspace / relative
        before = original.read_text(encoding="utf-8").splitlines(keepends=True) if original.exists() else []
        after = current.read_text(encoding="utf-8").splitlines(keepends=True) if current.exists() else []
        chunks.extend(
            difflib.unified_diff(
                before,
                after,
                fromfile=f"a/{relative}",
                tofile=f"b/{relative}",
            )
        )
    return "".join(chunks)


def _command_trace(task_id: str, result) -> dict:
    output = (result.stdout or result.stderr).strip().replace("\n", " ")[-500:]
    return {
        "task_id": task_id,
        "tool_name": f"command.{result.name}",
        "input_summary": " ".join(result.command),
        "result_summary": f"exit={result.returncode}; {output}",
        "duration_ms": result.duration_ms,
        "error": None if result.passed else ("timeout" if result.timed_out else f"exit_{result.returncode}"),
        "metadata": {"timed_out": result.timed_out},
    }


class CodingAgent:
    router_capability = "coding"

    def __init__(self, provider: PatchProvider, policy: CodingPolicy):
        self.provider = provider
        self.policy = policy

    def _context(self, issue: CodingIssue, workspace: Path) -> dict[str, str]:
        paths = list(issue.context_paths)
        paths.extend(path for path in issue.allowed_paths if (workspace / path).exists())
        return {
            path: (workspace / path).read_text(encoding="utf-8")
            for path in dict.fromkeys(paths)
        }

    def run(self, issue: CodingIssue, base: Path, workspace: Path) -> AgentRun:
        started = time.perf_counter()
        attempts: list[AttemptRecord] = []
        feedback: list[str] = []
        tool_traces: list[dict] = []
        safety_violations: list[str] = []
        provider_model: str | None = None
        input_tokens = cached_tokens = output_tokens = 0
        cost_usd = 0.0
        success = False
        failure_type: str | None = None
        final_plan: list[str] = []
        final_risks: list[str] = []

        baseline_tests = run_tests(workspace, self.policy.command_timeout_seconds, include_regression=False)
        baseline_lint = run_lint(workspace, self.policy.command_timeout_seconds)
        tool_traces.extend(
            [
                _command_trace(issue.task_id, baseline_tests),
                _command_trace(issue.task_id, baseline_lint),
            ]
        )
        if not baseline_tests.passed or not baseline_lint.passed:
            return AgentRun(
                task_id=issue.task_id,
                success=False,
                attempts=[],
                changed_paths=[],
                patch="",
                provider_model=None,
                latency_ms=(time.perf_counter() - started) * 1000,
                tool_traces=tool_traces,
                failure_type="invalid_fixture_baseline",
            )

        for attempt_number in range(1, self.policy.max_attempts + 1):
            record = AttemptRecord(attempt=attempt_number)
            try:
                provider_result = self.provider.propose(
                    issue,
                    self._context(issue, workspace),
                    feedback,
                    attempt_number,
                )
                provider_model = provider_result.model
                final_plan = provider_result.proposal.plan
                final_risks = provider_result.proposal.risks
                input_tokens += provider_result.input_tokens
                cached_tokens += provider_result.cached_input_tokens
                output_tokens += provider_result.output_tokens
                cost_usd += provider_result.cost_usd
                record.proposal_summary = provider_result.proposal.summary
                record.plan = provider_result.proposal.plan
                record.risks = provider_result.proposal.risks
                tool_traces.append(
                    {
                        "task_id": issue.task_id,
                        "tool_name": "llm.generate_patch",
                        "input_summary": (
                            f"attempt={attempt_number}; "
                            f"context_files={len(self._context(issue, workspace))}"
                        ),
                        "result_summary": f"edits={len(provider_result.proposal.edits)}; model={provider_result.model}",
                        "duration_ms": provider_result.latency_ms,
                        "error": None,
                        "metadata": {
                            "attempt": attempt_number,
                            "input_tokens": provider_result.input_tokens,
                            "cached_input_tokens": provider_result.cached_input_tokens,
                            "output_tokens": provider_result.output_tokens,
                            "cost_usd": provider_result.cost_usd,
                            "provider_request_id": provider_result.request_id,
                            "plan": provider_result.proposal.plan,
                            "risks": provider_result.proposal.risks,
                        },
                    }
                )
                written = apply_proposal(workspace, issue, self.policy, provider_result.proposal)
                record.changed_paths = changed_paths(base, workspace, issue.allowed_paths)
                for relative in written:
                    tool_traces.append(
                        {
                            "task_id": issue.task_id,
                            "tool_name": "repository.write",
                            "input_summary": relative,
                            "result_summary": "file replaced within isolated workspace",
                            "duration_ms": 0.0,
                            "error": None,
                            "metadata": {"attempt": attempt_number},
                        }
                    )
                record.public_tests = run_tests(workspace, self.policy.command_timeout_seconds)
                record.lint = run_lint(workspace, self.policy.command_timeout_seconds)
                tool_traces.extend(
                    [_command_trace(issue.task_id, record.public_tests), _command_trace(issue.task_id, record.lint)]
                )
                attempts.append(record)
                if record.public_tests.passed and record.lint.passed:
                    success = True
                    break
                feedback.append(
                    "The previous patch failed verification. "
                    f"pytest: {(record.public_tests.stdout + record.public_tests.stderr)[-2500:]}; "
                    f"ruff: {(record.lint.stdout + record.lint.stderr)[-1500:]}"
                )
                failure_type = "verification_failed"
            except PolicyViolation as error:
                record.error = str(error)
                attempts.append(record)
                safety_violations.append(str(error))
                feedback.append(f"The previous proposal violated policy: {error}")
                failure_type = "policy_violation"
            except ProviderFailure as error:
                record.error = str(error)
                attempts.append(record)
                feedback.append(str(error))
                failure_type = "provider_failure"

        final_paths = changed_paths(base, workspace, issue.allowed_paths)
        return AgentRun(
            task_id=issue.task_id,
            success=success,
            attempts=attempts,
            changed_paths=final_paths,
            patch=unified_patch(base, workspace, final_paths),
            provider_model=provider_model,
            plan=final_plan,
            risks=final_risks,
            input_tokens=input_tokens,
            cached_input_tokens=cached_tokens,
            output_tokens=output_tokens,
            cost_usd=cost_usd,
            latency_ms=(time.perf_counter() - started) * 1000,
            tool_traces=tool_traces,
            safety_violations=safety_violations,
            failure_type=None if success else (failure_type or "attempt_limit"),
        )
