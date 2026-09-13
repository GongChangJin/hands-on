from __future__ import annotations

import json

import pytest

from multimodal_agent.paths import TASKS_PATH
from multimodal_agent.types import RawModelResponse, Usage


def task_for(condition: str = "image-only", index: int = 0) -> dict:
    tasks = [
        json.loads(line)
        for line in TASKS_PATH.read_text(encoding="utf-8").splitlines()
        if line
    ]
    return [task for task in tasks if task["input"]["condition"] == condition][index]


class LabelGateway:
    provider = "deepseek"
    model_name = "deepseek-v4-flash-vision-exp"

    def __init__(self) -> None:
        self.calls = 0
        self.prompts: list[str] = []

    async def analyze(self, *, image, prompt):
        self.calls += 1
        self.prompts.append(prompt)
        label = image.label
        errors = [
            {
                "error_type": error_type,
                "severity": label["severity"],
                "evidence": label["evidence"],
                "uncertainty": label["acceptable_uncertainty"],
                "suggested_fix": "Adjust the affected UI component and verify the state.",
            }
            for error_type in label["expected_error_types"]
        ]
        value = {
            "summary": "A deterministic fake response used only by local tests.",
            "overall_severity": label["severity"],
            "errors": errors,
        }
        return RawModelResponse(
            content=json.dumps(value),
            usage=Usage(input_tokens=300, output_tokens=90, requests=1),
            model=self.model_name,
            latency_ms=10.0,
            cost_usd=0.0001254,
            pricing_tier="off-peak",
        )


@pytest.fixture
def label_gateway() -> LabelGateway:
    return LabelGateway()
