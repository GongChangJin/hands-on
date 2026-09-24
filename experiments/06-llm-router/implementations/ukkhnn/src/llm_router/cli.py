"""Command-line entry point."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from .classifiers import HeuristicClassifier, SolarClassifier
from .evaluation import export_evaluation, export_fallback, run_evaluation, run_fallback_suite
from .io import implementation_dir, load_dataset, load_metrics, load_policy
from .models import TaskRequest
from .report import evaluation_report
from .router import HybridRouter


def _classifier(name: str, timeout_seconds: float):
    if name == "solar":
        return SolarClassifier(
            model=os.getenv("ROUTER_CLASSIFIER_MODEL", "solar-pro4"),
            base_url=os.getenv("UPSTAGE_BASE_URL", "https://api.upstage.ai/v1"),
            timeout_seconds=timeout_seconds,
        )
    return HeuristicClassifier()


def evaluate(args: argparse.Namespace) -> int:
    policy = load_policy(args.policy)
    metrics = load_metrics(args.metrics)
    cases = load_dataset(args.dataset)
    router = HybridRouter(policy, metrics, classifier=_classifier(args.classifier, policy.classifier_timeout_seconds))
    records, summary = run_evaluation(cases, router)
    report = evaluation_report(summary, records, args.classifier)
    export_evaluation(args.output, records, summary, report)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary["routing_accuracy"] >= 0.9 else 1


def fallback(args: argparse.Namespace) -> int:
    policy = load_policy(args.policy)
    metrics = load_metrics(args.metrics)
    rows, summary = run_fallback_suite(policy, metrics)
    export_fallback(args.output, rows, summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary["passed"] == summary["scenarios"] else 1


def route(args: argparse.Namespace) -> int:
    policy = load_policy(args.policy)
    metrics = load_metrics(args.metrics)
    task = TaskRequest(
        task_id="cli-request",
        prompt=args.prompt,
        modalities=args.modality,
        data_scope=args.data_scope,
        complexity=args.complexity,
        risk=args.risk,
        needs_current_info=args.current,
        required_capabilities=args.capability,
        signals_complete=not args.infer,
    )
    decision = HybridRouter(policy, metrics, classifier=_classifier(args.classifier, policy.classifier_timeout_seconds)).route(task)
    print(decision.model_dump_json(indent=2))
    return 2 if decision.blocked else 0


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(prog="llm-router")
    result.set_defaults(policy=None, metrics=None)
    commands = result.add_subparsers(dest="command", required=True)

    evaluate_parser = commands.add_parser("evaluate")
    evaluate_parser.add_argument("--classifier", choices=("heuristic", "solar"), default="heuristic")
    evaluate_parser.add_argument("--dataset", type=Path)
    evaluate_parser.add_argument("--policy", type=Path)
    evaluate_parser.add_argument("--metrics", type=Path)
    evaluate_parser.add_argument("--output", type=Path, default=implementation_dir() / "results" / "hybrid-router")
    evaluate_parser.set_defaults(handler=evaluate)

    fallback_parser = commands.add_parser("fallback")
    fallback_parser.add_argument("--policy", type=Path)
    fallback_parser.add_argument("--metrics", type=Path)
    fallback_parser.add_argument("--output", type=Path, default=implementation_dir() / "results" / "fallback-suite")
    fallback_parser.set_defaults(handler=fallback)

    route_parser = commands.add_parser("route")
    route_parser.add_argument("prompt")
    route_parser.add_argument("--classifier", choices=("heuristic", "solar"), default="heuristic")
    route_parser.add_argument("--policy", type=Path)
    route_parser.add_argument("--metrics", type=Path)
    route_parser.add_argument("--modality", action="append", default=["text"])
    route_parser.add_argument("--data-scope", choices=("public", "private", "local_only"), default="public")
    route_parser.add_argument("--complexity", choices=("low", "moderate", "high"), default="moderate")
    route_parser.add_argument("--risk", choices=("low", "medium", "high"), default="low")
    route_parser.add_argument("--current", action="store_true")
    route_parser.add_argument("--capability", action="append", default=[])
    route_parser.add_argument("--infer", action="store_true")
    route_parser.set_defaults(handler=route)
    return result


def main() -> int:
    args = parser().parse_args()
    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
