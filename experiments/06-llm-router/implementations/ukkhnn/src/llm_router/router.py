"""Policy-first hybrid model and specialist-agent router."""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from .classifiers import AgentClassifier, infer_agents_from_text
from .models import (
    AgentRoute,
    ClassifierResult,
    DataScope,
    Level,
    LogicalModel,
    ProjectMetrics,
    RiskLevel,
    RouteDecision,
    RouterPolicy,
    TaskRequest,
)


@dataclass
class CircuitBreaker:
    threshold: int
    failures: int = 0
    is_open: bool = False

    def success(self) -> None:
        self.failures = 0

    def failure(self) -> None:
        self.failures += 1
        if self.failures >= self.threshold:
            self.is_open = True


@dataclass
class HybridRouter:
    policy: RouterPolicy
    metrics: ProjectMetrics
    classifier: AgentClassifier | None = None
    availability: dict[str, bool] = field(default_factory=dict)
    circuit_breaker: CircuitBreaker = field(init=False)

    def __post_init__(self) -> None:
        self.circuit_breaker = CircuitBreaker(self.policy.circuit_breaker_failures)

    def _select_model(self, task: TaskRequest) -> tuple[LogicalModel, str]:
        if task.data_scope in {DataScope.PRIVATE, DataScope.LOCAL_ONLY}:
            return self.policy.private_model, f"{task.data_scope.value} data uses the private model route"
        if task.risk is RiskLevel.HIGH or task.complexity is Level.HIGH:
            return self.policy.high_risk_model, "high risk or complexity uses the frontier route"
        if task.complexity is Level.LOW and not task.required_capabilities and not task.needs_current_info:
            return LogicalModel.SMALL, "low-complexity direct request uses the small route"
        return self.policy.default_model, "default policy uses the balanced route"

    def _agents_from_capabilities(self, task: TaskRequest) -> list[AgentRoute]:
        return list(dict.fromkeys(
            self.policy.agent_capability_map[capability]
            for capability in task.required_capabilities
            if capability in self.policy.agent_capability_map
        ))

    def _safe_fallback_model(self, task: TaskRequest) -> LogicalModel:
        if task.data_scope is DataScope.LOCAL_ONLY:
            return LogicalModel.LOCAL
        if task.risk is RiskLevel.HIGH or task.complexity is Level.HIGH:
            return self.policy.high_risk_model
        return self.policy.fallback_model

    def _classify_agents(self, task: TaskRequest) -> tuple[list[AgentRoute], ClassifierResult | None, bool, str | None]:
        if self.classifier is None:
            return infer_agents_from_text(task), None, True, "classifier_unavailable"
        if self.circuit_breaker.is_open:
            return infer_agents_from_text(task), None, True, "classifier_circuit_open"
        try:
            result = self.classifier.classify(task)
        except TimeoutError:
            self.circuit_breaker.failure()
            return infer_agents_from_text(task), None, True, "classifier_timeout"
        except (RuntimeError, ValueError):
            self.circuit_breaker.failure()
            return infer_agents_from_text(task), None, True, "classifier_failure"
        if result.confidence < self.policy.confidence_threshold:
            self.circuit_breaker.failure()
            return infer_agents_from_text(task), result, True, "classifier_low_confidence"
        self.circuit_breaker.success()
        return result.agents, result, False, None

    def route(self, task: TaskRequest) -> RouteDecision:
        started = time.perf_counter()
        model, model_reason = self._select_model(task)
        reasons = [model_reason]
        classifier_result: ClassifierResult | None = None
        fallback = False
        fallback_reason: str | None = None
        strategy = "rule"
        confidence = 0.96

        if task.signals_complete:
            agents = self._agents_from_capabilities(task)
            reasons.append("specialist agents derived from explicit capability signals")
        else:
            strategy = "hybrid"
            agents, classifier_result, fallback, fallback_reason = self._classify_agents(task)
            if fallback:
                model = self._safe_fallback_model(task)
                confidence = 0.70
                reasons.append(f"deterministic fallback applied: {fallback_reason}")
            else:
                confidence = min(0.95, classifier_result.confidence if classifier_result else 0.0)
                reasons.append("specialist agents inferred by the ambiguity classifier")

        model_metric = self.metrics.logical_models[model]
        actual_model: str | None = model_metric.actual_model
        blocked = False
        if not self.availability.get(actual_model, True):
            if task.data_scope is DataScope.LOCAL_ONLY:
                actual_model = None
                blocked = True
                confidence = 1.0
                reasons.append("local model unavailable; external fallback blocked by local-only policy")
            else:
                unavailable_model = model
                model = self._safe_fallback_model(task)
                actual_model = self.metrics.logical_models[model].actual_model
                fallback = True
                fallback_reason = "selected_model_unavailable"
                reasons.append(f"{unavailable_model.value} unavailable; safe fallback selected")

        return RouteDecision(
            task_id=task.task_id,
            selected_model=model,
            actual_model=actual_model,
            selected_agents=agents,
            reason=reasons,
            confidence=confidence,
            strategy=strategy,
            latency_ms=(time.perf_counter() - started) * 1000,
            fallback=fallback,
            fallback_from="classifier" if fallback_reason and fallback_reason.startswith("classifier") else ("model" if fallback else None),
            fallback_reason=fallback_reason,
            blocked=blocked,
            classifier=classifier_result,
        )
