#!/usr/bin/env python3
# 기준선(all-frontier) 대비 라우팅 전략 비교.
#   python compare.py --tasks tasks/routing.jsonl --strategies rule hybrid --repeats 3
from __future__ import annotations

import argparse
from pathlib import Path

import evalkit_bridge  # noqa: F401

from evalkit import build_report, load_tasks, run_suite  # noqa: E402

from eval_agent import build  # noqa: E402

EXPERIMENT = "06-llm-router"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tasks", default="tasks/routing.jsonl")
    ap.add_argument("--strategies", nargs="+", default=["all_frontier", "rule", "hybrid"])
    ap.add_argument("--repeats", type=int, default=1)
    ap.add_argument("--out", default="runs")
    args = ap.parse_args()

    outdir = Path(args.out)
    outdir.mkdir(parents=True, exist_ok=True)
    tasks = load_tasks(args.tasks)

    sections = []
    for strategy in args.strategies:
        records = run_suite(
            tasks,
            build(strategy),
            experiment=EXPERIMENT,
            implementation=f"us788/{strategy}",
            repeats=args.repeats,
            out_path=outdir / f"{strategy}.jsonl",
        )
        sections.append(build_report(records, title=f"전략: {strategy}"))

    report = "\n\n".join(sections)
    (outdir / "compare.md").write_text(report, encoding="utf-8")
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
