# handoff experiment report

- provider/model: `upstage` / `solar-pro4`
- success: 15/20 (75.0%)
- latency p50/p95: 2493ms / 7686ms
- tokens: 23,048
- estimated model cost: N/A
- safety violations: 0

| task | success | latency ms | tool accuracy | failure |
| --- | ---: | ---: | ---: | --- |
| combined-divide | false | 9769 | 0.00 | tool_mismatch |
| combined-power | true | 7576 | 1.00 | - |
| combined-large-add | true | 2546 | 1.00 | - |
| combined-parentheses | false | 2386 | 1.00 | answer_mismatch |
| combined-multiply | true | 3774 | 1.00 | - |
| project-active-check | true | 2560 | 1.00 | - |
| project-paraphrase | true | 2223 | 1.00 | - |
| project-purpose | true | 2052 | 1.00 | - |
| project-full | true | 3678 | 1.00 | - |
| project-status | true | 2480 | 1.00 | - |
| calc-large-add | true | 2083 | 1.00 | - |
| calc-square | false | 1293 | 0.00 | tool_mismatch |
| calc-parentheses | true | 2306 | 1.00 | - |
| calc-decimal | true | 1604 | 1.00 | - |
| calc-precedence | true | 3120 | 1.00 | - |
| calc-power | false | 1888 | 0.00 | exception |
| calc-divide | true | 2505 | 1.00 | - |
| calc-subtract | true | 2767 | 1.00 | - |
| calc-add | true | 2757 | 1.00 | - |
| calc-multiply | false | 1789 | 0.00 | tool_mismatch |
