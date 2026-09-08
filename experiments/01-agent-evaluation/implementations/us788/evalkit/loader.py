# JSONL 태스크 로더. 주석(#)과 빈 줄은 건너뛴다.
from __future__ import annotations

import json
from pathlib import Path

from .schema import Task


def load_tasks(path: str | Path) -> list[Task]:
    tasks: list[Task] = []
    seen: set[str] = set()
    with open(path, encoding="utf-8") as f:
        for lineno, raw in enumerate(f, 1):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as e:
                raise ValueError(f"{path}:{lineno} JSON 파싱 실패: {e}") from e
            task = Task(**obj)
            if task.task_id in seen:
                raise ValueError(f"{path}:{lineno} task_id 중복: {task.task_id}")
            seen.add(task.task_id)
            tasks.append(task)
    if not tasks:
        raise ValueError(f"{path} 에 태스크가 없습니다")
    return tasks
