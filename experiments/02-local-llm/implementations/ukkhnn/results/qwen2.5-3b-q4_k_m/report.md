# qwen2.5:3b benchmark

- adapter: `ollama`
- success: 60/72 (83.3%)
- JSON schema: 72/72 (100.0%)
- total latency p50/p95: 369.5ms / 757.4ms
- first token p50/p95: 178.6ms / 205.3ms
- generation: 89.1 tokens/s
- measured request cost: $0.000000 (100% coverage)
- safety violations: 0

| task | repetition | success | schema | latency ms | first token ms | tokens/s | failure |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| local-cls-sentiment-01 | 1 | true | true | 584 | 417.7 | 93.5 | - |
| local-cls-sentiment-02 | 1 | true | true | 323 | 151.7 | 92.6 | - |
| local-cls-sentiment-03 | 1 | true | true | 325 | 146.6 | 88.1 | - |
| local-cls-sentiment-04 | 1 | false | true | 265 | 146.2 | 91.3 | answer_mismatch |
| local-cls-intent-01 | 1 | true | true | 373 | 178.9 | 89.6 | - |
| local-cls-intent-02 | 1 | true | true | 328 | 148.0 | 87.4 | - |
| local-cls-intent-03 | 1 | true | true | 349 | 147.8 | 84.3 | - |
| local-cls-intent-04 | 1 | true | true | 339 | 145.3 | 85.3 | - |
| local-extract-01 | 1 | true | true | 584 | 179.1 | 87.9 | - |
| local-extract-02 | 1 | true | true | 528 | 178.0 | 87.1 | - |
| local-extract-03 | 1 | true | true | 741 | 185.0 | 87.6 | - |
| local-extract-04 | 1 | true | true | 749 | 209.5 | 85.2 | - |
| local-extract-05 | 1 | true | true | 508 | 178.8 | 86.5 | - |
| local-extract-06 | 1 | true | true | 622 | 188.7 | 86.6 | - |
| local-extract-07 | 1 | true | true | 592 | 202.3 | 87.6 | - |
| local-extract-08 | 1 | true | true | 511 | 189.2 | 87.5 | - |
| local-qa-01 | 1 | false | true | 369 | 179.6 | 91.2 | answer_mismatch |
| local-qa-02 | 1 | false | true | 400 | 150.8 | 90.1 | answer_mismatch |
| local-qa-03 | 1 | false | true | 346 | 181.0 | 94.0 | answer_mismatch |
| local-qa-04 | 1 | true | true | 347 | 153.4 | 92.0 | - |
| local-qa-05 | 1 | true | true | 348 | 181.8 | 94.5 | - |
| local-qa-06 | 1 | true | true | 287 | 148.1 | 88.4 | - |
| local-qa-07 | 1 | true | true | 370 | 147.2 | 88.0 | - |
| local-qa-08 | 1 | true | true | 354 | 146.0 | 92.1 | - |
| local-cls-sentiment-01 | 2 | true | true | 348 | 180.0 | 93.6 | - |
| local-cls-sentiment-02 | 2 | true | true | 320 | 153.1 | 94.5 | - |
| local-cls-sentiment-03 | 2 | true | true | 327 | 148.6 | 85.8 | - |
| local-cls-sentiment-04 | 2 | false | true | 259 | 146.6 | 94.8 | answer_mismatch |
| local-cls-intent-01 | 2 | true | true | 367 | 180.6 | 90.7 | - |
| local-cls-intent-02 | 2 | true | true | 320 | 152.7 | 92.6 | - |
| local-cls-intent-03 | 2 | true | true | 335 | 147.6 | 90.2 | - |
| local-cls-intent-04 | 2 | true | true | 338 | 147.3 | 89.6 | - |
| local-extract-01 | 2 | true | true | 598 | 183.8 | 84.7 | - |
| local-extract-02 | 2 | true | true | 538 | 186.9 | 88.8 | - |
| local-extract-03 | 2 | true | true | 769 | 179.0 | 84.3 | - |
| local-extract-04 | 2 | true | true | 771 | 204.9 | 84.4 | - |
| local-extract-05 | 2 | true | true | 529 | 181.6 | 85.2 | - |
| local-extract-06 | 2 | true | true | 636 | 182.5 | 85.8 | - |
| local-extract-07 | 2 | true | true | 622 | 213.7 | 86.2 | - |
| local-extract-08 | 2 | true | true | 519 | 182.8 | 87.2 | - |
| local-qa-01 | 2 | false | true | 381 | 183.9 | 91.1 | answer_mismatch |
| local-qa-02 | 2 | false | true | 413 | 154.6 | 88.5 | answer_mismatch |
| local-qa-03 | 2 | false | true | 352 | 178.4 | 91.6 | answer_mismatch |
| local-qa-04 | 2 | true | true | 352 | 148.6 | 89.3 | - |
| local-qa-05 | 2 | true | true | 361 | 180.8 | 88.0 | - |
| local-qa-06 | 2 | true | true | 286 | 149.2 | 93.5 | - |
| local-qa-07 | 2 | true | true | 382 | 159.3 | 91.7 | - |
| local-qa-08 | 2 | true | true | 369 | 157.1 | 92.3 | - |
| local-cls-sentiment-01 | 3 | true | true | 357 | 187.1 | 94.7 | - |
| local-cls-sentiment-02 | 3 | true | true | 325 | 155.9 | 94.4 | - |
| local-cls-sentiment-03 | 3 | true | true | 327 | 150.0 | 90.0 | - |
| local-cls-sentiment-04 | 3 | false | true | 271 | 149.6 | 90.5 | answer_mismatch |
| local-cls-intent-01 | 3 | true | true | 375 | 180.2 | 89.2 | - |
| local-cls-intent-02 | 3 | true | true | 327 | 148.4 | 89.7 | - |
| local-cls-intent-03 | 3 | true | true | 342 | 147.5 | 90.3 | - |
| local-cls-intent-04 | 3 | true | true | 350 | 148.4 | 87.2 | - |
| local-extract-01 | 3 | true | true | 614 | 182.6 | 85.2 | - |
| local-extract-02 | 3 | true | true | 550 | 180.6 | 86.7 | - |
| local-extract-03 | 3 | true | true | 789 | 187.6 | 83.6 | - |
| local-extract-04 | 3 | true | true | 767 | 205.9 | 85.4 | - |
| local-extract-05 | 3 | true | true | 519 | 178.5 | 84.6 | - |
| local-extract-06 | 3 | true | true | 639 | 184.9 | 83.4 | - |
| local-extract-07 | 3 | true | true | 605 | 204.4 | 87.0 | - |
| local-extract-08 | 3 | true | true | 510 | 187.7 | 90.3 | - |
| local-qa-01 | 3 | false | true | 375 | 182.0 | 90.7 | answer_mismatch |
| local-qa-02 | 3 | false | true | 404 | 153.9 | 90.4 | answer_mismatch |
| local-qa-03 | 3 | false | true | 351 | 182.9 | 92.1 | answer_mismatch |
| local-qa-04 | 3 | true | true | 353 | 155.0 | 91.6 | - |
| local-qa-05 | 3 | true | true | 356 | 188.3 | 94.5 | - |
| local-qa-06 | 3 | true | true | 294 | 150.6 | 86.9 | - |
| local-qa-07 | 3 | true | true | 371 | 149.1 | 90.4 | - |
| local-qa-08 | 3 | true | true | 371 | 147.6 | 85.0 | - |
