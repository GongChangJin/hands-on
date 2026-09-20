"""CLI for preparation, safe analysis, evaluation, and comparison."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
from pathlib import Path
from typing import Any

from .contracts import validate_contract
from .evaluation import load_adaptive_tasks, load_tasks, run_adaptive_evaluation, run_evaluation
from .fixtures import prepare_shared, validate_fixtures
from .observability import configure_phoenix, shutdown_phoenix
from .paths import CONTEXT_DIR, IMPLEMENTATION_DIR, PROJECT_DIR, TASKS_PATH
from .preprocessing import load_label
from .provider import DEFAULT_MODEL, DeepSeekVisionGateway
from .reporting import compare_results
from .workflow import MultimodalAgent


def _runtime_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--model", default=os.getenv("DEEPSEEK_MODEL", DEFAULT_MODEL))
    parser.add_argument(
        "--phoenix-endpoint",
        default=os.getenv("PHOENIX_COLLECTOR_ENDPOINT", "http://localhost:6006/v1/traces"),
    )
    parser.add_argument("--no-phoenix", action="store_true")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Privacy-gated DeepSeek multimodal UI evaluator")
    commands = parser.add_subparsers(dest="command", required=True)

    commands.add_parser("prepare", help="합성 fixture, label, context와 paired task를 재생성하고 검증")
    commands.add_parser("validate-fixtures", help="공통 fixture 안전성과 연결을 전체 검증")

    analyze = commands.add_parser("analyze", help="하나의 fixture를 TaskRequest로 분석")
    analyze.add_argument("image", type=Path)
    analyze.add_argument(
        "--condition",
        choices=("image-only", "image-with-context"),
        default="image-only",
    )
    analyze.add_argument("--task-id")
    _runtime_options(analyze)

    evaluate = commands.add_parser("evaluate", help="한 입력 조건의 전체 또는 smoke 평가")
    evaluate.add_argument(
        "--condition",
        choices=("image-only", "image-with-context", "adaptive-context"),
        required=True,
    )
    evaluate.add_argument("--tasks", type=Path, default=TASKS_PATH)
    evaluate.add_argument("--limit", type=int)
    evaluate.add_argument("--output", type=Path, required=True)
    _runtime_options(evaluate)

    compare = commands.add_parser("compare", help="두 입력 조건의 정확도·비용·지연시간 비교")
    compare.add_argument("first", type=Path)
    compare.add_argument("second", type=Path)
    compare.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def _analyze_task(image: Path, *, condition: str, task_id: str | None) -> dict[str, Any]:
    resolved = image.resolve()
    label = load_label(resolved.stem)
    context_path = CONTEXT_DIR / f"{resolved.stem}.json"
    task = {
        "task_id": task_id or f"interactive-{resolved.stem}-{condition}",
        "task_type": "vision",
        "input": {
            "condition": condition,
            "image_path": str(resolved),
            "context_path": str(context_path) if condition == "image-with-context" else None,
        },
        "attachments": [
            {
                "type": "image",
                "uri": f"shared/fixtures/{resolved.name}",
                "metadata": {"mime_type": label["mime_type"], "sha256": label["sha256"]},
            }
        ],
        "constraints": {
            "allowed_tools": ["image_preprocessor", "privacy_scanner", "deepseek_vision"],
            "forbidden_actions": ["send_unscanned_image", "expose_personal_data", "invent_pixel_coordinates"],
            "max_steps": 5,
            "max_tool_calls": 3,
        },
        "expected_output": {
            "fixture_id": resolved.stem,
            "error_types": label["expected_error_types"],
            "severity": label["severity"],
            "evidence": label["evidence"],
            "acceptable_uncertainty": label["acceptable_uncertainty"],
        },
        "metadata": {"condition": condition, "interactive": True},
    }
    validate_contract("task-request", task)
    return task


async def _run_model_command(args: argparse.Namespace) -> None:
    gateway = DeepSeekVisionGateway(args.model)
    phoenix_provider = None
    if not args.no_phoenix:
        phoenix_provider = configure_phoenix(args.phoenix_endpoint)
    try:
        agent = MultimodalAgent(gateway)
        if args.command == "analyze":
            outcome = await agent.run(
                _analyze_task(args.image, condition=args.condition, task_id=args.task_id)
            )
            print(json.dumps(outcome.as_dict(), ensure_ascii=False, indent=2))
        else:
            if args.condition == "adaptive-context":
                tasks = load_adaptive_tasks(args.tasks, limit=args.limit)
                summary = await run_adaptive_evaluation(agent, tasks, output=args.output)
            else:
                tasks = load_tasks(args.tasks, condition=args.condition, limit=args.limit)
                summary = await run_evaluation(
                    agent,
                    tasks,
                    output=args.output,
                    condition=args.condition,
                )
            print(json.dumps(summary, ensure_ascii=False, indent=2))
    finally:
        shutdown_phoenix(phoenix_provider)


def main() -> None:
    args = parse_args()
    try:
        if args.command == "prepare":
            print(json.dumps(prepare_shared(), ensure_ascii=False, indent=2))
        elif args.command == "validate-fixtures":
            print(json.dumps(validate_fixtures(), ensure_ascii=False, indent=2))
        elif args.command == "compare":
            compare_results(args.first, args.second, args.output)
            print(str(args.output))
        else:
            asyncio.run(_run_model_command(args))
    except (RuntimeError, ValueError, OSError) as exc:
        raise SystemExit(str(exc)) from exc


if __name__ == "__main__":
    main()
