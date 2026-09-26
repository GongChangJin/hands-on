"""Semgrep and Bandit execution plus normalized finding deduplication."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from .container import ContainerRunner
from .models import ExpectedFinding, Finding, ScanResult


def _relative(value: str) -> str:
    marker = "/workspace/"
    return value.split(marker, 1)[1] if marker in value else value.lstrip("./")


def _bandit_category(rule_id: str) -> str | None:
    if rule_id == "B608":
        return "sqli"
    if rule_id in {"B105", "B106", "B107"}:
        return "hardcoded_secret"
    return None


def normalize_findings(
    semgrep_payload: dict,
    bandit_payload: dict,
    expected: list[ExpectedFinding],
) -> list[Finding]:
    """Merge tool-specific output into stable findings keyed by location."""
    grouped: dict[tuple[str, str, int], list[dict]] = defaultdict(list)
    for item in semgrep_payload.get("results", []):
        category = str(item.get("extra", {}).get("metadata", {}).get("category", "unknown"))
        grouped[(category, _relative(item["path"]), int(item["start"]["line"]))].append({
            "tool": "semgrep",
            "rule_id": item["check_id"],
            "severity": item.get("extra", {}).get("severity", "WARNING"),
            "message": item.get("extra", {}).get("message", ""),
        })
    for item in bandit_payload.get("results", []):
        category = _bandit_category(item["test_id"])
        if category is None:
            continue
        grouped[(category, _relative(item["filename"]), int(item["line_number"]))].append({
            "tool": "bandit",
            "rule_id": item["test_id"],
            "severity": item["issue_severity"],
            "message": item["issue_text"],
        })
    expected_by_key = {(item.category, item.path, item.line): item.id for item in expected}
    findings = []
    for (category, path, line), items in sorted(grouped.items()):
        findings.append(Finding(
            category=category,
            path=path,
            line=line,
            severity="ERROR" if any(item["severity"] in {"ERROR", "HIGH"} for item in items) else "WARNING",
            message=" | ".join(dict.fromkeys(item["message"] for item in items)),
            tools=sorted({item["tool"] for item in items}),
            rule_ids=sorted({item["rule_id"] for item in items}),
            expected_id=expected_by_key.get((category, path, line)),
        ))
    return findings


class SecurityScanner:
    def __init__(self, runner: ContainerRunner, expected: list[ExpectedFinding]):
        self.runner = runner
        self.expected = expected

    def scan(self, workspace: Path) -> ScanResult:
        semgrep = self.runner.run(
            workspace,
            "semgrep",
            [
                "scan", "--config", "/rules/semgrep.yml", "--metrics", "off",
                "--json", "--quiet", "--jobs", "1", "--timeout", "10", "/workspace/src",
            ],
            {0, 1},
        )
        bandit = self.runner.run(
            workspace,
            "bandit",
            ["-r", "/workspace/src", "-f", "json", "-q"],
            {0, 1},
        )
        findings = normalize_findings(
            json.loads(semgrep.stdout or "{}"),
            json.loads(bandit.stdout or "{}"),
            self.expected,
        )
        return ScanResult(findings=findings, semgrep=semgrep, bandit=bandit)
