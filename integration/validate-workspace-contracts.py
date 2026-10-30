"""Validate the workspace bridge against the unchanged Hands-on JSON Schemas."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from jsonschema import Draft202012Validator


def main() -> None:
    repo = Path(__file__).resolve().parents[1]
    experiment = repo / "experiments/17-personal-ai-handoff"
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", type=Path, default=experiment / "implementations/ukkhnn/results")
    args = parser.parse_args()
    counts = {}
    for filename, contract in {
        "task-requests.jsonl": "task-request",
        "agent-results.jsonl": "agent-result",
        "tool-traces.jsonl": "tool-trace",
        "records.jsonl": "evaluation-record",
    }.items():
        schema = json.loads((repo / "common/contracts" / f"{contract}.schema.json").read_text())
        Draft202012Validator.check_schema(schema)
        validator = Draft202012Validator(schema)
        rows = [json.loads(line) for line in (args.results / filename).read_text().splitlines() if line]
        if not rows:
            raise ValueError(f"Empty results: {filename}")
        for row in rows:
            validator.validate(row)
        counts[contract] = len(rows)
    schema = json.loads((experiment / "shared/handoff-plan.schema.json").read_text())
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(json.loads((args.results / "handoff-plan.json").read_text()))
    print(json.dumps({"validated_records": counts, "source_handoff_schema": "passed"}))


if __name__ == "__main__":
    main()
