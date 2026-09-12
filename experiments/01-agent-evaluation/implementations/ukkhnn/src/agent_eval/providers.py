"""Model provider adapters for OpenAI-compatible chat completion APIs."""

from __future__ import annotations

import os
from dataclasses import dataclass

from agents.models.openai_chatcompletions import OpenAIChatCompletionsModel
from openai import (
    APIConnectionError,
    APIError,
    APITimeoutError,
    AsyncOpenAI,
    AuthenticationError,
    BadRequestError,
    RateLimitError,
)


@dataclass(frozen=True)
class ProviderSpec:
    api_key_env: str
    base_url: str
    default_model: str
    experiment_concurrency: int
    check_models_before_experiment: bool = False


PROVIDERS = {
    "upstage": ProviderSpec(
        api_key_env="UPSTAGE_API_KEY",
        base_url="https://api.upstage.ai/v1",
        default_model="solar-pro4",
        experiment_concurrency=3,
    ),
    "deepseek": ProviderSpec(
        api_key_env="DEEPSEEK_API_KEY",
        base_url="https://api.deepseek.com",
        default_model="deepseek-v4-flash",
        experiment_concurrency=1,
        check_models_before_experiment=True,
    ),
}


def provider_spec(provider: str) -> ProviderSpec:
    try:
        return PROVIDERS[provider]
    except KeyError as exc:
        choices = ", ".join(PROVIDERS)
        raise ValueError(f"지원하지 않는 provider입니다: {provider} (선택: {choices})") from exc


def build_client(provider: str) -> AsyncOpenAI:
    spec = provider_spec(provider)
    api_key = os.getenv(spec.api_key_env)
    if not api_key:
        raise RuntimeError(
            f"{spec.api_key_env}가 설정되지 않았습니다. 키는 현재 터미널 환경 변수로만 설정하세요."
        )

    return AsyncOpenAI(
        api_key=api_key,
        base_url=spec.base_url,
        timeout=60.0,
        max_retries=0,
    )


def build_model(
    provider: str,
    model_name: str | None = None,
    *,
    client: AsyncOpenAI | None = None,
) -> OpenAIChatCompletionsModel:
    """Build an Agents SDK model backed by the selected provider."""

    spec = provider_spec(provider)
    return OpenAIChatCompletionsModel(
        model=model_name or spec.default_model,
        openai_client=client or build_client(provider),
    )


def provider_error_message(provider: str, error: APIError) -> str:
    """Translate provider failures into a short, actionable Korean message."""

    if isinstance(error, APITimeoutError):
        return f"{provider} API 연결 시간이 초과되었습니다. 잠시 후 다시 실행해 주세요."
    if isinstance(error, AuthenticationError):
        return f"{provider} API 키 인증에 실패했습니다. 현재 터미널의 키를 확인해 주세요."
    if isinstance(error, RateLimitError):
        return f"{provider} API 요청 한도에 도달했습니다. 잠시 후 다시 실행해 주세요."
    if isinstance(error, BadRequestError):
        return f"{provider} API가 요청을 거절했습니다. 모델 ID와 요청 형식을 확인해 주세요."
    if isinstance(error, APIConnectionError):
        return f"{provider} API 서버에 연결할 수 없습니다. 네트워크 상태를 확인해 주세요."
    return f"{provider} API 요청에 실패했습니다: {type(error).__name__}"
