import pytest

from agent_eval.contracts import ContractError, ContractRegistry


def test_rejects_task_without_required_fields() -> None:
    contracts = ContractRegistry()

    with pytest.raises(ContractError, match="task_id"):
        contracts.validate("task_request", {"task_type": "evaluation"})


def test_accepts_minimal_agent_result() -> None:
    contracts = ContractRegistry()
    contracts.validate(
        "agent_result",
        {
            "task_id": "task-1",
            "status": "success",
            "output": "done",
            "evidence": [],
            "actions": [],
            "limitations": [],
        },
    )
