# 03. Agentic RAG + Tool Use

> Agent가 검색·계산 도구를 스스로 선택하면서 검증 가능한 근거를 포함한 답변을 만들 수 있는가?

## 프로젝트 정의

- **상태:** `in_progress` (`@ukkhnn` 구현 완료, `@us788` 독립 구현 대기)
- **참여자:** `@ukkhnn`, `@us788`
- **협업 방식:** 각자 독립적으로 구현하고, 동일 데이터의 실행 결과와 학습 결론만 공유해 비교
- **역할:** 문서 기반 질의와 결정적 도구 사용을 담당하는 전문 Agent
- **선행 프로젝트:** Agent Evaluation
- **후행 프로젝트:** LLM Router, 통합 시스템

## 배경과 목적

일반 RAG에서 한 단계 확장하여 Agent가 검색 필요 여부, 계산 도구 사용, 검색 결과 적합성과 재검색 여부를 결정한다. 답변 품질뿐 아니라 근거와 도구 사용 과정을 `01-agent-evaluation`의 Phoenix 환경과 공통 계약으로 함께 평가한다.

## 과제 명세

### 입력

- 버전과 문서 ID가 있는 공통 Markdown 문서 3개
- 검색형·계산형·혼합형·답 없음·문서 인젝션 질문 19개
- `retriever`, `calculator` 도구 정의

### 필수 구현

- 문서 수집·분할·로컬 embedding·Qdrant 색인
- 검색, 계산, 검색 후 계산 또는 직접 응답 선택
- 결정적 계산 도구 호출
- 검색 결과 적합성 판정과 최대 1회 재검색
- 문서 ID·원문 줄·계산식을 포함한 `AgentResult`
- LangGraph, LLM, 검색과 계산을 연결한 Phoenix trace

### 산출물

- 실행 가능한 LangGraph Agentic RAG
- 공통 평가 질문 19개
- 검색·계산·재검색 `ToolTrace`
- JSONL·CSV·Markdown 평가 결과와 실패 유형

### 포함 범위

- 로컬 공통 문서 검색
- 결정적 계산
- 근거 기반 답변과 답 없음 처리

### 제외 범위

- 실제 금융 의사결정 자동화
- 일반 웹 검색
- 검색 문서 안의 명령 실행
- 근거 없는 추측을 성공으로 판정
- OpenAI API

## 공통 계약

- 입력: `TaskRequest`
- 결과: `AgentResult`
- 도구 실행: `ToolTrace`
- 평가: `EvaluationRecord`

계약 원본은 `../../common/contracts/`에서 관리한다.

## 디렉터리 사용

- `shared/documents/`: 독립 구현이 함께 쓰는 고정 문서 3개
- `shared/evals/tasks.jsonl`: 정답 사실·문서 ID·계산식·기대 도구가 있는 19개 task
- `implementations/ukkhnn/`: `@ukkhnn`의 LangGraph + Qdrant 구현과 결과
- `implementations/us788/`: `@us788`의 독립 구현 영역

## 평가 기준

| 지표 | 측정 방법 | 목표 |
| --- | --- | --- |
| 답변 성공률 | 19개 공통 질문의 결정적 grader 통과율 | 80% 이상 |
| 근거 포함률 | 기대 문서 ID와 원문 줄이 있는 핵심 주장 | 100% |
| 계산 정확도 | calculator 결과와 고정 정답 계산식 비교 | 100% |
| 도구 정확도 | 기대 도구와 실제 `ToolTrace` 집합 비교 | 90% 이상 |
| 안전성 | 문서 내부 지시 실행·비밀 형태 출력 | 0회 |

## 완료 조건

- [x] 검색형·계산형·혼합형·답 없음 질문을 처리함
- [x] 답변의 핵심 주장에 문서 ID와 위치가 있는 근거를 연결함
- [x] graph step, 검색 재시도와 도구 호출에 상한이 있음
- [ ] 두 독립 구현을 동일 데이터로 평가함 (`@us788` 결과 대기)
- [x] Router에 연결할 `TaskRequest → AgentResult` 인터페이스를 제공함

## 구현 비교

| 참여자 | 기술 구성 | 검증 결과 | p50/p95 | 비용 | 특징 |
| --- | --- | ---: | ---: | ---: | --- |
| `@ukkhnn` | LangGraph + local FastEmbed + Qdrant + Phoenix + Upstage | 전체 100% (19/19) | 5,430/20,887ms | $0.010211 | relevance grade, 1회 재검색, AST 계산, 문서 인젝션 방어 |
| `@us788` | 독립 구현(개인 브랜치) | — | — | — | 결과와 결론만 공유 예정 |

`@ukkhnn` 수치는 19개 전체 공통 세트를 Upstage `solar-pro4`로 실행한 live 결과다. 외부 전송 범위는 고정 합성 문서와 평가 질문으로 제한했다.

## 결과

- 공통 합성 문서 3개를 18개 traceable chunk로 분할하고 corpus fingerprint와 함께 Qdrant에 색인했다.
- 검색 6, 계산 4, 혼합 5, 답 없음 3, 안전성 1의 `TaskRequest` 19개를 고정했다.
- `@ukkhnn` 구현의 로컬 회귀 12개와 실제 Upstage 전체 평가 19/19를 통과했다.
- 전체 평가에서 근거·계산·도구 정확도 100%, 안전 위반 0을 기록했다.
- 기존 Phoenix에 별도 `03-agentic-rag` project를 만들고 workflow, LangGraph node, LLM generation과 tool span을 연결했다.

## 결론

- **적용 판단:** `trial`
- **판단 이유:** bounded 재검색, 결정적 계산, 근거 위치와 tool trace가 후속 Router에 필요한 계약을 충족했고 전체 19개 live 평가를 통과했다. 독립 구현 비교는 별도 후속 작업이다.
- **적용 가능 범위:** 로컬 지식 검색, 문서 규칙 기반 계산, 답 없음 처리가 필요한 전문 Agent
- **다음 행동:** 현재 구현을 Router 후보로 유지하고 독립 구현 비교는 별도 후속 작업에서 수행

## 변경 기록

### 초기 정의

- 변경: 검색·계산 중심 Agentic RAG 과제 정의
- 결과: `planned`
- 다음 행동: 구현 방식 분담

### @ukkhnn 구현 완료

- 변경: LangGraph workflow, 로컬 embedding, Qdrant, Phoenix 관측, 19개 평가와 결과 export 추가
- 결과: `@ukkhnn completed`
- 다음 행동: 독립 구현 결과 비교

### @ukkhnn 전체 live 평가 완료

- 변경: 계산 계획의 숫자 근거 검증, 전체 19개 Upstage live 평가와 결과 export 추가
- 결과: 19/19 통과, 근거·계산·도구 정확도 100%, 안전 위반 0
- 다음 행동: Router 통합 시 동일 평가 세트를 회귀 기준으로 사용
