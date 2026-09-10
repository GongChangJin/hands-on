# 06. LLM Router

> 요청에 맞는 모델과 전문 Agent를 선택하여 품질을 유지하면서 비용이나 지연시간을 줄일 수 있는가?

## 프로젝트 정의

- **상태:** `planned`
- **참여자:** `@ukkhnn`, `@us788`
- **역할:** 모델·전문 Agent 선택과 fallback을 담당하는 오케스트레이션 계층
- **선행 프로젝트:** Agent Evaluation, Local/Open-weight LLM, Agentic RAG, Multimodal Agent, AI Research Agent
- **후행 프로젝트:** Computer-use Agent, Coding Agent, 통합 시스템

## 배경과 목적

요청의 유형, 난이도, modality, 도구 필요 여부, 비용과 위험도에 따라 사용할 모델과 전문 Agent를 선택합니다. 앞선 프로젝트의 실측 결과를 정책 입력으로 사용하여 비싼 모델을 항상 호출하는 기준선과 비교합니다.

## 과제 명세

### 입력

- `TaskRequest`
- 사용 가능한 모델과 Agent 목록
- 프로젝트별 품질·비용·지연시간 결과
- 라우팅 정책, confidence 기준과 fallback 조건

### 필수 구현

- `small`, `balanced`, `frontier`, `local` 논리 모델 라우트
- `rag`, `vision`, `research`, `browser`, `coding` Agent 라우트
- 규칙 기반·LLM 기반 또는 하이브리드 분류
- timeout·모델 장애·낮은 confidence fallback
- 선택 결과와 이유를 포함한 구조화 출력

### 산출물

- Router와 정책 설정
- all-frontier 기준선
- 질문별 선택 모델·Agent·이유
- 품질·비용·지연시간 비교표
- fallback 테스트 결과

### 포함 범위

- 단일 또는 복수 전문 Agent 선택
- 계정과 환경에 따른 실제 모델 매핑
- 정책 변경이 가능한 설정 기반 라우팅

### 제외 범위

- 전문 업무를 Router 내부에서 직접 처리
- 모델 ID의 애플리케이션 코드 고정
- 라우터 자체 비용을 제외한 성능 비교

## 권장 기술

- Python 3.11 이상
- Pydantic Structured Output
- 규칙 기반 classifier와 선택적인 소형 LLM classifier
- timeout·retry·circuit breaker
- 공통 LLM·Agent adapter

## 디렉터리 사용

- `shared/`: 공통 질문, 기대 라우트, 모델·Agent capability와 기준선
- `implementations/ukkhnn/`: `ukkhnn`의 라우팅 전략
- `implementations/us788/`: `us788`의 라우팅 전략

## 평가 기준

| 지표 | 측정 방법 | 목표 |
| --- | --- | --- |
| 라우팅 정확도 | 기대 라우트와 비교 | 90% 이상 시도 |
| 품질 | all-frontier 대비 | 5% 이내 저하 시도 |
| 비용 | 태스크당 실측 비용 | 절감률 기록 |
| 지연시간 | p50/p95 | 개선률 기록 |
| fallback | 의도적 장애·낮은 confidence | 정상 복구 |

## 완료 조건

- [ ] 논리 모델명과 실제 모델 매핑이 분리됨
- [ ] 전문 Agent와 모델을 모두 선택할 수 있음
- [ ] all-frontier 기준선과 공정하게 비교함
- [ ] 장애와 낮은 confidence fallback을 검증함
- [ ] 선택 이유와 비용이 `ToolTrace` 또는 metadata에 기록됨

## 구현 비교

| 참여자 | 라우팅 방식 | 정확도 | 품질 | 비용 | 특징 |
| --- | --- | ---: | ---: | ---: | --- |
| `@ukkhnn` | TBD | — | — | — | — |
| `@us788` | TBD | — | — | — | — |

## 결과

진행 후 기록합니다.

## 결론

- **적용 판단:** 미정
- **판단 이유:**
- **적용 가능 범위:**
- **다음 행동:** 선행 프로젝트의 capability·평가 결과 연결

## 변경 기록

### 초기 정의

- 변경: 모델·Agent 이중 라우팅과 fallback 과제 정의
- 결과: `planned`
- 다음 행동: 두 라우팅 전략 선택
