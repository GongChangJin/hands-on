"""CLI for the integration replay suite."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .evaluation import load_scenarios, run_suite
from .live import run_live_smoke
from .paths import INTEGRATION_DIR


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(prog="integrated-agent")
    result.add_argument("command", choices=("replay", "live-smoke"))
    result.add_argument("--scenarios", type=Path, default=INTEGRATION_DIR / "scenarios/replay-v1.jsonl")
    result.add_argument("--output", type=Path, default=INTEGRATION_DIR / "results/replay-v1")
    return result


def main() -> int:
    args = parser().parse_args()
    if args.command == "live-smoke":
        if args.output == INTEGRATION_DIR / "results/replay-v1":
            args.output = INTEGRATION_DIR / "results/live-smoke-v1"
        summary = run_live_smoke(args.output)
    else:
        summary = run_suite(load_scenarios(args.scenarios), args.output)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary["passed"] == summary["scenarios"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
