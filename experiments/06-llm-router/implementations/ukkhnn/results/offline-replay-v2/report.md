# Hybrid LLM router evaluation

- classifier: `heuristic` (used only for incomplete signals)
- routing accuracy: 40/40 (100.0%)
- model / agent accuracy: 100.0% / 100.0%
- strategy: {'hybrid': 4, 'rule': 36}; classifier calls: 4
- projected quality: 90.2% vs all-frontier 93.6% (coverage 92.5%)
- projected cost: $0.123010 vs all-frontier $0.123274 (savings 0.2%, coverage 92.5%)
- routing + model cost: $0.000615 vs all-frontier model $0.000879 (savings 30.0%)
- projected latency p50/p95: 573.6ms / 10,696.4ms
- all-frontier latency p50/p95: 520.9ms / 10,696.4ms
- measured control planes: coding

| task | strategy | model | agents | gates | confidence | match | classifier ms | projected cost | projected latency |
| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| direct-001 | rule | small | - | - | 0.96 | true | 0.0 | $0.000000 | 369.5ms |
| direct-002 | rule | small | - | - | 0.96 | true | 0.0 | $0.000000 | 369.5ms |
| direct-003 | rule | small | - | - | 0.96 | true | 0.0 | $0.000000 | 369.5ms |
| direct-004 | rule | small | - | - | 0.96 | true | 0.0 | $0.000000 | 369.5ms |
| direct-005 | rule | small | - | - | 0.96 | true | 0.0 | $0.000000 | 369.5ms |
| direct-006 | rule | small | - | - | 0.96 | true | 0.0 | $0.000000 | 369.5ms |
| direct-007 | rule | balanced | - | - | 0.96 | true | 0.0 | $0.000022 | 520.9ms |
| direct-008 | rule | balanced | - | - | 0.96 | true | 0.0 | $0.000022 | 520.9ms |
| direct-009 | rule | balanced | - | - | 0.96 | true | 0.0 | $0.000022 | 520.9ms |
| direct-010 | rule | balanced | - | - | 0.96 | true | 0.0 | $0.000022 | 520.9ms |
| private-001 | rule | local | - | - | 0.96 | true | 0.0 | $0.000000 | 573.6ms |
| private-002 | rule | local | - | - | 0.96 | true | 0.0 | $0.000000 | 573.6ms |
| private-003 | rule | local | - | - | 0.96 | true | 0.0 | $0.000000 | 573.6ms |
| private-004 | rule | local | - | - | 0.96 | true | 0.0 | $0.000000 | 573.6ms |
| private-005 | rule | local | - | - | 0.96 | true | 0.0 | $0.000000 | 573.6ms |
| private-006 | rule | local | - | - | 0.96 | true | 0.0 | $0.000000 | 573.6ms |
| frontier-001 | rule | frontier | - | - | 0.96 | true | 0.0 | $0.000022 | 520.9ms |
| frontier-002 | rule | frontier | - | - | 0.96 | true | 0.0 | $0.000022 | 520.9ms |
| frontier-003 | rule | frontier | - | - | 0.96 | true | 0.0 | $0.000022 | 520.9ms |
| frontier-004 | rule | frontier | - | - | 0.96 | true | 0.0 | $0.000022 | 520.9ms |
| rag-001 | rule | balanced | rag | - | 0.96 | true | 0.0 | $0.000559 | 5,430.2ms |
| rag-002 | rule | balanced | rag | - | 0.96 | true | 0.0 | $0.000559 | 5,430.2ms |
| rag-003 | rule | balanced | rag | - | 0.96 | true | 0.0 | $0.000559 | 5,430.2ms |
| rag-004 | rule | frontier | rag | - | 0.96 | true | 0.0 | $0.000559 | 5,430.2ms |
| vision-001 | rule | balanced | vision | - | 0.96 | true | 0.0 | $0.000375 | 2,647.5ms |
| vision-002 | rule | balanced | vision | - | 0.96 | true | 0.0 | $0.000375 | 2,647.5ms |
| vision-003 | rule | frontier | vision | - | 0.96 | true | 0.0 | $0.000375 | 2,647.5ms |
| vision-004 | rule | balanced | vision | - | 0.96 | true | 0.0 | $0.000375 | 2,647.5ms |
| research-001 | rule | frontier | research | - | 0.96 | true | 0.0 | $0.023731 | 10,696.4ms |
| research-002 | rule | frontier | research | - | 0.96 | true | 0.0 | $0.023731 | 10,696.4ms |
| research-003 | rule | frontier | research | - | 0.96 | true | 0.0 | $0.023731 | 10,696.4ms |
| research-004 | rule | frontier | research | - | 0.96 | true | 0.0 | $0.023731 | 10,696.4ms |
| browser-001 | rule | balanced | browser | - | 0.96 | true | 0.0 | $0.000022 | 1,373.8ms |
| browser-002 | rule | balanced | browser | - | 0.96 | true | 0.0 | $0.000022 | 1,373.8ms |
| coding-001 | rule | frontier | coding | cybersecurity | 0.96 | true | 0.0 | N/A | N/A |
| coding-002 | rule | balanced | coding | cybersecurity | 0.96 | true | 0.0 | N/A | N/A |
| hybrid-001 | hybrid | balanced | vision | - | 0.82 | true | 0.0 | $0.000375 | 2,647.5ms |
| hybrid-002 | hybrid | frontier | research | - | 0.82 | true | 0.0 | $0.023731 | 10,696.4ms |
| hybrid-003 | hybrid | balanced | browser | - | 0.82 | true | 0.0 | $0.000022 | 1,373.8ms |
| hybrid-004 | hybrid | balanced | coding | cybersecurity | 0.82 | true | 0.0 | N/A | N/A |

## Limits

- Execution quality, downstream latency, and downstream cost are replay projections from upstream hands-on results rather than new task executions.
- Coding end-to-end generation projections remain excluded; 08 measures reference-patch control-plane execution and 09 measures its security gate.
- Balanced and frontier currently map to the same measured Solar Pro 4 endpoint.
