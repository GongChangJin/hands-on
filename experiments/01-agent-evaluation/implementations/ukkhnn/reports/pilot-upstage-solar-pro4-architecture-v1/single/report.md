# single experiment report

- provider/model: `upstage` / `solar-pro4`
- success: 18/20 (90.0%)
- latency p50/p95: 2009ms / 3565ms
- tokens: 18,277
- estimated model cost: $0.006476
- safety violations: 0

| task | success | latency ms | tool accuracy | failure |
| --- | ---: | ---: | ---: | --- |
| combined-large-add | true | 2285 | 1.00 | - |
| combined-divide | true | 2028 | 1.00 | - |
| combined-parentheses | false | 1493 | 1.00 | answer_mismatch |
| combined-multiply | true | 4250 | 1.00 | - |
| combined-power | true | 3521 | 1.00 | - |
| project-active-check | true | 3529 | 1.00 | - |
| project-paraphrase | true | 1932 | 1.00 | - |
| project-purpose | true | 2326 | 1.00 | - |
| project-status | true | 1803 | 1.00 | - |
| project-full | true | 2399 | 1.00 | - |
| calc-square | true | 2237 | 1.00 | - |
| calc-large-add | true | 1553 | 1.00 | - |
| calc-parentheses | true | 2684 | 1.00 | - |
| calc-decimal | true | 1783 | 1.00 | - |
| calc-power | false | 3180 | 1.00 | answer_mismatch |
| calc-precedence | true | 1712 | 1.00 | - |
| calc-divide | true | 1112 | 1.00 | - |
| calc-add | true | 1990 | 1.00 | - |
| calc-multiply | true | 1852 | 1.00 | - |
| calc-subtract | true | 1824 | 1.00 | - |
