# Agent architecture comparison

| architecture | success | p50 | p95 | tokens | estimated cost | safety violations |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| single | 90.0% | 2009ms | 3565ms | 18,277 | $0.006476 | 0 |
| handoff | 75.0% | 2493ms | 7686ms | 23,048 | N/A | 0 |

Task success is determined only by CODE evaluators. Optional LLM evaluator results are recorded as diagnostics and never change task_success.
