# 05. AI Research Agent

> 논문 검색부터 비교·근거 정리·후속 가설 제안까지 출처를 잃지 않고 자동화할 수 있는가?

## 프로젝트 정의

- **상태:** `in_progress` — `@ukkhnn` 구현·실데이터 평가는 완료, `@us788` 구현은 미작성
- **참여자:** `@ukkhnn`, `@us788`
- **역할:** 학술 정보 검색·검증·비교를 담당하는 전문 Agent
- **선행 프로젝트:** Agent Evaluation
- **후행 프로젝트:** LLM Router, 통합 시스템
- **실행일:** 2026-09-16 UTC

## 고정 연구 질문

> RAG 시스템에서 query rewriting, reranking, corrective retrieval, self-reflective retrieval 기법은 검색 품질과 답변의 faithfulness를 어떤 조건에서 개선하며, latency·비용·구현 복잡도 측면에서 어떤 trade-off를 만드는가?

영문 1차 연구를 대상으로 2020-01-01부터 실행일까지 검색한다. 초록 또는 합법적으로 접근 가능한 원문과 검증 가능한 DOI, arXiv ID, Semantic Scholar paperId가 있어야 한다. 설문 논문은 배경과 citation chaining에만 사용하며, 논문 주장과 Agent 가설을 별도 구조로 저장한다. 상세 조건과 해시는 [`shared/`](./shared/)에 고정했다.

## 실험 조건

| 조건 | 검색원 | 검증 방식 |
| --- | --- | --- |
| `semantic-scholar-only` | Semantic Scholar | 형식 검증과 Semantic Scholar 식별자 확인 |
| `federated-verified` | Semantic Scholar, Crossref, arXiv | DOI → arXiv ID → paperId 순서의 보수적 중복 제거와 교차 검색원 확인 |

두 조건은 동일한 고정 검색어 4개와 DeepSeek가 확장한 검색어 4개를 사용한다. 확장은 `run-all`에서 한 번만 실행하고 두 조건이 공유한다.

## @ukkhnn 실데이터 결과

| 지표 | Semantic Scholar only | Federated verified |
| --- | ---: | ---: |
| 원시 검색 레코드 | 40 | 165 |
| 검증 논문 | 18 | 18 |
| 제거한 중복 | 0 | 75 |
| 식별자 실패 / 잔존 중복 | 0 / 0 | 0 / 0 |
| 논문 근거 claim | 75 | 47 |
| claim이 있는 검증 논문 | 18/18 | 14/18 |
| 논문 단위 근거 coverage | 100% | 77.8% |
| claim 인용·locator·식별자 유효성 | 100% | 100% |
| 검색 API 요청 | S2 22 | S2 24, Crossref 10, arXiv 8 |
| 분석 모델 요청 | 5 | 5 |
| 조건별 API 요청 합계 | 27 | 47 |
| 모델 토큰 | 43,984 | 31,739 |
| 모델 호출 latency p50 / p95 | 11.78s / 14.82s | 10.70s / 14.50s |
| 계산 비용 | $0.027941472 | $0.023709300 |
| 결정론적 평가 | 통과 | 실패 |

공유 query expansion은 별도로 1회, 248 tokens, $0.0001257이었고 조건별 합계에 중복 산입하지 않았다. 비용은 공급자 usage와 실행 당시 공식 요율로 계산한 추정치이며 청구 금액이 아니다. 조건별 요청 수 보정 근거는 [`request-attribution-correction.json`](./implementations/ukkhnn/results/request-attribution-correction.json)에 남겼다.

실패도 성공으로 숨기지 않았다. Semantic Scholar는 각각 6회와 8회의 HTTP 429를 반환했으며 federated 결과에는 보수적으로 병합하지 않은 제목 유사 후보 6건이 있다. Federated 분석은 모델이 4개 논문에 유효한 claim을 반환하지 않아 엄격한 100% paper coverage 기준을 통과하지 못했다. 모든 저장 claim은 검증 식별자, HTTPS 출처, `abstract excerpt` locator에 연결되어 있다.

## 구현과 안전 경계

