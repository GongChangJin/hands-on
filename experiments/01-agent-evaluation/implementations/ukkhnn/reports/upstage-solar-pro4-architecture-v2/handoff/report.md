# handoff experiment report

- provider/model: `upstage` / `solar-pro4`
- success: 19/20 (95.0%)
- latency p50/p95: 2651ms / 3927ms
- tokens: 24,046
- estimated Agent-call cost: $0.008477 (100% of runs covered)
- evaluator-call cost: excluded
- safety violations: 0

| task | success | latency ms | tool accuracy | failure |
| --- | ---: | ---: | ---: | --- |
| combined-large-add | true | 3642 | 1.00 | - |
| combined-divide | true | 2877 | 1.00 | - |
| combined-parentheses | true | 2818 | 1.00 | - |
| combined-multiply | true | 2904 | 1.00 | - |
| combined-power | true | 2791 | 1.00 | - |
| project-paraphrase | true | 4193 | 1.00 | - |
| project-active-check | true | 2961 | 1.00 | - |
| project-purpose | true | 3913 | 1.00 | - |
| project-status | true | 2441 | 1.00 | - |
| project-full | true | 2839 | 1.00 | - |
| calc-large-add | true | 2024 | 1.00 | - |
| calc-square | true | 1801 | 1.00 | - |
| calc-decimal | true | 1985 | 1.00 | - |
| calc-parentheses | true | 2133 | 1.00 | - |
| calc-precedence | true | 2733 | 1.00 | - |
| calc-power | true | 2128 | 1.00 | - |
| calc-divide | false | 2005 | 0.00 | tool_mismatch |
| calc-subtract | true | 2570 | 1.00 | - |
| calc-multiply | true | 2415 | 1.00 | - |
| calc-add | true | 2336 | 1.00 | - |
