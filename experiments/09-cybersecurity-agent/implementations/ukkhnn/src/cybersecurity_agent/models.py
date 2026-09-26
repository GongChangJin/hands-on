"""Validated security policy, finding, tool, and decision models."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class SecurityPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    container_image: str
    semgrep_version: str
    bandit_version: str
    pytest_version: str
    network: str
    read_only_root: bool
    cap_drop: list[str]
    no_new_privileges: bool
    memory_mb: int = Field(ge=128)
    cpus: float = Field(gt=0)
    pids_limit: int = Field(ge=16)
    timeout_seconds: int = Field(ge=1)
    allowed_tools: list[str]
    allowed_categories: list[str]
    minimum_detection_rate: float = Field(ge=0, le=1)
    minimum_remediation_rate: float = Field(ge=0, le=1)


class ExpectedFinding(BaseModel):
    id: str
    category: str
    path: str
    line: int = Field(ge=1)
    symbol: str


class Finding(BaseModel):
    category: str
    path: str
    line: int = Field(ge=1)
    severity: str
    message: str
    tools: list[str]
    rule_ids: list[str]
    expected_id: str | None = None


class ToolExecution(BaseModel):
    tool: str
    exit_code: int
    duration_ms: float = Field(ge=0)
    stdout: str
    stderr: str
    timed_out: bool = False
    container_args: list[str] = Field(default_factory=list)


class ScanResult(BaseModel):
    findings: list[Finding]
    semgrep: ToolExecution
    bandit: ToolExecution


class SecurityEvaluation(BaseModel):
    detected_expected: int
    expected_total: int
    detection_rate: float
    residual_expected: int
    remediated_expected: int
    remediation_rate: float
    false_positives: int
    clean_controls: int
    functional_tests_before: bool
    security_tests_before_failed: bool
    all_tests_after: bool
    decision: str
    remaining_risks: list[str]
    metadata: dict[str, Any] = Field(default_factory=dict)
