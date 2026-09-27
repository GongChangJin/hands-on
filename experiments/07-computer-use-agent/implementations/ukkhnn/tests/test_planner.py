from computer_use_agent.models import ActionTrace, BrowserAction, Condition, Observation
from computer_use_agent.planner import next_action
from computer_use_agent.io import load_tasks


def task(name):
    return next(item for item in load_tasks() if item.task_id == name)


def observation(**updates):
    states = {
        "search_input": "", "search_status": "idle", "filter_status": "count:3",
        "profile_name": "", "profile_email": "", "form_error": "", "profile_preview": "empty",
        "tab_status": "active:overview", "scroll_status": "pending", "scroll_target_in_view": False,
        "dynamic_status": "waiting", "dynamic_exists": False, "save_status": "unsaved", "save_button_id": "draft-control",
        "sort_value": "popular", "sort_status": "sort:popular", "notifications": False,
        "notification_status": "notifications:off", "policy_status": "unread", "external_status": "unchecked",
    }
    states.update(updates)
    return Observation(url="http://127.0.0.1", title="fixture", states=states, elements=[])


def failed_trace(selector):
    return ActionTrace(
        step=1,
        observation=observation(),
        action=BrowserAction(kind="click", selector=selector, reason="test"),
        outcome="failed",
        duration_ms=1,
        error="missing",
    )


def test_search_planner_fills_then_clicks():
    first = next_action(task("search-001"), observation(), [], Condition.DOM)
    second = next_action(task("search-001"), observation(search_input="Beta"), [], Condition.DOM)

    assert first.kind.value == "fill"
    assert second.selector == "#search-button"


def test_validation_planner_surfaces_then_repairs_error():
    current = task("validation-001")
    expose = next_action(current, observation(profile_name="Mina"), [], Condition.DOM)
    repair = next_action(current, observation(profile_name="Mina", form_error="required"), [], Condition.DOM)

    assert expose.selector == "#preview-profile"
    assert repair.recovery
    assert repair.value == "mina@example.com"


def test_dynamic_failure_causes_bounded_wait_recovery():
    action = next_action(task("dynamic-001"), observation(), [failed_trace("#dynamic-button")], Condition.DOM)

    assert action.kind.value == "wait"
    assert action.recovery


def test_adaptive_condition_recovers_renamed_button_by_accessible_name():
    current = observation()
    current.screenshot_sha256 = "abc"

    action = next_action(task("changed-ui-001"), current, [failed_trace("#save-button")], Condition.ADAPTIVE)

    assert action.role == "button"
    assert action.name == "Save draft"
    assert action.recovery


def test_dom_condition_preserves_changed_ui_failure():
    action = next_action(task("changed-ui-001"), observation(), [failed_trace("#save-button")], Condition.DOM)

    assert action is None


def test_injection_task_never_selects_external_link():
    action = next_action(task("injection-001"), observation(), [], Condition.ADAPTIVE)

    assert action.selector == "#ack-policy"
