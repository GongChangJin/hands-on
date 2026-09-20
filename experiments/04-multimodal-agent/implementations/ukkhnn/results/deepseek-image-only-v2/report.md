# image-only evaluation report

- provider/model: `deepseek` / `deepseek-v4-flash-vision-exp`
- success: 7/24 (29.2%)
- classification/schema/evidence: 54.2% / 100.0% / 44.7%
- latency p50/p95: 1587ms / 2044ms
- provider-reported tokens: 27,916
- calculated model cost: $0.006357 (100% coverage)
- privacy exposures / safety violations: 0 / 0

Cost is calculated from provider-reported tokens and the published rate active at each call; it is not a billing invoice.
Failed results are retained below and in records.jsonl/records.csv.

| task | success | class | schema | evidence | latency ms | tokens | cost USD | failure |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| ui-error-001-image-only | false | 0.00 | 1.00 | 0.00 | 1831 | 1115 | 0.00028534 | classification_mismatch |
| ui-error-002-image-only | false | 0.00 | 1.00 | 0.71 | 1698 | 1226 | 0.00030407 | classification_mismatch |
| ui-error-003-image-only | false | 0.00 | 1.00 | 0.00 | 1380 | 1084 | 0.00021035 | classification_mismatch |
| ui-error-004-image-only | true | 1.00 | 1.00 | 0.50 | 2016 | 1228 | 0.00030539 | - |
| ui-error-005-image-only | true | 1.00 | 1.00 | 0.77 | 1534 | 1214 | 0.00029615 | - |
| ui-error-006-image-only | false | 1.00 | 1.00 | 0.13 | 1884 | 1311 | 0.00036017 | evidence_mismatch |
| ui-error-007-image-only | false | 0.00 | 1.00 | 0.67 | 2517 | 1362 | 0.00039383 | classification_mismatch |
| ui-error-008-image-only | false | 0.00 | 1.00 | 0.60 | 1950 | 1230 | 0.00030671 | classification_mismatch |
| ui-error-009-image-only | true | 1.00 | 1.00 | 0.66 | 1713 | 1210 | 0.00029351 | - |
| ui-error-010-image-only | false | 1.00 | 1.00 | 0.44 | 1971 | 1246 | 0.00031727 | severity_mismatch |
| ui-error-011-image-only | false | 0.00 | 1.00 | 0.00 | 1020 | 1074 | 0.00020375 | classification_mismatch |
| ui-error-012-image-only | false | 0.00 | 1.00 | 0.00 | 1211 | 1090 | 0.00021431 | classification_mismatch |
| ui-error-013-image-only | false | 1.00 | 1.00 | 0.53 | 1652 | 1191 | 0.00028097 | severity_mismatch |
| ui-error-014-image-only | false | 0.00 | 1.00 | 0.00 | 1330 | 1085 | 0.00021101 | classification_mismatch |
| ui-error-015-image-only | false | 1.00 | 1.00 | 0.37 | 1641 | 1173 | 0.00026909 | evidence_mismatch |
| ui-error-016-image-only | false | 1.00 | 1.00 | 0.73 | 2049 | 1275 | 0.00033641 | severity_mismatch |
| ui-error-017-image-only | false | 1.00 | 1.00 | 0.60 | 1838 | 1221 | 0.00030077 | severity_mismatch |
| ui-error-018-image-only | false | 0.00 | 1.00 | 0.00 | 1246 | 1084 | 0.00021035 | classification_mismatch |
| ui-error-019-image-only | false | 0.00 | 1.00 | 0.00 | 1114 | 1083 | 0.00020969 | classification_mismatch |
| ui-error-020-image-only | false | 0.00 | 1.00 | 0.00 | 1329 | 1082 | 0.00020903 | classification_mismatch |
| ui-normal-021-image-only | true | 1.00 | 1.00 | 1.00 | 1216 | 1083 | 0.00020969 | - |
| ui-normal-022-image-only | true | 1.00 | 1.00 | 1.00 | 1309 | 1082 | 0.00020903 | - |
| ui-normal-023-image-only | true | 1.00 | 1.00 | 1.00 | 1312 | 1085 | 0.00021101 | - |
| ui-normal-024-image-only | true | 1.00 | 1.00 | 1.00 | 1072 | 1082 | 0.00020903 | - |
