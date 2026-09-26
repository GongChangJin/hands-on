from cybersecurity_agent.evaluation import evaluate_fixture
from cybersecurity_agent.models import ExpectedFinding, Finding


def finding(expected_id=None):
    return Finding(
        category="sqli", path="src/app.py", line=1, severity="ERROR",
        message="unsafe", tools=["semgrep"], rule_ids=["rule"], expected_id=expected_id,
    )


def expected():
    return [ExpectedFinding(id="SEC-1", category="sqli", path="src/app.py", line=1, symbol="query")]


def test_evaluation_approves_complete_detection_and_remediation():
    result = evaluate_fixture(expected(), [finding("SEC-1")], [], True, True, True, [{"passed": True}], 1.0, 0.8, 3)
    assert result.decision == "approve"
    assert result.detection_rate == 1.0
    assert result.remediation_rate == 1.0


def test_evaluation_blocks_residual_finding():
    result = evaluate_fixture(expected(), [finding("SEC-1")], [finding("SEC-1")], True, True, True, [{"passed": True}], 1.0, 0.8, 3)
    assert result.decision == "block"
    assert result.residual_expected == 1


def test_evaluation_counts_unexpected_findings():
    result = evaluate_fixture(expected(), [finding("SEC-1"), finding()], [], True, True, True, [{"passed": True}], 1.0, 0.8, 3)
    assert result.false_positives == 1


def test_evaluation_blocks_isolation_failure():
    result = evaluate_fixture(expected(), [finding("SEC-1")], [], True, True, True, [{"passed": False}], 1.0, 0.8, 3)
    assert result.decision == "block"
