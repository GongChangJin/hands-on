from __future__ import annotations

import io
from datetime import datetime, timezone

import httpx
import pytest
from pypdf import PdfWriter

from research_agent.content import SafeContentFetcher, validate_public_url
from research_agent.deepseek import DEFAULT_MODEL, DeepSeekGateway, calculate_cost_usd
from research_agent.observability import safe_attributes
from research_agent.types import Usage, WorkflowFailure
from research_agent.workflow import _confidence


def public_resolver(host: str, port: int, **kwargs):
    return [(2, 1, 6, "", ("8.8.8.8", port))]


def private_resolver(host: str, port: int, **kwargs):
    return [(2, 1, 6, "", ("127.0.0.1", port))]


@pytest.mark.parametrize("url", ["http://arxiv.org/pdf/test", "https://user:pass@arxiv.org/test", "https://arxiv.org:8443/test"])
def test_url_policy_rejects_unsafe_shape(url: str) -> None:
    with pytest.raises(WorkflowFailure):
        validate_public_url(url, resolver=public_resolver)


def test_ssrf_and_hostname_allowlist_block_private_or_unknown_hosts() -> None:
    with pytest.raises(WorkflowFailure, match="non-public") as caught:
        validate_public_url("https://arxiv.org/pdf/test", resolver=private_resolver)
    assert caught.value.kind == "ssrf_blocked"
    with pytest.raises(WorkflowFailure) as caught:
        validate_public_url("https://example.com/file.pdf", resolver=public_resolver)
    assert caught.value.kind == "hostname_not_allowed"


def test_redirect_target_is_revalidated() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(302, headers={"Location": "https://127.0.0.1/private"})

    fetcher = SafeContentFetcher(client=httpx.Client(transport=httpx.MockTransport(handler)), resolver=public_resolver)
    with pytest.raises(WorkflowFailure) as caught:
        fetcher.fetch("https://arxiv.org/pdf/test")
    assert caught.value.kind in ("hostname_not_allowed", "ssrf_blocked")


def test_pdf_mime_signature_and_size_limits() -> None:
    mismatch = httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(200, headers={"Content-Type": "application/pdf"}, content=b"not-pdf")))
    fetcher = SafeContentFetcher(client=mismatch, resolver=public_resolver)
    with pytest.raises(WorkflowFailure) as caught:
        fetcher.fetch("https://arxiv.org/pdf/test")
    assert caught.value.kind == "mime_signature_mismatch"

    oversized = httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(200, headers={"Content-Type": "application/pdf", "Content-Length": "9999"}, content=b"%PDF-test")))
    fetcher = SafeContentFetcher(client=oversized, resolver=public_resolver, maximum_bytes=100)
    with pytest.raises(WorkflowFailure) as caught:
        fetcher.fetch("https://arxiv.org/pdf/test")
    assert caught.value.kind == "content_size_limit"


def test_pdf_page_limit_is_enforced() -> None:
    buffer = io.BytesIO()
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    writer.add_blank_page(width=100, height=100)
    writer.write(buffer)
    client = httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(200, headers={"Content-Type": "application/pdf"}, content=buffer.getvalue())))
    fetcher = SafeContentFetcher(client=client, resolver=public_resolver, maximum_pages=1)
    with pytest.raises(WorkflowFailure) as caught:
        fetcher.fetch("https://arxiv.org/pdf/test")
    assert caught.value.kind == "pdf_page_limit"


def test_openai_key_is_not_a_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "must-not-be-used")
    with pytest.raises(RuntimeError, match="DEEPSEEK_API_KEY"):
        DeepSeekGateway()


def test_deepseek_endpoint_is_restricted() -> None:
    client = httpx.Client(base_url="https://api.openai.com", transport=httpx.MockTransport(lambda request: httpx.Response(200)))
    with pytest.raises(RuntimeError, match="api.deepseek.com"):
        DeepSeekGateway(client=client, api_key="test")
    with pytest.raises(RuntimeError, match="pinned"):
        DeepSeekGateway("unapproved-model", api_key="test")


def test_provider_usage_and_cost_use_reported_tokens() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.host == "api.deepseek.com"
        return httpx.Response(
            200,
            json={
                "model": "DeepSeek-V4.1-Flash",
                "choices": [{"message": {"content": '{"ok":true}'}}],
                "usage": {"prompt_tokens": 1000, "completion_tokens": 100, "prompt_tokens_details": {"cached_tokens": 200}},
            },
        )

    client = httpx.Client(base_url="https://api.deepseek.com", transport=httpx.MockTransport(handler))
    result = DeepSeekGateway(client=client, api_key="test").complete_json(system="safe", user="input")
    assert result.value == {"ok": True}
    assert result.usage.total_tokens == 1100
    assert result.usage.cached_input_tokens == 200
    assert result.cost_usd > 0
    assert result.response_model == "DeepSeek-V4.1-Flash"


def test_peak_pricing_is_twice_off_peak() -> None:
    usage = Usage(input_tokens=1000, output_tokens=100, cached_input_tokens=100)
    off_peak, off_tier = calculate_cost_usd(usage, at=datetime(2026, 9, 13, 12, tzinfo=timezone.utc))
    peak, peak_tier = calculate_cost_usd(usage, at=datetime(2026, 9, 16, 2, tzinfo=timezone.utc))
    assert off_tier == "off-peak"
    assert peak_tier == "peak"
    assert peak == pytest.approx(off_peak * 2)


def test_trace_attribute_allowlist_excludes_secrets_and_content() -> None:
    attributes = safe_attributes(
        {
            "task_id": "task-1",
            "model": DEFAULT_MODEL,
            "content_hash": "abc",
            "api_key": "secret",
            "authorization": "Bearer secret",
            "raw_prompt": "private prompt",
            "raw_response": "full response",
            "abstract": "full abstract",
        }
    )
    assert attributes == {"task_id": "task-1", "model": DEFAULT_MODEL, "content_hash": "abc"}


def test_model_confidence_labels_are_bounded_deterministically() -> None:
    assert _confidence("low") == 0.25
    assert _confidence("medium") == 0.5
    assert _confidence("high") == 0.8
    assert _confidence("unexpected") == 0.0
    assert _confidence(1.5) == 1.0
