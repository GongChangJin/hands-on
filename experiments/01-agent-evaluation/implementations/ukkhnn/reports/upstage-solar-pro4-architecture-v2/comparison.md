# Agent architecture comparison

| architecture | success | p50 | p95 | tokens | estimated cost | cost coverage | safety violations |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| single | 100.0% | 2071ms | 3564ms | 18,661 | $0.006528 | 100% | 0 |
| handoff | 95.0% | 2651ms | 3927ms | 24,046 | $0.008477 | 100% | 0 |

Task success is determined only by CODE evaluators. Optional LLM evaluator results are recorded as diagnostics and never change task_success.
