"""Benchmark orchestration."""

from __future__ import annotations

import platform
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .dataset import load_dataset
from .evaluation import build_run_records
from .prompts import build_request
from .report import export_results, summarize
from .types import LLMAdapter


def run_benchmark(
    adapter: LLMAdapter,
    *,
    repetitions: int,
    output_dir: Path,
    dataset_path: Path | None = None,
) -> tuple[dict[str, Any], Path]:
    if repetitions < 1:
        raise ValueError("repetitions는 1 이상이어야 합니다.")
    tasks = load_dataset(dataset_path)
    warmup = adapter.warmup()
    model_info = adapter.inspect()
    environment = {
        "executed_at": datetime.now(timezone.utc).isoformat(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "python": sys.version.split()[0],
        "dataset_tasks": len(tasks),
        "model": model_info,
        "warmup": {
            "total_latency_ms": warmup.total_latency_ms,
            "load_duration_ms": warmup.load_duration_ms,
            "error": warmup.error,
        },
    }
    implementation_id = f"ukkhnn:{adapter.adapter_name}:{adapter.model}"
    agent_results: list[dict[str, Any]] = []
    tool_traces: list[dict[str, Any]] = []
    evaluation_records: list[dict[str, Any]] = []
    for repetition in range(1, repetitions + 1):
        for task in tasks:
            response = adapter.generate(build_request(task))
            agent_result, tool_trace, evaluation_record = build_run_records(
                task,
                response,
                implementation_id=implementation_id,
                adapter_name=adapter.adapter_name,
                repetition=repetition,
            )
            agent_results.append(agent_result)
            tool_traces.append(tool_trace)
            evaluation_records.append(evaluation_record)
    summary = summarize(
        evaluation_records,
        implementation_id=implementation_id,
        adapter=adapter.adapter_name,
        model=adapter.model,
        repetitions=repetitions,
        environment=environment,
    )
    report_path = export_results(
        output_dir,
        summary=summary,
        agent_results=agent_results,
        tool_traces=tool_traces,
        evaluation_records=evaluation_records,
    )
    return summary, report_path
