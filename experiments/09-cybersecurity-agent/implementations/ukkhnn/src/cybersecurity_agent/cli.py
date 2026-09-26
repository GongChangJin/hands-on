"""Command-line entry point."""

from __future__ import annotations

import argparse
from pathlib import Path

from .agent import CybersecurityAgent, RUN_ID
from .io import implementation_dir, load_policy


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the container-isolated security evaluation.")
    parser.add_argument("--output", type=Path, default=implementation_dir() / "results" / RUN_ID)
    args = parser.parse_args()
    summary = CybersecurityAgent(load_policy()).run(args.output.resolve())
    print(
        f"decision={summary['fixture']['decision']} "
        f"detection={summary['fixture']['detection_rate']:.0%} "
        f"remediation={summary['fixture']['remediation_rate']:.0%} "
        f"handoffs={summary['coding_handoffs']['approved']}/{summary['coding_handoffs']['total']}"
    )


if __name__ == "__main__":
    main()
