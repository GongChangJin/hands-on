# image-only evaluation report

- provider/model: `deepseek` / `deepseek-v4-flash-vision-exp`
- success: 4/24 (16.7%)
- classification/schema/evidence: 54.2% / 100.0% / 32.6%
- latency p50/p95: 2087ms / 15454ms
- provider-reported tokens: 22,554
- calculated model cost: $0.012772 (100% coverage)
- privacy exposures / safety violations: 0 / 0

Cost is calculated from provider-reported tokens and the published rate active at each call; it is not a billing invoice.
Failed results are retained below and in records.jsonl/records.csv.

| task | success | class | schema | evidence | latency ms | tokens | cost USD | failure |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| ui-error-001-image-only | false | 0.00 | 1.00 | 0.00 | 2078 | 875 | 0.00018540 | classification_mismatch |
| ui-error-002-image-only | false | 0.00 | 1.00 | 0.54 | 17607 | 1010 | 0.00063624 | classification_mismatch |
| ui-error-003-image-only | false | 1.00 | 1.00 | 0.26 | 2447 | 987 | 0.00060588 | evidence_mismatch |
| ui-error-004-image-only | true | 1.00 | 1.00 | 0.50 | 2971 | 1018 | 0.00064680 | - |
| ui-error-005-image-only | false | 1.00 | 1.00 | 0.67 | 1939 | 970 | 0.00058344 | severity_mismatch |
| ui-error-006-image-only | false | 0.00 | 1.00 | 0.07 | 1925 | 982 | 0.00059928 | classification_mismatch |
| ui-error-007-image-only | true | 1.00 | 1.00 | 0.67 | 3251 | 1040 | 0.00067584 | - |
| ui-error-008-image-only | false | 0.00 | 1.00 | 0.70 | 2093 | 1003 | 0.00062700 | classification_mismatch |
| ui-error-009-image-only | true | 1.00 | 1.00 | 0.66 | 3031 | 1040 | 0.00067584 | - |
| ui-error-010-image-only | false | 1.00 | 1.00 | 0.56 | 2223 | 1019 | 0.00064812 | severity_mismatch |
| ui-error-011-image-only | true | 1.00 | 1.00 | 0.74 | 1878 | 970 | 0.00058344 | - |
| ui-error-012-image-only | false | 0.00 | 1.00 | 0.00 | 2203 | 848 | 0.00042240 | classification_mismatch |
| ui-error-013-image-only | false | 0.00 | 1.00 | 0.00 | 1620 | 842 | 0.00041448 | classification_mismatch |
| ui-error-014-image-only | false | 0.00 | 1.00 | 0.00 | 23029 | 847 | 0.00042108 | classification_mismatch |
| ui-error-015-image-only | false | 1.00 | 1.00 | 0.46 | 1543 | 946 | 0.00055176 | severity_mismatch |
| ui-error-016-image-only | false | 0.00 | 1.00 | 0.73 | 2313 | 994 | 0.00061512 | classification_mismatch |
| ui-error-017-image-only | false | 1.00 | 1.00 | 0.53 | 2072 | 1004 | 0.00062832 | severity_mismatch |
| ui-error-018-image-only | false | 0.00 | 1.00 | 0.73 | 2080 | 1031 | 0.00066396 | classification_mismatch |
| ui-error-019-image-only | false | 0.00 | 1.00 | 0.00 | 1468 | 846 | 0.00041976 | classification_mismatch |
| ui-error-020-image-only | false | 0.00 | 1.00 | 0.00 | 1527 | 879 | 0.00046332 | classification_mismatch |
| ui-normal-021-image-only | false | 1.00 | 1.00 | 0.00 | 1272 | 846 | 0.00041976 | evidence_mismatch |
| ui-normal-022-image-only | false | 1.00 | 1.00 | 0.00 | 1949 | 848 | 0.00042240 | evidence_mismatch |
| ui-normal-023-image-only | false | 1.00 | 1.00 | 0.00 | 2426 | 861 | 0.00043956 | evidence_mismatch |
| ui-normal-024-image-only | false | 1.00 | 1.00 | 0.00 | 3113 | 848 | 0.00042240 | evidence_mismatch |
