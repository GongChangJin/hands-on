# 태스크 스위트 실행기.
# 실패한 실행도 기록에 남긴다 (실험 규칙: 실패 실행 삭제 금지).
from __future__ import annotations

import time
import traceback
from pathlib import Path
from typing import Callable, Iterable

from .graders import get_grader
from .schema import AgentResult, Grade, RunRecord, Task, new_run_id

AgentFn = Callable[[Task], AgentResult]


def run_suite(
    tasks: Iterable[Task],
    agent: AgentFn,
    *,
    experiment: str,
    implementation: str = "us788",
    repeats: int = 1,
    out_path: str | Path | None = None,
    run_id: str | None = None,
) -> list[RunRecord]:
    rid = run_id or new_run_id()
    records: list[RunRecord] = []
    sink = open(out_path, "a", encoding="utf-8") if out_path else None
    try:
        for repeat in range(repeats):
            for task in tasks:
                rec = RunRecord(
                    run_id=rid,
                    task_id=task.task_id,
                    experiment=experiment,
                    implementation=implementation,
                    repeat_index=repeat,
                )
                t0 = time.perf_counter()
                try:
                    result = agent(task)
                except Exception:
                    rec.error = traceback.format_exc(limit=3)
                    result = None
                rec.latency_ms = (time.perf_counter() - t0) * 1000

                if result is not None:
                    rec.output = result.output
                    rec.tool_calls = result.tool_calls
                    rec.input_tokens = result.input_tokens
                    rec.output_tokens = result.output_tokens
                    rec.cost_usd = result.cost_usd
                    rec.logical_route = result.logical_route
                    rec.provider = result.provider
                    rec.model_id = result.model_id
                    rec.forbidden_actions = result.forbidden_actions
                    if result.latency_ms:
                        rec.latency_ms = result.latency_ms
                    for name in task.graders:
                        try:
                            rec.grades.append(get_grader(name)(task, result))
                        except Exception as e:
                            rec.grades.append(Grade(name, False, 0.0, f"grader 오류: {e}"))
                else:
                    rec.grades.append(Grade("run", False, 0.0, "에이전트 실행 실패"))

                records.append(rec)
                if sink:
                    sink.write(rec.to_json() + "\n")
                    sink.flush()
    finally:
        if sink:
            sink.close()
    return records
