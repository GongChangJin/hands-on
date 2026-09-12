"""Upload the small golden dataset used by the Phoenix experiment."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from phoenix.client import Client


DATASET_NAME = "agent-tool-use-golden-v1"


def default_dataset_path() -> Path:
    return Path(__file__).resolve().parents[2] / "data" / "golden_dataset.jsonl"


def load_examples(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as dataset_file:
        return [json.loads(line) for line in dataset_file if line.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(description="Upload the golden dataset to Phoenix.")
    parser.add_argument("--dataset", type=Path, default=default_dataset_path())
    parser.add_argument("--name", default=DATASET_NAME)
    parser.add_argument(
        "--phoenix-url",
        default=os.getenv("PHOENIX_BASE_URL", "http://localhost:6006"),
    )
    args = parser.parse_args()

    dataset = Client(base_url=args.phoenix_url).datasets.create_dataset(
        name=args.name,
        examples=load_examples(args.dataset),
        dataset_description="Tool selection and grounded answer cases for the Agent evaluation hands-on.",
    )
    print(f"dataset: {dataset.name}")
    print(f"examples: {len(dataset.examples)}")


if __name__ == "__main__":
    main()
