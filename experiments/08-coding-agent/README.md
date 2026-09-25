# 08. Coding Agent

> Agent가 Issue를 분석하고 제한된 범위의 코드를 수정한 뒤 테스트로 결과를 검증할 수 있는가?

## 프로젝트 정의

- **상태:** `validated` (`@ukkhnn` 실행 제어 계층 평가 완료, live 모델 평가는 후속 작업)
- **참여자:** `@ukkhnn`, `@us788`
- **역할:** 요구사항을 검증된 코드 patch로 전환하는 실행형 Agent
- **선행 프로젝트:** Agent Evaluation, LLM Router
- **후행 프로젝트:** Cybersecurity Agent, 통합 시스템

## 배경과 목적

Issue 분석, 저장소 탐색, patch 작성, 테스트와 재수정 루프를 자동화합니다. 코드 생성량보다 요구사항 일치, 회귀 방지, 변경 범위와 재현 가능한 검증 결과를 중점적으로 평가합니다.

## 과제 명세

### 입력

- 테스트가 포함된 샘플 저장소
- 버그·validation·리팩터링 Issue 5개 이상
- 수정 허용 범위와 금지 Git 작업
- 공개 테스트와 별도 판정 테스트

### 필수 구현

- Issue 요구사항과 완료 조건 추출
- 관련 파일 탐색과 수정 계획
- patch 적용
- 기존 테스트·신규 회귀 테스트·lint 실행
- 실패 원인 분석과 제한된 재수정
- 최종 diff·검증 결과·남은 위험 요약

### 산출물

- Coding Agent
- Issue별 코드 patch
- 신규 또는 수정된 테스트
- 테스트·lint 실행 결과
- Issue 성공률과 변경 범위 비교표

### 포함 범위

- 개인 branch 또는 임시 worktree의 샘플 저장소
- 결정적 테스트가 가능한 작은 Issue
- 승인 전 patch와 결과 요약 생성

### 제외 범위

- 보호 브랜치 직접 수정
- force push와 자동 merge
- 테스트 없는 변경의 성공 판정
- 비밀값을 모델 입력에 포함

## 권장 기술

- Git과 격리된 worktree
- Python 프로젝트는 pytest·ruff, TypeScript 프로젝트는 대응 테스트·lint 도구
- 파일 검색·patch·명령 실행 tool adapter
- LLM Router와 공통 evaluation runner

## 디렉터리 사용

- `shared/`: 샘플 저장소 준비법, Issue, 공개 테스트와 판정 규칙
- `implementations/ukkhnn/`: `ukkhnn`의 Coding Agent
- `implementations/us788/`: `us788`의 Coding Agent

## 평가 기준

| 지표 | 측정 방법 | 목표 |
| --- | --- | --- |
| Issue 성공률 | 판정 테스트 통과율 | 80% 이상 |
| 회귀 | 기존 기능 테스트 | 전체 통과 |
| 테스트 품질 | 신규 회귀 테스트 확인 | 변경별 포함 |
| 변경 범위 | 요구와 무관한 diff | 0건 |
| 안전성 | 금지 Git 작업 | 0회 |

## 완료 조건

- [x] Issue 5개를 공통 조건으로 실행함
- [x] 기존 테스트와 신규 회귀 테스트가 통과함
- [x] 요구와 무관한 변경을 검사함
- [x] 실패와 미수행 이유를 결과에 포함함
- [x] Cybersecurity Agent에 patch와 검증 결과를 전달할 수 있음

## 구현 비교

| 참여자 | 모델·도구 구성 | 성공률 | 평균 반복 | 비용 | 특징 |
| --- | --- | ---: | ---: | ---: | --- |
| `@ukkhnn` | Python·pytest·ruff·고정 참조 patch replay | 100.0% | 1.00 | $0.000000 | 격리 실행, 정책 선검사, 독립 held-out 판정 |
| `@us788` | TBD | — | — | — | — |

## 결과

`@ukkhnn` 구현은 태그 정규화, 우선순위 파싱, 중첩 설정 병합, 영업일 계산, 제목 축약의 5개 Issue를 각각 새 임시 작업공간에서 실행했다. 공개 테스트, Agent가 추가한 회귀 테스트, patch 생성 뒤에만 주입한 held-out 테스트와 ruff가 전부 통과했다. 각 회귀 테스트는 원본 fixture에서 실패하는지 별도로 확인했다.

| 지표 | 결과 |
| --- | ---: |
| Issue 성공률 | 5/5 (100.0%) |
| 공개 / 회귀 / held-out / lint 통과율 | 각 100.0% |
| 원본 버그 탐지 회귀 테스트 | 5/5 (100.0%) |
| 허용 변경 범위 준수 | 5/5 (100.0%) |
| 평균 시도 | 1.00 |
| p50 / p95 | 497.4 / 598.5ms |
| 안전 위반 / 금지 Git 작업 | 0 / 0 |

이번 평가는 외부 제공자에 소스 코드를 전송하지 않고 고정 참조 patch를 재생했다. 따라서 위 성공률은 patch 적용, 제한된 재시도, 결정적 도구 실행, 독립 판정, 결과 export가 올바르게 연결됐다는 기준선이다. live 모델의 Issue 해석과 patch 생성 품질은 측정하지 않았다. 외부 provider 경로는 구현했지만 코드 전송 승인이 없어 실행하지 않았고, 로컬 생성 모델도 설치되어 있지 않았다. 명백한 process·network·직접 파일 접근 구문은 실행 전에 거부하지만, 이 정적 검사는 우회 불가능한 OS sandbox를 대신하지 않는다.

결과 디렉터리는 5개 diff와 `TaskRequest`, `AgentResult`, `ToolTrace`, `EvaluationRecord`를 보존한다. `cybersecurity-handoff.json`은 09가 각 patch를 보안 재검증할 수 있도록 변경 경로, 테스트 판정, 안전 위반과 검토 결정을 묶는다.

## 결론

- **적용 판단:** 실행·평가 제어 계층 `trial`, 자동 patch 생성 `hold`
- **판단 이유:** 5개 기준선에서 기능·회귀·범위·안전 판정은 모두 통과했지만 live 모델의 생성 품질은 검증하지 않았다.
- **적용 가능 범위:** 허용 경로와 결정적 테스트가 명확한 로컬 샘플의 patch 검증·평가
- **다음 행동:** Cybersecurity Agent(09)가 handoff patch를 정적 분석·보안 테스트로 재검증하고, 별도 승인 또는 로컬 모델 준비 후 live provider 비교를 추가한다.

## 변경 기록

### 초기 정의

- 변경: Issue→patch→test 과제와 권한 경계 정의
- 결과: `planned`
- 다음 행동: 구현 도구 조합 선택

### 2026-09-25 — @ukkhnn 실행 제어 계층 검증 완료

- 변경: 격리 fixture, 허용 경로 정책, 제한된 patch loop, 원본 실패 회귀 검사, held-out 판정, 공통 계약과 09 handoff 구현
- 결과: 참조 replay 5/5 성공, 회귀·held-out·lint·범위 각 100%, 안전 위반과 금지 Git 작업 0건
- 다음 행동: 09에서 patch 보안 재검증 후 승인된 live provider 또는 로컬 모델 비교
