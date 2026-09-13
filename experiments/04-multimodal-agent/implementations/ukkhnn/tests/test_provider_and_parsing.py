from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

import multimodal_agent.provider as provider_module
from multimodal_agent.parsing import OutputParseError, parse_analysis
from multimodal_agent.paths import FIXTURES_DIR
from multimodal_agent.preprocessing import preprocess_image
from multimodal_agent.provider import DeepSeekVisionGateway, ProviderFailure, calculate_cost_usd
from multimodal_agent.types import Usage


VALID_ANALYSIS = {
    "summary": "The action overlaps the total.",
    "overall_severity": "high",
    "errors": [
        {
            "error_type": "layout_break",
            "severity": "high",
            "evidence": [{"region": "order-summary", "claim": "Pay now covers the total."}],
            "uncertainty": "The CSS cause is not visible.",
            "suggested_fix": "Place the button below the total.",
        }
    ],
}


def test_json_parser_accepts_object_and_fenced_json() -> None:
    import json

    encoded = json.dumps(VALID_ANALYSIS)
    assert parse_analysis(encoded) == VALID_ANALYSIS
    assert parse_analysis(f"```json\n{encoded}\n```") == VALID_ANALYSIS


@pytest.mark.parametrize(
    "content",
    [
        "not json",
        "[]",
        '{"summary":"missing fields"}',
        '{"summary":"normal","overall_severity":"high","errors":[]}',
    ],
)
def test_json_parser_preserves_invalid_output_as_error(content: str) -> None:
    with pytest.raises(OutputParseError):
        parse_analysis(content)


def test_openai_key_is_never_a_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "must-not-be-used")
    with pytest.raises(RuntimeError, match="DEEPSEEK_API_KEY"):
        DeepSeekVisionGateway()


def test_cost_uses_peak_and_off_peak_rates() -> None:
    usage = Usage(input_tokens=1000, output_tokens=100, cached_input_tokens=100)
    off_peak, off_peak_tier = calculate_cost_usd(
        usage, at=datetime(2026, 9, 13, 12, tzinfo=timezone.utc)
    )
    peak, peak_tier = calculate_cost_usd(
        usage, at=datetime(2026, 9, 14, 2, tzinfo=timezone.utc)
    )
    assert off_peak_tier == "off-peak"
    assert peak_tier == "peak"
    assert peak == pytest.approx(off_peak * 2)


class FakeCompletions:
    def __init__(self) -> None:
        self.kwargs = None

    async def create(self, **kwargs):
        self.kwargs = kwargs
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content='{"summary":"normal","overall_severity":"none","errors":[]}'))],
            usage=SimpleNamespace(prompt_tokens=25, completion_tokens=10, prompt_cache_hit_tokens=5),
            model="deepseek-v4-flash-vision-exp",
        )


class FakeClient:
    def __init__(self) -> None:
        self.base_url = "https://api.deepseek.com"
        self.chat = SimpleNamespace(completions=FakeCompletions())


def test_gateway_sends_only_deepseek_vision_shape() -> None:
    client = FakeClient()
    gateway = DeepSeekVisionGateway(client=client)  # type: ignore[arg-type]
    image = preprocess_image(FIXTURES_DIR / "ui-normal-021.png")
    result = asyncio.run(gateway.analyze(image=image, prompt="analyze"))
    kwargs = client.chat.completions.kwargs
    assert kwargs["model"] == "deepseek-v4-flash-vision-exp"
    assert kwargs["messages"][0]["content"][1]["type"] == "image_url"
    assert kwargs["messages"][0]["content"][1]["image_url"]["url"].startswith("data:image/png;base64,")
    assert result.usage.total_tokens == 35
    assert result.usage.cached_input_tokens == 5


def test_request_body_limit_is_enforced(monkeypatch: pytest.MonkeyPatch) -> None:
    client = FakeClient()
    gateway = DeepSeekVisionGateway(client=client)  # type: ignore[arg-type]
    image = preprocess_image(FIXTURES_DIR / "ui-normal-021.png")
    monkeypatch.setattr(provider_module, "MAX_REQUEST_BYTES", 100)
    with pytest.raises(ProviderFailure) as caught:
        asyncio.run(gateway.analyze(image=image, prompt="analyze"))
    assert caught.value.kind == "request_size_limit"
    assert client.chat.completions.kwargs is None


def test_injected_non_deepseek_endpoint_is_rejected() -> None:
    client = FakeClient()
    client.base_url = "https://api.openai.com/v1"
    with pytest.raises(RuntimeError, match="api.deepseek.com"):
        DeepSeekVisionGateway(client=client)  # type: ignore[arg-type]
