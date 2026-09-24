from llm_router.io import load_metrics, load_policy
from llm_router.models import AgentRoute, ClassifierResult, LogicalModel, TaskRequest
from llm_router.router import HybridRouter


class VisionClassifier:
    def classify(self, task):
        return ClassifierResult(agents=["vision"], confidence=0.91, reason="image input")


def make_router(**kwargs):
    return HybridRouter(load_policy(), load_metrics(), **kwargs)


def test_routes_low_complexity_direct_request_to_small():
    decision = make_router().route(TaskRequest(task_id="small", prompt="classify", complexity="low"))

    assert decision.selected_model is LogicalModel.SMALL
    assert decision.selected_agents == []
    assert decision.strategy == "rule"


def test_routes_private_request_to_local_even_when_high_risk():
    task = TaskRequest(task_id="private", prompt="secret", data_scope="local_only", risk="high")

    decision = make_router().route(task)

    assert decision.selected_model is LogicalModel.LOCAL


def test_routes_high_complexity_request_to_frontier():
    decision = make_router().route(TaskRequest(task_id="hard", prompt="analyze", complexity="high"))

    assert decision.selected_model is LogicalModel.FRONTIER


def test_maps_explicit_capabilities_to_agents():
    task = TaskRequest(
        task_id="agents",
        prompt="work",
        required_capabilities=["knowledge_base", "code_execution"],
    )

    decision = make_router().route(task)

    assert decision.selected_agents == [AgentRoute.RAG, AgentRoute.CODING]


def test_incomplete_signals_use_classifier():
    task = TaskRequest(
        task_id="hybrid",
        prompt="inspect attachment",
        modalities=["text", "image"],
        signals_complete=False,
    )

    decision = make_router(classifier=VisionClassifier()).route(task)

    assert decision.strategy == "hybrid"
    assert decision.selected_agents == [AgentRoute.VISION]
    assert not decision.fallback


def test_local_only_request_is_blocked_when_local_model_is_unavailable():
    actual = load_metrics().logical_models[LogicalModel.LOCAL].actual_model
    task = TaskRequest(task_id="blocked", prompt="secret", data_scope="local_only")

    decision = make_router(availability={actual: False}).route(task)

    assert decision.blocked
    assert decision.actual_model is None
    assert not decision.fallback


def test_private_request_can_fallback_when_local_model_is_unavailable():
    actual = load_metrics().logical_models[LogicalModel.LOCAL].actual_model
    task = TaskRequest(task_id="fallback", prompt="internal", data_scope="private")

    decision = make_router(availability={actual: False}).route(task)

    assert decision.fallback
    assert decision.selected_model is LogicalModel.BALANCED
    assert decision.actual_model == "solar-pro4"
