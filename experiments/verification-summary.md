# 01·03·04·05 검증 요약

이 문서는 현재 구현의 공통 계약, 회귀 테스트, live 평가 결과와 적용 경계를 한곳에서 확인하기 위한 기술 요약이다. 독립 구현 간 비교는 범위에서 제외한다.

## 최종 결과

| 핸즈온 | 검증 결과 | 안전 결과 | 적용 판단 |
| --- | --- | --- | --- |
| 01 Agent Evaluation | single 20/20, handoff 19/20 | 안전 위반 0 | 작은 도구형 Agent에는 single 구조 적용 |
| 03 Agentic RAG | 전체 19/19, 근거·계산·도구 정확도 100% | 안전 위반 0 | Router 후보로 trial |
| 04 Multimodal Agent | adaptive 반복 성공률 37.5~45.8%, 분류 정확도 75.0~87.5%, schema 100% | 개인정보 노출·안전 위반 0 | 합성 UI 범위에서 adaptive-context 제한 적용 |
| 05 Research Agent | 두 검색 조건 모두 18/18 evidence coverage, citation·locator 100% | 결과 내 비밀·안전 위반 0 | federated 검색 기본 적용 |

## 회귀 검증

네 구현의 로컬 회귀 테스트 118개가 모두 통과했다.

| 핸즈온 | 통과 |
| --- | ---: |
| 01 | 27 |
| 03 | 12 |
| 04 | 37 |
| 05 | 42 |

모든 구현은 공통 `TaskRequest`, `AgentResult`, `ToolTrace`, `EvaluationRecord` 계약을 유지한다. Live 결과는 provider가 반환한 token과 실행 당시 요율을 사용하며 실제 청구서로 해석하지 않는다.

## 보존된 실패와 제약

- 01: handoff 구조에서 calculator 호출이 누락된 1건을 보존했다.
- 03: 최초 전체 실행의 잘못된 직접 계산 경로를 보존하고, 숫자 근거 검증 후 19문항 전체를 재실행했다.
- 04: 24장 합성 corpus와 두 번의 adaptive 반복만 검증했다. Layout/clipping 경계와 severity 판단에는 실행 간 변동이 남아 있다.
- 05: Semantic Scholar 429와 arXiv 406을 source failure로 보존했다. 선택된 논문과 근거가 모든 결정론적 기준을 만족할 때만 성공으로 판정한다.

## 주요 산출물

- 03 최종 평가: [`03-agentic-rag/implementations/ukkhnn/results/upstage-solar-pro4-full-19-v2/`](03-agentic-rag/implementations/ukkhnn/results/upstage-solar-pro4-full-19-v2/)
- 04 보완 상태: [`04-multimodal-agent/implementations/ukkhnn/results/remediation-verification-status.json`](04-multimodal-agent/implementations/ukkhnn/results/remediation-verification-status.json)
- 05 보완 상태: [`05-research-agent/implementations/ukkhnn/results/remediation-v2/verification-status.json`](05-research-agent/implementations/ukkhnn/results/remediation-v2/verification-status.json)
