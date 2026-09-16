"""Official scholarly metadata API adapters and parsers."""

from __future__ import annotations

import hashlib
import html
import json
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Any
from urllib.parse import quote

from .http import ResilientClient
from .paths import MAX_ABSTRACT_CACHE_CHARS
from .types import WorkflowFailure


SEMANTIC_SEARCH_URL = "https://api.semanticscholar.org/graph/v1/paper/search"
SEMANTIC_PAPER_URL = "https://api.semanticscholar.org/graph/v1/paper"
CROSSREF_URL = "https://api.crossref.org/works"
ARXIV_URL = "https://export.arxiv.org/api/query"
SEMANTIC_FIELDS = "paperId,title,abstract,year,authors,externalIds,url,openAccessPdf,publicationTypes,venue"
ARXIV_NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "arxiv": "http://arxiv.org/schemas/atom",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _text(value: Any) -> str | None:
    if value is None:
        return None
    cleaned = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", str(value)))).strip()
    return cleaned or None


def _abstract_fields(value: Any) -> dict[str, Any]:
    abstract = _text(value)
    if not abstract:
        return {"abstract_present": False, "abstract_sha256": None, "abstract_excerpt": None}
    return {
        "abstract_present": True,
        "abstract_sha256": hashlib.sha256(abstract.encode()).hexdigest(),
        "abstract_excerpt": abstract[:MAX_ABSTRACT_CACHE_CHARS],
    }


def _source_record(
    *, source: str, source_url: str, query: str, query_origin: str, rank: int, identifier: str, filters: dict[str, Any]
) -> dict[str, Any]:
    return {
        "source": source,
        "source_url": source_url,
        "retrieved_at": utc_now(),
        "query": query,
        "query_origin": query_origin,
        "rank": rank,
        "filters": filters,
        "response_identifier": identifier,
    }


