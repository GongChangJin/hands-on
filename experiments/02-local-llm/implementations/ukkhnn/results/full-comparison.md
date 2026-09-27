# Local and API LLM comparison

| adapter / model | success | JSON schema | p50 | p95 | first token p50 | tokens/s | model memory | request cost |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| ollama / `qwen2.5:3b` | 83.3% | 100.0% | 369.5ms | 757.4ms | 178.6ms | 89.1 | 2.16 GiB | $0.000000 |
| ollama / `qwen2.5:latest` | 95.8% | 100.0% | 573.6ms | 1,241.3ms | 336.4ms | 48.5 | 4.48 GiB | $0.000000 |
| api / `solar-pro4` | 100.0% | 100.0% | 520.9ms | 954.5ms | N/A | N/A | N/A | $0.001582 |

`success` requires both a valid schema and an exact deterministic answer. Local request cost is recorded as $0; hardware and electricity are not estimated.
