"""Validated input, policy, and output models."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class LogicalModel(str, Enum):
    SMALL = "small"
    BALANCED = "balanced"
    FRONTIER = "frontier"
    LOCAL = "local"


class AgentRoute(str, Enum):
    RAG = "rag"
    VISION = "vision"
    RESEARCH = "research"
    BROWSER = "browser"
    CODING = "coding"


class DataScope(str, Enum):
    PUBLIC = "public"
    PRIVATE = "private"
    LOCAL_ONLY = "local_only"


class Level(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class TaskRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task_id: str = Field(min_length=1)
    prompt: str = Field(min_length=1)
    modalities: list[str] = Field(default_factory=lambda: ["text"])
    data_scope: DataScope = DataScope.PUBLIC
    complexity: Level = Level.MODERATE
    risk: RiskLevel = RiskLevel.LOW
    needs_current_info: bool = False
    required_capabilities: list[str] = Field(default_factory=list)
    signals_complete: bool = True


class DatasetCase(TaskRequest):
    expected_models: list[LogicalModel] = Field(min_length=1)
    expected_agents: list[AgentRoute] = Field(default_factory=list)

    def request(self) -> TaskRequest:
        values = self.model_dump(exclude={"expected_models", "expected_agents"})
        return TaskRequest.model_validate(values)


class RouterPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    confidence_threshold: float = Field(ge=0, le=1)
    classifier_timeout_seconds: float = Field(gt=0)
    circuit_breaker_failures: int = Field(ge=1)
    default_model: LogicalModel
    high_risk_model: LogicalModel
    private_model: LogicalModel
    fallback_model: LogicalModel
    agent_capability_map: dict[str, AgentRoute]


class ClassifierResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    agents: list[AgentRoute]
    confidence: float = Field(ge=0, le=1)
    reason: str = Field(min_length=1)
    latency_ms: float = Field(ge=0, default=0)
    input_tokens: int = Field(ge=0, default=0)
    output_tokens: int = Field(ge=0, default=0)
    cost_usd: float = Field(ge=0, default=0)
    provider_request_id: str | None = None


class RouteDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task_id: str
    selected_model: LogicalModel
    actual_model: str | None
    selected_agents: list[AgentRoute]
    reason: list[str]
    confidence: float = Field(ge=0, le=1)
    strategy: str
    latency_ms: float = Field(ge=0)
    fallback: bool = False
    fallback_from: str | None = None
    fallback_reason: str | None = None
    blocked: bool = False
    classifier: ClassifierResult | None = None

    @model_validator(mode="after")
    def blocked_has_no_actual_model(self) -> "RouteDecision":
        if self.blocked and self.actual_model is not None:
            raise ValueError("blocked route cannot expose an actual model")
        return self


class ModelMetric(BaseModel):
    actual_model: str
    provider: str
    quality_score: float = Field(ge=0, le=1)
    latency_p50_ms: float = Field(ge=0)
    request_cost_usd: float = Field(ge=0)
    source: str


class AgentMetric(BaseModel):
    quality_score: float | None = Field(default=None, ge=0, le=1)
    latency_p50_ms: float | None = Field(default=None, ge=0)
    request_cost_usd: float | None = Field(default=None, ge=0)
    source: str


class ProjectMetrics(BaseModel):
    recorded_at: str
    logical_models: dict[LogicalModel, ModelMetric]
    agents: dict[AgentRoute, AgentMetric]


class EvaluationRecord(BaseModel):
    task_id: str
    route: RouteDecision
    expected_models: list[LogicalModel]
    expected_agents: list[AgentRoute]
    model_match: bool
    agent_match: bool
    route_match: bool
    projected_quality: float | None
    baseline_quality: float | None
    projected_cost_usd: float | None
    baseline_cost_usd: float | None
    projected_latency_ms: float | None
    baseline_latency_ms: float | None
    metadata: dict[str, Any] = Field(default_factory=dict)
