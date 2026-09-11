"""Run agents, preserve failures, and emit EvaluationRecord dictionaries."""

from __future__ import annotations

import json
import math
import statistics
import time
from pathlib import Path
from typing import Any, Iterable

from .agents import Agent
from .contracts import ContractError, ContractRegistry
from .graders import DeterministicGrader


class EvaluationRunner:
    def __init__(
        self,
        contracts: ContractRegistry | None = None,
        grader: DeterministicGrader | None = None,
    ) -> None:
        self.contracts = contracts or ContractRegistry()
        self.grader = grader or DeterministicGrader()

    def load_tasks(self, dataset_path: Path) -> list[dict[str, Any]]:
        tasks = []
        with dataset_path.open(encoding="utf-8") as dataset_file:
            for line_number, line in enumerate(dataset_file, start=1):
                if not line.strip():
                    continue
                try:
                    task = json.loads(line)
                    self.contracts.validate("task_request", task)
                except (json.JSONDecodeError, ContractError) as exc:
                    raise ValueError(f"{dataset_path}:{line_number}: {exc}") from exc
                tasks.append(task)
        return tasks

    def evaluate(self, tasks: Iterable[dict[str, Any]], agent: Agent) -> list[dict[str, Any]]:
        return [self.evaluate_one(task, agent) for task in tasks]

    def evaluate_one(self, task: dict[str, Any], agent: Agent) -> dict[str, Any]:
        self.contracts.validate("task_request", task)
        started_at = time.perf_counter()

        try:
            execution = agent.run(task)
            latency_ms = (time.perf_counter() - started_at) * 1_000
            self.contracts.validate("agent_result", execution.result)
            for trace in execution.traces:
                self.contracts.validate("tool_trace", trace)
            grade = self.grader.grade(task, execution.result, execution.traces)
            record = {
                "task_id": task["task_id"],
                "implementation_id": agent.implementation_id,
                "task_success": grade.task_success,
                "quality_score": grade.quality_score,
                "tool_accuracy": grade.tool_accuracy,
                "latency_ms": latency_ms,
                "safety_violations": grade.safety_violations,
                "failure_type": grade.failure_type,
                "metadata": grade.details,
            }
        except ContractError as exc:
            record = self._failure_record(
                task=task,
                agent=agent,
                latency_ms=(time.perf_counter() - started_at) * 1_000,
                failure_type="schema_validation",
                error=str(exc),
            )
        except Exception as exc:  # The evaluator must preserve unexpected agent failures.
            record = self._failure_record(
                task=task,
                agent=agent,
                latency_ms=(time.perf_counter() - started_at) * 1_000,
                failure_type="agent_exception",
                error=f"{type(exc).__name__}: {exc}",
            )

        self.contracts.validate("evaluation_record", record)
        return record

    @staticmethod
    def _failure_record(
        task: dict[str, Any],
        agent: Agent,
        latency_ms: float,
        failure_type: str,
        error: str,
    ) -> dict[str, Any]:
        return {
            "task_id": task["task_id"],
            "implementation_id": agent.implementation_id,
            "task_success": False,
            "quality_score": 0.0,
            "tool_accuracy": 0.0,
            "latency_ms": latency_ms,
            "safety_violations": [],
            "failure_type": failure_type,
            "metadata": {"error": error},
        }


def write_jsonl(records: Iterable[dict[str, Any]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as output_file:
        for record in records:
            output_file.write(json.dumps(record, ensure_ascii=False) + "\n")


def summarize(records: list[dict[str, Any]]) -> dict[str, Any]:
    if not records:
        return {"runs": 0, "success_rate": 0.0, "p50_latency_ms": 0.0, "p95_latency_ms": 0.0}

    latencies = sorted(record["latency_ms"] for record in records)
    p95_index = max(0, math.ceil(len(latencies) * 0.95) - 1)
    return {
        "runs": len(records),
        "success_rate": sum(record["task_success"] for record in records) / len(records),
        "p50_latency_ms": statistics.median(latencies),
        "p95_latency_ms": latencies[p95_index],
    }
