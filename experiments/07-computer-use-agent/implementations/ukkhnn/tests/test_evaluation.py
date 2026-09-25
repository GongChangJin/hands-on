from computer_use_agent.evaluation import summarize
from computer_use_agent.models import Condition, TaskRun


def run(task_id, *, success=True, recovery=None, context_id="a"):
    return TaskRun(
        task_id=task_id,
        repetition=1,
        condition=Condition.DOM,
        success=success,
        status="success" if success else "failed",
        latency_ms=100,
        action_count=2,
        recovery_count=1 if recovery is not None else 0,
        recovery_success=recovery,
        final_value="ok" if success else "bad",
        failure_type=None if success else "dom_assertion_failed",
        safety_violations=[],
        blocked_requests=[],
        context_id=context_id,
        trace=[],
        task_request={},
        agent_result={},
        tool_traces=[],
        evaluation_record={},
    )


def test_summary_counts_success_recovery_and_isolated_contexts():
    summary = summarize([
        run("a", recovery=True, context_id="one"),
        run("b", success=False, recovery=False, context_id="two"),
    ])

    assert summary["success_rate"] == 0.5
    assert summary["recovery_rate"] == 0.5
    assert summary["isolated_contexts"] == 2
    assert summary["failures"][0]["task_id"] == "b"
