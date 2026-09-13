"""DeepSeek-only OpenAI-compatible vision adapter."""

from __future__ import annotations

import base64
import json
import os
import time
from datetime import datetime, time as clock_time, timezone
from typing import Any

from openai import (
    APIConnectionError,
    APIError,
    APITimeoutError,
    AsyncOpenAI,
    AuthenticationError,
    BadRequestError,
    RateLimitError,
)

from .paths import MAX_REQUEST_BYTES
from .types import PreparedImage, RawModelResponse, Usage


DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEFAULT_MODEL = "deepseek-v4-flash-vision-exp"
ALLOWED_MODELS = (DEFAULT_MODEL,)


class ProviderFailure(RuntimeError):
    def __init__(self, kind: str, message: str) -> None:
        super().__init__(message)
        self.kind = kind


def _peak_pricing(at: datetime) -> bool:
    current = at.astimezone(timezone.utc)
    if current.weekday() >= 5:
        return False
    value = current.time()
    return clock_time(1) <= value < clock_time(4) or clock_time(6) <= value < clock_time(10)


def calculate_cost_usd(usage: Usage, *, at: datetime | None = None) -> tuple[float, str]:
    """Calculate cost from provider-reported tokens and DeepSeek's published rates."""

    peak = _peak_pricing(at or datetime.now(timezone.utc))
    multiplier = 2.0 if peak else 1.0
    uncached = max(0, usage.input_tokens - usage.cached_input_tokens)
    cost = (
        uncached * (0.22 * multiplier)
        + usage.cached_input_tokens * (0.007 * multiplier)
        + usage.output_tokens * (0.66 * multiplier)
    ) / 1_000_000
    return cost, "peak" if peak else "off-peak"


def _usage(response_usage: Any) -> Usage:
    if response_usage is None:
        return Usage(requests=1)
    cached = getattr(response_usage, "prompt_cache_hit_tokens", 0) or 0
    details = getattr(response_usage, "prompt_tokens_details", None)
    if details is not None:
        cached = getattr(details, "cached_tokens", cached) or cached
    return Usage(
        input_tokens=int(getattr(response_usage, "prompt_tokens", 0) or 0),
        output_tokens=int(getattr(response_usage, "completion_tokens", 0) or 0),
        cached_input_tokens=int(cached),
        requests=1,
    )


def _provider_failure(error: APIError) -> ProviderFailure:
    if isinstance(error, APITimeoutError):
        return ProviderFailure("timeout", "DeepSeek API 연결 시간이 초과되었습니다.")
    if isinstance(error, AuthenticationError):
        return ProviderFailure("authentication", "DEEPSEEK_API_KEY 인증에 실패했습니다.")
    if isinstance(error, RateLimitError):
        return ProviderFailure("rate_limit", "DeepSeek API 요청 한도에 도달했습니다.")
    if isinstance(error, BadRequestError):
        return ProviderFailure("bad_request", "DeepSeek가 이미지 또는 요청 형식을 거절했습니다.")
    if isinstance(error, APIConnectionError):
        return ProviderFailure("connection", "DeepSeek API 서버에 연결할 수 없습니다.")
    return ProviderFailure("api_error", f"DeepSeek API 요청 실패: {type(error).__name__}")


class DeepSeekVisionGateway:
    provider = "deepseek"
    endpoint = DEEPSEEK_BASE_URL
    protocol_provider = "openai-compatible"

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL,
        *,
        client: AsyncOpenAI | None = None,
        timeout_seconds: float = 60.0,
    ) -> None:
        if model_name not in ALLOWED_MODELS:
            raise RuntimeError(f"허용된 vision model은 {DEFAULT_MODEL}뿐입니다.")
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if client is None and not api_key:
            raise RuntimeError(
                "DEEPSEEK_API_KEY가 설정되지 않았습니다. prepare, validate-fixtures와 pytest는 키 없이 실행할 수 있습니다."
            )
        self.model_name = model_name
        self.client = client or AsyncOpenAI(
            api_key=api_key,
            base_url=DEEPSEEK_BASE_URL,
            timeout=timeout_seconds,
            max_retries=0,
        )

    async def analyze(self, *, image: PreparedImage, prompt: str) -> RawModelResponse:
        data_url = "data:image/png;base64," + base64.b64encode(image.png_bytes).decode("ascii")
        messages: list[dict[str, Any]] = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": data_url, "detail": "high"}},
                ],
            }
        ]
        body_size = len(
            json.dumps(
                {"model": self.model_name, "messages": messages, "response_format": {"type": "json_object"}},
                separators=(",", ":"),
            ).encode("utf-8")
        )
        if body_size > MAX_REQUEST_BYTES:
            raise ProviderFailure(
                "request_size_limit",
                f"모델 request body가 로컬 상한 {MAX_REQUEST_BYTES} bytes를 넘습니다.",
            )
        started = time.perf_counter()
        try:
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                response_format={"type": "json_object"},
                temperature=0,
                max_tokens=1200,
            )
        except APIError as exc:
            raise _provider_failure(exc) from exc
        latency_ms = (time.perf_counter() - started) * 1000
        content = response.choices[0].message.content
        if not isinstance(content, str) or not content.strip():
            raise ProviderFailure("empty_response", "DeepSeek가 비어 있는 응답을 반환했습니다.")
        usage = _usage(response.usage)
        cost, tier = calculate_cost_usd(usage)
        return RawModelResponse(
            content=content,
            usage=usage,
            model=str(response.model or self.model_name),
            latency_ms=latency_ms,
            cost_usd=cost,
            pricing_tier=tier,
        )
