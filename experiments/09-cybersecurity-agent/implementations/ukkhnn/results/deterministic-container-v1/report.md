# Cybersecurity Agent evaluation

- Run: `deterministic-container-v1`
- Decision: **approve**
- Detection: 6/6 (100%)
- Remediation: 6/6 (100%)
- False positives: 0
- Regression/security tests after remediation: pass
- Isolation probes: 3/3

## Coding Agent handoff review

| Task | Decision | Findings | Tests |
| --- | --- | ---: | --- |
| `coding-tags-001` | approve | 0 | pass |
| `coding-priority-002` | approve | 0 | pass |
| `coding-preferences-003` | approve | 0 | pass |
| `coding-dates-004` | approve | 0 | pass |
| `coding-titles-005` | approve | 0 | pass |

## Limits

- The rule set is intentionally scoped to SQL injection, path traversal, and hardcoded secrets in Python.
- Deterministic reference fixes and replay patches validate the gate and evidence chain; they do not measure live LLM generation quality.
- Dependency and dynamic application security scanning remain outside this experiment.
