from llm_router.classifiers import HeuristicClassifier
from llm_router.evaluation import run_evaluation
from llm_router.io import load_dataset, load_metrics, load_policy
from llm_router.router import HybridRouter


def evaluated():
    router = HybridRouter(load_policy(), load_metrics(), classifier=HeuristicClassifier())
    return run_evaluation(load_dataset(), router)


def test_offline_replay_meets_routing_target():
    records, summary = evaluated()

    assert len(records) == 40
    assert summary["routing_accuracy"] >= 0.9
    assert summary["classifier_calls"] == 4


def test_quality_stays_within_five_percentage_points():
    _, summary = evaluated()

    assert summary["quality"]["within_five_percent"]
    assert summary["quality"]["coverage"] == 0.925


def test_cost_and_latency_comparison_reports_coverage():
    _, summary = evaluated()

    assert summary["cost"]["coverage"] == 0.925
    assert summary["latency"]["coverage"] == 0.925
    assert summary["cost"]["router_total_usd"] is not None
    assert summary["cost"]["routing_and_model_savings_rate"] > 0
    assert summary["latency"]["router_p50_ms"] is not None


def test_every_record_keeps_reason_and_mapping_metadata():
    records, _ = evaluated()

    assert all(record.route.reason for record in records)
    assert all(record.route.actual_model for record in records)
    assert all(record.metadata["projection_basis"] for record in records)
