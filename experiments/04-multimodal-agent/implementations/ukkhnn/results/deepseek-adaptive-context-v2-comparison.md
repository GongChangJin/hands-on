# DeepSeek input condition comparison

Model: `deepseek-v4-flash-vision-exp`; endpoint provider: `deepseek`; protocol: `openai-compatible`.

| metric | image-only | adaptive-context | adaptive-context - image-only |
| --- | ---: | ---: | ---: |
| success rate | 29.2% | 45.8% | 16.7% |
| classification accuracy | 54.2% | 87.5% | 33.3% |
| schema compliance | 100.0% | 100.0% | 0.0% |
| evidence accuracy | 44.7% | 64.3% | 19.7% |
| severity accuracy | 50.0% | 66.7% | 16.7% |
| latency p50 ms | 1587 | 2703 | 1116 |
| latency p95 ms | 2044 | 4426 | 2382 |
| total tokens | 27916 | 45974 | 18058 |
| calculated cost USD | 0.006357 | 0.006288 | -0.000069 |
| privacy exposures | 0 | 0 | 0 |
| safety violations | 0 | 0 | 0 |

## Retained failures

- image-only: `{"classification_mismatch": 11, "evidence_mismatch": 2, "severity_mismatch": 4}`
- adaptive-context: `{"classification_mismatch": 3, "evidence_mismatch": 3, "severity_mismatch": 7}`

Cost uses provider-reported token usage and the rate active at each call; cache hits and peak/off-peak timing mean the two totals are observational rather than a controlled price comparison. It is not a billing invoice.
