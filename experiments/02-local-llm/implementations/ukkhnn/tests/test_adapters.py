import json
from datetime import datetime, timezone

import pytest

from local_llm.adapters import OpenAICompatibleAdapter, estimate_upstage_cost, parse_ollama_stream
from local_llm.types import GenerationRequest


def test_ollama_stream_metrics_are_derived_from_provider_counters():
    lines = [
        json.dumps({"message": {"content": "{\"answer\":"}, "done": False}).encode(),
        json.dumps({
            "model": "qwen-test",
            "message": {"content": "42}"},
            "done": True,
            "prompt_eval_count": 10,
            "eval_count": 4,
            "load_duration": 2_000_000,
            "prompt_eval_duration": 50_000_000,
            "eval_duration": 200_000_000,
        }).encode(),
    ]
    ticks = iter([1.020, 1.250])
    result = parse_ollama_stream(lines, started_at=1.0, clock=lambda: next(ticks))
    assert result.text == '{"answer":42}'
    assert result.first_token_latency_ms == pytest.approx(20)
    assert result.total_latency_ms == pytest.approx(250)
    assert result.generation_tokens_per_second == pytest.approx(20)
    assert result.load_duration_ms == pytest.approx(2)


def test_api_baseline_refuses_to_run_without_credential(monkeypatch):
    monkeypatch.delenv("UPSTAGE_API_KEY", raising=False)
    adapter = OpenAICompatibleAdapter(model="solar-pro4")
    request = GenerationRequest(
        task_id="x",
        system="JSON",
        prompt="{}",
        response_schema={"type": "object"},
    )
    with pytest.raises(RuntimeError, match="UPSTAGE_API_KEY"):
        adapter.generate(request)


def test_api_inspection_never_returns_a_credential(monkeypatch):
    monkeypatch.setenv("UPSTAGE_API_KEY", "secret-value-that-must-not-leak")
    info = OpenAICompatibleAdapter(model="solar-pro4").inspect()
    assert info["credential_available"] is True
    assert "secret-value" not in json.dumps(info)


def test_solar_pro4_cost_uses_dated_promotion_and_unknown_models_are_not_guessed():
    cost, pricing = estimate_upstage_cost(
        "solar-pro4",
        prompt_tokens=1_000_000,
        cached_prompt_tokens=0,
        output_tokens=1_000_000,
        at=datetime(2026, 9, 24, tzinfo=timezone.utc),
    )
    assert cost == pytest.approx(0.45)
    assert "promotion" in pricing["price_period"]
    assert estimate_upstage_cost(
        "unknown",
        prompt_tokens=1,
        cached_prompt_tokens=0,
        output_tokens=1,
    ) == (None, None)
