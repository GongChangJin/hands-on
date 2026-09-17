# DeepSeek input condition comparison

Model: `deepseek-v4-flash-vision-exp`; endpoint provider: `deepseek`; protocol: `openai-compatible`.

| metric | image-only | image-with-context | context - only |
| --- | ---: | ---: | ---: |
| success rate | 16.7% | 16.7% | 0.0% |
| classification accuracy | 54.2% | 66.7% | 12.5% |
| schema compliance | 100.0% | 95.8% | -4.2% |
| evidence accuracy | 32.6% | 38.9% | 6.4% |
| severity accuracy | 58.3% | 45.8% | -12.5% |
| latency p50 ms | 2087 | 3217 | 1130 |
| latency p95 ms | 15454 | 52228 | 36774 |
| total tokens | 22554 | 23687 | 1133 |
| calculated cost USD | 0.012772 | 0.007863 | -0.004909 |
| privacy exposures | 0 | 0 | 0 |
| safety violations | 0 | 0 | 0 |

## Retained failures

- image-only: `{"classification_mismatch": 11, "evidence_mismatch": 5, "severity_mismatch": 4}`
- image-with-context: `{"classification_mismatch": 7, "evidence_mismatch": 5, "severity_mismatch": 7, "timeout": 1}`

Cost uses provider-reported token usage and the rate active at each call; cache hits and peak/off-peak timing mean the two totals are observational rather than a controlled price comparison. It is not a billing invoice.
