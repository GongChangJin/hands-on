# 공통 자료

두 구현이 같은 입력과 기준선으로 비교되도록 라우팅 corpus, 정책과 선행 프로젝트 실측치를 둡니다. 계정별 비밀값은 커밋하지 않습니다.

## 파일

- `task-requests.jsonl`: direct·private·RAG·vision·research·browser·coding·모호 요청 40건과 기대 모델·Agent
- `routing-policy.json`: confidence, circuit breaker, fallback과 capability→Agent 매핑
- `project-metrics.json`: 02~05 결과에서 가져온 논리 모델·Agent 품질, p50 지연시간과 실행 비용

`small`, `local`, `balanced`, `frontier`는 정책에서만 사용하는 논리 이름이다. 실제 모델은 `project-metrics.json`에서 매핑하며, 현재 계정에서는 `balanced`와 `frontier`가 모두 `solar-pro4`를 사용한다.

Browser와 coding 수치는 07·08 완료 전까지 `null`이다. 이 두 Agent가 포함된 요청은 라우팅 정확도에는 포함하지만 품질·비용·지연시간 projection에서는 제외한다.
