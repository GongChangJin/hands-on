"""DeepSeek-only JSON gateway with current official model and pricing."""

from __future__ import annotations

import json
import os
import re
import time
from datetime import datetime, time as clock_time, timezone
from typing import Any
from urllib.parse import urlparse

import httpx

from .types import ModelResult, Usage, WorkflowFailure


DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_HOSTNAME = "api.deepseek.com"
DEFAULT_MODEL = "deepseek-flash"
ALLOWED_MODELS = (DEFAULT_MODEL,)
PRICING_CHECKED_AT = "2026-09-16"
PRICING_SOURCE = "https://api-docs.deepseek.com/quick_start/pricing/"
OFF_PEAK_RATES_PER_MILLION = {"cache_hit_input": 0.003, "cache_miss_input": 0.15, "output": 0.60}


def is_peak(at: datetime) -> bool:
    current = at.astimezone(timezone.utc)
    if current.weekday() >= 5:
        return False
    value = current.time()
    return clock_time(1) <= value < clock_time(4) or clock_time(6) <= value < clock_time(10)


def calculate_cost_usd(usage: Usage, *, at: datetime | None = None) -> tuple[float, str]:
    peak = is_peak(at or datetime.now(timezone.utc))
    multiplier = 2 if peak else 1
    uncached = max(0, usage.input_tokens - usage.cached_input_tokens)
    cost = (
        uncached * OFF_PEAK_RATES_PER_MILLION["cache_miss_input"] * multiplier
        + usage.cached_input_tokens * OFF_PEAK_RATES_PER_MILLION["cache_hit_input"] * multiplier
        + usage.output_tokens * OFF_PEAK_RATES_PER_MILLION["output"] * multiplier
    ) / 1_000_000
    return cost, "peak" if peak else "off-peak"


def _parse_json_text(content: str) -> dict[str, Any]:
    candidate = content.strip()
    fenced = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", candidate, flags=re.DOTALL | re.IGNORECASE)
    if fenced:
        candidate = fenced.group(1)
    try:
        value = json.loads(candidate)
    except json.JSONDecodeError as exc:
        raise WorkflowFailure("model_parsing", "DeepSeek returned invalid JSON") from exc
    if not isinstance(value, dict):
        raise WorkflowFailure("model_parsing", "DeepSeek JSON must be an object")
    return value


def _failure(response: httpx.Response) -> WorkflowFailure:
    if response.status_code in (401, 403):
        return WorkflowFailure("authentication", "DeepSeek authentication failed")
    if response.status_code == 429:
        return WorkflowFailure("rate_limit", "DeepSeek rate limit reached", retryable=True)
    if response.status_code >= 500:
        return WorkflowFailure("server_error", "DeepSeek server error", retryable=True)
    return WorkflowFailure("bad_request", f"DeepSeek returned HTTP {response.status_code}")


class DeepSeekGateway:
    provider = "deepseek"
    protocol_provider = "openai-compatible"
    endpoint = DEEPSEEK_BASE_URL

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        *,
        client: httpx.Client | None = None,
        api_key: str | None = None,
        maximum_attempts: int = 2,
    ) -> None:
        if model not in ALLOWED_MODELS:
            raise RuntimeError(f"Only the pinned DeepSeek text model is allowed: {DEFAULT_MODEL}")
        key = api_key or os.getenv("DEEPSEEK_API_KEY")
        if client is None and not key:
            raise RuntimeError("DEEPSEEK_API_KEY is not available; model execution is unexecuted")
        if client is not None:
            parsed = urlparse(str(client.base_url))
            if parsed.scheme != "https" or parsed.hostname != DEEPSEEK_HOSTNAME:
                raise RuntimeError("Injected clients must use https://api.deepseek.com only")
        self.model = model
        self.maximum_attempts = maximum_attempts
        self.client = client or httpx.Client(
            base_url=DEEPSEEK_BASE_URL,
            timeout=httpx.Timeout(120),
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        )

    def complete_json(self, *, system: str, user: str, max_tokens: int = 5000) -> ModelResult:
        payload = {
            "model": self.model,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "response_format": {"type": "json_object"},
            "thinking": {"type": "disabled"},
            "temperature": 0,
            "max_tokens": max_tokens,
        }
        last: WorkflowFailure | None = None
        for attempt in range(self.maximum_attempts):
            started = time.perf_counter()
            try:
                response = self.client.post("/chat/completions", json=payload)
            except httpx.TimeoutException as exc:
                last = WorkflowFailure("timeout", "DeepSeek request timed out", retryable=True)
                if attempt + 1 == self.maximum_attempts:
                    raise last from exc
                continue
            except httpx.RequestError as exc:
                last = WorkflowFailure("connection", "DeepSeek connection failed", retryable=True)
                if attempt + 1 == self.maximum_attempts:
                    raise last from exc
                continue
            if response.status_code >= 400:
                last = _failure(response)
                if not last.retryable or attempt + 1 == self.maximum_attempts:
                    raise last
                continue
            latency_ms = (time.perf_counter() - started) * 1000
            try:
                body = response.json()
                content = body["choices"][0]["message"]["content"]
                usage_body = body.get("usage") or {}
            except (json.JSONDecodeError, KeyError, IndexError, TypeError) as exc:
                raise WorkflowFailure("model_parsing", "DeepSeek response envelope is invalid") from exc
            details = usage_body.get("prompt_tokens_details") or {}
            usage = Usage(
                input_tokens=int(usage_body.get("prompt_tokens") or 0),
                output_tokens=int(usage_body.get("completion_tokens") or 0),
                cached_input_tokens=int(details.get("cached_tokens") or usage_body.get("prompt_cache_hit_tokens") or 0),
                requests=1,
            )
            cost, tier = calculate_cost_usd(usage)
            return ModelResult(
                value=_parse_json_text(str(content)),
                usage=usage,
                response_model=str(body.get("model") or self.model),
                latency_ms=latency_ms,
                cost_usd=cost,
                pricing_tier=tier,
            )
        assert last is not None
        raise last

    def expand_queries(self, question: str, seeds: list[str]) -> ModelResult:
        return self.complete_json(
            system="Return strict JSON only. Expand an academic RAG research query without changing its scope.",
            user=json.dumps(
                {
                    "question": question,
                    "seed_queries": seeds,
                    "requirements": {"additional_queries": "array of 1 to 4 English strings", "avoid": ["Google Scholar syntax", "new research scope"]},
                },
                ensure_ascii=False,
            ),
            max_tokens=1000,
        )
