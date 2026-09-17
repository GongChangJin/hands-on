# image-with-context evaluation report

- provider/model: `deepseek` / `deepseek-v4-flash-vision-exp`
- success: 4/24 (16.7%)
- classification/schema/evidence: 66.7% / 95.8% / 38.9%
- latency p50/p95: 3217ms / 52228ms
- provider-reported tokens: 23,687
- calculated model cost: $0.007863 (96% coverage)
- privacy exposures / safety violations: 0 / 0

Cost is calculated from provider-reported tokens and the published rate active at each call; it is not a billing invoice.
Failed results are retained below and in records.jsonl/records.csv.

| task | success | class | schema | evidence | latency ms | tokens | cost USD | failure |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| ui-error-001-image-with-context | false | 0.00 | 1.00 | 0.00 | 4502 | 918 | 0.00019024 | classification_mismatch |
| ui-error-002-image-with-context | false | 0.00 | 1.00 | 0.46 | 4637 | 1029 | 0.00033676 | classification_mismatch |
| ui-error-003-image-with-context | false | 1.00 | 1.00 | 0.57 | 2338 | 1062 | 0.00038208 | severity_mismatch |
| ui-error-004-image-with-context | false | 0.00 | 1.00 | 0.60 | 4539 | 1204 | 0.00057216 | classification_mismatch |
| ui-error-005-image-with-context | true | 1.00 | 1.00 | 0.57 | 3579 | 1043 | 0.00035876 | - |
| ui-error-006-image-with-context | false | 0.00 | 1.00 | 0.47 | 3964 | 1013 | 0.00032268 | classification_mismatch |
| ui-error-007-image-with-context | true | 1.00 | 1.00 | 0.57 | 2604 | 1072 | 0.00039704 | - |
| ui-error-008-image-with-context | false | 1.00 | 1.00 | 0.60 | 5060 | 1190 | 0.00055368 | severity_mismatch |
| ui-error-009-image-with-context | false | 1.00 | 1.00 | 0.57 | 3154 | 1091 | 0.00041860 | severity_mismatch |
| ui-error-010-image-with-context | true | 1.00 | 1.00 | 0.52 | 5012 | 1115 | 0.00045908 | - |
| ui-error-011-image-with-context | false | 1.00 | 1.00 | 0.66 | 5189 | 1034 | 0.00034952 | severity_mismatch |
| ui-error-012-image-with-context | false | 1.00 | 1.00 | 0.47 | 2980 | 1071 | 0.00039660 | evidence_mismatch |
| ui-error-013-image-with-context | false | 0.00 | 1.00 | 0.00 | 1422 | 898 | 0.00016824 | classification_mismatch |
| ui-error-014-image-with-context | false | 0.00 | 1.00 | 0.00 | 1487 | 901 | 0.00017484 | classification_mismatch |
| ui-error-015-image-with-context | false | 0.00 | 0.00 | 0.00 | 60343 | 0 | N/A | timeout |
| ui-error-016-image-with-context | false | 0.00 | 1.00 | 0.67 | 2914 | 1064 | 0.00037944 | classification_mismatch |
| ui-error-017-image-with-context | true | 1.00 | 1.00 | 0.53 | 2751 | 1071 | 0.00039132 | - |
| ui-error-018-image-with-context | false | 1.00 | 1.00 | 0.93 | 2977 | 1069 | 0.00038516 | severity_mismatch |
| ui-error-019-image-with-context | false | 1.00 | 1.00 | 0.61 | 3281 | 1155 | 0.00050748 | severity_mismatch |
| ui-error-020-image-with-context | false | 1.00 | 1.00 | 0.56 | 2272 | 1062 | 0.00038824 | severity_mismatch |
| ui-normal-021-image-with-context | false | 1.00 | 1.00 | 0.00 | 1549 | 897 | 0.00016692 | evidence_mismatch |
| ui-normal-022-image-with-context | false | 1.00 | 1.00 | 0.00 | 2588 | 904 | 0.00018056 | evidence_mismatch |
| ui-normal-023-image-with-context | false | 1.00 | 1.00 | 0.00 | 6243 | 910 | 0.00018848 | evidence_mismatch |
| ui-normal-024-image-with-context | false | 1.00 | 1.00 | 0.00 | 73183 | 914 | 0.00019464 | evidence_mismatch |
