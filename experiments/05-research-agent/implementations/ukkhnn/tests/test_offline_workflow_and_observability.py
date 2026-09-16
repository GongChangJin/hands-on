from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from research_agent.contracts import validate_contract, validate_research
from research_agent.paths import IMPLEMENTATION_DIR
from research_agent.reporting import read_jsonl
from research_agent.workflow import ResearchWorkflow


FIXTURE = IMPLEMENTATION_DIR / "tests" / "fixtures" / "offline-search-records.jsonl"


def workflow() -> ResearchWorkflow:
    return ResearchWorkflow(offline=True, offline_fixture=FIXTURE)


def test_offline_end_to_end_writes_all_required_formats(tmp_path: Path) -> None:
    status = workflow().run_all(tmp_path)
    assert status["success"] is True
    assert status["model_execution"] == "offline_mock"
    for condition in ("semantic-scholar-only", "federated-verified"):
        search_dir = tmp_path / condition
        analysis_dir = tmp_path / f"{condition}-analysis"
        evaluation_dir = tmp_path / f"{condition}-evaluation"
        assert {"search-records.jsonl", "validated-papers.json", "deduplication-report.json"}.issubset({path.name for path in search_dir.iterdir()})
        assert {"claims.jsonl", "claim-evidence.csv", "references.bib", "report.md", "summary.json", "validated-papers.json"}.issubset({path.name for path in analysis_dir.iterdir()})
        assert {"evaluation-records.jsonl", "summary.json", "report.md"}.issubset({path.name for path in evaluation_dir.iterdir()})
        summary = json.loads((evaluation_dir / "summary.json").read_text())
        assert summary["verified_papers"] >= 10
        assert summary["evidence_coverage"] == 1.0
        for record in read_jsonl(evaluation_dir / "evaluation-records.jsonl"):
            validate_contract("evaluation-record", record)
        papers = json.loads((analysis_dir / "validated-papers.json").read_text())
        claims = read_jsonl(analysis_dir / "claims.jsonl")
        report = json.loads((analysis_dir / "research-report.json").read_text())
        for paper in papers:
            validate_research("paper-record", paper)
        for claim in claims:
            validate_research("claim-evidence", claim)
        validate_research("research-report", report)
        assert all(item["attribution"] == "agent_hypothesis_not_paper_conclusion" for item in report["hypotheses"])
        traces = (analysis_dir / "tool-traces.jsonl").read_text()
        assert "DEEPSEEK_API_KEY" not in traces
        assert "Authorization" not in traces
        assert "raw_prompt" not in traces
        assert "raw_response" not in traces
    assert (tmp_path / "research-condition-comparison.md").exists()
    assert (tmp_path / "verification-status.json").exists()


def test_federated_fixture_removes_cross_source_duplicates(tmp_path: Path) -> None:
    run = workflow()
    class NoNetwork:
        def fetch(self, identifier):
            raise AssertionError("offline validation must not call an external adapter")

        def fetch_many(self, identifiers):
            raise AssertionError("offline validation must not call an external adapter")

    run.adapters = {"semantic_scholar": NoNetwork(), "crossref": NoNetwork(), "arxiv": NoNetwork()}
    output = tmp_path / "federated"
    run.search("federated-verified", output)
    summary = run.validate_corpus(output)
    report = json.loads((output / "deduplication-report.json").read_text())
    assert summary["verified_papers"] == 12
    assert report["duplicates_removed"] == 3
    assert report["minimum_met"] is True


def test_required_span_hierarchy_is_nested_under_workflow(tmp_path: Path) -> None:
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
    workflow().run_all(tmp_path)
    spans = exporter.get_finished_spans()
    roots = [item for item in spans if item.name == "research.workflow"]
    assert len(roots) == 1
    root = roots[0]
    required = {
        "query.expand",
        "paper.search",
        "identifier.validate",
        "paper.deduplicate",
        "content.fetch",
        "evidence.extract",
        "report.synthesize",
        "evaluation.deterministic",
    }
    children = {item.name for item in spans if item.parent and item.parent.span_id == root.context.span_id}
    assert required.issubset(children)
    for item in spans:
        assert "raw_prompt" not in item.attributes
        assert "raw_response" not in item.attributes
        assert "authorization" not in item.attributes
        assert "abstract" not in item.attributes


def test_cli_smoke_uses_committed_fixture_and_no_network(tmp_path: Path) -> None:
    output = tmp_path / "cli-smoke"
    environment = dict(os.environ)
    environment.pop("DEEPSEEK_API_KEY", None)
    completed = subprocess.run(
        [str(IMPLEMENTATION_DIR / "run-research-agent"), "run-all", "--offline", "--no-phoenix", "--output", str(output)],
        cwd=IMPLEMENTATION_DIR,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert completed.returncode == 0, completed.stderr
    status = json.loads(completed.stdout)
    assert status["offline"] is True
    assert status["model_execution"] == "offline_mock"