- 공식 Semantic Scholar, Crossref, arXiv API만 사용하며 재시도, backoff, pagination, timeout을 제한한다.
- DeepSeek 전용 gateway는 `deepseek-flash`와 `https://api.deepseek.com`만 허용하고 OpenAI 환경 변수로 대체 실행하지 않는다.
- DOI, arXiv ID, paperId를 정규화·검증하고 DOI → arXiv ID → paperId → 보수적 제목 유사도 순으로 중복을 판정한다.
- robots, paywall, 인증 우회 없이 공개 초록과 허용된 PDF만 처리한다. URL scheme·DNS·redirect·MIME·PDF signature·크기·페이지 수를 검사한다.
- Phoenix에는 span 이름, 해시, 모델명, token/cost/latency, 결과 수, 실패 유형만 남긴다. API key, Authorization, raw prompt/response, 전체 초록·PDF 본문은 기록하지 않는다.
- Research Router는 연구형 요청만 수락하고 그 외 요청은 외부 호출 전에 거절한다.
- 재현 가능한 offline fixture는 live 결과로 표시하지 않는다.

## 산출물과 재현

- 공통 질문·전략·필터·schema·평가 corpus: [`shared/`](./shared/)
- 구현 및 실행법: [`implementations/ukkhnn/README.md`](./implementations/ukkhnn/README.md)
- 최종 실험 산출물: [`implementations/ukkhnn/results/final/`](./implementations/ukkhnn/results/final/)
- 조건 비교: [`research-condition-comparison.md`](./implementations/ukkhnn/results/research-condition-comparison.md)
- Phoenix 검증: [`phoenix-verification.json`](./implementations/ukkhnn/results/phoenix-verification.json)
- 최종 판정: [`verification-status.json`](./implementations/ukkhnn/results/verification-status.json)

## 독립 협업 규칙

`@ukkhnn`과 `@us788`은 `shared/`의 질문·필터·검색 조건·schema·평가 task만 공통 기준으로 사용한다. 구현 코드, API 실행, 결과 디렉터리, 실패 분석은 각자 소유하고 상대 구현을 수정하지 않는다. 참가자 간 비교에는 실제로 커밋된 결과만 사용하며, 아직 없는 `@us788` 수치나 결론은 계속 pending으로 둔다.

## 완료 조건

- [x] 공통 질문으로 각 조건에서 논문 18편을 검증함
- [x] 생성된 모든 claim에 검증 식별자, 출처 URL, 근거 위치가 연결됨
- [x] 논문 결과와 Agent 가설이 schema와 출력에서 분리됨
- [x] 두 검색 조건의 범위, 오류, 비용, 지연을 비교함
- [x] Router에 제공할 `TaskRequest` / `AgentResult` 인터페이스를 구현함
- [ ] `@us788` 구현과 참가자 간 비교 — 해당 디렉터리는 변경하지 않음

## 구현 비교

| 참여자 | 검색원·구성 | 논문 수 | 인용 오류 | 결과 | 특징 |
| --- | --- | ---: | ---: | --- | --- |
| `@ukkhnn` | S2 단독 / S2+Crossref+arXiv | 조건별 18 | 0 | 단독 통과, federated 보류 | 결정론적 검증, DeepSeek 분석, Phoenix 추적 |
| `@us788` | 미작성 | — | — | 대기 | 디렉터리 미변경 |

## 결론

- **적용 판단:** 품질 또는 안전 기준 미달로 적용 보류
- **판단 이유:** 식별자·인용·locator·schema·가설 분리는 통과했지만 federated 조건의 논문 단위 근거 coverage가 77.8%로 고정 임계값 100%에 미달했다.
- **적용 가능 범위:** 현재 상태는 검색·검증·관측·offline 회귀 테스트용 실험 구현으로 사용할 수 있다. 자동 최종 연구 결론 생성에는 사용하지 않는다.
- **다음 행동:** Semantic Scholar API key 또는 더 완만한 호출 간격으로 429를 줄이고, 누락 논문 추출 재시도와 1차 실험 적합성 screening을 강화한 뒤 동일 corpus와 결정론적 grader로 재실행한다.

## 변경 기록

### 2026-09-20 — @ukkhnn 구현 완료

- 변경: 고정 질문, 공식 검색 adapter, 식별자 검증, 중복 제거, DeepSeek 분석, Phoenix 추적, 회귀 테스트와 실데이터 산출물 추가
- 결과: Semantic Scholar only 통과, federated verified 보류
- 다음 행동: 429 완화와 federated evidence coverage 개선

### 초기 정의

- 변경: 검색·검증·비교·가설 생성 범위 정의
- 결과: `planned`
- 다음 행동: 검색 전략 분담
