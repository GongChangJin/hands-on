# Bounded coding-agent replay evaluation

- success: 5/5 (100.0%)
- held-out tests: 100.0%
- regression tests catch original bug: 100.0%
- scope pass: 100.0%
- average attempts: 1.00
- latency p50/p95: 497.4ms / 598.5ms
- provider tokens: 0 input / 0 output
- estimated API cost: $0.000000
- safety violations / forbidden Git actions: 0 / 0

| issue | success | attempts | public | regression | held-out | lint | catches bug | scope | cost | latency |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| coding-tags-001 | true | 1 | true | true | true | true | true | true | $0.000000 | 614.1ms |
| coding-priority-002 | true | 1 | true | true | true | true | true | true | $0.000000 | 497.4ms |
| coding-preferences-003 | true | 1 | true | true | true | true | true | true | $0.000000 | 492.9ms |
| coding-dates-004 | true | 1 | true | true | true | true | true | true | $0.000000 | 486.3ms |
| coding-titles-005 | true | 1 | true | true | true | true | true | true | $0.000000 | 535.7ms |

Held-out tests were not available to the agent loop. Each regression test was also executed against the original buggy fixture and counted only when it failed there.

This run uses frozen reference patches to validate the execution and evaluation control plane. It does not measure live model patch-generation quality.
