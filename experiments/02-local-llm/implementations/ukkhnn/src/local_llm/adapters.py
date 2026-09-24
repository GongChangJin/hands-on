"""Ollama and OpenAI-compatible API adapters."""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Iterable

from .types import GenerationRequest, GenerationResponse


def _post_json(url: str, payload: dict[str, Any], headers: dict[str, str] | None = None, timeout: float = 120.0):
    request = urllib.request.Request(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json", **(headers or {})},
        method="POST",
    )
    return urllib.request.urlopen(request, timeout=timeout)


def _get_json(url: str, timeout: float = 10.0) -> dict[str, Any]:
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return json.load(response)


def _nanoseconds_to_ms(value: int | float | None) -> float | None:
    return float(value) / 1_000_000 if value is not None else None


def estimate_upstage_cost(
    model: str,
    *,
    prompt_tokens: int,
    cached_prompt_tokens: int,
    output_tokens: int,
    at: datetime | None = None,
) -> tuple[float | None, dict[str, Any] | None]:
    """Estimate Solar Pro 4 cost from the dated official price table.

    Unknown models deliberately return no estimate. The promotional interval is
    encoded because it was active during the recorded 2026-09-24 benchmark.
    """

    if model != "solar-pro4":
        return None, None
    instant = (at or datetime.now(timezone.utc)).astimezone(timezone.utc)
    promotion_start = datetime(2026, 9, 11, tzinfo=timezone.utc)
    promotion_end = datetime(2026, 10, 10, tzinfo=timezone.utc)
    if promotion_start <= instant < promotion_end:
        prices = {"input_per_million": 0.09, "cached_input_per_million": 0.018, "output_per_million": 0.36, "price_period": "2026-09-11/2026-10-10-promotion"}
    else:
        prices = {"input_per_million": 0.30, "cached_input_per_million": 0.06, "output_per_million": 1.20, "price_period": "standard"}
    uncached = max(0, prompt_tokens - cached_prompt_tokens)
    cost = (
        uncached * prices["input_per_million"]
        + cached_prompt_tokens * prices["cached_input_per_million"]
        + output_tokens * prices["output_per_million"]
    ) / 1_000_000
    return cost, prices


def parse_ollama_stream(lines: Iterable[bytes], *, started_at: float, clock=time.perf_counter) -> GenerationResponse:
    chunks: list[str] = []
    first_token_latency_ms: float | None = None
    final: dict[str, Any] = {}
    for raw_line in lines:
        if not raw_line.strip():
            continue
        chunk = json.loads(raw_line)
        content = str(chunk.get("message", {}).get("content", ""))
        if content and first_token_latency_ms is None:
            first_token_latency_ms = (clock() - started_at) * 1000
        chunks.append(content)
        if chunk.get("done"):
            final = chunk
    output_tokens = int(final.get("eval_count", 0))
    generation_duration_ns = int(final.get("eval_duration", 0))
    tokens_per_second = None
    if output_tokens and generation_duration_ns:
        tokens_per_second = output_tokens / (generation_duration_ns / 1_000_000_000)
    return GenerationResponse(
        text="".join(chunks),
        model=str(final.get("model", "")),
        total_latency_ms=(clock() - started_at) * 1000,
        first_token_latency_ms=first_token_latency_ms,
        prompt_tokens=int(final.get("prompt_eval_count", 0)),
        output_tokens=output_tokens,
        generation_tokens_per_second=tokens_per_second,
        load_duration_ms=_nanoseconds_to_ms(final.get("load_duration")),
        prompt_eval_duration_ms=_nanoseconds_to_ms(final.get("prompt_eval_duration")),
        generation_duration_ms=_nanoseconds_to_ms(final.get("eval_duration")),
        cost_usd=0.0,
        metadata={"done_reason": final.get("done_reason"), "created_at": final.get("created_at")},
    )


