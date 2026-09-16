"""Identifier normalization and bounded official-source validation."""

from __future__ import annotations

import re
from typing import Any

from .types import WorkflowFailure


DOI_PATTERN = re.compile(r"^10\.\d{4,9}/[-._;()/:A-Z0-9]+$", re.IGNORECASE)
ARXIV_PATTERN = re.compile(r"^(?:\d{4}\.\d{4,5}|[a-z-]+(?:\.[A-Z]{2})?/\d{7})(?:v\d+)?$", re.IGNORECASE)
PAPER_ID_PATTERN = re.compile(r"^[0-9a-f]{40}$", re.IGNORECASE)


def normalize_doi(value: Any) -> str | None:
    if not value:
        return None
    text = str(value).strip().strip("<>[]{}() .,;")
    text = re.sub(r"^(?:https?://(?:dx\.)?doi\.org/|doi:\s*)", "", text, flags=re.IGNORECASE)
    text = text.strip().lower()
    return text if DOI_PATTERN.fullmatch(text) else None


def normalize_arxiv_id(value: Any) -> str | None:
    if not value:
        return None
    text = str(value).strip()
    text = re.sub(r"^https?://arxiv\.org/(?:abs|pdf)/", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^arxiv:\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\.pdf$", "", text, flags=re.IGNORECASE)
    if not ARXIV_PATTERN.fullmatch(text):
        return None
    return re.sub(r"v\d+$", "", text, flags=re.IGNORECASE).lower()


def normalize_paper_id(value: Any) -> str | None:
    if not value:
        return None
    text = str(value).strip().lower()
    return text if PAPER_ID_PATTERN.fullmatch(text) else None


def normalize_identifiers(value: dict[str, Any]) -> tuple[dict[str, str | None], list[dict[str, Any]]]:
    checks: list[dict[str, Any]] = []
    functions = {
        "doi": normalize_doi,
        "arxiv_id": normalize_arxiv_id,
        "semantic_scholar_paper_id": normalize_paper_id,
    }
    normalized: dict[str, str | None] = {}
    for name, function in functions.items():
        original = value.get(name)
        result = function(original)
        normalized[name] = result
        if original:
            checks.append({"identifier": name, "status": "syntax_valid" if result else "invalid", "value": result})
    return normalized, checks


def canonical_source_present(paper: dict[str, Any], identifier: str) -> bool:
    expected = {"doi": "crossref", "arxiv_id": "arxiv", "semantic_scholar_paper_id": "semantic_scholar"}[identifier]
    return any(record.get("source") == expected for record in paper.get("source_records", []))


def validate_identifiers(
    paper: dict[str, Any], *, condition: str, source_adapters: dict[str, Any], external_checks: dict[str, dict[str, dict[str, Any]]] | None = None
) -> tuple[str, list[dict[str, Any]]]:
    identifiers, checks = normalize_identifiers(paper.get("identifiers") or {})
    paper["identifiers"] = identifiers
    verified = 0
    attempted = 0
    source_for = {
        "doi": ("crossref", "crossref"),
        "arxiv_id": ("arxiv", "arxiv"),
        "semantic_scholar_paper_id": ("semantic_scholar", "semantic_scholar"),
    }
    for name in ("doi", "arxiv_id", "semantic_scholar_paper_id"):
        value = identifiers.get(name)
        if not value:
            continue
        attempted += 1
        source, adapter_key = source_for[name]
        if canonical_source_present(paper, name):
            checks.append({"identifier": name, "status": "verified", "method": f"official_{source}_search_response", "value": value})
            verified += 1
            continue
        if external_checks is not None:
            external = external_checks.get(name, {}).get(value)
            if external and external.get("status") == "verified":
                checks.append({"identifier": name, "status": "verified", "method": external["method"], "value": value})
                verified += 1
            else:
                checks.append(
                    {
                        "identifier": name,
                        "status": "unresolved",
                        "method": "bounded_federated_lookup",
                        "failure_type": (external or {}).get("failure_type", "not_resolved_in_batch"),
                        "value": value,
                    }
                )
            continue
        if condition == "semantic-scholar-only" and name != "semantic_scholar_paper_id":
            checks.append({"identifier": name, "status": "syntax_valid_only", "method": "condition_source_boundary", "value": value})
            continue
        try:
            source_adapters[adapter_key].fetch(value)
        except WorkflowFailure as exc:
            checks.append({"identifier": name, "status": "unresolved", "method": f"official_{source}_lookup", "failure_type": exc.kind, "value": value})
        else:
            checks.append({"identifier": name, "status": "verified", "method": f"official_{source}_lookup", "value": value})
            verified += 1
    if verified:
        return "verified", checks
    return ("invalid" if attempted == 0 else "unresolved"), checks
