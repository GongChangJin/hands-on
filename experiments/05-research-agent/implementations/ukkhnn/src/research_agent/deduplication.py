"""Conservative DOI → arXiv → paperId → title deduplication."""

from __future__ import annotations

import re
import unicodedata
from copy import deepcopy
from difflib import SequenceMatcher
from typing import Any

from .identifiers import normalize_identifiers


def normalize_title(value: str) -> str:
    text = unicodedata.normalize("NFKD", value).lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return " ".join(text.split())


def _family_names(authors: list[str]) -> set[str]:
    return {normalize_title(author).split()[-1] for author in authors if normalize_title(author)}


def _title_match(first: dict[str, Any], second: dict[str, Any], *, threshold: float) -> tuple[bool, float, list[str]]:
    first_title = normalize_title(str(first.get("title") or ""))
    second_title = normalize_title(str(second.get("title") or ""))
    similarity = SequenceMatcher(None, first_title, second_title).ratio()
    evidence = [f"normalized_title_similarity={similarity:.4f}"]
    if similarity < threshold:
        return False, similarity, evidence
    first_year, second_year = first.get("year"), second.get("year")
    if isinstance(first_year, int) and isinstance(second_year, int) and abs(first_year - second_year) > 1:
        evidence.append("year_conflict")
        return False, similarity, evidence
    first_authors, second_authors = _family_names(first.get("authors") or []), _family_names(second.get("authors") or [])
    if first_authors and second_authors and not first_authors.intersection(second_authors):
        evidence.append("author_conflict")
        return False, similarity, evidence
    evidence.extend(["compatible_year", "compatible_authors"])
    return True, similarity, evidence


def duplicate_decision(
    first: dict[str, Any], second: dict[str, Any], *, title_threshold: float = 0.97
) -> dict[str, Any]:
    first_ids, _ = normalize_identifiers(first.get("identifiers") or {})
    second_ids, _ = normalize_identifiers(second.get("identifiers") or {})
    for name, confidence in (("doi", 1.0), ("arxiv_id", 0.995), ("semantic_scholar_paper_id", 0.99)):
        if first_ids.get(name) and first_ids[name] == second_ids.get(name):
            return {"duplicate": True, "method": name, "confidence": confidence, "evidence": [f"equal_{name}"]}
    matched, similarity, evidence = _title_match(first, second, threshold=title_threshold)
    return {
        "duplicate": matched,
        "method": "normalized_title" if matched else "none",
        "confidence": similarity if matched else 0.0,
        "evidence": evidence,
    }


def _merge(base: dict[str, Any], incoming: dict[str, Any], decision: dict[str, Any]) -> None:
    base_ids, _ = normalize_identifiers(base.get("identifiers") or {})
    incoming_ids, _ = normalize_identifiers(incoming.get("identifiers") or {})
    for key in base_ids:
        if not base_ids.get(key) and incoming_ids.get(key):
            base_ids[key] = incoming_ids[key]
    base["identifiers"] = base_ids
    seen_sources = {(item.get("source"), item.get("response_identifier")) for item in base.get("source_records", [])}
    for source in incoming.get("source_records", []):
        marker = (source.get("source"), source.get("response_identifier"))
        if marker not in seen_sources:
            base.setdefault("source_records", []).append(source)
            seen_sources.add(marker)
    for key in ("content_urls", "authors"):
        base[key] = list(dict.fromkeys([*(base.get(key) or []), *(incoming.get(key) or [])]))
    if not base.get("abstract_present") and incoming.get("abstract_present"):
        for key in ("abstract_present", "abstract_sha256", "abstract_excerpt"):
            base[key] = incoming.get(key)
    base.setdefault("deduplication", {"merged_records": [], "unresolved_candidates": []})["merged_records"].append(
        {
            "method": decision["method"],
            "confidence": decision["confidence"],
            "evidence": decision["evidence"],
            "incoming_sources": [item.get("source") for item in incoming.get("source_records", [])],
        }
    )


def deduplicate(records: list[dict[str, Any]], *, title_threshold: float = 0.97) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    unique: list[dict[str, Any]] = []
    merges: list[dict[str, Any]] = []
    possible_duplicates: list[dict[str, Any]] = []
    for incoming in records:
        candidate = deepcopy(incoming)
        candidate["normalized_title"] = normalize_title(str(candidate.get("title") or ""))
        matched = False
        for index, existing in enumerate(unique):
            decision = duplicate_decision(existing, candidate, title_threshold=title_threshold)
            if decision["duplicate"]:
                _merge(existing, candidate, decision)
                merges.append({"kept_index": index, "incoming_title": candidate.get("title"), **decision})
                matched = True
                break
            similarity_evidence = decision.get("evidence") or []
            if any(item.startswith("normalized_title_similarity=0.9") for item in similarity_evidence):
                possible_duplicates.append(
                    {"first_title": existing.get("title"), "second_title": candidate.get("title"), "status": "unresolved_not_merged", **decision}
                )
        if not matched:
            candidate.setdefault("deduplication", {"merged_records": [], "unresolved_candidates": []})
            unique.append(candidate)
    report = {
        "input_records": len(records),
        "unique_records": len(unique),
        "duplicates_removed": len(records) - len(unique),
        "merges": merges,
        "unresolved_duplicates": possible_duplicates,
        "order": ["doi", "arxiv_id", "semantic_scholar_paper_id", "normalized_title"],
        "title_threshold": title_threshold,
    }
    return unique, report
