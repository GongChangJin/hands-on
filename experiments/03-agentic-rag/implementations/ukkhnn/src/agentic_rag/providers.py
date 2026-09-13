"""Upstage and DeepSeek chat adapters for LangGraph nodes."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from .types import Usage


@dataclass(frozen=True)
class ProviderSpec:
    api_key_env: str
    base_url: str
    default_model: str


PROVIDERS = {
    "upstage": ProviderSpec(
        api_key_env="UPSTAGE_API_KEY",
        base_url="https://api.upstage.ai/v1",
        default_model="solar-pro4",
    ),
    "deepseek": ProviderSpec(
        api_key_env="DEEPSEEK_API_KEY",
        base_url="https://api.deepseek.com",
        default_model="deepseek-v4-flash",
    ),
}


def provider_spec(provider: str) -> ProviderSpec:
    try:
        return PROVIDERS[provider]
    except KeyError as exc:
        raise ValueError(f"지원 provider는 {', '.join(PROVIDERS)}입니다: {provider}") from exc


def _message_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and isinstance(item.get("text"), str):
                parts.append(item["text"])
        return "".join(parts)
    return str(content)


def parse_json_object(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.removeprefix("```json").removeprefix("```")
        stripped = stripped.removesuffix("```").strip()
    try:
        value = json.loads(stripped)
        if isinstance(value, dict):
            return value
    except json.JSONDecodeError:
        pass
    start = stripped.find("{")
    if start >= 0:
        try:
            value, _ = json.JSONDecoder().raw_decode(stripped[start:])
            if isinstance(value, dict):
                return value
        except json.JSONDecodeError:
            pass
    raise ValueError(f"모델이 JSON object를 반환하지 않았습니다: {stripped[:160]}")


class ChatGateway:
    """A small JSON-only gateway that keeps provider usage separate from graph state."""

    def __init__(self, provider: str, model_name: str | None = None) -> None:
        spec = provider_spec(provider)
        api_key = os.getenv(spec.api_key_env)
        if not api_key:
            raise RuntimeError(
                f"{spec.api_key_env}가 설정되지 않았습니다. 키는 현재 터미널 환경 변수로만 설정하세요."
            )
        self.provider = provider
        self.model_name = model_name or spec.default_model
        self.usage = Usage()
        self._model = ChatOpenAI(
            api_key=api_key,
            base_url=spec.base_url,
            model=self.model_name,
            temperature=0,
            timeout=60,
            max_retries=1,
        )

    def reset_usage(self) -> None:
        self.usage = Usage()

    def _record_usage(self, message: Any) -> None:
        usage = getattr(message, "usage_metadata", None) or {}
        input_details = usage.get("input_token_details") or {}
        self.usage.input_tokens += int(usage.get("input_tokens") or 0)
        self.usage.output_tokens += int(usage.get("output_tokens") or 0)
        self.usage.cached_input_tokens += int(input_details.get("cache_read") or 0)
        self.usage.calls += 1

    async def complete_json(
        self,
        *,
        operation: str,
        system: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        user_content = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        response = await self._model.ainvoke(
            [SystemMessage(content=system), HumanMessage(content=user_content)],
            config={
                "run_name": f"agent.{operation}",
                "tags": ["03-agentic-rag", operation, self.provider],
                "metadata": {"provider": self.provider, "model": self.model_name},
            },
        )
        self._record_usage(response)
        text = _message_text(response.content)
        try:
            return parse_json_object(text)
        except ValueError:
            # Some OpenAI-compatible models occasionally ignore JSON-only output
            # instructions for the final prose answer. The grounding decision has
            # already been made by the grade node, so preserve the prose and attach
            # only the chunk IDs that were actually supplied to this answer call.
            if operation == "answer" and text.strip():
                return {
                    "answer": text.strip(),
                    "citation_chunk_ids": [
                        chunk["chunk_id"] for chunk in payload.get("evidence_chunks", [])
                    ],
                }
            if operation == "rewrite" and text.strip():
                return {"query": text.strip().strip('"')}
            raise
