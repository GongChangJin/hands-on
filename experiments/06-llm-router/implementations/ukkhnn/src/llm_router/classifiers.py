"""Agent classifiers used only when request signals are incomplete."""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol

from .models import AgentRoute, ClassifierResult, TaskRequest


def estimate_solar_pro4_cost(prompt_tokens: int, cached_tokens: int, output_tokens: int) -> float:
    """Use the official rate active for the 2026-09-24 benchmark run."""

    now = datetime.now(timezone.utc)
    promotional = datetime(2026, 9, 11, tzinfo=timezone.utc) <= now < datetime(2026, 10, 10, tzinfo=timezone.utc)
    if promotional:
        input_rate, cached_rate, output_rate = 0.09, 0.018, 0.36
    else:
        input_rate, cached_rate, output_rate = 0.30, 0.06, 1.20
    uncached_tokens = max(0, prompt_tokens - cached_tokens)
    return (uncached_tokens * input_rate + cached_tokens * cached_rate + output_tokens * output_rate) / 1_000_000


class AgentClassifier(Protocol):
    def classify(self, task: TaskRequest) -> ClassifierResult: ...


def infer_agents_from_text(task: TaskRequest) -> list[AgentRoute]:
    text = task.prompt.casefold()
    agents: list[AgentRoute] = []
    keyword_groups = {
        AgentRoute.VISION: ("스크린샷", "화면", "이미지", "첨부", "image", "screenshot"),
        AgentRoute.RESEARCH: ("논문", "여러 출처", "조사", "연구", "research", "papers"),
        AgentRoute.BROWSER: ("브라우저", "사이트", "웹 ", "페이지를 열", "browser", "website"),
        AgentRoute.CODING: ("저장소", "코드", "타입 오류", "테스트", "repository", "code"),
        AgentRoute.RAG: ("문서에서", "지식 베이스", "내부 문서", "knowledge base"),
    }
    if "image" in task.modalities:
        agents.append(AgentRoute.VISION)
    for agent, keywords in keyword_groups.items():
        if agent not in agents and any(keyword in text for keyword in keywords):
            agents.append(agent)
    return agents


@dataclass
class HeuristicClassifier:
    confidence: float = 0.82

    def classify(self, task: TaskRequest) -> ClassifierResult:
        started = time.perf_counter()
        return ClassifierResult(
            agents=infer_agents_from_text(task),
            confidence=self.confidence,
            reason="incomplete request signals resolved by deterministic text and modality hints",
            latency_ms=(time.perf_counter() - started) * 1000,
        )


@dataclass
class SolarClassifier:
    model: str = "solar-pro4"
    base_url: str = "https://api.upstage.ai/v1"
    api_key_env: str = "UPSTAGE_API_KEY"
    timeout_seconds: float = 15.0

    def _api_key(self) -> str:
        value = os.getenv(self.api_key_env)
        if not value:
            raise RuntimeError(f"{self.api_key_env} is not configured")
        return value

    def classify(self, task: TaskRequest) -> ClassifierResult:
        schema = {
            "agents": ["zero or more of rag, vision, research, browser, coding"],
            "confidence": "number from 0 to 1",
            "reason": "short explanation",
        }
        prompt = {
            "request": task.model_dump(mode="json"),
            "rules": {
                "rag": "search a supplied knowledge base or internal documents",
                "vision": "inspect an image or screenshot",
                "research": "synthesize multiple external sources or papers",
                "browser": "interact with or navigate a live website",
                "coding": "inspect, edit, or execute a code repository",
            },
            "output_schema": schema,
        }
        body = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a routing classifier. Return only one JSON object. Select only agents required to execute the request.",
                },
                {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0,
            "stream": False,
        }
        request = urllib.request.Request(
            f"{self.base_url.rstrip('/')}/chat/completions",
            data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {self._api_key()}"},
            method="POST",
        )
        started = time.perf_counter()
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                payload = json.load(response)
        except TimeoutError:
            raise
        except urllib.error.URLError as error:
            if isinstance(error.reason, TimeoutError):
                raise TimeoutError(str(error)) from error
            raise RuntimeError(f"classifier provider failure: {error}") from error
        latency_ms = (time.perf_counter() - started) * 1000
        try:
            content = json.loads(payload["choices"][0]["message"]["content"])
            usage = payload.get("usage", {})
            prompt_tokens = int(usage.get("prompt_tokens", 0))
            output_tokens = int(usage.get("completion_tokens", 0))
            cached_tokens = int(usage.get("prompt_tokens_details", {}).get("cached_tokens", 0))
            content.update(
                {
                    "latency_ms": latency_ms,
                    "input_tokens": prompt_tokens,
                    "output_tokens": output_tokens,
                    "cost_usd": estimate_solar_pro4_cost(prompt_tokens, cached_tokens, output_tokens),
                    "provider_request_id": payload.get("id"),
                }
            )
            return ClassifierResult.model_validate(content)
        except (KeyError, TypeError, json.JSONDecodeError, ValueError) as error:
            raise ValueError(f"invalid classifier response: {error}") from error
