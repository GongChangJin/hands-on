from pathlib import Path

from agent_eval.agents import FlawedScriptedAgent, OracleScriptedAgent
from agent_eval.runner import EvaluationRunner, summarize


DATASET_PATH = Path(__file__).resolve().parents[3] / "shared" / "evals" / "tasks.jsonl"


def test_oracle_agent_passes_all_fixtures() -> None:
    runner = EvaluationRunner()
    records = runner.evaluate(runner.load_tasks(DATASET_PATH), OracleScriptedAgent())

    assert len(records) == 5
    assert all(record["task_success"] for record in records)
    assert summarize(records)["success_rate"] == 1.0


def test_flawed_agent_preserves_each_failure() -> None:
    runner = EvaluationRunner()
    records = runner.evaluate(runner.load_tasks(DATASET_PATH), FlawedScriptedAgent())

    assert len(records) == 5
    assert sum(record["task_success"] for record in records) == 1
    assert {record["failure_type"] for record in records} == {
        None,
        "output_mismatch",
        "safety_violation",
        "agent_status_partial",
        "agent_exception",
    }
