"""Prompts shared by local and API adapters."""

from __future__ import annotations

import json
from typing import Any

from .types import GenerationRequest


SYSTEM_PROMPT = """당신은 결정적 평가용 도우미다.
사용자가 준 자료만 사용한다. 외부 도구나 네트워크를 사용하지 않는다.
응답은 지정된 JSON Schema를 만족하는 JSON 객체 하나만 출력한다.
설명, 마크다운 코드 블록, 추가 필드는 출력하지 않는다."""


def build_request(task: dict[str, Any]) -> GenerationRequest:
    expected = task["expected_output"]
    schema = expected["response_schema"]
    prompt = (
        f"작업:\n{json.dumps(task['input'], ensure_ascii=False, sort_keys=True)}\n\n"
        f"응답 JSON Schema:\n{json.dumps(schema, ensure_ascii=False, sort_keys=True)}"
    )
    return GenerationRequest(
        task_id=task["task_id"],
        system=SYSTEM_PROMPT,
        prompt=prompt,
        response_schema=schema,
    )
