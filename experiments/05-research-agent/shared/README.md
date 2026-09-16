# AI Research Agent 공통 자료

이 디렉터리는 `@ukkhnn`과 `@us788`이 독립 구현에서 동일하게 사용하는 연구 질문, 범위, 검색 전략, 필터, 내부 schema와 deterministic 평가 작업을 고정합니다.

## 고정 기준

- `research-question.json`: 질문 원문, 포함·제외 기준, 2020년 이후 범위와 최소 10편 조건
- `search-strategies.json`: 네 개의 deterministic seed query, 모델 확장 규칙, 검색원별 변환과 비교 조건
- `filters.json`: 언어·기간·문서 유형·합법적 접근·콘텐츠 안전 제한
- `schemas/`: paper record, claim-evidence, research report, Agent hypothesis의 내부 계약
- `evals/tasks.jsonl`: 검색부터 종합 평가까지 고정 규칙으로 확인할 `TaskRequest`

공통 질문은 다음과 같습니다.

> RAG 시스템에서 query rewriting, reranking, corrective retrieval, self-reflective retrieval 기법은 검색 품질과 답변의 faithfulness를 어떤 조건에서 개선하며, latency·비용·구현 복잡도 측면에서 어떤 trade-off를 만드는가?

## 독립 협업 규칙

1. 두 구현은 이 파일들의 질문·기간·언어·seed query·후보 수 제한을 바꾸지 않습니다.
2. 모델 확장 query는 seed query와 구분하고, 실패 시 seed query만으로 계속합니다.
3. API 결과에는 검색 시각, 원문 query, filter, source, rank와 응답 식별자를 기록합니다.
4. DOI, arXiv ID, Semantic Scholar paperId가 invalid 또는 unresolved인 논문은 유효 근거로 인용하지 않습니다.
5. survey는 배경과 인용 추적에만 사용하며 primary research를 대체하지 않습니다.
6. `@ukkhnn`과 `@us788`은 서로의 구현·개인 README·실행 결과를 수정하지 않습니다. 상대 결과가 없으면 비교 항목을 `pending`으로 남깁니다.
7. 실제 API key, 인증 정보, 사내 자료, 개인정보, 전체 PDF·초록 또는 모델의 raw prompt/response를 이 공통 자료에 저장하지 않습니다.

내부 schema는 저장소 공통 `TaskRequest`, `AgentResult`, `ToolTrace`, `EvaluationRecord`를 보완할 뿐 우회하지 않습니다.
