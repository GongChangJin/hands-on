# Computer-use condition comparison

| condition | success | average actions | recovery | p50 | p95 | screenshot observations |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| DOM/accessibility | 91.7% | 1.75 | 66.7% | 1275.8ms | 2243.1ms | 0 |
| failure-triggered screenshot + accessibility fallback | 100.0% | 1.83 | 100.0% | 1373.8ms | 2268.8ms | 4 |

Safety probes passed 6/6; actual external navigations: 0.

The adaptive condition records screenshot evidence only after an action error, then uses an accessible-name fallback. Routine steps retain the lower-overhead DOM/accessibility representation.
