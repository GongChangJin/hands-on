# adaptive-context evaluation report

- provider/model: `deepseek` / `deepseek-v4-flash-vision-exp`
- success: 9/24 (37.5%)
- classification/schema/evidence: 75.0% / 100.0% / 60.4%
- latency p50/p95: 2648ms / 4584ms
- provider-reported tokens: 47,187
- calculated model cost: $0.008469 (100% coverage)
- privacy exposures / safety violations: 0 / 0

Cost is calculated from provider-reported tokens and the published rate active at each call; it is not a billing invoice.
Failed results are retained below and in records.jsonl/records.csv.

| task | success | class | schema | evidence | latency ms | tokens | cost USD | failure |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| ui-error-001-adaptive-context | false | 0.00 | 1.00 | 0.80 | 4093 | 2483 | 0.00049359 | classification_mismatch |
| ui-error-002-adaptive-context | false | 0.00 | 1.00 | 0.46 | 1721 | 1234 | 0.00020030 | classification_mismatch |
| ui-error-003-adaptive-context | false | 1.00 | 1.00 | 0.17 | 1888 | 1214 | 0.00018710 | evidence_mismatch |
| ui-error-004-adaptive-context | true | 1.00 | 1.00 | 0.50 | 1574 | 1221 | 0.00019172 | - |
| ui-error-005-adaptive-context | true | 1.00 | 1.00 | 0.57 | 1752 | 1198 | 0.00017654 | - |
| ui-error-006-adaptive-context | false | 1.00 | 1.00 | 0.13 | 2461 | 1312 | 0.00025178 | evidence_mismatch |
| ui-error-007-adaptive-context | false | 0.00 | 1.00 | 0.67 | 2356 | 1358 | 0.00028214 | classification_mismatch |
| ui-error-008-adaptive-context | false | 0.00 | 1.00 | 0.60 | 1812 | 1221 | 0.00019172 | classification_mismatch |
| ui-error-009-adaptive-context | false | 0.00 | 1.00 | 0.57 | 4967 | 2667 | 0.00061503 | classification_mismatch |
| ui-error-010-adaptive-context | false | 1.00 | 1.00 | 0.76 | 4224 | 2524 | 0.00052505 | severity_mismatch |
| ui-error-011-adaptive-context | true | 1.00 | 1.00 | 0.57 | 3015 | 2358 | 0.00041417 | - |
| ui-error-012-adaptive-context | true | 1.00 | 1.00 | 0.60 | 3072 | 2342 | 0.00040273 | - |
| ui-error-013-adaptive-context | false | 1.00 | 1.00 | 0.53 | 1328 | 1171 | 0.00015872 | severity_mismatch |
| ui-error-014-adaptive-context | false | 0.00 | 1.00 | 0.00 | 2866 | 2217 | 0.00032155 | classification_mismatch |
| ui-error-015-adaptive-context | false | 1.00 | 1.00 | 0.37 | 1802 | 1166 | 0.00015542 | evidence_mismatch |
| ui-error-016-adaptive-context | false | 1.00 | 1.00 | 0.53 | 4521 | 2710 | 0.00064165 | severity_mismatch |
| ui-error-017-adaptive-context | false | 1.00 | 1.00 | 0.60 | 4198 | 2571 | 0.00055123 | severity_mismatch |
| ui-error-018-adaptive-context | false | 1.00 | 1.00 | 1.00 | 4595 | 2603 | 0.00057059 | severity_mismatch |
| ui-error-019-adaptive-context | true | 1.00 | 1.00 | 0.57 | 3720 | 2397 | 0.00043903 | - |
| ui-error-020-adaptive-context | false | 1.00 | 1.00 | 0.50 | 3374 | 2401 | 0.00044343 | severity_mismatch |
| ui-normal-021-adaptive-context | true | 1.00 | 1.00 | 1.00 | 2351 | 2199 | 0.00030835 | - |
| ui-normal-022-adaptive-context | true | 1.00 | 1.00 | 1.00 | 2081 | 2203 | 0.00031319 | - |
| ui-normal-023-adaptive-context | true | 1.00 | 1.00 | 1.00 | 2834 | 2186 | 0.00030197 | - |
| ui-normal-024-adaptive-context | true | 1.00 | 1.00 | 1.00 | 1936 | 2231 | 0.00033211 | - |
