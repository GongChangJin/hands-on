"""Issue evaluation, held-out judging, contract export, and aggregation."""

from __future__ import annotations

import math
import shutil
import tempfile
from pathlib import Path
from statistics import mean
from typing import Any

from .agent import CodingAgent, _command_trace
from .contracts import validate
from .io import implementation_dir, shared_dir, write_json, write_jsonl
from .models import CodingIssue, CodingPolicy, EvaluationRun
from .runner import run_fixed, run_lint, run_single_regression

IGNORED_PATH_PARTS = {".pytest_cache", ".ruff_cache", "__pycache__"}


def percentile(values: list[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    rank = (len(ordered) - 1) * fraction
    lower, upper = math.floor(rank), math.ceil(rank)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (rank - lower)


def _files(root: Path) -> dict[str, bytes]:
    result: dict[str, bytes] = {}
    for path in root.rglob("*"):
        if not path.is_file() or any(part in IGNORED_PATH_PARTS for part in path.parts):
            continue
        result[path.relative_to(root).as_posix()] = path.read_bytes()
    return result


def all_changed_paths(base: Path, workspace: Path) -> list[str]:
    before = _files(base)
    after = _files(workspace)
    return sorted(path for path in before.keys() | after.keys() if before.get(path) != after.get(path))


def task_request(issue: CodingIssue, policy: CodingPolicy) -> dict[str, Any]:
    return {
        "task_id": issue.task_id,
        "task_type": "coding",
        "input": {
            "title": issue.title,
            "description": issue.description,
            "acceptance_criteria": issue.acceptance_criteria,
            "context_paths": issue.context_paths,
        },
        "attachments": [],
        "constraints": {
            "allowed_tools": policy.allowed_tools,
            "forbidden_actions": policy.forbidden_actions,
            "max_steps": policy.max_attempts,
            "max_tool_calls": policy.max_attempts * 4 + 6,
        },
        "expected_output": {
            "allowed_paths": issue.allowed_paths,
            "regression_test_path": issue.regression_test_path,
            "verification": ["public_tests", "regression_test", "held_out_tests", "ruff", "scope"],
        },
        "metadata": {"router_capability": "coding", "held_out_tests_in_prompt": False},
    }


def _run_test_path(workspace: Path, path: str, policy: CodingPolicy, name: str):
    return run_fixed(name, ["pytest", "-q", path], workspace, policy.command_timeout_seconds)


def evaluate_issue(
    issue: CodingIssue,
    policy: CodingPolicy,
    agent: CodingAgent,
    output_root: Path,
) -> EvaluationRun:
    fixture = shared_dir() / "fixture"
    with tempfile.TemporaryDirectory(prefix=f"gcj-{issue.task_id}-") as temporary:
        temporary_root = Path(temporary)
        base = temporary_root / "base"
        workspace = temporary_root / "workspace"
        shutil.copytree(fixture, base)
        shutil.copytree(fixture, workspace)

        agent_run = agent.run(issue, base, workspace)
        agent_changed_paths = all_changed_paths(base, workspace)
        patch_path = output_root / "patches" / f"{issue.task_id}.diff"
        patch_path.parent.mkdir(parents=True, exist_ok=True)
        patch_path.write_text(agent_run.patch, encoding="utf-8")

        regression_path = workspace / issue.regression_test_path
        regression_test_added = regression_path.is_file() and "def test_" in regression_path.read_text(encoding="utf-8")

        pristine = temporary_root / "pristine"
        shutil.copytree(fixture, pristine)
        if regression_path.exists():
            pristine_regression = pristine / issue.regression_test_path
            pristine_regression.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(regression_path, pristine_regression)
            original_regression = run_single_regression(
                pristine,
                issue.regression_test_path,
                policy.command_timeout_seconds,
            )
            regression_test_catches_bug = not original_regression.passed
        else:
            original_regression = None
            regression_test_catches_bug = False

        judge_dir = workspace / "tests" / "judge"
        judge_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(shared_dir() / "judge" / issue.judge_file, judge_dir / issue.judge_file)

        public_result = _run_test_path(workspace, "tests/public", policy, "pytest-public")
        regression_result = _run_test_path(
            workspace,
            issue.regression_test_path,
            policy,
            "pytest-regression",
        )
        judge_result = _run_test_path(workspace, "tests/judge", policy, "pytest-held-out")
        lint_result = run_lint(workspace, policy.command_timeout_seconds)

        scope_passed = (
            set(agent_changed_paths) <= set(issue.allowed_paths)
            and len(agent_changed_paths) <= policy.max_changed_files
        )
        forbidden_git_actions = 0
        safety_violations = list(agent_run.safety_violations)
        if not scope_passed:
            safety_violations.append("unrelated_change")
        if (workspace / ".git").exists():
            safety_violations.append("git_state_created")

        tool_traces = list(agent_run.tool_traces)
        if original_regression is not None:
            tool_traces.append(_command_trace(issue.task_id, original_regression))
        tool_traces.extend(
            _command_trace(issue.task_id, result)
            for result in (public_result, regression_result, judge_result, lint_result)
        )

        success = all(
            [
                agent_run.success,
                public_result.passed,
                regression_result.passed,
                judge_result.passed,
                lint_result.passed,
                regression_test_added,
                regression_test_catches_bug,
                scope_passed,
                forbidden_git_actions == 0,
                not safety_violations,
            ]
        )
        if success:
            failure_type = None
        elif safety_violations:
            failure_type = "safety_violation"
        elif not judge_result.passed:
            failure_type = "held_out_test_failure"
        elif not regression_test_catches_bug:
            failure_type = "weak_regression_test"
        else:
            failure_type = agent_run.failure_type or "verification_failure"

        request = task_request(issue, policy)
        result = {
            "task_id": issue.task_id,
            "status": "success" if success else "failed",
            "output": {
                "patch_path": f"patches/{issue.task_id}.diff",
                "changed_paths": agent_changed_paths,
                "public_tests_passed": public_result.passed,
                "regression_tests_passed": regression_result.passed,
                "held_out_tests_passed": judge_result.passed,
                "lint_passed": lint_result.passed,
                "regression_test_catches_bug": regression_test_catches_bug,
                "plan": agent_run.plan,
                "remaining_risks": agent_run.risks,
            },
            "evidence": [
                {
                    "source": "patch",
                    "location": f"patches/{issue.task_id}.diff",
                    "claim": f"changed only {', '.join(agent_changed_paths) or 'no files'}",
                },
                {
                    "source": "held_out_tests",
                    "location": issue.judge_file,
                    "claim": f"exit={judge_result.returncode}",
                },
            ],
            "actions": [trace["tool_name"] for trace in tool_traces],
            "limitations": (
                ([failure_type or "unknown_failure"] if not success else [])
                + agent_run.risks
            ),
            "metadata": {
                "router_capability": "coding",
                "provider_model": agent_run.provider_model,
                "attempts": len(agent_run.attempts),
                "held_out_tests_in_prompt": False,
                "forbidden_git_actions": forbidden_git_actions,
            },
        }
        quality_checks = [
            public_result.passed,
            regression_result.passed,
            judge_result.passed,
            lint_result.passed,
            regression_test_catches_bug,
        ]
        record = {
            "task_id": issue.task_id,
            "implementation_id": f"ukkhnn:bounded-coding:{agent_run.provider_model or 'unknown'}",
            "task_success": success,
            "quality_score": sum(quality_checks) / len(quality_checks),
            "tool_accuracy": 1.0 if scope_passed and not safety_violations else 0.0,
            "latency_ms": agent_run.latency_ms,
            "usage": {
                "attempts": len(agent_run.attempts),
                "input_tokens": agent_run.input_tokens,
                "cached_input_tokens": agent_run.cached_input_tokens,
                "output_tokens": agent_run.output_tokens,
            },
            "cost": agent_run.cost_usd,
            "safety_violations": safety_violations,
            "failure_type": failure_type,
            "metadata": {
                "changed_paths": agent_changed_paths,
                "scope_passed": scope_passed,
                "regression_test_added": regression_test_added,
                "regression_test_catches_bug": regression_test_catches_bug,
                "forbidden_git_actions": forbidden_git_actions,
            },
        }
        validate("task-request", request)
        validate("agent-result", result)
        validate("evaluation-record", record)
        for trace in tool_traces:
            validate("tool-trace", trace)

        return EvaluationRun(
            task_id=issue.task_id,
            success=success,
            attempts=len(agent_run.attempts),
            changed_paths=agent_changed_paths,
            patch_path=f"patches/{issue.task_id}.diff",
            public_tests_passed=public_result.passed,
            regression_tests_passed=regression_result.passed,
            held_out_tests_passed=judge_result.passed,
            lint_passed=lint_result.passed,
            regression_test_added=regression_test_added,
            regression_test_catches_bug=regression_test_catches_bug,
            scope_passed=scope_passed,
            forbidden_git_actions=forbidden_git_actions,
            latency_ms=agent_run.latency_ms,
            input_tokens=agent_run.input_tokens,
            cached_input_tokens=agent_run.cached_input_tokens,
            output_tokens=agent_run.output_tokens,
            cost_usd=agent_run.cost_usd,
            failure_type=failure_type,
            safety_violations=safety_violations,
            task_request=request,
            agent_result=result,
            tool_traces=tool_traces,
            evaluation_record=record,
        )


def summarize(runs: list[EvaluationRun]) -> dict[str, Any]:
    latencies = [run.latency_ms for run in runs]
    return {
        "tasks": len(runs),
        "successful_tasks": sum(run.success for run in runs),
        "success_rate": sum(run.success for run in runs) / len(runs) if runs else 0.0,
        "public_test_pass_rate": sum(run.public_tests_passed for run in runs) / len(runs) if runs else 0.0,
        "regression_test_pass_rate": sum(run.regression_tests_passed for run in runs) / len(runs) if runs else 0.0,
        "held_out_test_pass_rate": sum(run.held_out_tests_passed for run in runs) / len(runs) if runs else 0.0,
        "lint_pass_rate": sum(run.lint_passed for run in runs) / len(runs) if runs else 0.0,
        "regression_test_catches_bug_rate": (
            sum(run.regression_test_catches_bug for run in runs) / len(runs)
            if runs
            else 0.0
        ),
        "scope_pass_rate": sum(run.scope_passed for run in runs) / len(runs) if runs else 0.0,
        "average_attempts": mean(run.attempts for run in runs) if runs else 0.0,
        "latency_p50_ms": percentile(latencies, 0.50),
        "latency_p95_ms": percentile(latencies, 0.95),
        "input_tokens": sum(run.input_tokens for run in runs),
        "cached_input_tokens": sum(run.cached_input_tokens for run in runs),
        "output_tokens": sum(run.output_tokens for run in runs),
        "cost_usd": sum(run.cost_usd for run in runs),
        "safety_violation_count": sum(len(run.safety_violations) for run in runs),
        "forbidden_git_actions": sum(run.forbidden_git_actions for run in runs),
        "failures": [
            {"task_id": run.task_id, "failure_type": run.failure_type}
            for run in runs
            if not run.success
        ],
    }


def export_results(output_root: Path, runs: list[EvaluationRun]) -> dict[str, Any]:
    from .report import evaluation_report

    output_root.mkdir(parents=True, exist_ok=True)
    summary = summarize(runs)
    write_jsonl(output_root / "task-runs.jsonl", [run.model_dump(mode="json") for run in runs])
    write_jsonl(output_root / "task-requests.jsonl", [run.task_request for run in runs])
    write_jsonl(output_root / "agent-results.jsonl", [run.agent_result for run in runs])
    write_jsonl(output_root / "evaluation-records.jsonl", [run.evaluation_record for run in runs])
    write_jsonl(output_root / "tool-traces.jsonl", [trace for run in runs for trace in run.tool_traces])
    write_json(output_root / "summary.json", summary)
    write_json(
        output_root / "cybersecurity-handoff.json",
        {
            "schema_version": "1.0",
            "source_project": "08-coding-agent",
            "evaluation_mode": "reference-replay-v1",
            "limitations": [
                "Frozen reference patches validate the control plane, not live model generation quality."
            ],
            "tasks": [
                {
                    "task_id": run.task_id,
                    "decision": "ready_for_security_review" if run.success else "blocked",
                    "patch_path": run.patch_path,
                    "changed_paths": run.changed_paths,
                    "verification": {
                        "public_tests": run.public_tests_passed,
                        "regression_tests": run.regression_tests_passed,
                        "held_out_tests": run.held_out_tests_passed,
                        "lint": run.lint_passed,
                        "scope": run.scope_passed,
                    },
                    "safety_violations": run.safety_violations,
                }
                for run in runs
            ],
        },
    )
    (output_root / "report.md").write_text(evaluation_report(summary, runs), encoding="utf-8")
    return summary


def relative_output(path: Path) -> str:
    try:
        return path.resolve().relative_to(implementation_dir().resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()
