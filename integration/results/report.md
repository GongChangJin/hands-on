# Integration v1 결과

실행일: 2026-09-27

## 결론

CLI 기반 통합 범위는 적용 가능합니다. 06 Router가 02~08 경로를 선택하고 모든 결과를 공통 계약으로 정규화했으며, Coding 경로는 09 Security gate가 성공해야만 승인됩니다. timeout과 잘못된 schema를 주입한 경우에도 성공으로 넘어가지 않았습니다.

현재 통합은 workflow와 안전 경계 검증에 적합합니다. 여러 Agent의 답을 합성하는 제품 품질, 장기 실행 신뢰성, UI와 배포 운영은 아직 검증하지 않았습니다.

## Replay

| 항목 | 결과 |
|---|---:|
| 시나리오 | 10 |
| 통과 | 10/10 |
| 정상 경로 | 7/7 |
| route 일치 | 10/10 |
| agent 일치 | 10/10 |
| 기대 status 일치 | 10/10 |
| fail-closed 주입 | 3/3 |
| 안전 위반 | 0 |
| 공통 계약 레코드 | 53 |

정상 경로는 local-only, direct model, RAG, Vision, Research, Browser, Coding을 포함합니다. Vision은 04의 실제 기준선 37.5%를 반영해 `partial`을 기대값으로 유지했습니다. 실패 경로는 RAG timeout, Security timeout, Security schema 오류입니다.

## Live smoke

| 경로 | 실행 결과 | 비고 |
|---|---|---|
| 06 → 03 RAG | 성공 | Upstage 실제 1건, 추정 `$0.0005193` |
| 06 → 05 Research | 성공 | deterministic offline corpus, 외부 모델 미실행 |
| 06 → 07 Browser | 성공 | adaptive 24/24, safety 6/6 |
| 06 → 08 Coding → 09 Security | 성공 | Coding 1/1, security approve |

Security live 실행은 기대 취약점 탐지 6/6, 보완 6/6, Coding handoff 승인 5/5, 격리 probe 3/3이었습니다. Browser의 DOM-only 조건은 변경 UI 2건을 놓쳤지만 adaptive screenshot 조건은 24/24를 통과했습니다.

## 개별 결과 대비

| Hands-on | 개별 기준선 | 통합에서 확인한 것 |
|---|---|---|
| 02 Local LLM | Qwen 7B 69/72, 95.8% | local-only가 local route와 로컬 artifact에만 연결됨 |
| 03 Agentic RAG | 19/19 | 실제 Router → RAG 요청과 공통 결과 변환 |
| 04 Multimodal | 9/24, 37.5% | 낮은 품질을 숨기지 않고 `partial` 전파 |
| 05 Research | task success, evidence 100% | offline 실행의 provenance 결과와 실행 모드 표시 |
| 06 Router | 39/40, 97.5% | 통합 시나리오 route/agent 10/10 |
| 07 Computer Use | adaptive 24/24 | 실제 로컬 Browser 실행과 안전 probe 유지 |
| 08 Coding | 5/5 | 1개 실제 bounded test 실행 후 보안 handoff |
| 09 Security | 탐지·보완 6/6 | Coding 성공 이후 필수 승인, 오류 시 차단 |

## 제약과 다음 판단

- 03 live 질문 1건은 연결 smoke이며 19개 기준선 평가를 대체하지 않습니다.
- 05 live-smoke는 DeepSeek 키가 없어 외부 모델을 실행하지 않았습니다.
- 04는 통합 연결보다 개별 모델 품질 개선이 우선입니다.
- replay 품질은 개별 실험 결과의 projection이며 cross-agent 답변 합성 품질이 아닙니다.
- 서비스화 전에 request persistence, retry 정책, 관측 backend, 사용자 권한 모델을 별도 설계해야 합니다.
