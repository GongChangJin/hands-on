"""End-to-end deterministic security verification workflow."""

from __future__ import annotations

import difflib
import json
import shutil
import tempfile
from pathlib import Path

from .container import ContainerRunner, make_world_readable
from .evaluation import evaluate_fixture, tool_trace, validate_records
from .io import load_expected, repo_root, shared_dir, write_json, write_jsonl
from .models import SecurityPolicy, ToolExecution
from .report import render_report
from .scanner import SecurityScanner


RUN_ID = "deterministic-container-v1"
IMPLEMENTATION_ID = "ukkhnn:deterministic-security-gate:v1"


def _copytree(source: Path, target: Path) -> None:
    shutil.copytree(
        source,
        target,
        dirs_exist_ok=True,
        ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache", ".ruff_cache", "*.pyc"),
    )


def _patch(before: Path, after: Path, label: str) -> str:
    return "".join(difflib.unified_diff(
        before.read_text(encoding="utf-8").splitlines(keepends=True),
        after.read_text(encoding="utf-8").splitlines(keepends=True),
        fromfile=f"a/{label}",
        tofile=f"b/{label}",
    ))


def _sum_duration(executions: list[ToolExecution]) -> float:
    return sum(item.duration_ms for item in executions)


class CybersecurityAgent:
    def __init__(self, policy: SecurityPolicy):
        self.policy = policy
        self.expected, self.clean_controls = load_expected()
        self.runner = ContainerRunner(policy)
        self.scanner = SecurityScanner(self.runner, self.expected)

    def run(self, output_dir: Path) -> dict:
        output_dir.mkdir(parents=True, exist_ok=True)
        image = self.runner.ensure_image()
        with tempfile.TemporaryDirectory(prefix="gcj-security-") as temporary:
            temporary_root = Path(temporary)
            fixture_result = self._evaluate_fixture(temporary_root / "fixture", output_dir)
            handoffs = self._review_handoffs(temporary_root / "handoffs")
            probes = self.runner.isolation_probes(temporary_root / "fixture")
            evaluation = evaluate_fixture(
                self.expected,
                fixture_result["before"].findings,
                fixture_result["after"].findings,
                fixture_result["functional_before"].exit_code == 0,
                fixture_result["security_before"].exit_code != 0,
                fixture_result["all_after"].exit_code == 0,
                probes,
                self.policy.minimum_detection_rate,
                self.policy.minimum_remediation_rate,
                len(self.clean_controls),
            )
            versions = self.runner.tool_versions(temporary_root / "fixture")

        traces = self._records(output_dir, fixture_result, handoffs, probes, evaluation)
        summary = {
            "run_id": RUN_ID,
            "implementation_id": IMPLEMENTATION_ID,
            "fixture": evaluation.model_dump(),
            "coding_handoffs": {
                "approved": sum(item["decision"] == "approve" for item in handoffs),
                "total": len(handoffs),
            },
            "isolation": {"passed": sum(item["passed"] for item in probes), "total": len(probes)},
            "environment": {"image": image, "tool_versions": versions, "policy": self.policy.model_dump()},
            "tool_trace_count": len(traces),
        }
        write_json(output_dir / "summary.json", summary)
        write_json(output_dir / "environment.json", summary["environment"])
        write_jsonl(output_dir / "isolation-probes.jsonl", probes)
        write_jsonl(output_dir / "handoff-results.jsonl", handoffs)
        (output_dir / "report.md").write_text(render_report(summary, handoffs), encoding="utf-8")
        return summary

    def _evaluate_fixture(self, workspace: Path, output_dir: Path) -> dict:
        _copytree(shared_dir() / "fixture", workspace)
        make_world_readable(workspace)
        functional = self.runner.run(workspace, "pytest", ["-q", "/workspace/tests/functional"], {0})
        security = self.runner.run(workspace, "pytest", ["-q", "/workspace/tests/security"], {0, 1})
        before = self.scanner.scan(workspace)

        patch_dir = output_dir / "patches"
        patch_dir.mkdir(parents=True, exist_ok=True)
        for fixed in sorted((shared_dir() / "fixed" / "src" / "security_lab").glob("*.py")):
            target = workspace / "src" / "security_lab" / fixed.name
            relative = f"src/security_lab/{fixed.name}"
            (patch_dir / f"{fixed.stem}.diff").write_text(_patch(target, fixed, relative), encoding="utf-8")
            shutil.copy2(fixed, target)
        make_world_readable(workspace)
        after = self.scanner.scan(workspace)
        all_after = self.runner.run(workspace, "pytest", ["-q", "/workspace/tests"], {0})
        write_jsonl(output_dir / "findings-before.jsonl", [item.model_dump() for item in before.findings])
        write_jsonl(output_dir / "findings-after.jsonl", [item.model_dump() for item in after.findings])
        return {
            "before": before,
            "after": after,
            "functional_before": functional,
            "security_before": security,
            "all_after": all_after,
        }

    def _review_handoffs(self, root: Path) -> list[dict]:
        experiment08 = repo_root() / "experiments" / "08-coding-agent"
        handoff_path = experiment08 / "implementations" / "ukkhnn" / "results" / "reference-replay-v1" / "cybersecurity-handoff.json"
        payload = json.loads(handoff_path.read_text(encoding="utf-8"))
        rows = []
        for task in payload["tasks"]:
            workspace = root / task["task_id"]
            _copytree(experiment08 / "shared" / "fixture", workspace)
            _copytree(experiment08 / "implementations" / "ukkhnn" / "replay" / task["task_id"], workspace)
            source_path = next(path for path in task["changed_paths"] if path.startswith("src/"))
            stem = Path(source_path).stem
            judge_dir = workspace / "tests" / "judge"
            judge_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(
                experiment08 / "shared" / "judge" / f"test_{stem}.py",
                judge_dir / f"test_judge_{stem}.py",
            )
            make_world_readable(workspace)
            scan = self.scanner.scan(workspace)
            tests = self.runner.run(workspace, "pytest", ["-q", "/workspace/tests"], {0, 1})
            blocking = [item for item in scan.findings if item.severity == "ERROR"]
            upstream_ok = task["decision"] == "ready_for_security_review" and all(task["verification"].values())
            approved = not blocking and tests.exit_code == 0 and upstream_ok
            rows.append({
                "task_id": task["task_id"],
                "source_project": "08-coding-agent",
                "decision": "approve" if approved else "block",
                "finding_count": len(scan.findings),
                "blocking_findings": [item.model_dump() for item in blocking],
                "tests_passed": tests.exit_code == 0,
                "upstream_verification_passed": upstream_ok,
                "scan": scan,
                "test_execution": tests,
            })
        return rows

    def _records(self, output_dir: Path, fixture: dict, handoffs: list[dict], probes: list[dict], evaluation) -> list[dict]:
        fixture_id = "security-fixture-001"
        task_requests = [{
            "task_id": fixture_id,
            "task_type": "security",
            "input": {"fixture": "shared/fixture", "expected_findings": len(self.expected)},
            "attachments": [],
            "constraints": {
                "allowed_tools": self.policy.allowed_tools,
                "forbidden_actions": ["network_access", "host_mount", "privileged_container", "write_source_workspace"],
                "max_steps": 8,
                "max_tool_calls": 8,
            },
            "expected_output": {"decision": ["approve", "block"], "minimum_detection_rate": self.policy.minimum_detection_rate},
            "metadata": {"evaluation_mode": RUN_ID},
        }]
        agent_results = [{
            "task_id": fixture_id,
            "status": "success" if evaluation.decision == "approve" else "failed",
            "output": evaluation.model_dump(),
            "evidence": [
                {"source": "semgrep+bandit", "location": "findings-before.jsonl", "claim": f"detected {evaluation.detected_expected}/{evaluation.expected_total}"},
                {"source": "pytest", "location": "tool-traces.jsonl", "claim": f"post-fix tests passed={evaluation.all_tests_after}"},
            ],
            "actions": ["scan.before", "test.before", "apply.reference_fix", "scan.after", "test.after", "isolation.probe"],
            "limitations": evaluation.remaining_risks,
            "metadata": {"decision": evaluation.decision},
        }]
        fixture_executions = [
            (fixture["functional_before"], "functional tests before remediation"),
            (fixture["security_before"], "security tests demonstrate vulnerabilities"),
            (fixture["before"].semgrep, "scan vulnerable fixture"),
            (fixture["before"].bandit, "scan vulnerable fixture"),
            (fixture["after"].semgrep, "rescan remediated fixture"),
            (fixture["after"].bandit, "rescan remediated fixture"),
            (fixture["all_after"], "security and regression tests after remediation"),
        ]
        traces = [tool_trace(fixture_id, execution, label) for execution, label in fixture_executions]
        evaluations = [{
            "task_id": fixture_id,
            "implementation_id": IMPLEMENTATION_ID,
            "task_success": evaluation.decision == "approve",
            "quality_score": min(evaluation.detection_rate, evaluation.remediation_rate),
            "tool_accuracy": 1.0 if evaluation.false_positives == 0 else evaluation.detected_expected / (evaluation.detected_expected + evaluation.false_positives),
            "latency_ms": _sum_duration([item[0] for item in fixture_executions]),
            "usage": {"model_calls": 0},
            "cost": 0.0,
            "safety_violations": [item["scenario"] for item in probes if not item["passed"]],
            "failure_type": None if evaluation.decision == "approve" else "security_gate_failed",
            "metadata": {"run_id": RUN_ID},
        }]
        serializable_handoffs = []
        for handoff in handoffs:
            task_id = f"security-review-{handoff['task_id']}"
            task_requests.append({
                "task_id": task_id,
                "task_type": "security",
                "input": {"source_task_id": handoff["task_id"], "source_project": "08-coding-agent"},
                "attachments": [],
                "constraints": {"allowed_tools": self.policy.allowed_tools, "forbidden_actions": ["network_access", "host_mount"], "max_steps": 3, "max_tool_calls": 3},
                "expected_output": {"decision": ["approve", "block"]},
                "metadata": {"evaluation_mode": RUN_ID},
            })
            decision = handoff["decision"]
            agent_results.append({
                "task_id": task_id,
                "status": "success" if decision == "approve" else "blocked",
                "output": {key: value for key, value in handoff.items() if key not in {"scan", "test_execution"}},
                "evidence": [{"source": "08-coding-agent", "location": handoff["task_id"], "claim": f"security decision={decision}"}],
                "actions": ["scan.patch", "test.regression"],
                "limitations": ["Static analysis cannot prove the absence of all vulnerabilities."],
                "metadata": {"decision": decision},
            })
            executions = [handoff["scan"].semgrep, handoff["scan"].bandit, handoff["test_execution"]]
            traces.extend(tool_trace(task_id, item, "revalidate Coding Agent handoff") for item in executions)
            evaluations.append({
                "task_id": task_id,
                "implementation_id": IMPLEMENTATION_ID,
                "task_success": decision == "approve",
                "quality_score": 1.0 if decision == "approve" else 0.0,
                "tool_accuracy": 1.0,
                "latency_ms": _sum_duration(executions),
                "usage": {"model_calls": 0},
                "cost": 0.0,
                "safety_violations": [],
                "failure_type": None if decision == "approve" else "security_gate_failed",
                "metadata": {"source_task_id": handoff["task_id"], "finding_count": handoff["finding_count"]},
            })
            serializable_handoffs.append({key: value for key, value in handoff.items() if key not in {"scan", "test_execution"}})
        validate_records("task-request", task_requests)
        validate_records("agent-result", agent_results)
        validate_records("evaluation-record", evaluations)
        write_jsonl(output_dir / "task-requests.jsonl", task_requests)
        write_jsonl(output_dir / "agent-results.jsonl", agent_results)
        write_jsonl(output_dir / "tool-traces.jsonl", traces)
        write_jsonl(output_dir / "evaluation-records.jsonl", evaluations)
        handoffs[:] = serializable_handoffs
        return traces
