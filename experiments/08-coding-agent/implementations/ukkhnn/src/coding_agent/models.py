"""Validated models for issues, proposals, commands, and task runs."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class CodingIssue(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task_id: str
    title: str
    description: str
    acceptance_criteria: list[str]
    context_paths: list[str]
    allowed_paths: list[str]
    regression_test_path: str
    judge_file: str


class CodingPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    max_attempts: int = Field(ge=1)
    max_changed_files: int = Field(ge=1)
    max_file_bytes: int = Field(ge=1)
    command_timeout_seconds: int = Field(ge=1)
    allowed_tools: list[str]
    forbidden_actions: list[str]


class FileEdit(BaseModel):
    model_config = ConfigDict(extra="forbid")

    path: str
    content: str


class PatchProposal(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: str
    plan: list[str] = Field(min_length=1)
    edits: list[FileEdit] = Field(min_length=1)
    risks: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def unique_paths(self) -> PatchProposal:
        paths = [edit.path for edit in self.edits]
        if len(paths) != len(set(paths)):
            raise ValueError("proposal contains duplicate edit paths")
        return self


class ProviderResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    proposal: PatchProposal
    model: str
    latency_ms: float = Field(ge=0)
    input_tokens: int = Field(ge=0)
    cached_input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    cost_usd: float = Field(ge=0)
    request_id: str | None = None


class CommandResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    command: list[str]
    returncode: int
    stdout: str
    stderr: str
    duration_ms: float = Field(ge=0)
    timed_out: bool = False

    @property
    def passed(self) -> bool:
        return self.returncode == 0 and not self.timed_out


class AttemptRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    attempt: int
    proposal_summary: str | None = None
    plan: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    changed_paths: list[str] = Field(default_factory=list)
    public_tests: CommandResult | None = None
    lint: CommandResult | None = None
    error: str | None = None


class AgentRun(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task_id: str
    success: bool
    attempts: list[AttemptRecord]
    changed_paths: list[str]
    patch: str
    provider_model: str | None
    plan: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    input_tokens: int = 0
    cached_input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    latency_ms: float = 0.0
    tool_traces: list[dict[str, Any]] = Field(default_factory=list)
    safety_violations: list[str] = Field(default_factory=list)
    failure_type: str | None = None


class EvaluationRun(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task_id: str
    success: bool
    attempts: int
    changed_paths: list[str]
    patch_path: str
    public_tests_passed: bool
    regression_tests_passed: bool
    held_out_tests_passed: bool
    lint_passed: bool
    regression_test_added: bool
    regression_test_catches_bug: bool
    scope_passed: bool
    forbidden_git_actions: int
    latency_ms: float
    input_tokens: int
    cached_input_tokens: int
    output_tokens: int
    cost_usd: float
    failure_type: str | None
    safety_violations: list[str]
    task_request: dict[str, Any]
    agent_result: dict[str, Any]
    tool_traces: list[dict[str, Any]]
    evaluation_record: dict[str, Any]
