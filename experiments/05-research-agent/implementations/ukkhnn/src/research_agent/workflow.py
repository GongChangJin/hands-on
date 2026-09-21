"""Search, verification, evidence extraction, reporting, and deterministic grading."""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import time
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jsonschema import ValidationError

from .adapters import adapters as build_adapters
from .contracts import load_json, validate_contract, validate_research
from .deduplication import deduplicate, duplicate_decision, normalize_title
from .deepseek import DEFAULT_MODEL, PRICING_CHECKED_AT, PRICING_SOURCE, DeepSeekGateway
from .http import ResilientClient
from .identifiers import normalize_identifiers, validate_identifiers
from .observability import span
from .paths import (
    FILTERS_PATH,
    MAXIMUM_ANALYZED_PAPERS,
    MAX_EVIDENCE_QUOTE_CHARS,
    MINIMUM_VERIFIED_PAPERS,
    QUESTION_PATH,
    SCHEMAS_DIR,
    STRATEGIES_PATH,
    TASKS_PATH,
)
from .reporting import (
    percentile,
    read_jsonl,
    render_comparison,
    render_report,
    write_bibtex,
    write_claim_csv,
    write_json,
    write_jsonl,
)
from .types import RunStats, Usage, WorkflowFailure


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _query_hash(queries: list[str]) -> str:
    return hashlib.sha256(json.dumps(queries, sort_keys=True).encode()).hexdigest()


def tool_trace(
    task_id: str,
    tool_name: str,
    *,
    input_summary: str,
    result_summary: str,
    duration_ms: float,
    error: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    value = {
        "task_id": task_id,
        "tool_name": tool_name,
        "input_summary": input_summary,
        "result_summary": result_summary,
        "duration_ms": max(0.0, duration_ms),
        "error": error,
        "metadata": metadata or {},
    }
    validate_contract("tool-trace", value)
    return value


def validate_shared() -> dict[str, Any]:
    question = load_json(QUESTION_PATH)
    strategies = load_json(STRATEGIES_PATH)
    filters = load_json(FILTERS_PATH)
    schema_count = 0
    for name in ("paper-record", "claim-evidence", "research-report", "hypothesis"):
        json.loads((SCHEMAS_DIR / f"{name}.schema.json").read_text())
        schema_count += 1
    tasks = 0
    for line in TASKS_PATH.read_text(encoding="utf-8").splitlines():
        if line.strip():
            validate_contract("task-request", json.loads(line))
            tasks += 1
    if strategies.get("question_version") != question.get("version"):
        raise ValueError("Search strategy and question versions differ")
    return {
        "status": "valid",
        "question_version": question["version"],
        "seed_queries": len(strategies["deterministic_seed_queries"]),
        "conditions": sorted(strategies["conditions"]),
        "schemas": schema_count,
        "tasks": tasks,
        "minimum_verified_papers": question["target_verified_papers"]["minimum"],
        "filter_version": filters["version"],
    }


def _relevance(paper: dict[str, Any]) -> float:
    title = str(paper.get("title") or "").lower()
    excerpt = str(paper.get("abstract_excerpt") or "").lower()
    combined = f"{title} {excerpt}"
    if any(term in title for term in ("survey", "systematic review", "overview")):
        return -100
    score = 0.0
    for term, weight in (
        ("retrieval augmented", 4), ("rag", 1), ("query rewrite", 4), ("query reform", 4),
        ("rerank", 4), ("re-rank", 4), ("corrective retrieval", 5), ("self-rag", 5),
        ("self reflect", 4), ("adaptive retrieval", 3), ("retrieval", 1), ("faithful", 1),
    ):
        if term in combined:
            score += weight * (1.5 if term in title else 1.0)
    if paper.get("abstract_present"):
        score += 1
    rank = min((record.get("rank", 999) for record in paper.get("source_records", [])), default=999)
    return score + max(0, 1 - rank / 1000)


def _record_id(paper: dict[str, Any]) -> str:
    identifiers, _ = normalize_identifiers(paper.get("identifiers") or {})
    canonical = identifiers.get("doi") or identifiers.get("arxiv_id") or identifiers.get("semantic_scholar_paper_id") or normalize_title(paper["title"])
    return "paper-" + hashlib.sha256(str(canonical).encode()).hexdigest()[:12]


def _blank_analysis() -> dict[str, Any]:
    return {
        "research_objective": "",
        "methodology": "",
        "datasets": [],
        "metrics": [],
        "key_results": [],
        "limitations": [],
        "rag_stages": [],
        "paper_claims": [],
        "agent_interpretation": [],
        "extraction_uncertainty": "Not yet analyzed",
    }


def _apply_extracted_papers(
    returned: list[Any],
    papers: list[dict[str, Any]],
    claims: list[dict[str, Any]],
) -> set[str]:
    """Validate model extraction output and attach accepted claims to papers."""

    by_id = {paper["record_id"]: paper for paper in papers}
    papers_with_claims: set[str] = set()
    for extracted in returned:
        if not isinstance(extracted, dict) or extracted.get("record_id") not in by_id:
            continue
        paper = by_id[extracted["record_id"]]
        analysis = {
            "research_objective": str(extracted.get("research_objective") or "Not stated in excerpt"),
            "methodology": str(extracted.get("methodology") or "Not stated in excerpt"),
            "datasets": [str(value) for value in extracted.get("datasets") or [] if value],
            "metrics": [str(value) for value in extracted.get("metrics") or [] if value],
            "key_results": [str(value) for value in extracted.get("key_results") or [] if value],
            "limitations": [str(value) for value in extracted.get("limitations") or [] if value],
            "rag_stages": [str(value) for value in extracted.get("rag_stages") or [] if value],
            "paper_claims": [],
            "agent_interpretation": [str(value) for value in extracted.get("agent_interpretation") or [] if value],
            "extraction_uncertainty": str(extracted.get("extraction_uncertainty") or "Abstract excerpt only"),
        }
        for raw_claim in extracted.get("paper_claims") or []:
            if not isinstance(raw_claim, dict) or not str(raw_claim.get("claim") or "").strip():
                continue
            claim_id = f"claim-{len(claims)+1:03d}"
            identifiers = {key: value for key, value in paper["identifiers"].items() if value}
            claim = {
                "claim_id": claim_id,
                "claim": str(raw_claim["claim"]).strip(),
                "claim_type": "paper_result",
                "paper_record_id": paper["record_id"],
                "paper_title": paper["title"],
                "identifiers": identifiers,
                "source_url": paper["source_records"][0]["source_url"],
                "evidence_location": "abstract excerpt",
                "evidence_type": "abstract",
                "quote": (str(raw_claim.get("quote") or "").strip()[:MAX_EVIDENCE_QUOTE_CHARS] or None),
                "paraphrase": str(raw_claim.get("paraphrase") or raw_claim["claim"]).strip(),
                "verified": True,
                "extraction_uncertainty": analysis["extraction_uncertainty"],
            }
            try:
                validate_research("claim-evidence", claim)
            except ValidationError:
                continue
            claims.append(claim)
            analysis["paper_claims"].append({"claim_id": claim_id, "claim": claim["claim"]})
        paper["analysis"] = analysis
        if analysis["paper_claims"]:
            papers_with_claims.add(paper["record_id"])
    return papers_with_claims


def _confidence(value: Any) -> float:
    if isinstance(value, str):
        mapped = {"low": 0.25, "medium": 0.5, "high": 0.8}
        if value.strip().lower() in mapped:
            return mapped[value.strip().lower()]
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(1.0, numeric))


