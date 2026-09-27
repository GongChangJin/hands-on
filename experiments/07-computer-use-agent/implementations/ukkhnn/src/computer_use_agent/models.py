"""Validated task, action, observation, and result models."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Condition(str, Enum):
    DOM = "dom-accessibility"
    ADAPTIVE = "adaptive-screenshot"


class ActionKind(str, Enum):
    CLICK = "click"
    FILL = "fill"
    SELECT = "select"
    CHECK = "check"
    SCROLL = "scroll"
    WAIT = "wait"


class Assertion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    selector: str
    property: str
    equals: str | bool


class ComputerTask(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task_id: str
    goal: str
    scenario: str
    input: dict[str, Any] = Field(default_factory=dict)
    variant: str = "default"
    expected: Assertion
    recovery_expected: bool = False

    def task_request(self, max_steps: int) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "task_type": "browser",
            "input": {"goal": self.goal, "scenario": self.scenario, "parameters": self.input},
            "attachments": [],
            "constraints": {
                "allowed_tools": ["browser.observe", "browser.act", "browser.assert"],
                "forbidden_actions": ["external_navigation", "submit", "download", "upload"],
                "max_steps": max_steps,
                "max_tool_calls": max_steps * 2,
            },
            "expected_output": self.expected.model_dump(),
            "metadata": {"router_capability": "web_navigation", "variant": self.variant},
        }


class BrowserPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    allowed_hosts: list[str]
    allowed_schemes: list[str]
    allowed_actions: list[ActionKind]
    forbidden_button_types: list[str]
    max_steps: int = Field(ge=1)
    max_recoveries: int = Field(ge=0)
    repetitions: int = Field(ge=1)
    action_timeout_ms: int = Field(ge=1)
    task_timeout_ms: int = Field(ge=1)
    block_external_navigation: bool = True
    block_popups: bool = True
    block_downloads: bool = True


class BrowserAction(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: ActionKind
    selector: str | None = None
    value: str | None = None
    role: str | None = None
    name: str | None = None
    duration_ms: int | None = Field(default=None, ge=0)
    reason: str
    recovery: bool = False

    @model_validator(mode="after")
    def validate_fields(self) -> "BrowserAction":
        if self.kind in {ActionKind.CLICK, ActionKind.FILL, ActionKind.SELECT, ActionKind.CHECK, ActionKind.SCROLL}:
            if not self.selector and not (self.role and self.name):
                raise ValueError(f"{self.kind.value} requires a selector or role/name")
        if self.kind in {ActionKind.FILL, ActionKind.SELECT} and self.value is None:
            raise ValueError(f"{self.kind.value} requires a value")
        if self.kind is ActionKind.WAIT and self.duration_ms is None:
            raise ValueError("wait requires duration_ms")
        return self


class Observation(BaseModel):
    url: str
    title: str
    states: dict[str, Any]
    elements: list[dict[str, Any]]
    screenshot_sha256: str | None = None


class ActionTrace(BaseModel):
    step: int
    observation: Observation
    action: BrowserAction
    outcome: str
    duration_ms: float
    error: str | None = None


class TaskRun(BaseModel):
    task_id: str
    repetition: int = Field(ge=1)
    condition: Condition
    success: bool
    status: str
    latency_ms: float
    action_count: int
    recovery_count: int
    recovery_success: bool | None
    final_value: str | bool | None
    failure_type: str | None
    safety_violations: list[str]
    blocked_requests: list[str]
    context_id: str
    trace: list[ActionTrace]
    task_request: dict[str, Any]
    agent_result: dict[str, Any]
    tool_traces: list[dict[str, Any]]
    evaluation_record: dict[str, Any]
