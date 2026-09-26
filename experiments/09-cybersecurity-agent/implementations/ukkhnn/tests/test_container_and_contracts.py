import json

import pytest

from cybersecurity_agent.container import ContainerPolicyError, ContainerRunner
from cybersecurity_agent.contracts import validate
from cybersecurity_agent.io import load_policy, repo_root
from cybersecurity_agent.report import render_report


def test_container_command_has_required_boundaries(tmp_path):
    command = ContainerRunner(load_policy())._base_command(tmp_path)
    joined = " ".join(command)
    assert command[:3] == ["docker", "run", "--rm"]
    assert "--network none" in joined
    assert "--cap-drop ALL" in joined
    assert "--read-only" in command
    assert ":/workspace:ro" in joined
    assert "--user 65532:65532" in joined


def test_unknown_tool_is_rejected_before_execution(tmp_path):
    with pytest.raises(ContainerPolicyError, match="tool_not_allowed"):
        ContainerRunner(load_policy()).run(tmp_path, "curl", [], {0})


def test_common_contract_accepts_security_request():
    validate("task-request", {
        "task_id": "security-test", "task_type": "security", "input": {},
        "constraints": {"allowed_tools": ["semgrep"], "forbidden_actions": ["network_access"]},
        "expected_output": {"decision": ["approve", "block"]},
    })


def test_coding_handoff_has_five_ready_tasks():
    path = repo_root() / "experiments/08-coding-agent/implementations/ukkhnn/results/reference-replay-v1/cybersecurity-handoff.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert len(payload["tasks"]) == 5
    assert all(item["decision"] == "ready_for_security_review" for item in payload["tasks"])


def test_judge_tests_receive_unique_names_during_handoff_review():
    source = (repo_root() / "experiments/09-cybersecurity-agent/implementations/ukkhnn/src/cybersecurity_agent/agent.py").read_text(encoding="utf-8")
    assert 'f"test_judge_{stem}.py"' in source


def test_report_contains_fixture_and_handoff_metrics():
    summary = {
        "run_id": "test", "fixture": {
            "decision": "approve", "detected_expected": 6, "expected_total": 6,
            "detection_rate": 1.0, "remediated_expected": 6, "remediation_rate": 1.0,
            "false_positives": 0, "all_tests_after": True,
        }, "isolation": {"passed": 3, "total": 3},
    }
    report = render_report(summary, [{"task_id": "coding-1", "decision": "approve", "finding_count": 0, "tests_passed": True}])
    assert "Detection: 6/6" in report
    assert "`coding-1`" in report