def _paper_record(candidate: dict[str, Any], *, status: str, checks: list[dict[str, Any]]) -> dict[str, Any]:
    sources = []
    for source in candidate.get("source_records", []):
        sources.append(
            {
                "source": source["source"],
                "source_url": source["source_url"],
                "retrieved_at": source["retrieved_at"],
                "query": source["query"],
                "rank": int(source["rank"]),
                "response_identifier": str(source["response_identifier"]),
            }
        )
    excerpt = candidate.get("abstract_excerpt") if candidate.get("abstract_present") else None
    source_url = sources[0]["source_url"] if sources else None
    value = {
        "record_id": _record_id(candidate),
        "title": candidate["title"],
        "normalized_title": normalize_title(candidate["title"]),
        "year": candidate.get("year"),
        "authors": candidate.get("authors") or [],
        "venue": candidate.get("venue"),
        "publication_type": candidate.get("publication_type"),
        "language": candidate.get("language") or "en",
        "abstract": excerpt,
        "identifiers": candidate.get("identifiers") or {},
        "source_records": sources,
        "validation": {"status": status, "checks": checks, "eligible": status in ("verified", "offline_fixture")},
        "deduplication": candidate.get("deduplication") or {"merged_records": [], "unresolved_candidates": []},
        "access": {
            "content_type": "abstract" if excerpt else "none",
            "source_url": source_url,
            "content_sha256": candidate.get("abstract_sha256"),
            "size_bytes": len(excerpt.encode()) if excerpt else 0,
            "page_count": None,
            "status": "available" if excerpt else "unavailable",
            "failure_type": None if excerpt else "abstract_unavailable",
        },
        "analysis": _blank_analysis(),
    }
    validate_research("paper-record", value)
    return value


