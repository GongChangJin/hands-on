# Agent architecture comparison

| architecture | success | p50 | p95 | tokens | estimated cost | cost coverage | safety violations |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| single | 100.0% | 1280ms | 5309ms | 18,663 | $0.006527 | 100% | 0 |
| handoff | 100.0% | 2082ms | 9695ms | 24,531 | $0.008607 | 100% | 0 |

Task success is determined only by CODE evaluators. Optional LLM evaluator results are recorded as diagnostics and never change task_success.
