"""Policy-bound orchestration across the validated Hands-on projects."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from .adapters import AdapterError, AdapterOutcome, ArtifactAdapter, FaultAdapter, RouterAdapter
from .contracts import validate


@dataclass
class Execution:
    request: dict[str, Any]
    result: dict[str, Any]
    traces: list[dict[str, Any]] = field(default_factory=list)
    route: dict[str, Any] | None = None
    outcomes: list[AdapterOutcome] = field(default_factory=list)


class Orchestrator:
    """Route one common request and fail closed at every adapter boundary."""

    def __init__(
        self,
        router: RouterAdapter | None = None,
        artifacts: ArtifactAdapter | None = None,
        faults: FaultAdapter | None = None,
    ) -> None:
        self.router = router or RouterAdapter()
        self.artifacts = artifacts or ArtifactAdapter()
        self.faults = faults or FaultAdapter()

    def execute(self, request: dict[str, Any]) -> Execution:
        validate("task-request", request)
        traces: list[dict[str, Any]] = []
        fault = request.get("metadata", {}).get("integration_fault")
        try:
            self.faults.raise_for(fault, "router")
            route, duration = self.router.route(request)
            traces.append(self._trace(request, "06-llm-router", route, duration))
        except AdapterError as error:
            traces.append(self._trace(request, "06-llm-router", None, 0, str(error)))
            return self._failure(request, traces, None, "failed", f"router_failed: {error}")

        if route.get("blocked"):
            return self._failure(request, traces, route, "blocked", "router_blocked")

        payload = request["input"] if isinstance(request["input"], dict) else {}
        if payload.get("data_scope") == "local_only" and route["selected_model"] != "local":
            return self._failure(request, traces, route, "blocked", "local_only_route_escaped_local_model")

        names = list(route["selected_agents"]) or [route["selected_model"]]
        outcomes: list[AdapterOutcome] = []
        limitations: list[str] = []
        evidence: list[dict[str, str]] = []
        actions = ["06-llm-router.route"]
        total_cost = 0.0
        costs_complete = True

        for name in names:
            if payload.get("data_scope") == "local_only" and name not in {"local", "small"}:
                return self._failure(request, traces, route, "blocked", f"local_only_external_adapter: {name}")
            try:
                self.faults.raise_for(fault, name)
                outcome = self.artifacts.run(name)
            except AdapterError as error:
                traces.append(self._trace(request, name, None, 0, str(error)))
                status = "blocked" if name in {"coding", "security"} else "failed"
                return self._failure(request, traces, route, status, f"{name}_failed: {error}", outcomes)
            outcomes.append(outcome)
            traces.append(self._trace(request, outcome.name, outcome.output, outcome.latency_ms))
            evidence.append({"source": outcome.source, "location": outcome.output["artifact"], "claim": outcome.claim})
            actions.append(f"{outcome.name}.run")
            limitations.extend(outcome.safety_violations)
            if outcome.cost is None:
                costs_complete = False
            else:
                total_cost += outcome.cost

        if "coding" in names:
            try:
                self.faults.raise_for(fault, "security")
                security = self.artifacts.run("security")
                if not isinstance(security.output.get("summary", {}).get("fixture", {}).get("decision"), str):
                    raise AdapterError("security decision is missing")
            except AdapterError as error:
                traces.append(self._trace(request, "09-cybersecurity-agent", None, 0, str(error)))
                return self._failure(
                    request,
                    traces,
                    route,
                    "blocked",
                    f"security_gate_failed: {error}",
                    outcomes,
                )
            outcomes.append(security)
            traces.append(self._trace(request, security.name, security.output, security.latency_ms))
            evidence.append({"source": security.source, "location": security.output["artifact"], "claim": security.claim})
            actions.append("09-cybersecurity-agent.gate")
            if security.status != "success":
                return self._failure(request, traces, route, "blocked", "security_gate_blocked", outcomes)

        status = "success" if all(item.status == "success" for item in outcomes) else "partial"
        output = {
            "route": route,
            "stages": [{"name": item.name, "status": item.status, "mode": item.mode} for item in outcomes],
            "estimated_cost_usd": total_cost if costs_complete else None,
            "security_gate": "approve" if "coding" in names else "not_required",
        }
        result = {
            "task_id": request["task_id"],
            "status": status,
            "output": output,
            "evidence": evidence,
            "actions": actions,
            "limitations": list(dict.fromkeys(limitations)),
            "metadata": {"mode": "replay", "fail_closed": True},
        }
        validate("agent-result", result)
        return Execution(request, result, traces, route, outcomes)

    def _failure(
        self,
        request: dict[str, Any],
        traces: list[dict[str, Any]],
        route: dict[str, Any] | None,
        status: str,
        limitation: str,
        outcomes: list[AdapterOutcome] | None = None,
    ) -> Execution:
        result = {
            "task_id": request["task_id"],
            "status": status,
            "output": {"route": route, "security_gate": "block" if status == "blocked" else "not_reached"},
            "evidence": [],
            "actions": [trace["tool_name"] for trace in traces],
            "limitations": [limitation],
            "metadata": {"mode": "replay", "fail_closed": True},
        }
        validate("agent-result", result)
        return Execution(request, result, traces, route, outcomes or [])

    @staticmethod
    def _trace(
        request: dict[str, Any],
        tool_name: str,
        output: dict[str, Any] | None,
        duration_ms: float,
        error: str | None = None,
    ) -> dict[str, Any]:
        trace = {
            "task_id": request["task_id"],
            "tool_name": tool_name,
            "input_summary": f"task_type={request['task_type']}",
            "result_summary": "failed" if error else json_summary(output),
            "duration_ms": max(0.0, duration_ms),
            "error": error,
            "metadata": {"boundary": "subprocess_or_artifact"},
        }
        validate("tool-trace", trace)
        return trace


def json_summary(value: dict[str, Any] | None) -> str:
    if value is None:
        return "no output"
    if "selected_model" in value:
        return f"model={value['selected_model']} agents={','.join(value.get('selected_agents', [])) or 'none'}"
    if "summary" in value:
        return "validated summary loaded"
    return "completed"
