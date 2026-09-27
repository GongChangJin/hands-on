import urllib.request

import pytest
from pydantic import ValidationError

from computer_use_agent.contracts import validate
from computer_use_agent.io import load_policy, load_tasks, shared_dir
from computer_use_agent.models import BrowserAction
from computer_use_agent.server import serve_site


def test_dataset_has_12_unique_tasks():
    tasks = load_tasks()

    assert len(tasks) == 12
    assert len({task.task_id for task in tasks}) == 12
    assert sum(task.recovery_expected for task in tasks) == 3


def test_policy_has_bounded_execution():
    policy = load_policy()

    assert policy.max_steps == 15
    assert policy.max_recoveries == 2
    assert policy.repetitions == 2
    assert policy.allowed_hosts == ["127.0.0.1", "localhost"]


def test_action_requires_target():
    with pytest.raises(ValidationError):
        BrowserAction(kind="click", reason="missing target")


def test_wait_requires_duration():
    with pytest.raises(ValidationError):
        BrowserAction(kind="wait", reason="missing duration")


def test_every_task_adapts_to_shared_task_request_contract():
    policy = load_policy()

    for task in load_tasks():
        validate("task-request", task.task_request(policy.max_steps))


def test_local_fixture_is_served_without_external_dependencies():
    with serve_site(shared_dir() / "site") as base_url:
        with urllib.request.urlopen(f"{base_url}/index.html", timeout=2) as response:
            body = response.read().decode("utf-8")

    assert response.status == 200
    assert "Computer-use Agent Test Site" in body
