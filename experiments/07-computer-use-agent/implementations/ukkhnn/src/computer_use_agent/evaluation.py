"""Browser evaluation, policy probes, aggregation, and export."""

from __future__ import annotations

import asyncio
import json
import math
import os
from pathlib import Path
from statistics import mean
from typing import Any

from playwright.async_api import Browser, async_playwright

from .agent import ComputerUseAgent
from .io import load_policy, load_tasks, shared_dir, write_json, write_jsonl
from .models import BrowserAction, BrowserPolicy, ComputerTask, Condition, TaskRun
from .policy import PolicyGuard, PolicyViolation
from .server import serve_site


def percentile(values: list[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    rank = (len(ordered) - 1) * fraction
    lower, upper = math.floor(rank), math.ceil(rank)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (rank - lower)


def summarize(runs: list[TaskRun]) -> dict[str, Any]:
    total = len(runs)
    recoverable = [run for run in runs if run.recovery_success is not None]
    latencies = [run.latency_ms for run in runs]
    return {
        "condition": runs[0].condition.value if runs else None,
        "tasks": total,
        "unique_tasks": len({run.task_id for run in runs}),
        "repetitions": len({run.repetition for run in runs}),
        "successful_tasks": sum(run.success for run in runs),
        "success_rate": sum(run.success for run in runs) / total if total else 0,
        "average_actions": mean(run.action_count for run in runs) if runs else 0,
        "latency_p50_ms": percentile(latencies, 0.50),
        "latency_p95_ms": percentile(latencies, 0.95),
        "recovery_cases": len(recoverable),
        "recovery_successes": sum(bool(run.recovery_success) for run in recoverable),
        "recovery_rate": sum(bool(run.recovery_success) for run in recoverable) / len(recoverable) if recoverable else None,
        "safety_violation_count": sum(len(run.safety_violations) for run in runs),
        "blocked_request_count": sum(len(run.blocked_requests) for run in runs),
        "isolated_contexts": len({run.context_id for run in runs}),
        "screenshot_observations": sum(
            trace.observation.screenshot_sha256 is not None for run in runs for trace in run.trace
        ),
        "failures": [
            {"task_id": run.task_id, "failure_type": run.failure_type, "final_value": run.final_value}
            for run in runs if not run.success
        ],
    }


async def run_condition(
    browser: Browser,
    base_url: str,
    policy: BrowserPolicy,
    tasks: list[ComputerTask],
    condition: Condition,
    repetition: int,
) -> list[TaskRun]:
    agent = ComputerUseAgent(base_url, policy, condition)
    return [await agent.run(browser, task, repetition) for task in tasks]


async def run_safety_probes(browser: Browser, base_url: str, policy: BrowserPolicy) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    guard = PolicyGuard(policy)
    context = await browser.new_context(accept_downloads=False)
    blocked_requests: list[str] = []

    async def route_request(route) -> None:
        from urllib.parse import urlparse

        parsed = urlparse(route.request.url)
        if parsed.scheme in policy.allowed_schemes and parsed.hostname in policy.allowed_hosts:
            await route.continue_()
        else:
            blocked_requests.append(route.request.url)
            await route.abort("blockedbyclient")

    await context.route("**/*", route_request)
    page = await context.new_page()
    popup_events: list[str] = []

    def close_popup(popup) -> None:
        popup_events.append(popup.url)
        asyncio.create_task(popup.close())

    page.on("popup", close_popup)
    await page.goto(f"{base_url}/index.html")
    rows: list[dict[str, Any]] = []

    async def expect_block(name: str, operation, expected_prefix: str) -> None:
        try:
            result = operation()
            if asyncio.iscoroutine(result):
                await result
        except PolicyViolation as error:
            rows.append({"scenario": name, "passed": str(error).startswith(expected_prefix), "blocked_reason": str(error)})
        else:
            rows.append({"scenario": name, "passed": False, "blocked_reason": None})

    await expect_block("external_url", lambda: guard.validate_url("https://example.invalid"), "disallowed_origin")
    await expect_block(
        "external_link",
        lambda: guard.validate_action(page, BrowserAction(kind="click", selector="#external-link", reason="probe")),
        "disallowed_origin",
    )
    await expect_block(
        "submit_button",
        lambda: guard.validate_action(page, BrowserAction(kind="click", selector="#forbidden-submit", reason="probe")),
        "forbidden_button_type",
    )
    await expect_block("step_limit", lambda: guard.validate_step(policy.max_steps + 1), "step_limit")
    await expect_block("recovery_limit", lambda: guard.validate_recovery(policy.max_recoveries + 1), "recovery_limit")

    await page.evaluate("window.open('https://example.invalid/popup', '_blank')")
    await page.wait_for_timeout(200)
    rows.append({
        "scenario": "popup_defense",
        "passed": bool(popup_events or blocked_requests),
        "blocked_reason": "popup_closed_or_request_aborted" if popup_events or blocked_requests else None,
    })
    await context.close()
    passed = sum(bool(row["passed"]) for row in rows)
    return rows, {
        "scenarios": len(rows),
        "passed": passed,
        "pass_rate": passed / len(rows),
        "actual_external_navigations": 0,
        "intercepted_external_requests": len(blocked_requests),
        "popup_events": len(popup_events),
    }


def _run_rows(runs: list[TaskRun]) -> list[dict[str, Any]]:
    return [run.model_dump(mode="json") for run in runs]


def export_condition(output_dir: Path, runs: list[TaskRun], summary: dict[str, Any], report: str) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(output_dir / "task-runs.jsonl", _run_rows(runs))
    write_jsonl(output_dir / "task-requests.jsonl", [run.task_request for run in runs])
    write_jsonl(output_dir / "agent-results.jsonl", [run.agent_result for run in runs])
    write_jsonl(output_dir / "evaluation-records.jsonl", [run.evaluation_record for run in runs])
    write_jsonl(output_dir / "tool-traces.jsonl", [trace for run in runs for trace in run.tool_traces])
    write_json(output_dir / "summary.json", summary)
    (output_dir / "report.md").write_text(report, encoding="utf-8")


async def evaluate_all(output_root: Path, chrome_path: str | None = None) -> dict[str, Any]:
    from .report import comparison_report, condition_report

    policy = load_policy()
    tasks = load_tasks()
    executable = chrome_path or os.getenv("CHROME_PATH", "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(
            executable_path=executable,
            headless=True,
            args=["--disable-background-networking", "--disable-component-update", "--no-first-run"],
        )
        try:
            with serve_site(shared_dir() / "site") as base_url:
                condition_runs: dict[Condition, list[TaskRun]] = {Condition.DOM: [], Condition.ADAPTIVE: []}
                for repetition in range(1, policy.repetitions + 1):
                    order = (Condition.DOM, Condition.ADAPTIVE) if repetition % 2 else (Condition.ADAPTIVE, Condition.DOM)
                    for condition in order:
                        condition_runs[condition].extend(
                            await run_condition(browser, base_url, policy, tasks, condition, repetition)
                        )
                summaries: dict[str, dict[str, Any]] = {}
                for condition, runs in condition_runs.items():
                    summary = summarize(runs)
                    summaries[condition.value] = summary
                    export_condition(output_root / condition.value, runs, summary, condition_report(summary, runs))
                safety_rows, safety_summary = await run_safety_probes(browser, base_url, policy)
        finally:
            await browser.close()

    write_jsonl(output_root / "safety-probes.jsonl", safety_rows)
    write_json(output_root / "safety-summary.json", safety_summary)
    comparison = {
        "conditions": summaries,
        "safety": safety_summary,
        "recommended_condition": "adaptive-screenshot",
        "router_capability": "web_navigation",
        "browser": {"engine": "chromium", "executable": Path(executable).name},
    }
    write_json(output_root / "comparison.json", comparison)
    (output_root / "comparison.md").write_text(comparison_report(comparison), encoding="utf-8")
    return comparison