@dataclass
class OllamaAdapter:
    model: str
    base_url: str = "http://127.0.0.1:11434"
    context_window: int = 4096
    timeout: float = 120.0
    keep_alive: str = "10m"
    adapter_name: str = "ollama"

    def generate(self, request: GenerationRequest) -> GenerationResponse:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": request.system},
                {"role": "user", "content": request.prompt},
            ],
            "format": request.response_schema,
            "stream": True,
            "keep_alive": self.keep_alive,
            "options": {"temperature": 0, "num_ctx": self.context_window, "seed": 42},
        }
        started_at = time.perf_counter()
        try:
            with _post_json(f"{self.base_url}/api/chat", payload, timeout=self.timeout) as response:
                result = parse_ollama_stream(response, started_at=started_at)
                result.model = result.model or self.model
                return result
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as error:
            return GenerationResponse(
                model=self.model,
                total_latency_ms=(time.perf_counter() - started_at) * 1000,
                cost_usd=0.0,
                error=f"{type(error).__name__}: {error}",
            )

    def warmup(self) -> GenerationResponse:
        request = GenerationRequest(
            task_id="warmup",
            system="JSON만 출력한다.",
            prompt='{"answer":"ok"}를 그대로 출력하라.',
            response_schema={
                "type": "object",
                "additionalProperties": False,
                "required": ["answer"],
                "properties": {"answer": {"const": "ok"}},
            },
        )
        return self.generate(request)

    def inspect(self) -> dict[str, Any]:
        with _post_json(f"{self.base_url}/api/show", {"model": self.model}, timeout=20.0) as response:
            show = json.load(response)
        try:
            ps = _get_json(f"{self.base_url}/api/ps", timeout=10.0)
        except urllib.error.URLError:
            ps = {"models": []}
        active = next((item for item in ps.get("models", []) if item.get("name") == self.model or item.get("model") == self.model), {})
        details = show.get("details", {})
        return {
            "adapter": self.adapter_name,
            "model": self.model,
            "family": details.get("family"),
            "parameter_size": details.get("parameter_size"),
            "quantization_level": details.get("quantization_level"),
            "context_window": self.context_window,
            "model_size_bytes": active.get("size"),
            "accelerator_memory_bytes": active.get("size_vram"),
            "license": next((line.strip() for line in show.get("license", "").splitlines() if line.strip()), None),
            "modified_at": show.get("modified_at"),
        }


@dataclass
class OpenAICompatibleAdapter:
    model: str
    api_key_env: str = "UPSTAGE_API_KEY"
    base_url: str = "https://api.upstage.ai/v1"
    timeout: float = 60.0
    adapter_name: str = "api"

    def _api_key(self) -> str:
        key = os.getenv(self.api_key_env)
        if not key:
            raise RuntimeError(f"{self.api_key_env}가 설정되지 않아 API 기준선을 실행할 수 없습니다.")
        return key

    def generate(self, request: GenerationRequest) -> GenerationResponse:
        started_at = time.perf_counter()
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": request.system},
                {"role": "user", "content": request.prompt},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0,
            "stream": False,
        }
        try:
            with _post_json(
                f"{self.base_url.rstrip('/')}/chat/completions",
                payload,
                headers={"Authorization": f"Bearer {self._api_key()}"},
                timeout=self.timeout,
            ) as response:
                data = json.load(response)
            usage = data.get("usage", {})
            prompt_tokens = int(usage.get("prompt_tokens", 0))
            output_tokens = int(usage.get("completion_tokens", 0))
            cached_prompt_tokens = int(usage.get("prompt_tokens_details", {}).get("cached_tokens", 0))
            cost, pricing = estimate_upstage_cost(
                self.model,
                prompt_tokens=prompt_tokens,
                cached_prompt_tokens=cached_prompt_tokens,
                output_tokens=output_tokens,
            )
            return GenerationResponse(
                text=str(data["choices"][0]["message"]["content"]),
                model=str(data.get("model", self.model)),
                total_latency_ms=(time.perf_counter() - started_at) * 1000,
                prompt_tokens=prompt_tokens,
                output_tokens=output_tokens,
                cost_usd=cost,
                metadata={"provider_request_id": data.get("id"), "pricing": pricing},
            )
        except RuntimeError:
            raise
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, KeyError) as error:
            return GenerationResponse(
                model=self.model,
                total_latency_ms=(time.perf_counter() - started_at) * 1000,
                error=f"{type(error).__name__}: {error}",
            )

    def warmup(self) -> GenerationResponse:
        return GenerationResponse(model=self.model, metadata={"skipped": "API warmup avoids billable extra calls"})

    def inspect(self) -> dict[str, Any]:
        return {
            "adapter": self.adapter_name,
            "model": self.model,
            "base_url": self.base_url,
            "credential_env": self.api_key_env,
            "credential_available": bool(os.getenv(self.api_key_env)),
        }
