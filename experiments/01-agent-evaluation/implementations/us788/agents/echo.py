# 배관 점검용 더미 에이전트. API 키 없이 run_eval.py 흐름을 확인할 때 쓴다.
from __future__ import annotations

from evalkit import AgentResult, Task


def build():
    def agent(task: Task) -> AgentResult:
        return AgentResult(output=str(task.expected), logical_route="dummy")

    return agent
