# 06. LLM Router

> 요청에 맞는 모델과 전문 Agent를 선택하여 품질을 유지하면서 비용이나 지연시간을 줄일 수 있는가?

## 프로젝트 정의

- **상태:** `validated`
- **참여자:** `@ukkhnn`, `@us788`
- **역할:** 모델·전문 Agent 선택과 fallback을 담당하는 오케스트레이션 계층
- **선행 프로젝트:** Agent Evaluation, Local/Open-weight LLM, Agentic RAG, Multimodal Agent, AI Research Agent
- **후행 프로젝트:** Computer-use Agent, Coding Agent, 통합 시스템

## 구현 범위

- `small`, `balanced`, `frontier`, `local` 논리 모델과 실제 모델 매핑 분리
- `rag`, `vision`, `research`, `browser`, `coding` 단일·복수 Agent 선택
- 명시 신호는 규칙, 모호한 요청은 선택적 LLM 분류기를 사용하는 하이브리드 라우팅
- timeout·provider/schema 오류·낮은 confidence·circuit breaker·모델 장애 fallback
- 논리/실제 모델, Agent, 이유, confidence, 비용과 fallback을 포함한 구조화 결과
- all-frontier 기준선과 02~05 실측 결과를 사용한 replay comparison

전문 업무 실행은 Router 내부에 포함하지 않는다. Browser와 coding Agent는 07·08 완료 전까지 라우팅만 검증한다.

## 공통 평가

40개 요청은 direct, private/local-only, RAG, vision, research, browser, coding과 불완전 신호를 포함한다. 품질·비용·지연시간은 같은 요청과 같은 전문 Agent를 유지한 채 모델 경로만 all-frontier로 바꾼 기준선과 비교한다.

| 지표 | 목표 | `@ukkhnn` 결과 |
| --- | ---: | ---: |
| 라우팅 정확도 | 90% 이상 | 39/40 (97.5%) |
| 품질 차이 | 5%p 이내 | 3.79%p |
| 모델+라우팅 비용 | 절감률 기록 | 10.52% 절감 |
| 전체 비용 | 절감률 기록 | 0.22% 절감 |
| projected p50 / p95 | 비교 기록 | 573.6ms / 10,696.4ms |
| fallback | 정상 복구 | 7/7 |

Projection coverage는 82.5%다. Browser와 coding은 아직 실측치가 없고, `balanced`와 `frontier`는 현재 동일한 `solar-pro4`에 매핑된다.

## 완료 조건

- [x] 논리 모델명과 실제 모델 매핑이 분리됨
- [x] 전문 Agent와 모델을 모두 선택할 수 있음
- [x] all-frontier 기준선과 같은 입력·Agent 조건으로 비교함
- [x] 장애와 낮은 confidence fallback을 검증함
- [x] 선택 이유와 비용이 route metadata에 기록됨

## 구현 비교

| 참여자 | 라우팅 방식 | 정확도 | 품질 차이 | 모델+라우팅 비용 | 특징 |
| --- | --- | ---: | ---: | ---: | --- |
| `@ukkhnn` | policy-first hybrid | 97.5% | 3.79%p | 10.52% 절감 | 모호 요청 4건만 Solar 분류, local-only 외부 fallback 차단 |
| `@us788` | TBD | — | — | — | — |

## 결과와 실패

`@ukkhnn` 구현은 실제 Solar 분류기를 호출한 4건 중 3건을 기대 Agent와 정확히 맞췄다. 나머지 연구 요청은 `research` 외에 `browser`를 추가해 과다 라우팅으로 남겼다. 36건은 규칙만 사용했다.

모델+라우팅 비용은 줄었으나 전체 비용은 Research Agent 실행 비용 때문에 0.22%만 줄었다. p50도 all-frontier보다 52.7ms 느렸다. 현재 로컬 7.6B 실측 p50이 Solar Pro 4보다 느리기 때문이다.

## 결론

- **적용 판단:** `trial`
- **판단 이유:** 97.5% 라우팅과 7/7 fallback을 달성했고 품질 차이가 목표 안에 있으나, 비용·지연 개선은 workload와 현재 모델 매핑에 크게 의존한다.
- **적용 가능 범위:** 명시 신호가 있는 요청, private/local-only 경계, 03~05에서 검증된 전문 Agent 선택
- **제한 범위:** browser/coding 최적화, latency 우선 workload, 서로 다른 balanced/frontier 모델이 필요한 환경
- **다음 행동:** 07·08 실측치를 연결하고 balanced/frontier 후보를 별도 평가한다.

## 변경 기록

### @ukkhnn 하이브리드 검증

- 변경: 정책·40문항 corpus·실측 metric replay·Solar ambiguity classifier·fallback suite 구현
- 결과: 실제 분류기 39/40, fallback 7/7, 회귀 테스트 19/19
- 판단: 제한 범위 `trial`
