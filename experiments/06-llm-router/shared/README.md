# 공통 자료

두 구현이 같은 입력과 기준선으로 비교되도록 라우팅 corpus, 정책과 선행 프로젝트 실측치를 둡니다. 계정별 비밀값은 커밋하지 않습니다.

## 파일

- `task-requests.jsonl`: direct·private·RAG·vision·research·browser·coding·모호 요청 40건과 기대 모델·Agent
- `routing-policy.json`: confidence, circuit breaker, fallback과 capability→Agent 매핑
- `project-metrics.json`: 02~08 결과에서 가져온 논리 모델·Agent 품질, p50 지연시간, 실행 비용과 09 보안 승인 지표

`small`, `local`, `balanced`, `frontier`는 정책에서만 사용하는 논리 이름이다. 실제 모델은 `project-metrics.json`에서 매핑하며, 현재 계정에서는 `balanced`와 `frontier`가 모두 `solar-pro4`를 사용한다.

Browser는 07 end-to-end 실측치를 사용한다. Coding은 08 참조 patch 제어 계층과 09 보안 승인 게이트를 `control_plane`으로 기록하며, live patch 생성 품질·비용·지연시간은 `null`로 유지해 end-to-end projection에서 제외한다.
