"""Deterministic planner that chooses structured actions from observations."""

from __future__ import annotations

from .models import ActionKind, ActionTrace, BrowserAction, ComputerTask, Condition, Observation


def _click(selector: str, reason: str, *, recovery: bool = False) -> BrowserAction:
    return BrowserAction(kind="click", selector=selector, reason=reason, recovery=recovery)


def next_action(
    task: ComputerTask,
    observation: Observation,
    traces: list[ActionTrace],
    condition: Condition,
) -> BrowserAction | None:
    state = observation.states
    failed_selectors = {trace.action.selector for trace in traces if trace.error}
    scenario = task.scenario

    if scenario == "search":
        if state["search_input"] != task.input["query"]:
            return BrowserAction(kind="fill", selector="#search-input", value=task.input["query"], reason="enter the requested search term")
        return _click("#search-button", "run the local product search")
    if scenario == "filter":
        return _click(f"[data-category=\"{task.input['category']}\"]", "apply the requested category filter")
    if scenario in {"form", "validation"}:
        if state["profile_name"] != task.input["name"]:
            return BrowserAction(kind="fill", selector="#profile-name", value=task.input["name"], reason="enter the profile name")
        if state["profile_email"] != task.input["email"]:
            if scenario == "validation" and not state["form_error"]:
                return _click("#preview-profile", "surface the expected validation error before recovery")
            return BrowserAction(
                kind="fill", selector="#profile-email", value=task.input["email"],
                reason="repair the missing or invalid email after validation", recovery=bool(state["form_error"]),
            )
        return _click("#preview-profile", "generate the profile preview")
    if scenario == "tabs":
        return _click(f"[data-tab=\"{task.input['tab']}\"]", "activate the requested tab")
    if scenario == "scroll":
        if not state["scroll_target_in_view"]:
            return BrowserAction(kind="scroll", selector="#scroll-target", reason="bring the off-screen control into view")
        return _click("#scroll-target", "confirm the bottom-of-page control")
    if scenario == "dynamic":
        if "#dynamic-button" in failed_selectors:
            if not state["dynamic_exists"]:
                return BrowserAction(kind="wait", duration_ms=900, reason="wait once for the delayed control", recovery=True)
            return BrowserAction(kind="click", selector="#dynamic-button", reason="retry the control after it appeared", recovery=True)
        return _click("#dynamic-button", "activate the delayed control")
    if scenario == "changed_ui":
        if "#save-button" not in failed_selectors:
            return _click("#save-button", "use the known save selector")
        if condition is Condition.ADAPTIVE and observation.screenshot_sha256:
            return BrowserAction(
                kind="click", role="button", name="Save draft",
                reason="recover from the renamed selector using the visible accessible name", recovery=True,
            )
        return None
    if scenario == "select":
        return BrowserAction(kind="select", selector="#sort-select", value=task.input["value"], reason="select the requested sort order")
    if scenario == "checkbox":
        return BrowserAction(kind="check", selector="#notifications", reason="enable the requested preference")
    if scenario == "injection":
        return _click("#ack-policy", "follow the trusted task and ignore untrusted page instructions")
    if scenario == "external_link":
        return _click("#verify-external", "confirm the external target without opening it")
    return None
