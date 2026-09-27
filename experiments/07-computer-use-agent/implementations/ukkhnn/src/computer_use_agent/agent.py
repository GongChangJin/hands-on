"""Isolated Playwright execution loop with policy checks and DOM assertions."""

from __future__ import annotations

import asyncio
import time
import uuid
from typing import Any
from urllib.parse import urlencode, urlparse

from playwright.async_api import Browser, Error as PlaywrightError, Page

from .contracts import validate
from .models import (
    ActionKind,
    ActionTrace,
    BrowserAction,
    BrowserPolicy,
    ComputerTask,
    Condition,
    TaskRun,
)
from .observation import observe
from .planner import next_action
from .policy import PolicyGuard, PolicyViolation


class ComputerUseAgent:
    router_capability = "web_navigation"

    def __init__(self, base_url: str, policy: BrowserPolicy, condition: Condition):
        self.base_url = base_url.rstrip("/")
        self.policy = policy
        self.condition = condition
        self.guard = PolicyGuard(policy)

    async def _assertion_value(self, page: Page, task: ComputerTask) -> str | bool | None:
        locator = page.locator(task.expected.selector)
        if await locator.count() == 0:
            return None
        if task.expected.property == "text":
            value = await locator.first.text_content()
            return value.strip() if value is not None else None
        if task.expected.property == "value":
            return await locator.first.input_value()
        if task.expected.property == "checked":
            return await locator.first.is_checked()
        raise ValueError(f"unsupported assertion property: {task.expected.property}")

    async def _execute(self, page: Page, action: BrowserAction) -> None:
        locator = page.get_by_role(action.role, name=action.name) if action.role and action.name else page.locator(action.selector or "")
        timeout = self.policy.action_timeout_ms
        if action.kind is ActionKind.CLICK:
            await locator.first.click(timeout=timeout)
        elif action.kind is ActionKind.FILL:
            await locator.first.fill(action.value or "", timeout=timeout)
        elif action.kind is ActionKind.SELECT:
            await locator.first.select_option(action.value or "", timeout=timeout)
        elif action.kind is ActionKind.CHECK:
            await locator.first.check(timeout=timeout)
        elif action.kind is ActionKind.SCROLL:
            await locator.first.scroll_into_view_if_needed(timeout=timeout)
        elif action.kind is ActionKind.WAIT:
            await page.wait_for_timeout(action.duration_ms or 0)
        else:
            raise PolicyViolation(f"unsupported_action:{action.kind.value}")

    async def run(self, browser: Browser, task: ComputerTask, repetition: int = 1) -> TaskRun:
        return await asyncio.wait_for(self._run(browser, task, repetition), timeout=self.policy.task_timeout_ms / 1000)

    async def _run(self, browser: Browser, task: ComputerTask, repetition: int) -> TaskRun:
        started = time.perf_counter()
        context_id = str(uuid.uuid4())
        blocked_requests: list[str] = []
        safety_violations: list[str] = []
        traces: list[ActionTrace] = []
        tool_traces: list[dict[str, Any]] = []
        recovery_count = 0
        failure_type: str | None = None
        context = await browser.new_context(accept_downloads=False)

        async def route_request(route) -> None:
            parsed = urlparse(route.request.url)
            if parsed.scheme in self.policy.allowed_schemes and parsed.hostname in self.policy.allowed_hosts:
                await route.continue_()
            else:
                blocked_requests.append(route.request.url)
                await route.abort("blockedbyclient")

        await context.route("**/*", route_request)
        page = await context.new_page()

        def close_popup(popup) -> None:
            blocked_requests.append(f"popup:{popup.url}")
            asyncio.create_task(popup.close())

        def cancel_download(download) -> None:
            blocked_requests.append(f"download:{download.suggested_filename}")
            asyncio.create_task(download.cancel())

        if self.policy.block_popups:
            page.on("popup", close_popup)
        if self.policy.block_downloads:
            page.on("download", cancel_download)

        target_url = f"{self.base_url}/index.html?{urlencode({'variant': task.variant, 'task': task.task_id})}"
        self.guard.validate_url(target_url)
        try:
            navigation_started = time.perf_counter()
            await page.goto(target_url, wait_until="domcontentloaded")
            navigation_ms = (time.perf_counter() - navigation_started) * 1000
            tool_traces.append({
                "task_id": task.task_id,
                "tool_name": "browser.navigate",
                "input_summary": "navigate to isolated localhost fixture",
                "result_summary": page.url,
                "duration_ms": navigation_ms,
                "error": None,
                "metadata": {"context_id": context_id},
            })

            for step in range(1, self.policy.max_steps + 1):
                self.guard.validate_step(step)
                current_value = await self._assertion_value(page, task)
                if current_value == task.expected.equals:
                    break
                capture_screenshot = (
                    self.condition is Condition.ADAPTIVE
                    and bool(traces)
                    and traces[-1].error is not None
                )
                observation = await observe(page, capture_screenshot=capture_screenshot)
                action = next_action(task, observation, traces, self.condition)
                if action is None:
                    failure_type = "planner_exhausted"
                    break
                action_started = time.perf_counter()
                error: str | None = None
                outcome = "ok"
                try:
                    await self.guard.validate_action(page, action)
                    if action.recovery:
                        recovery_count += 1
                        self.guard.validate_recovery(recovery_count)
                    await self._execute(page, action)
                except PolicyViolation as violation:
                    error = str(violation)
                    outcome = "blocked"
                    safety_violations.append(error)
                    failure_type = "policy_block"
                except PlaywrightError as play_error:
                    error = f"{type(play_error).__name__}: {play_error}".splitlines()[0]
                    outcome = "failed"
                duration_ms = (time.perf_counter() - action_started) * 1000
                action_trace = ActionTrace(
                    step=step,
                    observation=observation,
                    action=action,
                    outcome=outcome,
                    duration_ms=duration_ms,
                    error=error,
                )
                traces.append(action_trace)
                tool_traces.append({
                    "task_id": task.task_id,
                    "tool_name": f"browser.{action.kind.value}",
                    "input_summary": action.model_dump_json(exclude={"reason"}),
                    "result_summary": outcome,
                    "duration_ms": duration_ms,
                    "error": error,
                    "metadata": {
                        "step": step,
                        "reason": action.reason,
                        "recovery": action.recovery,
                        "url_after": page.url,
                        "screenshot_sha256": observation.screenshot_sha256,
                    },
                })
                if failure_type == "policy_block":
                    break
            else:
                failure_type = "step_limit"

            final_value = await self._assertion_value(page, task)
            success = final_value == task.expected.equals and not safety_violations
            if not success and failure_type is None:
                failure_type = "dom_assertion_failed"
            status = "success" if success else ("blocked" if failure_type == "policy_block" else "failed")
            latency_ms = (time.perf_counter() - started) * 1000
            recovery_success = success and recovery_count > 0 if task.recovery_expected else None
            agent_result = {
                "task_id": task.task_id,
                "status": status,
                "output": {"final_value": final_value, "expected": task.expected.equals},
                "evidence": [{
                    "source": "final_dom",
                    "location": task.expected.selector,
                    "claim": f"{task.expected.property}={final_value}",
                }],
                "actions": [trace.action.kind.value for trace in traces],
                "limitations": [] if success else [failure_type or "unknown_failure"],
                "metadata": {
                    "condition": self.condition.value,
                    "context_id": context_id,
                    "router_capability": self.router_capability,
                    "recovery_count": recovery_count,
                    "repetition": repetition,
                    "blocked_requests": blocked_requests,
                },
            }
            evaluation_record = {
                "task_id": task.task_id,
                "implementation_id": f"ukkhnn:playwright:{self.condition.value}",
                "task_success": success,
                "quality_score": 1.0 if success else 0.0,
                "tool_accuracy": 1.0 if not safety_violations else 0.0,
                "latency_ms": latency_ms,
                "usage": {"actions": len(traces), "recoveries": recovery_count},
                "cost": 0.0,
                "safety_violations": safety_violations,
                "failure_type": failure_type,
                "metadata": {
                    "condition": self.condition.value,
                    "context_id": context_id,
                    "final_value": final_value,
                    "expected_value": task.expected.equals,
                    "recovery_expected": task.recovery_expected,
                    "recovery_success": recovery_success,
                    "repetition": repetition,
                    "blocked_requests": blocked_requests,
                },
            }
            task_request = task.task_request(self.policy.max_steps)
            validate("task-request", task_request)
            validate("agent-result", agent_result)
            validate("evaluation-record", evaluation_record)
            for trace in tool_traces:
                validate("tool-trace", trace)
            return TaskRun(
                task_id=task.task_id,
                repetition=repetition,
                condition=self.condition,
                success=success,
                status=status,
                latency_ms=latency_ms,
                action_count=len(traces),
                recovery_count=recovery_count,
                recovery_success=recovery_success,
                final_value=final_value,
                failure_type=failure_type,
                safety_violations=safety_violations,
                blocked_requests=blocked_requests,
                context_id=context_id,
                trace=traces,
                task_request=task_request,
                agent_result=agent_result,
                tool_traces=tool_traces,
                evaluation_record=evaluation_record,
            )
        finally:
            await context.close()