def parse_semantic_scholar(
    payload: dict[str, Any], *, query: str, query_origin: str, start_rank: int = 1, filters: dict[str, Any] | None = None
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for offset, item in enumerate(payload.get("data") or []):
        paper_id = str(item.get("paperId") or "").strip()
        title = _text(item.get("title"))
        if not paper_id or not title:
            continue
        external = item.get("externalIds") or {}
        pdf = item.get("openAccessPdf") or {}
        paper_url = str(item.get("url") or f"https://www.semanticscholar.org/paper/{paper_id}")
        record = {
            "title": title,
            "year": item.get("year"),
            "authors": [str(author.get("name")) for author in item.get("authors") or [] if author.get("name")],
            "venue": _text(item.get("venue")),
            "publication_type": ",".join(item.get("publicationTypes") or []) or None,
            "language": "en",
            **_abstract_fields(item.get("abstract")),
            "identifiers": {
                "doi": external.get("DOI"),
                "arxiv_id": external.get("ArXiv"),
                "semantic_scholar_paper_id": paper_id,
            },
            "content_urls": [value for value in [pdf.get("url"), paper_url] if value],
            "source_records": [
                _source_record(
                    source="semantic_scholar",
                    source_url=paper_url,
                    query=query,
                    query_origin=query_origin,
                    rank=start_rank + offset,
                    identifier=paper_id,
                    filters=filters or {},
                )
            ],
        }
        records.append(record)
    return records


def _crossref_year(item: dict[str, Any]) -> int | None:
    for key in ("published-print", "published-online", "published", "issued", "created"):
        parts = (item.get(key) or {}).get("date-parts") or []
        if parts and parts[0]:
            try:
                return int(parts[0][0])
            except (TypeError, ValueError):
                pass
    return None


def parse_crossref(
    payload: dict[str, Any], *, query: str, query_origin: str, start_rank: int = 1, filters: dict[str, Any] | None = None
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for offset, item in enumerate(((payload.get("message") or {}).get("items") or [])):
        doi = str(item.get("DOI") or "").strip()
        title = _text((item.get("title") or [None])[0])
        if not doi or not title:
            continue
        authors = []
        for author in item.get("author") or []:
            name = " ".join(value for value in [author.get("given"), author.get("family")] if value)
            if name:
                authors.append(name)
        links = [link.get("URL") for link in item.get("link") or [] if link.get("URL")]
        source_url = str(item.get("URL") or f"https://doi.org/{doi}")
        records.append(
            {
                "title": title,
                "year": _crossref_year(item),
                "authors": authors,
                "venue": _text((item.get("container-title") or [None])[0]),
                "publication_type": item.get("type"),
                "language": item.get("language") or "en",
                **_abstract_fields(item.get("abstract")),
                "identifiers": {"doi": doi, "arxiv_id": None, "semantic_scholar_paper_id": None},
                "content_urls": [*links, source_url],
                "source_records": [
                    _source_record(
                        source="crossref",
                        source_url=source_url,
                        query=query,
                        query_origin=query_origin,
                        rank=start_rank + offset,
                        identifier=doi,
                        filters=filters or {},
                    )
                ],
            }
        )
    return records


def parse_arxiv(
    xml_text: str, *, query: str, query_origin: str, start_rank: int = 1, filters: dict[str, Any] | None = None
) -> list[dict[str, Any]]:
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        raise WorkflowFailure("parsing", "arXiv returned invalid Atom XML") from exc
    records: list[dict[str, Any]] = []
    for offset, entry in enumerate(root.findall("atom:entry", ARXIV_NS)):
        entry_url = _text(entry.findtext("atom:id", namespaces=ARXIV_NS))
        title = _text(entry.findtext("atom:title", namespaces=ARXIV_NS))
        if not entry_url or not title:
            continue
        arxiv_id = entry_url.rstrip("/").split("/")[-1].split("v")[0]
        published = _text(entry.findtext("atom:published", namespaces=ARXIV_NS))
        year = int(published[:4]) if published and published[:4].isdigit() else None
        authors = [
            name
            for author in entry.findall("atom:author", ARXIV_NS)
            if (name := _text(author.findtext("atom:name", namespaces=ARXIV_NS)))
        ]
        doi = _text(entry.findtext("arxiv:doi", namespaces=ARXIV_NS))
        links = [link.attrib.get("href") for link in entry.findall("atom:link", ARXIV_NS) if link.attrib.get("href")]
        records.append(
            {
                "title": title,
                "year": year,
                "authors": authors,
                "venue": _text(entry.findtext("arxiv:journal_ref", namespaces=ARXIV_NS)),
                "publication_type": "preprint",
                "language": "en",
                **_abstract_fields(entry.findtext("atom:summary", namespaces=ARXIV_NS)),
                "identifiers": {"doi": doi, "arxiv_id": arxiv_id, "semantic_scholar_paper_id": None},
                "content_urls": links or [entry_url],
                "source_records": [
                    _source_record(
                        source="arxiv",
                        source_url=entry_url,
                        query=query,
                        query_origin=query_origin,
                        rank=start_rank + offset,
                        identifier=arxiv_id,
                        filters=filters or {},
                    )
                ],
            }
        )
    return records


class SemanticScholarAdapter:
    source = "semantic_scholar"

    def __init__(self, http: ResilientClient, *, page_size: int = 100) -> None:
        self.http = http
        self.page_size = page_size

    def search(self, query: str, *, query_origin: str, limit: int, from_year: int, to_year: int) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        offset = 0
        filters = {"year": f"{from_year}-{to_year}", "limit": limit, "language": "en"}
        while len(results) < limit:
            page_limit = min(self.page_size, limit - len(results))
            response = self.http.request(
                self.source,
                "GET",
                SEMANTIC_SEARCH_URL,
                params={"query": query, "year": filters["year"], "offset": offset, "limit": page_limit, "fields": SEMANTIC_FIELDS},
            )
            try:
                payload = response.json()
            except json.JSONDecodeError as exc:
                raise WorkflowFailure("parsing", "Semantic Scholar returned invalid JSON") from exc
            page = parse_semantic_scholar(payload, query=query, query_origin=query_origin, start_rank=offset + 1, filters=filters)
            results.extend(page)
            if len(page) < page_limit:
                break
            offset += page_limit
        return results[:limit]

    def fetch(self, paper_id: str) -> dict[str, Any]:
        response = self.http.request(self.source, "GET", f"{SEMANTIC_PAPER_URL}/{quote(paper_id, safe='')}", params={"fields": SEMANTIC_FIELDS})
        try:
            payload = response.json()
        except json.JSONDecodeError as exc:
            raise WorkflowFailure("parsing", "Semantic Scholar returned invalid paper JSON") from exc
        values = parse_semantic_scholar({"data": [payload]}, query="identifier-fetch", query_origin="validation")
        if not values:
            raise WorkflowFailure("unresolved_identifier", "Semantic Scholar paperId did not resolve")
        values[0]["abstract_text"] = _text(payload.get("abstract"))
        return values[0]


class CrossrefAdapter:
    source = "crossref"

    def __init__(self, http: ResilientClient, *, page_size: int = 100) -> None:
        self.http = http
        self.page_size = page_size

    def search(self, query: str, *, query_origin: str, limit: int, from_year: int, to_year: int) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        offset = 0
        date_filter = f"from-pub-date:{from_year}-01-01,until-pub-date:{to_year}-12-31"
        filters = {"date": date_filter, "limit": limit, "language": "en"}
        while len(results) < limit:
            page_limit = min(self.page_size, limit - len(results))
            response = self.http.request(
                self.source,
                "GET",
                CROSSREF_URL,
                params={"query.bibliographic": query, "filter": date_filter, "rows": page_limit, "offset": offset},
            )
            try:
                payload = response.json()
            except json.JSONDecodeError as exc:
                raise WorkflowFailure("parsing", "Crossref returned invalid JSON") from exc
            page = parse_crossref(payload, query=query, query_origin=query_origin, start_rank=offset + 1, filters=filters)
            results.extend(page)
            if len(page) < page_limit:
                break
            offset += page_limit
        return results[:limit]

    def fetch(self, doi: str) -> dict[str, Any]:
        response = self.http.request(self.source, "GET", f"{CROSSREF_URL}/{quote(doi, safe='')}")
        try:
            item = response.json().get("message") or {}
        except json.JSONDecodeError as exc:
            raise WorkflowFailure("parsing", "Crossref returned invalid work JSON") from exc
        values = parse_crossref({"message": {"items": [item]}}, query="identifier-fetch", query_origin="validation")
        if not values:
            raise WorkflowFailure("unresolved_identifier", "DOI did not resolve in Crossref")
        values[0]["abstract_text"] = _text(item.get("abstract"))
        return values[0]


class ArxivAdapter:
    source = "arxiv"

    def __init__(self, http: ResilientClient, *, page_size: int = 100) -> None:
        self.http = http
        self.page_size = page_size

    def search(self, query: str, *, query_origin: str, limit: int, from_year: int, to_year: int) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        start = 0
        filters = {"from_year": from_year, "to_year": to_year, "limit": limit, "language": "en"}
        while len(results) < limit:
            page_limit = min(self.page_size, limit - len(results))
            response = self.http.request(
                self.source,
                "GET",
                ARXIV_URL,
                params={"search_query": f'all:"{query}"', "start": start, "max_results": page_limit, "sortBy": "relevance", "sortOrder": "descending"},
                headers={"Accept": "application/atom+xml"},
            )
            page = parse_arxiv(response.text, query=query, query_origin=query_origin, start_rank=start + 1, filters=filters)
            page = [item for item in page if isinstance(item.get("year"), int) and from_year <= item["year"] <= to_year]
            results.extend(page)
            if len(page) < page_limit:
                break
            start += page_limit
        return results[:limit]

    def fetch(self, arxiv_id: str) -> dict[str, Any]:
        response = self.http.request(self.source, "GET", ARXIV_URL, params={"id_list": arxiv_id, "max_results": 1}, headers={"Accept": "application/atom+xml"})
        values = parse_arxiv(response.text, query="identifier-fetch", query_origin="validation")
        if not values:
            raise WorkflowFailure("unresolved_identifier", "arXiv ID did not resolve")
        root = ET.fromstring(response.text)
        entry = root.find("atom:entry", ARXIV_NS)
        values[0]["abstract_text"] = _text(entry.findtext("atom:summary", namespaces=ARXIV_NS)) if entry is not None else None
        return values[0]

    def fetch_many(self, arxiv_ids: list[str]) -> dict[str, dict[str, Any]]:
        if not arxiv_ids:
            return {}
        response = self.http.request(
            self.source,
            "GET",
            ARXIV_URL,
            params={"id_list": ",".join(arxiv_ids), "max_results": len(arxiv_ids)},
            headers={"Accept": "application/atom+xml"},
        )
        values = parse_arxiv(response.text, query="identifier-batch-fetch", query_origin="validation")
        return {
            str(value["identifiers"]["arxiv_id"]): value
            for value in values
            if value.get("identifiers", {}).get("arxiv_id")
        }


def adapters(http: ResilientClient) -> dict[str, Any]:
    return {
        "semantic_scholar": SemanticScholarAdapter(http),
        "crossref": CrossrefAdapter(http),
        "arxiv": ArxivAdapter(http),
    }
