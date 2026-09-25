# 07. Computer-use Agent

> Agent가 허용된 테스트 사이트에서 검색·입력·검증 작업을 안전하고 재현 가능하게 완료할 수 있는가?

## 프로젝트 정의

- **상태:** `validated` (`@ukkhnn` 구현·로컬 평가 완료, 독립 구현 비교는 후속 작업)
- **참여자:** `@ukkhnn`, `@us788`
- **역할:** 브라우저 화면을 해석하고 제한된 행동을 실행하는 Agent
- **선행 프로젝트:** Agent Evaluation, Multimodal Agent, LLM Router
- **후행 프로젝트:** 통합 시스템

## 배경과 목적

Agent가 접근성 트리 또는 스크린샷을 보고 클릭·입력·스크롤 행동을 선택한 뒤 최종 DOM 상태로 성공 여부를 검증합니다. 외부 상태를 변경하는 Agent이므로 기능 성공률과 함께 권한·도메인·행동 제한을 검증합니다.

## 과제 명세

### 입력

- 로컬 또는 전용 테스트 사이트
- 검색·폼 입력·검증 태스크 10개 이상
- 허용 도메인·행동과 금지 행동
- 최대 step과 최종 성공 조건

### 필수 구현

- 태스크마다 격리된 browser context 생성
- 접근성 트리 또는 스크린샷 상태 수집
- 구조화된 browser action 생성과 실행
- 행동 후 화면·URL·DOM 재검증
- 전체 trace·행동·실패 원인 기록

### 산출물

- 브라우저 Agent
- 공통 테스트 사이트 또는 fixture
- 태스크별 실행 trace와 작은 결과 요약
- 성공률·평균 action·복구율 비교표

### 포함 범위

- 테스트 환경의 검색·입력·검증
- 실패 후 제한된 재시도와 복구
- read-only 또는 되돌릴 수 있는 행동

### 제외 범위

- 실제 결제·메일 발송·예약·계정 변경
- 허용되지 않은 도메인 접근
- 사람 승인 없는 되돌리기 어려운 최종 제출

## 권장 기술

- Playwright
- Python 또는 TypeScript
- Vision LLM 또는 접근성 snapshot 기반 LLM
- Pydantic·JSON Schema
- Playwright trace와 DOM assertion

## 디렉터리 사용

- `shared/`: 테스트 사이트, 태스크, 허용 정책과 성공 판정 조건
- `implementations/ukkhnn/`: `ukkhnn`의 browser Agent
- `implementations/us788/`: `us788`의 browser Agent

## 평가 기준

| 지표 | 측정 방법 | 목표 |
| --- | --- | --- |
| 태스크 성공률 | 최종 DOM 상태 검사 | 80% 이상 |
| 안전성 | 범위 밖 행동·도메인 접근 | 0회 |
| 효율 | 태스크당 action 수 | 비교 기록 |
| 복구율 | 의도적 UI 변경·실패 | 복구 결과 기록 |
| 재현성 | trace와 상태 검사 | 전 태스크 보존 |

## 완료 조건

- [x] 공통 태스크 12개를 조건별 2회 자동 실행함
- [x] 최종 DOM 상태로 성공 여부를 판정함
- [x] 도메인·행동·step·복구 제한을 검증함
- [x] DOM/accessibility와 실패 시 screenshot 증거·접근성 fallback을 비교함
- [x] 공통 계약과 `web_navigation` capability를 제공함

## 구현 비교

| 참여자 | 화면 표현 | 모델·도구 | 성공률 | 평균 action | 특징 |
| --- | --- | --- | ---: | ---: | --- |
| `@ukkhnn` | DOM/accessibility + 실패 시 screenshot 증거 | Python·Playwright·결정적 planner | 100.0% | 1.83 | 접근성 이름 fallback, 정책 선검사 |
| `@us788` | TBD | TBD | — | — | planned |

## 결과

`@ukkhnn` 구현은 12개 태스크를 두 조건에서 각각 2회 실행했다. 모든 실행은 새 browser context를 사용하고, Agent의 완료 선언이 아니라 최종 DOM assertion으로 성공을 판정했다.

| 조건 | 성공 | 평균 action | 복구 | p50 / p95 | screenshot 관측 |
| --- | ---: | ---: | ---: | ---: | ---: |
| DOM/accessibility | 22/24 (91.7%) | 1.75 | 4/6 (66.7%) | 1,275.8 / 2,243.1ms | 0 |
| 실패 시 screenshot 증거 + 접근성 fallback | 24/24 (100.0%) | 1.83 | 6/6 (100.0%) | 1,373.8 / 2,268.8ms | 4 |

DOM 전용 조건은 ID가 바뀐 저장 버튼을 두 반복 모두 찾지 못했다. 보완 조건은 action 오류가 난 시점에만 screenshot hash를 trace에 남기고 접근성 이름으로 재탐색해 두 건을 복구했다. 6개 안전 probe는 모두 통과했고 실제 외부 navigation은 0회였다. 48개 실행의 `TaskRequest`, `AgentResult`, `ToolTrace`, `EvaluationRecord`와 실패 trace를 결과 디렉터리에 보존했다.

현재 planner는 공통 fixture의 시나리오를 아는 결정적 baseline이다. Screenshot을 의미적으로 해석하는 vision model은 사용하지 않았으며, 단일 합성 사이트·Google Chrome·인증 없는 되돌릴 수 있는 행동만 검증했다. 따라서 실제 웹의 임의 UI와 장기 작업에 대한 일반화 근거로 사용하지 않는다.

## 결론

- **적용 판단:** `trial`
- **판단 이유:** 제한된 로컬 UI에서 목표 성공률과 안전 경계를 만족했고, 실패 시에만 증거를 추가하는 복구 방식의 효과를 재현했다.
- **적용 가능 범위:** 허용 origin과 최종 DOM 조건이 명확한 내부 테스트·되돌릴 수 있는 브라우저 작업
- **다음 행동:** Coding Agent(08) 구현 후 실행형 Agent의 공통 승인·검증 흐름을 통합한다.

## 변경 기록

### 초기 정의

- 변경: 브라우저 행동·검증·안전 경계를 과제로 정의
- 결과: `planned`
- 다음 행동: 화면 표현 방식 분담

### 2026-09-25 — @ukkhnn 구현 검증 완료

- 변경: 격리 실행, 정책 가드, 결정적 planner, 실패 시 screenshot 증거와 접근성 fallback, 공통 계약 export 구현
- 결과: adaptive 조건 24/24, 복구 6/6, 안전 probe 6/6, 회귀 테스트 18/18
- 다음 행동: `@us788` 독립 구현 비교와 통합 시스템 연결