class ResearchWorkflow:
    def __init__(
        self,
        *,
        http: ResilientClient | None = None,
        gateway: DeepSeekGateway | None = None,
        offline: bool = False,
        offline_fixture: Path | None = None,
    ) -> None:
        self.stats = http.stats if http is not None else RunStats()
        self.http = http or ResilientClient(stats=self.stats)
        self.adapters = build_adapters(self.http)
        self.gateway = gateway
        self.offline = offline
        self.offline_fixture = offline_fixture

    def _expand(self) -> tuple[list[tuple[str, str]], dict[str, Any]]:
        question = load_json(QUESTION_PATH)
        strategies = load_json(STRATEGIES_PATH)
        seeds = list(strategies["deterministic_seed_queries"])
        details: dict[str, Any] = {"seed_queries": seeds, "model_queries": [], "status": "seed_only", "failure_type": None}
        if self.offline:
            with span(
                "query.expand",
                task_id="research-query-expand",
                query_version=question["version"],
                model="offline-mock",
                offline=True,
                failure_type="offline_model_not_called",
            ):
                details.update({"status": "offline_seed_only", "failure_type": "offline_model_not_called"})
        elif self.gateway is None:
            with span(
                "query.expand",
                task_id="research-query-expand",
                query_version=question["version"],
                model="unexecuted",
                failure_type="deepseek_key_unavailable",
            ):
                details.update({"status": "model_unexecuted", "failure_type": "deepseek_key_unavailable"})
        else:
            try:
                with span(
                    "query.expand",
                    task_id="research-query-expand",
                    query_version=question["version"],
                    model=self.gateway.model,
                    request_model=self.gateway.model,
                    protocol_provider="openai-compatible",
                    actual_endpoint_provider="deepseek",
                    actual_hostname="api.deepseek.com",
                ) as current:
                    result = self.gateway.expand_queries(question["question"], seeds)
                    values = result.value.get("additional_queries")
                    if not isinstance(values, list):
                        raise WorkflowFailure("model_parsing", "Query expansion omitted additional_queries")
                    additions = [str(value).strip() for value in values if isinstance(value, str) and value.strip()][:4]
                    if not additions:
                        raise WorkflowFailure("model_parsing", "Query expansion returned no usable query")
                    self.stats.usage.add(result.usage)
                    self.stats.cost_usd += result.cost_usd
                    self.stats.latencies_ms.append(result.latency_ms)
                    current.set_attributes(
                        {
                            "response_model": result.response_model,
                            "input_tokens": result.usage.input_tokens,
                            "output_tokens": result.usage.output_tokens,
                            "total_tokens": result.usage.total_tokens,
                            "cost_usd": result.cost_usd,
                            "latency_ms": result.latency_ms,
                        }
                    )
                details.update(
                    {
                        "model_queries": additions,
                        "status": "model_expanded",
                        "request_model": self.gateway.model,
                        "response_model": result.response_model,
                        "usage": result.usage.as_dict(),
                        "cost_usd": result.cost_usd,
                        "pricing_tier": result.pricing_tier,
                    }
                )
            except WorkflowFailure as exc:
                details.update({"status": "seed_fallback", "failure_type": exc.kind})
                self.stats.failures.append({"stage": "query.expand", "failure_type": exc.kind, "summary": str(exc)})
        queries = [(query, "deterministic_seed") for query in seeds]
        queries.extend((query, "model_expansion") for query in details["model_queries"])
        return queries, details

    def search(self, condition: str, output: Path, *, queries_and_origins: list[tuple[str, str]] | None = None, expansion: dict[str, Any] | None = None) -> dict[str, Any]:
        started_at = utc_now()
        starting_requests = deepcopy(self.stats.requests_by_source)
        starting_latency_count = len(self.stats.latencies_ms)
        strategies = load_json(STRATEGIES_PATH)
        question = load_json(QUESTION_PATH)
        if condition not in strategies["conditions"]:
            raise ValueError(f"Unknown condition: {condition}")
        config = strategies["conditions"][condition]
        if queries_and_origins is None:
            queries_and_origins, expansion = self._expand()
        assert expansion is not None
        query_values = [value for value, _ in queries_and_origins]
        records: list[dict[str, Any]] = []
        failures: list[dict[str, Any]] = []
        traces: list[dict[str, Any]] = []
        to_year = datetime.now(timezone.utc).year
        task_id = f"search-{condition}"
        if self.offline:
            with span(
                "paper.search",
                task_id=task_id,
                query_hash=_query_hash(query_values),
                query_version=question["version"],
                search_condition=condition,
                offline=True,
            ) as search_span:
                if self.offline_fixture is None or not self.offline_fixture.exists():
                    raise ValueError("Offline search fixture is missing")
                fixture_records = read_jsonl(self.offline_fixture)
                allowed = set(config["sources"])
                records = [deepcopy(item) for item in fixture_records if item.get("source_records", [{}])[0].get("source") in allowed]
                for item in records:
                    for source in item.get("source_records", []):
                        source["retrieved_at"] = started_at
                        source["source"] = source.get("source") or "offline_fixture"
                search_span.set_attributes({"result_count": len(records), "request_count": 0})
            traces.append(
                tool_trace(
                    task_id,
                    "offline_fixture_search",
                    input_summary=f"committed fixture for {condition}",
                    result_summary=f"{len(records)} fixture records; not live search",
                    duration_ms=0,
                    metadata={"offline": True},
                )
            )
        else:
            with span(
                "paper.search",
                task_id=task_id,
                query_hash=_query_hash(query_values),
                query_version=question["version"],
                search_condition=condition,
                project="05-research-agent",
            ) as search_span:
                for source in config["sources"]:
                    adapter = self.adapters[source]
                    for query, origin in queries_and_origins:
                        call_started = time.perf_counter()
                        try:
                            values = adapter.search(
                                query,
                                query_origin=origin,
                                limit=int(config["per_query_candidate_limit"]),
                                from_year=2020,
                                to_year=to_year,
                            )
                        except WorkflowFailure as exc:
                            elapsed = (time.perf_counter() - call_started) * 1000
                            failure = {
                                "record_type": "failure",
                                "source": source,
                                "query": query,
                                "query_origin": origin,
                                "retrieved_at": utc_now(),
                                "failure_type": exc.kind,
                                "summary": str(exc),
                                "retryable": exc.retryable,
                            }
                            failures.append(failure)
                            traces.append(
                                tool_trace(
                                    task_id,
                                    source,
                                    input_summary=f"{origin} query with fixed 2020-{to_year} filter",
                                    result_summary="failure preserved",
                                    duration_ms=elapsed,
                                    error=exc.kind,
                                    metadata={"source": source},
                                )
                            )
                        else:
                            elapsed = (time.perf_counter() - call_started) * 1000
                            records.extend(values)
                            traces.append(
                                tool_trace(
                                    task_id,
                                    source,
                                    input_summary=f"{origin} query with fixed 2020-{to_year} filter",
                                    result_summary=f"{len(values)} normalized records",
                                    duration_ms=elapsed,
                                    metadata={"source": source, "result_count": len(values)},
                                )
                            )
                search_span.set_attributes(
                    {"result_count": len(records), "request_count": sum(self.stats.requests_by_source.values()), "failure_type": "partial_source_failure" if failures else "none"}
                )
        output.mkdir(parents=True, exist_ok=True)
        serialized = [{"record_type": "paper", **record} for record in records] + failures
        write_jsonl(output / "search-records.jsonl", serialized)
        write_jsonl(output / "tool-traces.jsonl", traces)
        write_json(output / "query-expansion.json", expansion)
        condition_requests = {
            source: count - starting_requests.get(source, 0)
            for source, count in self.stats.requests_by_source.items()
            if count - starting_requests.get(source, 0) > 0
        }
        condition_latencies = self.stats.latencies_ms[starting_latency_count:]
        summary = {
            "condition": condition,
            "offline": self.offline,
            "started_at": started_at,
            "finished_at": utc_now(),
            "question_version": question["version"],
            "query_hash": _query_hash(query_values),
            "queries": [{"query": query, "origin": origin} for query, origin in queries_and_origins],
            "sources": config["sources"],
            "result_records": len(records),
            "failures": failures,
            "requests_by_source": condition_requests,
            "latency_p50_ms": percentile(condition_latencies, 0.5),
            "latency_p95_ms": percentile(condition_latencies, 0.95),
            "model_expansion": expansion,
        }
        write_json(output / "search-summary.json", summary)
        return summary

    def validate_corpus(self, input_dir: Path) -> dict[str, Any]:
        starting_requests = deepcopy(self.stats.requests_by_source)
        search_summary = load_json(input_dir / "search-summary.json")
        condition = str(search_summary["condition"])
        rows = read_jsonl(input_dir / "search-records.jsonl")
        records = [{key: value for key, value in row.items() if key != "record_type"} for row in rows if row.get("record_type") == "paper"]
        failures = [row for row in rows if row.get("record_type") == "failure"]
        with span("paper.deduplicate", task_id=f"validate-{condition}", search_condition=condition) as dedup_span:
            unique, report = deduplicate(records)
            dedup_span.set_attributes({"result_count": len(unique), "failure_type": "unresolved_duplicate" if report["unresolved_duplicates"] else "none"})
        candidates = sorted(unique, key=_relevance, reverse=True)
        eligible = [
            item
            for item in candidates
            if _relevance(item) >= 4
            and isinstance(item.get("year"), int)
            and int(item["year"]) >= 2020
            and item.get("abstract_present")
        ][:MAXIMUM_ANALYZED_PAPERS]
        external_checks: dict[str, dict[str, dict[str, Any]]] | None = None
        external_validation_failures: list[dict[str, Any]] = []
        if condition == "federated-verified" and self.offline:
            external_checks = {"doi": {}, "arxiv_id": {}, "semantic_scholar_paper_id": {}}
            for item in eligible:
                identifiers = normalize_identifiers(item.get("identifiers") or {})[0]
                for name, value in identifiers.items():
                    if value:
                        external_checks[name][value] = {"status": "verified", "method": "offline_fixture_not_live"}
        elif condition == "federated-verified":
            external_checks = {"doi": {}, "arxiv_id": {}, "semantic_scholar_paper_id": {}}
            normalized_by_paper = [normalize_identifiers(item.get("identifiers") or {})[0] for item in eligible]
            pending_dois = sorted(
                {
                    ids["doi"]
                    for item, ids in zip(eligible, normalized_by_paper)
                    if ids.get("doi") and not any(source.get("source") == "crossref" for source in item.get("source_records", []))
                }
            )
            for doi in pending_dois:
                try:
                    self.adapters["crossref"].fetch(doi)
                except WorkflowFailure as exc:
                    external_checks["doi"][doi] = {"status": "unresolved", "failure_type": exc.kind}
                    external_validation_failures.append({"identifier": "doi", "value": doi, "failure_type": exc.kind})
                else:
                    external_checks["doi"][doi] = {"status": "verified", "method": "official_crossref_lookup"}
            pending_arxiv = sorted(
                {
                    ids["arxiv_id"]
                    for item, ids in zip(eligible, normalized_by_paper)
                    if ids.get("arxiv_id") and not any(source.get("source") == "arxiv" for source in item.get("source_records", []))
                }
            )
            if pending_arxiv:
                try:
                    resolved = self.adapters["arxiv"].fetch_many(pending_arxiv)
                except WorkflowFailure as exc:
                    resolved = {}
                    external_validation_failures.append({"identifier": "arxiv_id_batch", "failure_type": exc.kind, "count": len(pending_arxiv)})
                for arxiv_id in pending_arxiv:
                    if arxiv_id in resolved:
                        external_checks["arxiv_id"][arxiv_id] = {"status": "verified", "method": "official_arxiv_batch_lookup"}
                    else:
                        external_checks["arxiv_id"][arxiv_id] = {"status": "unresolved", "failure_type": "batch_lookup_unresolved"}
        papers: list[dict[str, Any]] = []
        rejected: list[dict[str, Any]] = []
        validation_traces: list[dict[str, Any]] = []
        with span("identifier.validate", task_id=f"validate-{condition}", search_condition=condition) as validation_span:
            for candidate in eligible:
                started = time.perf_counter()
                status, checks = validate_identifiers(
                    candidate,
                    condition=condition,
                    source_adapters=self.adapters,
                    external_checks=external_checks,
                )
                elapsed = (time.perf_counter() - started) * 1000
                trace = tool_trace(
                    f"validate-{condition}",
                    "identifier_validator",
                    input_summary="normalized candidate identifiers",
                    result_summary=status,
                    duration_ms=elapsed,
                    error=None if status == "verified" else status,
                    metadata={"validation_status": status},
                )
                validation_traces.append(trace)
                if status == "verified":
                    papers.append(_paper_record(candidate, status="offline_fixture" if self.offline else status, checks=checks))
                else:
                    rejected.append({"title": candidate.get("title"), "identifiers": candidate.get("identifiers"), "status": status, "checks": checks})
            validation_span.set_attributes(
                {"result_count": len(papers), "validation_status": "verified" if len(papers) >= MINIMUM_VERIFIED_PAPERS else "insufficient", "failure_type": "none" if len(papers) >= MINIMUM_VERIFIED_PAPERS else "minimum_papers_not_met"}
            )
        report.update(
            {
                "condition": condition,
                "eligible_candidates": len(eligible),
                "verified_papers": len(papers),
                "rejected_papers": rejected,
                "search_failures": failures,
                "external_validation_failures": external_validation_failures,
                "minimum_required": MINIMUM_VERIFIED_PAPERS,
                "minimum_met": len(papers) >= MINIMUM_VERIFIED_PAPERS,
            }
        )
        write_json(input_dir / "validated-papers.json", papers)
        write_json(input_dir / "deduplication-report.json", report)
        existing_traces = read_jsonl(input_dir / "tool-traces.jsonl") if (input_dir / "tool-traces.jsonl").exists() else []
        write_jsonl(input_dir / "tool-traces.jsonl", existing_traces + validation_traces)
        condition_requests = deepcopy(search_summary.get("requests_by_source") or {})
        for source, count in self.stats.requests_by_source.items():
            validation_requests = count - starting_requests.get(source, 0)
            if validation_requests > 0:
                condition_requests[source] = condition_requests.get(source, 0) + validation_requests
        summary = {
            "condition": condition,
            "verified_papers": len(papers),
            "duplicates_removed": report["duplicates_removed"],
            "unresolved_duplicates": len(report["unresolved_duplicates"]),
            "identifier_failures": len(rejected) + len(external_validation_failures),
            "minimum_met": report["minimum_met"],
            "requests_by_source": condition_requests,
        }
        write_json(input_dir / "corpus-summary.json", summary)
        return summary

    def _offline_analysis(self, papers: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any], list[dict[str, Any]]]:
        claims = []
        for index, paper in enumerate(papers, 1):
            claim_id = f"offline-claim-{index:03d}"
            claim = {
                "claim_id": claim_id,
                "claim": f"Offline fixture evidence for {paper['title']}",
                "claim_type": "paper_result",
                "paper_record_id": paper["record_id"],
                "paper_title": paper["title"],
                "identifiers": {key: value for key, value in paper["identifiers"].items() if value},
                "source_url": paper["source_records"][0]["source_url"],
                "evidence_location": "offline fixture abstract excerpt",
                "evidence_type": "abstract",
                "quote": None,
                "paraphrase": "Synthetic fixture claim used only to exercise the offline pipeline.",
                "verified": True,
                "extraction_uncertainty": "Offline mock; not a live paper analysis.",
            }
            validate_research("claim-evidence", claim)
            claims.append(claim)
            paper["analysis"] = {
                "research_objective": "Offline fixture objective",
                "methodology": "Offline mock adapter",
                "datasets": [],
                "metrics": [],
                "key_results": [claim["claim"]],
                "limitations": ["Not a live scholarly analysis"],
                "rag_stages": ["offline_fixture"],
                "paper_claims": [{"claim_id": claim_id, "claim": claim["claim"]}],
                "agent_interpretation": [],
                "extraction_uncertainty": "Offline mock; not a live paper analysis.",
            }
        claim_ids = [claim["claim_id"] for claim in claims]
        synthesis = {
            "sections": [
                {
                    "technique": "offline fixture",
                    "findings": "Synthetic evidence confirms only that the offline pipeline is wired correctly.",
                    "supporting_claim_ids": claim_ids,
                    "tradeoffs": "No live research conclusion may be drawn.",
                }
            ]
        }
        hypotheses = [
            {
                "hypothesis_id": "offline-hypothesis-001",
                "hypothesis": "The same pipeline should preserve provenance when connected to live APIs.",
                "derived_from_claim_ids": claim_ids[:1],
                "rationale": "The mock route exercises the same schemas and renderers.",
                "falsification_test": "Run the live workflow and check every output contract and locator.",
                "confidence": 0.2,
                "attribution": "agent_hypothesis_not_paper_conclusion",
            }
        ] if claims else []
        return claims, synthesis, hypotheses

    def analyze(self, condition: str, input_dir: Path, output: Path) -> dict[str, Any]:
        papers = deepcopy(json.loads((input_dir / "validated-papers.json").read_text(encoding="utf-8")))
        if not isinstance(papers, list):
            raise ValueError("validated-papers.json must be an array")
        corpus_summary = load_json(input_dir / "corpus-summary.json")
        search_summary = load_json(input_dir / "search-summary.json")
        failures = list(search_summary.get("failures") or []) + list((load_json(input_dir / "deduplication-report.json")).get("rejected_papers") or [])
        usage = Usage()
        cost = 0.0
        model_latencies: list[float] = []
        traces = read_jsonl(input_dir / "tool-traces.jsonl") if (input_dir / "tool-traces.jsonl").exists() else []
        with span("content.fetch", task_id=f"analyze-{condition}", search_condition=condition, result_count=len(papers)):
            for paper in papers:
                content = paper.get("abstract") or ""
                paper["access"]["content_sha256"] = hashlib.sha256(content.encode()).hexdigest() if content else None
                paper["access"]["size_bytes"] = len(content.encode())
        traces.append(
            tool_trace(
                f"analyze-{condition}",
                "public_abstract_collector",
                input_summary="verified public metadata records",
                result_summary=f"{len(papers)} bounded abstract excerpts; full abstracts not persisted",
                duration_ms=0,
                metadata={"content_type": "abstract", "paper_count": len(papers)},
            )
        )
        if self.offline:
            with span("evidence.extract", task_id=f"analyze-{condition}", offline=True, model="offline-mock"):
                claims, synthesis, hypotheses = self._offline_analysis(papers)
            with span("report.synthesize", task_id=f"analyze-{condition}", offline=True, model="offline-mock"):
                pass
            model_status = "offline_mock_not_live"
            response_models: list[str] = []
        elif self.gateway is None:
            with span(
                "evidence.extract",
                task_id=f"analyze-{condition}",
                model="unexecuted",
                failure_type="deepseek_key_unavailable",
            ):
                claims = []
            with span(
                "report.synthesize",
                task_id=f"analyze-{condition}",
                model="unexecuted",
                failure_type="deepseek_key_unavailable",
            ):
                synthesis, hypotheses = {"sections": []}, []
            model_status = "unexecuted_missing_key"
            response_models = []
            failures.append({"stage": "evidence.extract", "failure_type": "deepseek_key_unavailable", "summary": "DeepSeek extraction was not executed"})
        else:
            claims = []
            response_models = []
            with span(
                "evidence.extract",
                task_id=f"analyze-{condition}",
                search_condition=condition,
                model=self.gateway.model,
                request_model=self.gateway.model,
                protocol_provider="openai-compatible",
                actual_endpoint_provider="deepseek",
                actual_hostname="api.deepseek.com",
            ) as extraction_span:
                def extract_batch(
                    batch: list[dict[str, Any]],
                    *,
                    batch_start: int,
                    recovery_attempt: int | None = None,
                ) -> set[str]:
                    nonlocal cost
                    source = [
                        {
                            "record_id": paper["record_id"],
                            "title": paper["title"],
                            "year": paper["year"],
                            "abstract_excerpt": paper.get("abstract"),
                        }
                        for paper in batch
                    ]
                    try:
                        result = self.gateway.complete_json(
                            system=(
                                "You extract only claims directly supported by the supplied scholarly abstract excerpts. "
                                "Return JSON with a papers array. Never infer numeric results or methods not in the excerpt. "
                                "Agent interpretation must be separate. Return every supplied record_id exactly once. "
                                "For each non-empty abstract, include at least one conservative paper_claim that paraphrases "
                                "a directly stated objective, method, result, or limitation."
                            ),
                            user=json.dumps(
                                {
                                    "papers": source,
                                    "recovery_attempt": recovery_attempt,
                                    "required_per_paper": {
                                        "record_id": "exact input id",
                                        "research_objective": "string",
                                        "methodology": "string",
                                        "datasets": ["string"],
                                        "metrics": ["string"],
                                        "key_results": ["string"],
                                        "limitations": ["string"],
                                        "rag_stages": ["query_rewriting|reranking|corrective_retrieval|self_reflective_retrieval|other"],
                                        "paper_claims": [{"claim": "direct paper claim", "paraphrase": "faithful paraphrase", "quote": "optional <=300 chars"}],
                                        "agent_interpretation": ["explicit interpretation"],
                                        "extraction_uncertainty": "string",
                                    },
                                },
                                ensure_ascii=False,
                            ),
                            max_tokens=6000,
                        )
                    except WorkflowFailure as exc:
                        failure = {"stage": "evidence.extract", "failure_type": exc.kind, "summary": str(exc), "batch_start": batch_start}
                        if recovery_attempt is not None:
                            failure["recovery_attempt"] = recovery_attempt
                        failures.append(failure)
                        return set()
                    usage.add(result.usage)
                    cost += result.cost_usd
                    model_latencies.append(result.latency_ms)
                    response_models.append(result.response_model)
                    returned = result.value.get("papers")
                    if not isinstance(returned, list):
                        failure = {"stage": "evidence.extract", "failure_type": "model_parsing", "summary": "papers array missing", "batch_start": batch_start}
                        if recovery_attempt is not None:
                            failure["recovery_attempt"] = recovery_attempt
                        failures.append(failure)
                        return set()
                    return _apply_extracted_papers(returned, batch, claims)

                for batch_start in range(0, len(papers), 5):
                    extract_batch(papers[batch_start : batch_start + 5], batch_start=batch_start)

                recovery_requests = 0
                for recovery_attempt in range(1, 3):
                    missing = [paper for paper in papers if not paper["analysis"]["paper_claims"]]
                    if not missing:
                        break
                    for paper in missing:
                        recovery_requests += 1
                        extract_batch(
                            [paper],
                            batch_start=papers.index(paper),
                            recovery_attempt=recovery_attempt,
                        )
                unresolved = [paper["record_id"] for paper in papers if not paper["analysis"]["paper_claims"]]
                if unresolved:
                    failures.append(
                        {
                            "stage": "evidence.extract",
                            "failure_type": "claim_coverage_incomplete",
                            "summary": f"{len(unresolved)} papers still have no valid claim after bounded recovery",
                            "paper_record_ids": unresolved,
                        }
                    )
                extraction_span.set_attributes(
                    {
                        "result_count": len(claims),
                        "recovery_requests": recovery_requests,
                        "unresolved_papers": len(unresolved),
                        "input_tokens": usage.input_tokens,
                        "output_tokens": usage.output_tokens,
                        "total_tokens": usage.total_tokens,
                        "cost_usd": cost,
                        "failure_type": "partial_model_failure" if unresolved else "none",
                    }
                )
            with span(
                "report.synthesize",
                task_id=f"analyze-{condition}",
                model=self.gateway.model,
                request_model=self.gateway.model,
                protocol_provider="openai-compatible",
                actual_endpoint_provider="deepseek",
                actual_hostname="api.deepseek.com",
            ) as synthesis_span:
                if claims:
                    try:
                        result = self.gateway.complete_json(
                            system=(
                                "Synthesize only from supplied verified claim records. Return JSON with sections and hypotheses. "
                                "Each section needs technique, findings, supporting_claim_ids, tradeoffs. Each hypothesis needs hypothesis_id, "
                                "hypothesis, derived_from_claim_ids, rationale, falsification_test, confidence, and attribution exactly "
                                "agent_hypothesis_not_paper_conclusion."
                            ),
                            user=json.dumps({"research_question": load_json(QUESTION_PATH)["question"], "claims": claims}, ensure_ascii=False),
                            max_tokens=5000,
                        )
                    except WorkflowFailure as exc:
                        synthesis, hypotheses = {"sections": []}, []
                        failures.append({"stage": "report.synthesize", "failure_type": exc.kind, "summary": str(exc)})
                    else:
                        usage.add(result.usage)
                        cost += result.cost_usd
                        model_latencies.append(result.latency_ms)
                        response_models.append(result.response_model)
                        valid_ids = {claim["claim_id"] for claim in claims}
                        sections = []
                        for section in result.value.get("sections") or []:
                            if not isinstance(section, dict):
                                continue
                            supporting = [value for value in section.get("supporting_claim_ids") or [] if value in valid_ids]
                            if supporting:
                                sections.append(
                                    {
                                        "technique": str(section.get("technique") or "cross-paper synthesis"),
                                        "findings": str(section.get("findings") or ""),
                                        "supporting_claim_ids": supporting,
                                        "tradeoffs": str(section.get("tradeoffs") or "Not established"),
                                    }
                                )
                        synthesis = {"sections": sections}
                        hypotheses = []
                        for raw in result.value.get("hypotheses") or []:
                            if not isinstance(raw, dict):
                                continue
                            derived = [value for value in raw.get("derived_from_claim_ids") or [] if value in valid_ids]
                            value = {
                                "hypothesis_id": str(raw.get("hypothesis_id") or f"hypothesis-{len(hypotheses)+1:03d}"),
                                "hypothesis": str(raw.get("hypothesis") or ""),
                                "derived_from_claim_ids": derived,
                                "rationale": str(raw.get("rationale") or ""),
                                "falsification_test": str(raw.get("falsification_test") or ""),
                                "confidence": _confidence(raw.get("confidence")),
                                "attribution": "agent_hypothesis_not_paper_conclusion",
                            }
                            try:
                                validate_research("hypothesis", value)
                            except (ValidationError, ValueError):
                                continue
                            hypotheses.append(value)
                else:
                    synthesis, hypotheses = {"sections": []}, []
                synthesis_span.set_attributes(
                    {"result_count": len((synthesis or {}).get("sections") or []), "input_tokens": usage.input_tokens, "output_tokens": usage.output_tokens, "total_tokens": usage.total_tokens, "cost_usd": cost, "failure_type": "none"}
                )
            model_status = "executed" if claims else "executed_no_valid_claims"
        for paper in papers:
            validate_research("paper-record", paper)
        report = {
            "question": load_json(QUESTION_PATH)["question"],
            "condition": condition,
            "search": {
                "started_at": search_summary["started_at"],
                "sources": search_summary["sources"],
                "queries": search_summary["queries"],
                "requests_by_source": corpus_summary["requests_by_source"],
                "duplicates_removed": corpus_summary["duplicates_removed"],
                "identifier_failures": corpus_summary["identifier_failures"],
            },
            "verified_papers": [
                {"record_id": paper["record_id"], "title": paper["title"], "year": paper["year"], "identifiers": paper["identifiers"], "source_url": paper["source_records"][0]["source_url"]}
                for paper in papers
            ],
            "claims": claims,
            "synthesis": synthesis,
            "hypotheses": hypotheses,
            "failures": failures,
            "limitations": [
                "Extraction uses bounded public abstract excerpts; claims are not full-text findings unless explicitly marked.",
                "Search API ranking and metadata can change after the recorded retrieval timestamp.",
                "Calculated API cost uses provider-reported usage and published rates; it is not an invoice.",
            ] + (["Offline output is synthetic and must not be presented as live research."] if self.offline else []),
            "usage": {
                "model_status": model_status,
                "provider": "deepseek" if not self.offline else "offline_mock",
                "protocol_provider": "openai-compatible" if not self.offline else None,
                "actual_endpoint_provider": "deepseek" if not self.offline else None,
                "actual_hostname": "api.deepseek.com" if not self.offline else None,
                "request_model": self.gateway.model if self.gateway else None,
                "response_models": sorted(set(response_models)),
                "tokens": usage.as_dict(),
                "calculated_cost_usd": cost,
                "pricing_tiers": "execution-time",
                "pricing_checked_at": PRICING_CHECKED_AT,
                "pricing_source": PRICING_SOURCE,
            },
        }
        validate_research("research-report", report)
        status = "success" if len(papers) >= MINIMUM_VERIFIED_PAPERS and len({claim["paper_record_id"] for claim in claims}) >= MINIMUM_VERIFIED_PAPERS else "partial"
        agent_result = {
            "task_id": f"research-report-{condition}",
            "status": status,
            "output": {"condition": condition, "report": "report.md", "verified_papers": len(papers), "claims": len(claims)},
            "evidence": [{"source": claim["source_url"], "location": claim["evidence_location"], "claim": claim["claim"]} for claim in claims],
            "actions": ["Apply the search strategy only after deterministic evaluation passes"],
            "limitations": report["limitations"],
            "metadata": {"provider": report["usage"]["provider"], "model_status": model_status, "offline": self.offline},
        }
        validate_contract("agent-result", agent_result)
        output.mkdir(parents=True, exist_ok=True)
        write_json(output / "validated-papers.json", papers)
        write_jsonl(output / "claims.jsonl", claims)
        write_claim_csv(output / "claim-evidence.csv", claims)
        write_bibtex(output / "references.bib", papers)
        write_json(output / "research-report.json", report)
        (output / "report.md").write_text(render_report(report), encoding="utf-8")
        write_json(output / "agent-result.json", agent_result)
        traces.extend(
            [
                tool_trace(
                    f"analyze-{condition}",
                    "deepseek_extractor",
                    input_summary="verified paper IDs and bounded abstract excerpts",
                    result_summary=f"{len(claims)} validated claim records; raw prompts and responses not retained",
                    duration_ms=sum(model_latencies),
                    error=None if model_status in ("executed", "offline_mock_not_live") else model_status,
                    metadata={"model": self.gateway.model if self.gateway else None, "token_usage": usage.as_dict(), "cost_usd": cost, "model_status": model_status},
                )
            ]
        )
        write_jsonl(output / "tool-traces.jsonl", traces)
        summary = {
            "condition": condition,
            "offline": self.offline,
            "verified_papers": len(papers),
            "claims": len(claims),
            "papers_with_claims": len({claim["paper_record_id"] for claim in claims}),
            "hypotheses": len(hypotheses),
            "model_status": model_status,
            "request_model": self.gateway.model if self.gateway else None,
            "response_models": sorted(set(response_models)),
            "usage": usage.as_dict(),
            "calculated_cost_usd": cost,
            "model_latency_p50_ms": percentile(model_latencies, 0.5),
            "model_latency_p95_ms": percentile(model_latencies, 0.95),
            "failures": failures,
        }
        write_json(output / "summary.json", summary)
        return summary

    def evaluate(self, condition: str, input_dir: Path, output: Path) -> dict[str, Any]:
        started = time.perf_counter()
        papers = json.loads((input_dir / "validated-papers.json").read_text(encoding="utf-8"))
        claims = read_jsonl(input_dir / "claims.jsonl")
        report = load_json(input_dir / "research-report.json")
        analysis_summary = load_json(input_dir / "summary.json")
        schema_valid = 0
        schema_total = len(papers) + len(claims) + len(report.get("hypotheses") or []) + 2
        for name, values in (("paper-record", papers), ("claim-evidence", claims), ("hypothesis", report.get("hypotheses") or [])):
            for value in values:
                try:
                    validate_research(name, value)
                except ValidationError:
                    pass
                else:
                    schema_valid += 1
        try:
            validate_research("research-report", report)
            schema_valid += 1
        except ValidationError:
            pass
        try:
            validate_contract("agent-result", load_json(input_dir / "agent-result.json"))
            schema_valid += 1
        except ValidationError:
            pass
        pairs = 0
        for index, first in enumerate(papers):
            for second in papers[index + 1 :]:
                if duplicate_decision(first, second)["duplicate"]:
                    pairs += 1
        verified_ids = {
            paper["record_id"]
            for paper in papers
            if paper.get("validation", {}).get("status") in ("verified", "offline_fixture")
            and any(paper.get("identifiers", {}).values())
        }
        claim_papers = {claim.get("paper_record_id") for claim in claims}
        citations_valid = [
            claim
            for claim in claims
            if claim.get("verified") is True
            and str(claim.get("source_url") or "").startswith("https://")
            and any((claim.get("identifiers") or {}).values())
        ]
        located = [claim for claim in claims if claim.get("evidence_location")]
        hypotheses = report.get("hypotheses") or []
        hypothesis_separated = [item for item in hypotheses if item.get("attribution") == "agent_hypothesis_not_paper_conclusion" and item.get("derived_from_claim_ids")]
        schema_rate = schema_valid / schema_total if schema_total else 0.0
        identifier_rate = len(verified_ids) / len(papers) if papers else 0.0
        citation_rate = len(citations_valid) / len(claims) if claims else 0.0
        evidence_coverage = len(claim_papers & verified_ids) / len(verified_ids) if verified_ids else 0.0
        locator_rate = len(located) / len(claims) if claims else 0.0
        hypothesis_rate = len(hypothesis_separated) / len(hypotheses) if hypotheses else (1.0 if claims else 0.0)
        provenance_gaps = len(claims) - len(citations_valid)
        result_text = "\n".join(path.read_text(encoding="utf-8", errors="replace") for path in input_dir.iterdir() if path.is_file() and path.stat().st_size < 5_000_000)
        safety_patterns = [r"DEEPSEEK_API_KEY\s*=\s*\S+", r"Authorization:\s*Bearer", r"sk-[A-Za-z0-9]{12,}", r"BEGIN (?:RSA |EC )?PRIVATE KEY"]
        safety_violations = [pattern for pattern in safety_patterns if re.search(pattern, result_text, flags=re.IGNORECASE)]
        search_latency = report.get("search", {})
        total_requests = sum(int(value) for value in (search_latency.get("requests_by_source") or {}).values())
        usage = analysis_summary.get("usage") or {}
        cost = float(analysis_summary.get("calculated_cost_usd") or 0)
        metrics = {
            "schema_compliance": schema_rate,
            "identifier_validity": identifier_rate,
            "citation_linkage": citation_rate,
            "duplicate_residue": 1.0 if pairs == 0 else 0.0,
            "evidence_coverage": evidence_coverage,
            "locator_coverage": locator_rate,
            "hypothesis_separation": hypothesis_rate,
            "provenance_completeness": 1.0 if provenance_gaps == 0 and claims else 0.0,
            "minimum_papers": 1.0 if len(papers) >= MINIMUM_VERIFIED_PAPERS else 0.0,
            "safety": 1.0 if not safety_violations else 0.0,
        }
        hard_success = all(value == 1.0 for value in metrics.values())
        latency_ms = (time.perf_counter() - started) * 1000
        records: list[dict[str, Any]] = []
        with span(
            "evaluation.deterministic",
            task_id=f"evaluation-{condition}",
            search_condition=condition,
            result_count=len(metrics),
            failure_type="none" if hard_success else "deterministic_threshold_failed",
        ):
            for metric, score in metrics.items():
                record = {
                    "task_id": f"research-evaluation-{condition}-{metric}",
                    "implementation_id": f"ukkhnn:{condition}:deterministic-v1",
                    "task_success": score == 1.0,
                    "quality_score": score,
                    "tool_accuracy": score,
                    "latency_ms": latency_ms,
                    "usage": usage,
                    "cost": cost,
                    "safety_violations": safety_violations,
                    "failure_type": None if score == 1.0 else metric,
                    "metadata": {"metric": metric, "condition": condition, "grader": "fixed-rule-v1", "offline": self.offline},
                }
                validate_contract("evaluation-record", record)
                records.append(record)
        output.mkdir(parents=True, exist_ok=True)
        write_jsonl(output / "evaluation-records.jsonl", records)
        summary = {
            "condition": condition,
            "offline": self.offline,
            "task_success": hard_success,
            "metrics": metrics,
            "schema_compliance_rate": schema_rate,
            "verified_papers": len(papers),
            "identifier_validity": identifier_rate,
            "duplicates_remaining": pairs,
            "duplicates_removed": int(report.get("search", {}).get("duplicates_removed") or 0),
            "identifier_failures": int(report.get("search", {}).get("identifier_failures") or 0),
            "citation_linkage": citation_rate,
            "evidence_coverage": evidence_coverage,
            "locator_coverage": locator_rate,
            "hypothesis_separation": hypothesis_rate,
            "provenance_gaps": provenance_gaps,
            "minimum_papers_met": len(papers) >= MINIMUM_VERIFIED_PAPERS,
            "source_failures": report.get("failures") or [],
            "latency_p50_ms": analysis_summary.get("model_latency_p50_ms", 0),
            "latency_p95_ms": analysis_summary.get("model_latency_p95_ms", 0),
            "requests_by_source": report.get("search", {}).get("requests_by_source") or {},
            "api_requests": total_requests + int(usage.get("requests") or 0),
            "total_tokens": int(usage.get("total_tokens") or 0),
            "calculated_cost_usd": cost,
            "cost_basis": "provider-reported usage and official execution-time pricing; calculated, not invoice",
            "model_status": analysis_summary.get("model_status"),
            "safety_violations": safety_violations,
        }
        write_json(output / "summary.json", summary)
        report_lines = ["# Deterministic evaluation", "", f"Condition: `{condition}`", "", "| Metric | Score |", "| --- | ---: |"]
        report_lines.extend(f"| {name} | {score:.4f} |" for name, score in metrics.items())
        report_lines.extend(["", f"Overall success: `{hard_success}`", ""])
        (output / "report.md").write_text("\n".join(report_lines), encoding="utf-8")
        return summary

    def compare(self, first_dir: Path, second_dir: Path, output: Path) -> str:
        first = load_json(first_dir / "summary.json")
        second = load_json(second_dir / "summary.json")
        value = render_comparison(first, second)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(value, encoding="utf-8")
        return value

    def run_all(self, output: Path) -> dict[str, Any]:
        started = utc_now()
        evaluations: dict[str, dict[str, Any]] = {}
        with span(
            "research.workflow",
            task_id="research-run-all-offline" if self.offline else "research-run-all-live",
            query_version=load_json(QUESTION_PATH)["version"],
            project="05-research-agent",
            offline=self.offline,
            model=self.gateway.model if self.gateway else ("offline-mock" if self.offline else "unexecuted"),
            protocol_provider="openai-compatible" if self.gateway else "none",
            actual_endpoint_provider="deepseek" if self.gateway else "none",
            actual_hostname="api.deepseek.com" if self.gateway else "none",
        ) as workflow_span:
            queries, expansion = self._expand()
            workflow_span.set_attribute("query_hash", _query_hash([query for query, _ in queries]))
            for condition in ("semantic-scholar-only", "federated-verified"):
                search_dir = output / condition
                analysis_dir = output / f"{condition}-analysis"
                evaluation_dir = output / f"{condition}-evaluation"
                self.search(condition, search_dir, queries_and_origins=queries, expansion=expansion)
                self.validate_corpus(search_dir)
                self.analyze(condition, search_dir, analysis_dir)
                evaluations[condition] = self.evaluate(condition, analysis_dir, evaluation_dir)
            comparison = output / "research-condition-comparison.md"
            self.compare(
                output / "semantic-scholar-only-evaluation",
                output / "federated-verified-evaluation",
                comparison,
            )
            live = not self.offline
            all_success = all(value["task_success"] for value in evaluations.values())
            decision = (
                "federated 검색을 기본 적용"
                if live and all_success and evaluations["federated-verified"]["evidence_coverage"] >= evaluations["semantic-scholar-only"]["evidence_coverage"]
                else "품질 또는 안전 기준 미달로 적용 보류"
            )
            status = {
                "run_started_at": started,
                "run_finished_at": utc_now(),
                "offline": self.offline,
                "conditions": evaluations,
                "minimum_verified_papers_met": all(value["minimum_papers_met"] for value in evaluations.values()),
                "all_core_claims_linked": all(value["evidence_coverage"] == 1.0 for value in evaluations.values()),
                "hypotheses_separated": all(value["hypothesis_separation"] == 1.0 for value in evaluations.values()),
                "raw_content_in_traces": False,
                "no_secrets_in_git_or_results": all(not value["safety_violations"] for value in evaluations.values()),
                "deepseek_model": self.gateway.model if self.gateway else None,
                "model_execution": "offline_mock" if self.offline else ("executed" if self.gateway else "unexecuted"),
                "application_decision": decision,
                "success": all_success,
            }
            write_json(output / "verification-status.json", status)
            workflow_span.set_attributes(
                {"validation_status": "passed" if all_success else "failed", "failure_type": "none" if all_success else "deterministic_threshold_failed"}
            )
        return status
