"""Command-line entry point for the learning runner."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .agents import FlawedScriptedAgent, OracleScriptedAgent
from .runner import EvaluationRunner, summarize, write_jsonl


def default_dataset_path() -> Path:
    for candidate in Path(__file__).resolve().parents:
        if candidate.name == "01-agent-evaluation":
            return candidate / "shared" / "evals" / "tasks.jsonl"
    raise FileNotFoundError("01-agent-evaluation 프로젝트 루트를 찾을 수 없습니다.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run deterministic agent evaluation fixtures.")
    parser.add_argument("--agent", choices=("oracle", "flawed"), default="oracle")
    parser.add_argument("--dataset", type=Path, default=default_dataset_path())
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    agent = OracleScriptedAgent() if args.agent == "oracle" else FlawedScriptedAgent()
    output_path = args.output or Path("runs") / f"{args.agent}.jsonl"

    runner = EvaluationRunner()
    tasks = runner.load_tasks(args.dataset)
    records = runner.evaluate(tasks, agent)
    write_jsonl(records, output_path)

    print(json.dumps(summarize(records), ensure_ascii=False, indent=2))
    print(f"records: {output_path.resolve()}")


if __name__ == "__main__":
    main()
