"""Command-line entry point for every required research workflow stage."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from .deepseek import DEFAULT_MODEL, DeepSeekGateway
from .observability import configure_phoenix, shutdown_phoenix, span
from .paths import IMPLEMENTATION_DIR
from .workflow import ResearchWorkflow, validate_shared


CONDITIONS = ("semantic-scholar-only", "federated-verified")


def _runtime(parser: argparse.ArgumentParser, *, offline_option: bool = False) -> None:
    parser.add_argument("--model", default=os.getenv("DEEPSEEK_MODEL", DEFAULT_MODEL))
    parser.add_argument(
        "--phoenix-endpoint",
        default=os.getenv("PHOENIX_COLLECTOR_ENDPOINT", "http://localhost:6006/v1/traces"),
    )
    parser.add_argument("--no-phoenix", action="store_true")
    if offline_option:
        parser.add_argument("--offline", action="store_true")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verified DeepSeek research-agent experiment")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("prepare", help="validate fixed shared question, strategies, filters, schemas and tasks")
    commands.add_parser("validate-shared", help="validate shared contracts without external calls")

    search = commands.add_parser("search", help="search official scholarly metadata APIs")
    search.add_argument("--condition", choices=CONDITIONS, required=True)
    search.add_argument("--output", type=Path, required=True)
    _runtime(search)

    validate = commands.add_parser("validate-corpus", help="validate identifiers and conservatively deduplicate")
    validate.add_argument("input", type=Path)
    _runtime(validate)

    analyze = commands.add_parser("analyze", help="extract bounded evidence and synthesize a report")
    analyze.add_argument("--condition", choices=CONDITIONS, required=True)
    analyze.add_argument("--input", type=Path, required=True)
    analyze.add_argument("--output", type=Path, required=True)
    _runtime(analyze)

    evaluate = commands.add_parser("evaluate", help="run deterministic, non-LLM graders")
    evaluate.add_argument("--condition", choices=CONDITIONS, required=True)
    evaluate.add_argument("--input", type=Path, required=True)
    evaluate.add_argument("--output", type=Path, required=True)
    _runtime(evaluate)

    compare = commands.add_parser("compare", help="compare two deterministic evaluation directories")
    compare.add_argument("first", type=Path)
    compare.add_argument("second", type=Path)
    compare.add_argument("--output", type=Path, required=True)

    run_all = commands.add_parser("run-all", help="execute both conditions from search through comparison")
    run_all.add_argument("--output", type=Path, required=True)
    _runtime(run_all, offline_option=True)
    return parser.parse_args()


def _gateway(model: str, *, offline: bool) -> DeepSeekGateway | None:
    if offline or not os.getenv("DEEPSEEK_API_KEY"):
        return None
    return DeepSeekGateway(model)


def _workflow(args: argparse.Namespace, *, offline: bool = False) -> ResearchWorkflow:
    fixture = IMPLEMENTATION_DIR / "tests" / "fixtures" / "offline-search-records.jsonl"
    return ResearchWorkflow(
        gateway=_gateway(getattr(args, "model", DEFAULT_MODEL), offline=offline),
        offline=offline,
        offline_fixture=fixture if offline else None,
    )


def _print(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def main() -> None:
    args = parse_args()
    if args.command in ("prepare", "validate-shared"):
        _print(validate_shared())
        return
    if args.command == "compare":
        workflow = ResearchWorkflow()
        workflow.compare(args.first, args.second, args.output)
        print(args.output)
        return
    offline = bool(getattr(args, "offline", False))
    provider = None
    if not args.no_phoenix:
        provider = configure_phoenix(args.phoenix_endpoint)
    try:
        workflow = _workflow(args, offline=offline)
        if args.command == "search":
            with span("research.workflow", task_id=f"search-{args.condition}", project="05-research-agent", offline=False):
                value = workflow.search(args.condition, args.output)
        elif args.command == "validate-corpus":
            with span("research.workflow", task_id="validate-corpus", project="05-research-agent", offline=False):
                value = workflow.validate_corpus(args.input)
        elif args.command == "analyze":
            with span("research.workflow", task_id=f"analyze-{args.condition}", project="05-research-agent", offline=False):
                value = workflow.analyze(args.condition, args.input, args.output)
        elif args.command == "evaluate":
            with span("research.workflow", task_id=f"evaluate-{args.condition}", project="05-research-agent", offline=False):
                value = workflow.evaluate(args.condition, args.input, args.output)
        else:
            value = workflow.run_all(args.output)
        _print(value)
    finally:
        shutdown_phoenix(provider)


if __name__ == "__main__":
    main()
