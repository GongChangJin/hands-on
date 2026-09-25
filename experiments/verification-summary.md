# 01~07 검증 요약

이 문서는 현재 구현의 공통 계약, 회귀 테스트, live 평가 결과와 적용 경계를 한곳에서 확인하기 위한 기술 요약이다. 독립 구현 간 비교는 범위에서 제외한다.

## 최종 결과

| 핸즈온 | 검증 결과 | 안전 결과 | 적용 판단 |
| --- | --- | --- | --- |
| 01 Agent Evaluation | single 20/20, handoff 19/20 | 안전 위반 0 | 작은 도구형 Agent에는 single 구조 적용 |
| 02 Local LLM | 3B 60/72, 7.6B 69/72, API 72/72; schema 모두 100% | 안전 위반 0 | 7.6B 분류·추출 trial, 계산은 fallback |
| 03 Agentic RAG | 전체 19/19, 근거·계산·도구 정확도 100% | 안전 위반 0 | Router 후보로 trial |
| 04 Multimodal Agent | adaptive 반복 성공률 37.5~45.8%, 분류 정확도 75.0~87.5%, schema 100% | 개인정보 노출·안전 위반 0 | 합성 UI 범위에서 adaptive-context 제한 적용 |
| 05 Research Agent | 두 검색 조건 모두 18/18 evidence coverage, citation·locator 100% | 결과 내 비밀·안전 위반 0 | federated 검색 기본 적용 |
| 06 LLM Router | 실제 분류기 39/40, 품질 차이 3.79%p, fallback 7/7 | local-only 외부 fallback 0 | policy-first hybrid 제한 범위 trial |
| 07 Computer-use Agent | DOM 22/24, adaptive 24/24, 복구 6/6 | 안전 probe 6/6, 실제 외부 navigation 0 | 내부 테스트·되돌릴 수 있는 작업에 trial |

## 회귀 검증

일곱 구현의 로컬 회귀 테스트 170개가 모두 통과했다.

| 핸즈온 | 통과 |
| --- | ---: |
| 01 | 27 |
| 02 | 15 |
| 03 | 12 |
| 04 | 37 |
| 05 | 42 |
| 06 | 19 |
| 07 | 18 |

모든 구현은 공통 `TaskRequest`, `AgentResult`, `ToolTrace`, `EvaluationRecord` 계약을 유지한다. Live 결과는 provider가 반환한 token과 실행 당시 요율을 사용하며 실제 청구서로 해석하지 않는다.

## 보존된 실패와 제약

- 01: handoff 구조에서 calculator 호출이 누락된 1건을 보존했다.
- 02: 3B의 4개 실패 유형과 7.6B의 기본 산술 실패를 세 반복 모두 보존했다. 3B는 비상업 연구 라이선스이며 API는 비스트리밍이라 첫 토큰을 비교하지 않았다.
- 03: 최초 전체 실행의 잘못된 직접 계산 경로를 보존하고, 숫자 근거 검증 후 19문항 전체를 재실행했다.
- 04: 24장 합성 corpus와 두 번의 adaptive 반복만 검증했다. Layout/clipping 경계와 severity 판단에는 실행 간 변동이 남아 있다.
- 05: Semantic Scholar 429와 arXiv 406을 source failure로 보존했다. 선택된 논문과 근거가 모든 결정론적 기준을 만족할 때만 성공으로 판정한다.
- 06: 연구 요청 1건에서 `browser`를 추가 선택한 과다 라우팅을 보존했다. 모델+라우팅 비용은 10.52% 줄었지만 전체 비용 절감은 0.22%였고 p50은 52.7ms 늘었다. Browser는 07 실측치를 offline replay에 반영했고 coding projection은 08 실측 전까지 제외한다.
- 07: DOM 전용 조건은 ID가 바뀐 버튼을 두 번 모두 찾지 못했다. Adaptive 조건은 실패 시 screenshot hash를 증거로 남기고 접근성 이름으로 복구했지만, screenshot 의미 해석과 실제 웹 일반화는 검증하지 않았다.

## 주요 산출물

- 02 최종 비교: [`02-local-llm/implementations/ukkhnn/results/full-comparison.md`](02-local-llm/implementations/ukkhnn/results/full-comparison.md)
- 03 최종 평가: [`03-agentic-rag/implementations/ukkhnn/results/upstage-solar-pro4-full-19-v2/`](03-agentic-rag/implementations/ukkhnn/results/upstage-solar-pro4-full-19-v2/)
- 04 보완 상태: [`04-multimodal-agent/implementations/ukkhnn/results/remediation-verification-status.json`](04-multimodal-agent/implementations/ukkhnn/results/remediation-verification-status.json)
- 05 보완 상태: [`05-research-agent/implementations/ukkhnn/results/remediation-v2/verification-status.json`](05-research-agent/implementations/ukkhnn/results/remediation-v2/verification-status.json)
- 06 최종 평가: [`06-llm-router/implementations/ukkhnn/results/hybrid-solar-pro4/`](06-llm-router/implementations/ukkhnn/results/hybrid-solar-pro4/)
- 07 조건 비교: [`07-computer-use-agent/implementations/ukkhnn/results/playwright-local-site/comparison.md`](07-computer-use-agent/implementations/ukkhnn/results/playwright-local-site/comparison.md)
