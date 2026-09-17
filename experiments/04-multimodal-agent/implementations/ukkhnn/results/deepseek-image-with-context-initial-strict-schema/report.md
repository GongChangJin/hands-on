# image-with-context evaluation report

- provider/model: `deepseek` / `deepseek-v4-flash-vision-exp`
- success: 4/24 (16.7%)
- classification/schema/evidence: 62.5% / 95.8% / 40.7%
- latency p50/p95: 4218ms / 14254ms
- provider-reported tokens: 24,889
- calculated model cost: $0.014972 (100% coverage)
- privacy exposures / safety violations: 0 / 0

Cost is calculated from provider-reported tokens and the published rate active at each call; it is not a billing invoice.
Failed results are retained below and in records.jsonl/records.csv.

| task | success | class | schema | evidence | latency ms | tokens | cost USD | failure |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| ui-error-001-image-with-context | false | 0.00 | 1.00 | 0.80 | 9961 | 1087 | 0.00068596 | classification_mismatch |
| ui-error-002-image-with-context | false | 0.00 | 1.00 | 0.46 | 9947 | 1028 | 0.00060808 | classification_mismatch |
| ui-error-003-image-with-context | false | 1.00 | 1.00 | 0.66 | 2538 | 1061 | 0.00065340 | severity_mismatch |
| ui-error-004-image-with-context | true | 1.00 | 1.00 | 0.50 | 2445 | 1140 | 0.00076032 | - |
| ui-error-005-image-with-context | true | 1.00 | 1.00 | 0.57 | 2740 | 1043 | 0.00063140 | - |
| ui-error-006-image-with-context | false | 0.00 | 1.00 | 0.60 | 4626 | 1065 | 0.00066396 | classification_mismatch |
| ui-error-007-image-with-context | false | 0.00 | 1.00 | 0.57 | 3837 | 1179 | 0.00081092 | classification_mismatch |
| ui-error-008-image-with-context | false | 1.00 | 1.00 | 0.60 | 49111 | 1189 | 0.00082500 | severity_mismatch |
| ui-error-009-image-with-context | false | 1.00 | 1.00 | 0.57 | 1938 | 1078 | 0.00067408 | severity_mismatch |
| ui-error-010-image-with-context | true | 1.00 | 1.00 | 0.56 | 15011 | 1074 | 0.00067760 | - |
| ui-error-011-image-with-context | false | 1.00 | 1.00 | 0.66 | 6308 | 1023 | 0.00060764 | severity_mismatch |
| ui-error-012-image-with-context | false | 1.00 | 1.00 | 0.47 | 5824 | 1062 | 0.00065736 | evidence_mismatch |
| ui-error-013-image-with-context | false | 0.00 | 1.00 | 0.00 | 9899 | 897 | 0.00043956 | classification_mismatch |
| ui-error-014-image-with-context | false | 0.00 | 1.00 | 0.00 | 3120 | 901 | 0.00044748 | classification_mismatch |
| ui-error-015-image-with-context | false | 0.00 | 1.00 | 0.00 | 4815 | 903 | 0.00044396 | classification_mismatch |
| ui-error-016-image-with-context | false | 0.00 | 1.00 | 0.73 | 7733 | 1053 | 0.00063756 | classification_mismatch |
| ui-error-017-image-with-context | true | 1.00 | 1.00 | 0.53 | 2883 | 1079 | 0.00067452 | - |
| ui-error-018-image-with-context | false | 1.00 | 1.00 | 0.93 | 2970 | 1073 | 0.00066308 | severity_mismatch |
| ui-error-019-image-with-context | false | 0.00 | 0.00 | 0.00 | 5945 | 1249 | 0.00090420 | output_parse_error |
| ui-error-020-image-with-context | false | 1.00 | 1.00 | 0.56 | 2380 | 1072 | 0.00067408 | severity_mismatch |
| ui-normal-021-image-with-context | false | 1.00 | 1.00 | 0.00 | 4598 | 905 | 0.00045012 | evidence_mismatch |
| ui-normal-022-image-with-context | false | 1.00 | 1.00 | 0.00 | 1975 | 904 | 0.00045320 | evidence_mismatch |
| ui-normal-023-image-with-context | false | 1.00 | 1.00 | 0.00 | 1883 | 910 | 0.00046112 | evidence_mismatch |
| ui-normal-024-image-with-context | false | 1.00 | 1.00 | 0.00 | 1745 | 914 | 0.00046728 | evidence_mismatch |
