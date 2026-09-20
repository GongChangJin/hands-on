from __future__ import annotations

import json

import httpx

from research_agent.adapters import (
    ArxivAdapter,
    CrossrefAdapter,
    SemanticScholarAdapter,
    parse_arxiv,
    parse_crossref,
    parse_semantic_scholar,
)
from research_agent.http import ResilientClient


SEMANTIC_ITEM = {
    "paperId": "a" * 40,
    "title": "Corrective Retrieval Augmented Generation",
    "abstract": "We evaluate corrective retrieval and faithfulness.",
    "year": 2024,
    "authors": [{"name": "A. Researcher"}],
    "externalIds": {"DOI": "10.5555/test.1", "ArXiv": "2401.00001"},
    "url": "https://www.semanticscholar.org/paper/" + "a" * 40,
    "openAccessPdf": {"url": "https://arxiv.org/pdf/2401.00001"},
    "publicationTypes": ["JournalArticle"],
    "venue": "Test Venue",
}


def test_semantic_scholar_parser_preserves_provenance_without_raw_payload() -> None:
    values = parse_semantic_scholar(
        {"data": [SEMANTIC_ITEM]},
        query="corrective retrieval",
        query_origin="deterministic_seed",
        filters={"year": "2020-2026"},
    )
    assert len(values) == 1
    paper = values[0]
    assert paper["identifiers"]["doi"] == "10.5555/test.1"
    assert paper["abstract_present"] is True
    assert paper["source_records"][0]["rank"] == 1
    assert paper["source_records"][0]["query_origin"] == "deterministic_seed"
    assert "raw_payload" not in json.dumps(paper)


def test_crossref_parser_handles_author_date_and_abstract() -> None:
    payload = {
        "message": {
            "items": [
                {
                    "DOI": "10.5555/Test.2",
                    "title": ["Reranking for RAG"],
                    "abstract": "<jats:p>Direct experiment.</jats:p>",
                    "author": [{"given": "B", "family": "Author"}],
                    "published": {"date-parts": [[2023, 1, 2]]},
                    "URL": "https://doi.org/10.5555/Test.2",
                    "type": "journal-article",
                    "container-title": ["Test Journal"],
                }
            ]
        }
    }
    paper = parse_crossref(payload, query="reranking", query_origin="deterministic_seed")[0]
    assert paper["year"] == 2023
    assert paper["authors"] == ["B Author"]
    assert paper["abstract_excerpt"] == "Direct experiment."


def test_arxiv_parser_handles_atom_and_identifier() -> None:
    xml = """<?xml version="1.0"?>
    <feed xmlns="http://www.w3.org/2005/Atom" xmlns:arxiv="http://arxiv.org/schemas/atom">
      <entry><id>https://arxiv.org/abs/2401.00003v2</id><updated>2024-01-03T00:00:00Z</updated>
      <published>2024-01-02T00:00:00Z</published><title>Self-RAG Test</title>
      <summary>Self reflective retrieval experiment.</summary><author><name>C Author</name></author>
      <arxiv:doi>10.5555/test.3</arxiv:doi><link href="https://arxiv.org/pdf/2401.00003" type="application/pdf"/></entry>
    </feed>"""
    paper = parse_arxiv(xml, query="self rag", query_origin="deterministic_seed")[0]
    assert paper["identifiers"]["arxiv_id"] == "2401.00003"
    assert paper["identifiers"]["doi"] == "10.5555/test.3"
    assert paper["authors"] == ["C Author"]


def test_pagination_and_query_transform_are_bounded() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        params = request.url.params
        offset = int(params.get("offset", 0))
        item = dict(SEMANTIC_ITEM, paperId=("a" if offset == 0 else "b") * 40)
        return httpx.Response(200, json={"data": [item]})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    adapter = SemanticScholarAdapter(ResilientClient(client=client), page_size=1)
    values = adapter.search("query rewrite", query_origin="deterministic_seed", limit=2, from_year=2020, to_year=2026)
    assert len(values) == 2
    assert len(requests) == 2
    assert requests[0].url.params["year"] == "2020-2026"
    assert requests[1].url.params["offset"] == "1"


def test_retry_is_limited_and_exponential() -> None:
    attempts = 0
    sleeps: list[float] = []

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            return httpx.Response(429)
        return httpx.Response(200, json={"ok": True})

    resilient = ResilientClient(
        client=httpx.Client(transport=httpx.MockTransport(handler)),
        maximum_attempts=3,
        backoff_seconds=0.1,
        sleep=sleeps.append,
    )
    response = resilient.request("semantic_scholar", "GET", "https://example.test")
    assert response.status_code == 200
    assert attempts == 3
    assert sleeps == [0.1, 0.2]


def test_source_requests_are_rate_limited_before_separate_calls() -> None:
    sleeps: list[float] = []
    resilient = ResilientClient(
        client=httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(200))),
        sleep=sleeps.append,
        minimum_intervals={"semantic_scholar": 1.0},
    )
    resilient.request("semantic_scholar", "GET", "https://example.test/one")
    resilient.request("semantic_scholar", "GET", "https://example.test/two")
    assert len(sleeps) == 1
    assert 0.9 <= sleeps[0] <= 1.0


def test_all_adapters_expose_pagination_configuration() -> None:
    resilient = ResilientClient(client=httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(500))))
    assert SemanticScholarAdapter(resilient, page_size=7).page_size == 7
    assert CrossrefAdapter(resilient, page_size=8).page_size == 8
    assert ArxivAdapter(resilient, page_size=9).page_size == 9
