from cybersecurity_agent.models import ExpectedFinding
from cybersecurity_agent.scanner import normalize_findings


EXPECTED = [ExpectedFinding(id="SEC-SQL-001", category="sqli", path="src/app.py", line=4, symbol="query")]


def test_normalizer_deduplicates_tools_by_location():
    semgrep = {"results": [{
        "path": "/workspace/src/app.py",
        "start": {"line": 4},
        "check_id": "sql.rule",
        "extra": {"metadata": {"category": "sqli"}, "severity": "ERROR", "message": "unsafe sql"},
    }]}
    bandit = {"results": [{
        "filename": "/workspace/src/app.py",
        "line_number": 4,
        "test_id": "B608",
        "issue_severity": "MEDIUM",
        "issue_text": "sql string",
    }]}
    findings = normalize_findings(semgrep, bandit, EXPECTED)
    assert len(findings) == 1
    assert findings[0].tools == ["bandit", "semgrep"]
    assert findings[0].expected_id == "SEC-SQL-001"


def test_unknown_bandit_rules_are_ignored():
    findings = normalize_findings({}, {"results": [{
        "filename": "/workspace/src/app.py",
        "line_number": 2,
        "test_id": "B101",
        "issue_severity": "LOW",
        "issue_text": "assert",
    }]}, EXPECTED)
    assert findings == []


def test_unexpected_finding_is_marked_as_false_positive_candidate():
    semgrep = {"results": [{
        "path": "/workspace/src/other.py",
        "start": {"line": 1},
        "check_id": "sql.rule",
        "extra": {"metadata": {"category": "sqli"}, "severity": "ERROR", "message": "unsafe"},
    }]}
    finding = normalize_findings(semgrep, {}, EXPECTED)[0]
    assert finding.expected_id is None
    assert finding.path == "src/other.py"
