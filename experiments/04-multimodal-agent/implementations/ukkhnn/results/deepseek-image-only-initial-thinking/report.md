# image-only evaluation report

- provider/model: `deepseek` / `deepseek-v4-flash-vision-exp`
- success: 3/24 (12.5%)
- classification/schema/evidence: 50.0% / 66.7% / 28.6%
- latency p50/p95: 6245ms / 9900ms
- provider-reported tokens: 29,714
- calculated model cost: $0.025579 (79% coverage)
- privacy exposures / safety violations: 0 / 0

Cost is calculated from provider-reported tokens and the published rate active at each call; it is not a billing invoice.
Failed results are retained below and in records.jsonl/records.csv.

| task | success | class | schema | evidence | latency ms | tokens | cost USD | failure |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| ui-error-001-image-only | false | 0.00 | 0.00 | 0.00 | 7556 | 0 | N/A | empty_response |
| ui-error-002-image-only | false | 0.00 | 0.00 | 0.00 | 7770 | 2016 | 0.00194304 | output_parse_error |
| ui-error-003-image-only | false | 1.00 | 1.00 | 0.26 | 6203 | 1490 | 0.00124872 | evidence_mismatch |
| ui-error-004-image-only | false | 0.00 | 1.00 | 0.60 | 6301 | 1560 | 0.00134112 | classification_mismatch |
| ui-error-005-image-only | false | 1.00 | 1.00 | 0.67 | 4523 | 1493 | 0.00125268 | severity_mismatch |
| ui-error-006-image-only | false | 0.00 | 0.00 | 0.00 | 7809 | 2016 | 0.00194304 | output_parse_error |
| ui-error-007-image-only | true | 1.00 | 1.00 | 0.50 | 6083 | 1709 | 0.00153780 | - |
| ui-error-008-image-only | false | 0.00 | 1.00 | 0.57 | 5439 | 1682 | 0.00150216 | classification_mismatch |
| ui-error-009-image-only | false | 1.00 | 1.00 | 0.66 | 4743 | 1374 | 0.00109560 | severity_mismatch |
| ui-error-010-image-only | true | 1.00 | 1.00 | 0.76 | 4046 | 1427 | 0.00116556 | - |
| ui-error-011-image-only | true | 1.00 | 1.00 | 0.74 | 4906 | 1548 | 0.00132528 | - |
| ui-error-012-image-only | false | 0.00 | 1.00 | 0.00 | 6934 | 1947 | 0.00185196 | classification_mismatch |
| ui-error-013-image-only | false | 1.00 | 1.00 | 0.53 | 15710 | 1436 | 0.00117744 | severity_mismatch |
| ui-error-014-image-only | false | 0.00 | 0.00 | 0.00 | 6288 | 0 | N/A | empty_response |
| ui-error-015-image-only | false | 1.00 | 1.00 | 0.37 | 6500 | 1883 | 0.00176748 | evidence_mismatch |
| ui-error-016-image-only | false | 0.00 | 1.00 | 0.53 | 3726 | 1345 | 0.00105732 | classification_mismatch |
| ui-error-017-image-only | false | 1.00 | 1.00 | 0.67 | 5084 | 1442 | 0.00118536 | severity_mismatch |
| ui-error-018-image-only | false | 0.00 | 0.00 | 0.00 | 10241 | 0 | N/A | empty_response |
| ui-error-019-image-only | false | 0.00 | 0.00 | 0.00 | 7968 | 0 | N/A | empty_response |
| ui-error-020-image-only | false | 0.00 | 0.00 | 0.00 | 7479 | 0 | N/A | empty_response |
| ui-normal-021-image-only | false | 1.00 | 1.00 | 0.00 | 2559 | 1136 | 0.00078144 | evidence_mismatch |
| ui-normal-022-image-only | false | 1.00 | 1.00 | 0.00 | 2532 | 1094 | 0.00072600 | evidence_mismatch |
| ui-normal-023-image-only | false | 1.00 | 1.00 | 0.00 | 2972 | 1100 | 0.00073392 | evidence_mismatch |
| ui-normal-024-image-only | false | 0.00 | 0.00 | 0.00 | 7685 | 2016 | 0.00194304 | output_parse_error |
