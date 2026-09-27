from local_llm.contracts import validate_contract
from local_llm.dataset import iter_categories, load_dataset


def test_dataset_is_fixed_24_task_suite():
    tasks = load_dataset()
    assert len(tasks) == 24
    assert len({task["task_id"] for task in tasks}) == 24
    assert iter_categories(tasks) == {"classification", "extraction", "short_qa"}


def test_dataset_has_eight_tasks_per_category():
    tasks = load_dataset()
    counts = {category: 0 for category in iter_categories(tasks)}
    for task in tasks:
        counts[task["metadata"]["category"]] += 1
    assert counts == {"classification": 8, "extraction": 8, "short_qa": 8}


def test_every_task_uses_shared_contract_and_forbids_tools():
    for task in load_dataset():
        validate_contract("task-request", task)
        assert task["constraints"]["allowed_tools"] == []
        assert task["constraints"]["max_tool_calls"] == 0
        assert task["expected_output"]["response_schema"]["additionalProperties"] is False
