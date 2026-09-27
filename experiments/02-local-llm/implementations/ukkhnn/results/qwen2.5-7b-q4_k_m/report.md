# qwen2.5:latest benchmark

- adapter: `ollama`
- success: 69/72 (95.8%)
- JSON schema: 72/72 (100.0%)
- total latency p50/p95: 573.6ms / 1,241.3ms
- first token p50/p95: 336.4ms / 410.7ms
- generation: 48.5 tokens/s
- measured request cost: $0.000000 (100% coverage)
- safety violations: 0

| task | repetition | success | schema | latency ms | first token ms | tokens/s | failure |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| local-cls-sentiment-01 | 1 | true | true | 751 | 575.3 | 52.1 | - |
| local-cls-sentiment-02 | 1 | true | true | 451 | 275.2 | 52.3 | - |
| local-cls-sentiment-03 | 1 | true | true | 453 | 276.3 | 52.0 | - |
| local-cls-sentiment-04 | 1 | true | true | 549 | 273.4 | 47.8 | - |
| local-cls-intent-01 | 1 | true | true | 640 | 339.4 | 48.2 | - |
| local-cls-intent-02 | 1 | true | true | 543 | 270.3 | 48.4 | - |
| local-cls-intent-03 | 1 | true | true | 578 | 276.8 | 48.4 | - |
| local-cls-intent-04 | 1 | true | true | 572 | 267.8 | 47.4 | - |
| local-extract-01 | 1 | true | true | 996 | 344.6 | 45.7 | - |
| local-extract-02 | 1 | true | true | 900 | 339.8 | 46.0 | - |
| local-extract-03 | 1 | true | true | 1245 | 347.8 | 44.7 | - |
| local-extract-04 | 1 | true | true | 1275 | 412.5 | 45.4 | - |
| local-extract-05 | 1 | true | true | 876 | 342.6 | 45.6 | - |
| local-extract-06 | 1 | true | true | 1032 | 340.4 | 45.5 | - |
| local-extract-07 | 1 | true | true | 1042 | 408.7 | 46.0 | - |
| local-extract-08 | 1 | true | true | 1116 | 343.8 | 44.9 | - |
| local-qa-01 | 1 | false | true | 549 | 335.4 | 49.5 | answer_mismatch |
| local-qa-02 | 1 | true | true | 575 | 275.1 | 49.2 | - |
| local-qa-03 | 1 | true | true | 611 | 337.4 | 47.5 | - |
| local-qa-04 | 1 | true | true | 484 | 267.9 | 50.2 | - |
| local-qa-05 | 1 | true | true | 518 | 343.6 | 52.3 | - |
| local-qa-06 | 1 | true | true | 486 | 276.0 | 51.7 | - |
| local-qa-07 | 1 | true | true | 531 | 280.4 | 51.3 | - |
| local-qa-08 | 1 | true | true | 516 | 272.4 | 49.1 | - |
| local-cls-sentiment-01 | 2 | true | true | 514 | 334.8 | 51.0 | - |
| local-cls-sentiment-02 | 2 | true | true | 450 | 269.1 | 50.1 | - |
| local-cls-sentiment-03 | 2 | true | true | 446 | 271.3 | 52.2 | - |
| local-cls-sentiment-04 | 2 | true | true | 537 | 272.3 | 49.7 | - |
| local-cls-intent-01 | 2 | true | true | 641 | 338.4 | 47.4 | - |
| local-cls-intent-02 | 2 | true | true | 541 | 273.0 | 49.0 | - |
| local-cls-intent-03 | 2 | true | true | 569 | 274.8 | 49.4 | - |
| local-cls-intent-04 | 2 | true | true | 577 | 275.6 | 47.6 | - |
| local-extract-01 | 2 | true | true | 973 | 335.8 | 46.5 | - |
| local-extract-02 | 2 | true | true | 893 | 344.3 | 47.0 | - |
| local-extract-03 | 2 | true | true | 1233 | 345.0 | 45.2 | - |
| local-extract-04 | 2 | true | true | 1260 | 408.8 | 45.9 | - |
| local-extract-05 | 2 | true | true | 864 | 339.8 | 46.5 | - |
| local-extract-06 | 2 | true | true | 1019 | 342.8 | 46.4 | - |
| local-extract-07 | 2 | true | true | 1041 | 409.2 | 45.8 | - |
| local-extract-08 | 2 | true | true | 1106 | 345.4 | 45.7 | - |
| local-qa-01 | 2 | false | true | 548 | 338.8 | 51.5 | answer_mismatch |
| local-qa-02 | 2 | true | true | 584 | 274.9 | 47.8 | - |
| local-qa-03 | 2 | true | true | 611 | 339.5 | 48.5 | - |
| local-qa-04 | 2 | true | true | 498 | 273.4 | 48.5 | - |
| local-qa-05 | 2 | true | true | 517 | 339.9 | 51.9 | - |
| local-qa-06 | 2 | true | true | 480 | 273.0 | 51.4 | - |
| local-qa-07 | 2 | true | true | 534 | 277.3 | 48.1 | - |
| local-qa-08 | 2 | true | true | 514 | 267.8 | 48.2 | - |
| local-cls-sentiment-01 | 3 | true | true | 525 | 343.1 | 50.6 | - |
| local-cls-sentiment-02 | 3 | true | true | 454 | 269.1 | 49.5 | - |
| local-cls-sentiment-03 | 3 | true | true | 448 | 269.2 | 51.1 | - |
| local-cls-sentiment-04 | 3 | true | true | 542 | 273.1 | 49.3 | - |
| local-cls-intent-01 | 3 | true | true | 643 | 340.5 | 47.7 | - |
| local-cls-intent-02 | 3 | true | true | 542 | 274.0 | 49.5 | - |
| local-cls-intent-03 | 3 | true | true | 571 | 268.4 | 47.8 | - |
| local-cls-intent-04 | 3 | true | true | 585 | 277.4 | 47.0 | - |
| local-extract-01 | 3 | true | true | 991 | 339.6 | 45.8 | - |
| local-extract-02 | 3 | true | true | 902 | 336.9 | 45.6 | - |
| local-extract-03 | 3 | true | true | 1238 | 345.5 | 45.2 | - |
| local-extract-04 | 3 | true | true | 1291 | 418.3 | 45.0 | - |
| local-extract-05 | 3 | true | true | 869 | 349.2 | 46.9 | - |
| local-extract-06 | 3 | true | true | 1031 | 349.7 | 46.3 | - |
| local-extract-07 | 3 | true | true | 1053 | 423.9 | 46.7 | - |
| local-extract-08 | 3 | true | true | 1096 | 344.2 | 46.7 | - |
| local-qa-01 | 3 | false | true | 545 | 338.5 | 52.3 | answer_mismatch |
| local-qa-02 | 3 | true | true | 565 | 271.6 | 51.4 | - |
| local-qa-03 | 3 | true | true | 604 | 344.9 | 51.5 | - |
| local-qa-04 | 3 | true | true | 492 | 276.9 | 51.2 | - |
| local-qa-05 | 3 | true | true | 523 | 351.4 | 54.0 | - |
| local-qa-06 | 3 | true | true | 484 | 271.5 | 49.8 | - |
| local-qa-07 | 3 | true | true | 523 | 275.0 | 49.7 | - |
| local-qa-08 | 3 | true | true | 513 | 271.5 | 49.5 | - |
