from __future__ import annotations

import pytest

from research_agent.deduplication import deduplicate, duplicate_decision, normalize_title
from research_agent.identifiers import (
    normalize_arxiv_id,
    normalize_doi,
    normalize_paper_id,
    validate_identifiers,
)
from research_agent.types import WorkflowFailure


def paper(title: str, *, year: int = 2024, author: str = "A Author", doi: str | None = None, arxiv: str | None = None, paper_id: str | None = None, source: str = "semantic_scholar") -> dict:
    identifier = paper_id or doi or arxiv or "source-id"
    return {
        "title": title,
        "year": year,
        "authors": [author],
        "abstract_present": True,
        "abstract_excerpt": "retrieval augmented generation experiment",
        "abstract_sha256": "hash",
        "identifiers": {"doi": doi, "arxiv_id": arxiv, "semantic_scholar_paper_id": paper_id},
        "content_urls": ["https://example.org/paper"],
        "source_records": [{"source": source, "source_url": "https://example.org/paper", "retrieved_at": "2026-09-16T00:00:00+00:00", "query": "rag", "rank": 1, "response_identifier": identifier}],
    }


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("https://doi.org/10.1145/ABC.123", "10.1145/abc.123"),
        ("doi: 10.5555/test_1", "10.5555/test_1"),
        ("not-a-doi", None),
    ],
)
def test_doi_normalization(value: str, expected: str | None) -> None:
    assert normalize_doi(value) == expected


def test_arxiv_and_paper_id_normalization() -> None:
    assert normalize_arxiv_id("https://arxiv.org/abs/2401.12345v2") == "2401.12345"
    assert normalize_arxiv_id("cs/0101001v3") == "cs/0101001"
    assert normalize_arxiv_id("bad") is None
    assert normalize_paper_id("A" * 40) == "a" * 40
    assert normalize_paper_id("short") is None


def test_deduplication_order_prefers_doi_then_merges_provenance() -> None:
    first = paper("A RAG Study", doi="10.5555/test.1", paper_id="a" * 40)
    second = paper("A RAG Study Extended", doi="https://doi.org/10.5555/TEST.1", source="crossref")
    unique, report = deduplicate([first, second])
    assert len(unique) == 1
    assert report["duplicates_removed"] == 1
    assert report["merges"][0]["method"] == "doi"
    assert {item["source"] for item in unique[0]["source_records"]} == {"semantic_scholar", "crossref"}


def test_title_fallback_requires_compatible_year_and_author() -> None:
    first = paper("Query Rewriting for Retrieval-Augmented Generation", author="A Kim")
    compatible = paper("Query rewriting for retrieval augmented generation", author="A Kim")
    incompatible = paper("Query rewriting for retrieval augmented generation", year=2020, author="B Lee")
    assert duplicate_decision(first, compatible)["duplicate"] is True
    decision = duplicate_decision(first, incompatible)
    assert decision["duplicate"] is False
    assert "year_conflict" in decision["evidence"]


def test_similar_but_distinct_titles_are_not_forced_to_merge() -> None:
    first = paper("Reranking in Medical RAG", author="A Kim")
    second = paper("Reranking in Legal RAG", author="B Lee")
    unique, report = deduplicate([first, second])
    assert len(unique) == 2
    assert report["duplicates_removed"] == 0
    assert normalize_title(first["title"]) != normalize_title(second["title"])


class FailingAdapter:
    def fetch(self, identifier: str):
        raise WorkflowFailure("unresolved_identifier", "not found")


def test_identifier_validation_failure_is_preserved() -> None:
    value = paper("Unresolved DOI", doi="10.5555/missing", paper_id=None, source="semantic_scholar")
    value["source_records"][0]["source"] = "semantic_scholar"
    status, checks = validate_identifiers(
        value,
        condition="federated-verified",
        source_adapters={"crossref": FailingAdapter(), "arxiv": FailingAdapter(), "semantic_scholar": FailingAdapter()},
    )
    assert status == "unresolved"
    assert any(item.get("failure_type") == "unresolved_identifier" for item in checks)
