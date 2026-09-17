"""Stable JSON/JSONL/CSV/Markdown/BibTeX artifact rendering."""

from __future__ import annotations

import csv
import json
import math
import re
from pathlib import Path
from typing import Any


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, values: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(value, ensure_ascii=False, sort_keys=True) + "\n" for value in values), encoding="utf-8")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def percentile(values: list[float], fraction: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    rank = max(0, math.ceil(fraction * len(ordered)) - 1)
    return float(ordered[rank])


def write_claim_csv(path: Path, claims: list[dict[str, Any]]) -> None:
    fields = [
        "claim_id", "claim", "claim_type", "paper_record_id", "paper_title", "doi", "arxiv_id",
        "semantic_scholar_paper_id", "source_url", "evidence_location", "evidence_type", "quote", "paraphrase",
        "verified", "extraction_uncertainty",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        for claim in claims:
            identifiers = claim.get("identifiers") or {}
            row = {key: claim.get(key) for key in fields}
            for key in ("doi", "arxiv_id", "semantic_scholar_paper_id"):
                row[key] = identifiers.get(key)
            writer.writerow(row)


def _bib_key(paper: dict[str, Any], index: int) -> str:
    authors = paper.get("authors") or []
    family = re.sub(r"[^A-Za-z0-9]", "", authors[0].split()[-1]) if authors else "Paper"
    return f"{family}{paper.get('year') or 'nd'}RAG{index}"


def write_bibtex(path: Path, papers: list[dict[str, Any]]) -> None:
    entries = []
    for index, paper in enumerate(papers, 1):
        identifiers = paper.get("identifiers") or {}
        fields = {
            "title": "{" + str(paper.get("title") or "Untitled").replace("{", "").replace("}", "") + "}",
            "author": " and ".join(paper.get("authors") or ["Unknown"]),
            "year": str(paper.get("year") or "unknown"),
            "url": (paper.get("source_records") or [{}])[0].get("source_url", ""),
        }
        if identifiers.get("doi"):
            fields["doi"] = identifiers["doi"]
        if identifiers.get("arxiv_id"):
            fields["eprint"] = identifiers["arxiv_id"]
            fields["archivePrefix"] = "arXiv"
        body = ",\n".join(f"  {key} = {{{value}}}" for key, value in fields.items() if value)
        entries.append(f"@misc{{{_bib_key(paper, index)},\n{body}\n}}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n\n".join(entries) + ("\n" if entries else ""), encoding="utf-8")


def render_report(report: dict[str, Any]) -> str:
    search = report.get("search") or {}
    usage = report.get("usage") or {}
    lines = [
        "# Verified RAG research report",
        "",
        f"- Condition: `{report.get('condition')}`",
        f"- Question: {report.get('question')}",
        f"- Search started: {search.get('started_at', 'unknown')}",
        f"- Verified papers: {len(report.get('verified_papers') or [])}",
        f"- Evidence claims: {len(report.get('claims') or [])}",
        f"- Model status: `{usage.get('model_status', 'unknown')}`",
        "",
        "## Search and verification",
        "",
        f"Sources: {', '.join(search.get('sources') or [])}. Requests: {search.get('requests_by_source', {})}. "
        f"Deduplicated: {search.get('duplicates_removed', 0)}. Identifier failures: {search.get('identifier_failures', 0)}.",
        "",
        "## Claim–evidence",
        "",
        "| Claim ID | Paper | Claim | Locator |",
        "| --- | --- | --- | --- |",
    ]
    for claim in report.get("claims") or []:
        compact = str(claim.get("claim") or "").replace("|", "\\|")
        title = str(claim.get("paper_title") or "").replace("|", "\\|")
        lines.append(f"| {claim.get('claim_id')} | {title} | {compact} | {claim.get('evidence_location')} |")
    lines.extend(["", "## Method, results, limitations, and trade-offs", ""])
    synthesis = report.get("synthesis") or {}
    sections = synthesis.get("sections") if isinstance(synthesis, dict) else None
    if sections:
        for section in sections:
            lines.extend(
                [
                    f"### {section.get('technique', 'Synthesis')}",
                    "",
                    str(section.get("findings") or "No supported finding was produced."),
                    "",
                    f"Supporting claims: {', '.join(section.get('supporting_claim_ids') or [])}",
                    "",
                    f"Trade-offs: {section.get('tradeoffs') or 'Not established.'}",
                    "",
                ]
            )
    else:
        lines.extend(["Structured synthesis was not executed or produced no supported section.", ""])
    lines.extend(["## Agent hypotheses (not paper conclusions)", ""])
    for item in report.get("hypotheses") or []:
        lines.extend(
            [
                f"- **{item.get('hypothesis_id')}**: {item.get('hypothesis')}",
                f"  - Derived from: {', '.join(item.get('derived_from_claim_ids') or [])}",
                f"  - Falsification test: {item.get('falsification_test')}",
                f"  - Confidence: {item.get('confidence')}",
            ]
        )
    if not report.get("hypotheses"):
        lines.append("- None generated.")
    lines.extend(["", "## Representative failures", ""])
    for failure in (report.get("failures") or [])[:12]:
        lines.append(f"- `{failure.get('failure_type', 'unknown')}`: {failure.get('summary', failure.get('source', 'preserved failure'))}")
    if not report.get("failures"):
        lines.append("- None observed.")
    lines.extend(["", "## Limitations", ""])
    lines.extend(f"- {value}" for value in report.get("limitations") or [])
    lines.extend(
        [
            "",
            "## Usage and calculated cost",
            "",
            f"Provider-reported usage: `{usage.get('tokens', {})}`. Calculated cost: `${float(usage.get('calculated_cost_usd') or 0):.8f}`. "
            "This is a calculation from published rates, not an invoice.",
            "",
        ]
    )
    return "\n".join(lines)


def render_comparison(first: dict[str, Any], second: dict[str, Any]) -> str:
    def cell(value: Any) -> str:
        return "pending" if value is None else str(value)

    rows = [
        ("verified papers", first.get("verified_papers"), second.get("verified_papers")),
        ("duplicates removed", first.get("duplicates_removed"), second.get("duplicates_removed")),
        ("identifier errors", first.get("identifier_failures"), second.get("identifier_failures")),
        ("evidence coverage", first.get("evidence_coverage"), second.get("evidence_coverage")),
        ("locator coverage", first.get("locator_coverage"), second.get("locator_coverage")),
        ("latency p50 ms", first.get("latency_p50_ms"), second.get("latency_p50_ms")),
        ("latency p95 ms", first.get("latency_p95_ms"), second.get("latency_p95_ms")),
        ("API requests", first.get("api_requests"), second.get("api_requests")),
        ("model tokens", first.get("total_tokens"), second.get("total_tokens")),
        ("calculated cost USD", first.get("calculated_cost_usd"), second.get("calculated_cost_usd")),
        ("task success", first.get("task_success"), second.get("task_success")),
    ]
    lines = [
        "# Research search-condition comparison",
        "",
        "| Metric | semantic-scholar-only | federated-verified |",
        "| --- | ---: | ---: |",
    ]
    lines.extend(f"| {name} | {cell(left)} | {cell(right)} |" for name, left, right in rows)
    lines.extend(
        [
            "",
            "The costs above are calculations from provider-reported tokens and the official rate at execution time, not invoice amounts.",
            "Failures and unexecuted model work remain visible rather than being counted as successes.",
            "",
        ]
    )
    return "\n".join(lines)
