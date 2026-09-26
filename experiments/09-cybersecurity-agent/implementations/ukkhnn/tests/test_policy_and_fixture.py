import json

from cybersecurity_agent.io import load_expected, load_policy, repo_root, shared_dir


def test_policy_enforces_isolation_and_allowlist():
    policy = load_policy()
    assert policy.network == "none"
    assert policy.read_only_root is True
    assert policy.cap_drop == ["ALL"]
    assert policy.allowed_tools == ["semgrep", "bandit", "pytest"]


def test_tool_versions_are_pinned():
    policy = load_policy()
    assert (policy.semgrep_version, policy.bandit_version, policy.pytest_version) == ("1.178.0", "1.9.4", "9.1.1")


def test_expected_fixture_has_six_findings_and_three_controls():
    expected, controls = load_expected()
    assert len(expected) == 6
    assert len(controls) == 3
    assert {item.category for item in expected} == {"sqli", "path_traversal", "hardcoded_secret"}


def test_expected_lines_match_fixture_source():
    expected, _ = load_expected()
    for finding in expected:
        line = (shared_dir() / "fixture" / finding.path).read_text(encoding="utf-8").splitlines()[finding.line - 1]
        assert finding.symbol.split("_")[0] in line.lower() or finding.category in {"sqli", "path_traversal"}


def test_only_fake_secrets_are_committed():
    source = (shared_dir() / "fixture" / "src/security_lab/secrets.py").read_text(encoding="utf-8")
    payload = json.loads((shared_dir() / "expected-findings.json").read_text(encoding="utf-8"))
    assert "fake_" in source
    assert "not real secrets" in source
    assert len(payload["vulnerabilities"]) == 6


def test_repository_root_contains_common_contracts():
    assert (repo_root() / "common/contracts/task-request.schema.json").is_file()
