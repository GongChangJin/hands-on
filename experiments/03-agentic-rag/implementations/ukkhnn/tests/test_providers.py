from agentic_rag.providers import PROVIDERS, parse_json_object


def test_only_allowed_provider_endpoints_are_configured() -> None:
    assert set(PROVIDERS) == {"upstage", "deepseek"}
    assert PROVIDERS["upstage"].base_url == "https://api.upstage.ai/v1"
    assert PROVIDERS["deepseek"].base_url == "https://api.deepseek.com"
    assert all("api.openai.com" not in spec.base_url for spec in PROVIDERS.values())


def test_json_parser_accepts_fenced_provider_output() -> None:
    assert parse_json_object('```json\n{"action":"search"}\n```') == {"action": "search"}
