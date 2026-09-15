# Verification status

Live validation completed on 2026-09-15:

- 24 shared synthetic fixtures and 48 paired tasks passed format, signature, dimensions, metadata, hash, privacy-pattern, label, and TaskRequest checks.
- 35 regression tests passed. Tests cover preprocessing, path/symlink/request/endpoint limits, privacy blocking before model calls, schema parsing, empty responses with usage retention, repeated taxonomy findings, provider failures, deterministic grading, all four report formats, comparison, and the Router adapter.
- A real DeepSeek smoke and both 24-task conditions ran with request model `deepseek-v4-flash-vision-exp`. The API reported response model alias `deepseek-flash`.
- Final image-only results are in `deepseek-image-only/`; final context results are in `deepseek-image-with-context/`; `deepseek-condition-comparison.md` compares them. Every model or grader failure remains in JSONL/CSV/report outputs.
- The reused `01-agent-evaluation` Phoenix container returned `OK`. Project `04-multimodal-agent` contained 98 workflow roots and 583 spans at verification time, with no orphan children, persisted raw inputs/outputs, or sensitive marker hits.

The final live comparison found that context improved classification accuracy from 54.2% to 66.7% and evidence accuracy from 32.6% to 38.9%, while task success stayed at 16.7%, severity accuracy fell from 58.3% to 45.8%, and p95 latency rose from 15.5s to 52.2s. One context request timed out and is retained. Because the runs occurred sequentially and received different cache/peak pricing, their calculated costs are observational, not a controlled price comparison.

The first thinking-enabled image-only run and the first overly strict context-schema run are preserved in `deepseek-image-only-initial-thinking/` and `deepseek-image-with-context-initial-strict-schema/` as audit evidence. `verification-status.json` is the machine-readable verification record. No mock measurement is presented as live output.
