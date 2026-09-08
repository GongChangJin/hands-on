#!/usr/bin/env python3
# 평가 실행 CLI.
#   python run_eval.py --tasks tasks/sample.jsonl --agent agents.echo:build --repeats 3
from __future__ import annotations

import argparse
import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from evalkit import build_report, load_tasks, run_suite  # noqa: E402


def resolve_agent(spec: str):
    # "module.path:factory" 형식. factory()는 AgentFn을 돌려준다.
    module_name, _, attr = spec.partition(":")
    if not attr:
        raise SystemExit("--agent 는 module:factory 형식이어야 합니다")
    return getattr(importlib.import_module(module_name), attr)()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tasks", required=True)
    ap.add_argument("--agent", required=True, help="module:factory")
    ap.add_argument("--experiment", default="01-agent-evaluation")
    ap.add_argument("--implementation", default="us788")
    ap.add_argument("--repeats", type=int, default=1)
    ap.add_argument("--out", default="runs/records.jsonl")
    ap.add_argument("--report", default="runs/report.md")
    args = ap.parse_args()

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    tasks = load_tasks(args.tasks)
    agent = resolve_agent(args.agent)
    records = run_suite(
        tasks,
        agent,
        experiment=args.experiment,
        implementation=args.implementation,
        repeats=args.repeats,
        out_path=args.out,
    )
    report = build_report(records, title=f"{args.experiment} / {args.implementation}")
    Path(args.report).write_text(report, encoding="utf-8")
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
