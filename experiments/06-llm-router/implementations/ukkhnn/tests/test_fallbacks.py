from llm_router.evaluation import run_fallback_suite
from llm_router.io import load_metrics, load_policy
from llm_router.models import ClassifierResult, TaskRequest
from llm_router.router import HybridRouter


class AlwaysFails:
    def classify(self, task):
        raise RuntimeError("failure")


class LowConfidence:
    def classify(self, task):
        return ClassifierResult(agents=[], confidence=0.1, reason="uncertain")


def ambiguous(task_id="x"):
    return TaskRequest(
        task_id=task_id,
        prompt="첨부 화면을 확인해줘.",
        modalities=["text", "image"],
        signals_complete=False,
    )


def test_low_confidence_uses_deterministic_fallback():
    router = HybridRouter(load_policy(), load_metrics(), classifier=LowConfidence())

    decision = router.route(ambiguous())

    assert decision.fallback
    assert decision.fallback_reason == "classifier_low_confidence"
    assert [agent.value for agent in decision.selected_agents] == ["vision"]


def test_circuit_breaker_opens_after_threshold():
    router = HybridRouter(load_policy(), load_metrics(), classifier=AlwaysFails())

    router.route(ambiguous("one"))
    router.route(ambiguous("two"))
    decision = router.route(ambiguous("three"))

    assert router.circuit_breaker.is_open
    assert decision.fallback_reason == "classifier_circuit_open"


def test_fallback_suite_passes_every_scenario():
    rows, summary = run_fallback_suite(load_policy(), load_metrics())

    assert summary == {"scenarios": 7, "passed": 7, "pass_rate": 1.0}
    assert all(row["passed"] for row in rows)
