# adaptive-context evaluation report

- provider/model: `deepseek` / `deepseek-v4-flash-vision-exp`
- success: 11/24 (45.8%)
- classification/schema/evidence: 87.5% / 100.0% / 64.3%
- latency p50/p95: 2703ms / 4426ms
- provider-reported tokens: 45,974
- calculated model cost: $0.006288 (100% coverage)
- privacy exposures / safety violations: 0 / 0

Cost is calculated from provider-reported tokens and the published rate active at each call; it is not a billing invoice.
Failed results are retained below and in records.jsonl/records.csv.

| task | success | class | schema | evidence | latency ms | tokens | cost USD | failure |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| ui-error-001-adaptive-context | false | 0.00 | 1.00 | 0.80 | 4049 | 2353 | 0.00027147 | classification_mismatch |
| ui-error-002-adaptive-context | false | 0.00 | 1.00 | 0.54 | 2182 | 1243 | 0.00020624 | classification_mismatch |
| ui-error-003-adaptive-context | false | 1.00 | 1.00 | 0.26 | 1746 | 1237 | 0.00020228 | evidence_mismatch |
| ui-error-004-adaptive-context | true | 1.00 | 1.00 | 0.50 | 2054 | 1230 | 0.00019766 | - |
| ui-error-005-adaptive-context | false | 1.00 | 1.00 | 0.77 | 1619 | 1218 | 0.00018974 | severity_mismatch |
| ui-error-006-adaptive-context | false | 1.00 | 1.00 | 0.13 | 2460 | 1316 | 0.00025442 | evidence_mismatch |
| ui-error-007-adaptive-context | true | 1.00 | 1.00 | 0.67 | 2249 | 1256 | 0.00021482 | - |
| ui-error-008-adaptive-context | false | 0.00 | 1.00 | 0.60 | 1914 | 1221 | 0.00019172 | classification_mismatch |
| ui-error-009-adaptive-context | true | 1.00 | 1.00 | 0.57 | 3815 | 2562 | 0.00040941 | - |
| ui-error-010-adaptive-context | false | 1.00 | 1.00 | 0.44 | 3286 | 2478 | 0.00035837 | severity_mismatch |
| ui-error-011-adaptive-context | false | 1.00 | 1.00 | 0.66 | 3300 | 2328 | 0.00025805 | severity_mismatch |
| ui-error-012-adaptive-context | true | 1.00 | 1.00 | 0.67 | 2624 | 2354 | 0.00027433 | - |
| ui-error-013-adaptive-context | true | 1.00 | 1.00 | 0.53 | 1793 | 1203 | 0.00017984 | - |
| ui-error-014-adaptive-context | false | 1.00 | 1.00 | 0.46 | 1586 | 1190 | 0.00017126 | severity_mismatch |
| ui-error-015-adaptive-context | false | 1.00 | 1.00 | 0.37 | 1340 | 1164 | 0.00015410 | evidence_mismatch |
| ui-error-016-adaptive-context | true | 1.00 | 1.00 | 0.73 | 4460 | 2695 | 0.00049543 | - |
| ui-error-017-adaptive-context | false | 1.00 | 1.00 | 0.60 | 4236 | 2566 | 0.00041161 | severity_mismatch |
| ui-error-018-adaptive-context | false | 1.00 | 1.00 | 0.93 | 4502 | 2584 | 0.00042173 | severity_mismatch |
| ui-error-019-adaptive-context | true | 1.00 | 1.00 | 0.83 | 3690 | 2484 | 0.00036013 | - |
| ui-error-020-adaptive-context | false | 1.00 | 1.00 | 0.38 | 3351 | 2425 | 0.00032295 | severity_mismatch |
| ui-normal-021-adaptive-context | true | 1.00 | 1.00 | 1.00 | 2990 | 2199 | 0.00017203 | - |
| ui-normal-022-adaptive-context | true | 1.00 | 1.00 | 1.00 | 2567 | 2216 | 0.00018545 | - |
| ui-normal-023-adaptive-context | true | 1.00 | 1.00 | 1.00 | 2852 | 2212 | 0.00018281 | - |
| ui-normal-024-adaptive-context | true | 1.00 | 1.00 | 1.00 | 2783 | 2240 | 0.00020173 | - |
