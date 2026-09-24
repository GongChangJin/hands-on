import json

from local_llm.report import comparison_markdown, summarize
from local_llm.runner import run_benchmark
from local_llm.types import GenerationResponse


class PerfectAdapter:
    adapter_name = "fake"
    model = "perfect"

    def warmup(self):
        return GenerationResponse(model=self.model, total_latency_ms=10, load_duration_ms=5)

    def inspect(self):
        return {"model": self.model, "quantization_level": "test"}

    def generate(self, request):
        schema = request.response_schema
        answer_schema = schema["properties"]["answer"]
        if "enum" in answer_schema:
            answer = answer_schema["enum"][0]
        elif answer_schema.get("type") == "integer":
            answer = 0
        else:
            answer = "wrong-but-valid"
        return GenerationResponse(
            text=json.dumps({"answer": answer}, ensure_ascii=False),
            model=self.model,
            total_latency_ms=50,
            first_token_latency_ms=10,
            output_tokens=4,
            generation_tokens_per_second=40,
            cost_usd=0,
        )


def test_runner_exports_all_contract_records(tmp_path):
    summary, report_path = run_benchmark(PerfectAdapter(), repetitions=1, output_dir=tmp_path)
    assert summary["runs"] == 24
    assert report_path.exists()
    for name in ("agent-results.jsonl", "tool-traces.jsonl", "records.jsonl"):
        assert len((tmp_path / name).read_text(encoding="utf-8").splitlines()) == 24


def test_summary_keeps_schema_and_answer_rates_separate():
    records = [
        {
            "task_id": "a",
            "task_success": False,
            "latency_ms": 100,
            "cost": 0,
            "safety_violations": [],
            "failure_type": "answer_mismatch",
            "usage": {"requests": 1},
            "metadata": {"category": "x", "schema_pass": True, "first_token_latency_ms": 20, "generation_tokens_per_second": 30},
        }
    ]
    summary = summarize(records, implementation_id="x", adapter="fake", model="m", repetitions=1, environment={})
    assert summary["success_rate"] == 0
    assert summary["schema_pass_rate"] == 1


def test_comparison_states_local_cost_boundary():
    summary = {
        "adapter": "ollama",
        "model": "m",
        "success_rate": 1,
        "schema_pass_rate": 1,
        "latency_p50_ms": 10,
        "latency_p95_ms": 20,
        "first_token_p50_ms": 5,
        "generation_tokens_per_second_mean": 30,
        "estimated_cost_usd": 0,
        "environment": {"model": {"accelerator_memory_bytes": 1024 ** 3}},
    }
    report = comparison_markdown([summary])
    assert "hardware and electricity are not estimated" in report
