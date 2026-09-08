# 평가 태스크와 실행 기록(telemetry)의 공통 스키마.
# 03 Agentic RAG, 06 LLM Router 구현이 같은 RunRecord를 뱉도록 맞춘다.
from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass
class Task:
    task_id: str
    prompt: str
    expected: Any = None
    graders: list[str] = field(default_factory=lambda: ["exact"])
    tags: list[str] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolCall:
    name: str
    args: dict[str, Any] = field(default_factory=dict)
    ok: bool = True
    latency_ms: float = 0.0
    error: str | None = None


@dataclass
class Grade:
    grader: str
    passed: bool
    score: float | None = None
    reason: str = ""


@dataclass
class AgentResult:
    # 피평가 에이전트가 반환해야 하는 최소 계약.
    output: str
    tool_calls: list[ToolCall] = field(default_factory=list)
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    latency_ms: float = 0.0
    logical_route: str | None = None
    provider: str | None = None
    model_id: str | None = None
    forbidden_actions: int = 0
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class RunRecord:
    run_id: str
    task_id: str
    experiment: str
    implementation: str
    repeat_index: int = 0
    output: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    latency_ms: float = 0.0
    logical_route: str | None = None
    provider: str | None = None
    model_id: str | None = None
    forbidden_actions: int = 0
    grades: list[Grade] = field(default_factory=list)
    error: str | None = None
    started_at: float = field(default_factory=time.time)

    @property
    def passed(self) -> bool:
        # grader가 하나도 없으면 판정 불가로 보고 실패 처리한다.
        return bool(self.grades) and all(g.passed for g in self.grades)

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)


def new_run_id() -> str:
    return uuid.uuid4().hex[:12]
