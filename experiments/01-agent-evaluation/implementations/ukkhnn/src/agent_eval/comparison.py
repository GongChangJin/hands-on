"""Run the same Phoenix experiment for both Agent architectures."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from .agent import ARCHITECTURES
from .dataset import DATASET_NAME
from .providers import PROVIDERS
from .report import comparison_markdown, default_report_root


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare single and handoff Agents in Phoenix.")
    parser.add_argument(
        "--provider",
        choices=tuple(PROVIDERS),
        default=os.getenv("AGENT_PROVIDER", "upstage"),
    )
    parser.add_argument("--model", default=os.getenv("AGENT_MODEL"))
    parser.add_argument("--dataset", default=DATASET_NAME)
    parser.add_argument("--repetitions", type=int, default=1)
    parser.add_argument("--llm-judge", action="store_true")
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument(
        "--phoenix-url",
        default=os.getenv("PHOENIX_BASE_URL", "http://localhost:6006"),
    )
    parser.add_argument(
        "--phoenix-endpoint",
        default=os.getenv("PHOENIX_COLLECTOR_ENDPOINT", "http://localhost:6006/v1/traces"),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.repetitions < 1:
        raise SystemExit("--repetitions는 1 이상이어야 합니다.")
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output_dir = args.output_dir or default_report_root() / f"{timestamp}-{args.provider}-comparison"
    output_dir.mkdir(parents=True, exist_ok=True)

    summaries = []
    for architecture in ARCHITECTURES:
        report_dir = output_dir / architecture
        command = [
            sys.executable,
            "-m",
            "agent_eval.experiment",
            "--provider",
            args.provider,
            "--architecture",
            architecture,
            "--dataset",
            args.dataset,
            "--repetitions",
            str(args.repetitions),
            "--report-dir",
            str(report_dir),
            "--phoenix-url",
            args.phoenix_url,
            "--phoenix-endpoint",
            args.phoenix_endpoint,
        ]
        if args.model:
            command.extend(["--model", args.model])
        if args.llm_judge:
            command.append("--llm-judge")
        print(f"\n▶ {architecture} architecture")
        subprocess.run(command, check=True)
        summaries.append(
            json.loads((report_dir / "summary.json").read_text(encoding="utf-8"))
        )

    (output_dir / "summaries.json").write_text(
        json.dumps(summaries, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    comparison_path = output_dir / "comparison.md"
    comparison_path.write_text(comparison_markdown(summaries), encoding="utf-8")
    print(f"\n📊 Comparison: {comparison_path}")


if __name__ == "__main__":
    main()
