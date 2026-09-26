# 09. Cybersecurity Agent

> Agent가 로컬 취약 코드와 Coding Agent의 patch를 검사하고 결정적 도구로 안전하게 재검증할 수 있는가?

## 프로젝트 정의

- **상태:** `validated` (`@ukkhnn` 결정적 보안 게이트 평가 완료)
- **참여자:** `@ukkhnn`, `@us788`
- **역할:** 코드 변경의 보안 분석·수정·승인 근거를 제공하는 검증 계층
- **선행 프로젝트:** Agent Evaluation, Coding Agent
- **후행 프로젝트:** 통합 시스템

## 배경과 목적

LLM이 취약점을 단독 판단하는 대신 정적 분석과 보안 테스트 결과를 해석하고, 수정 patch를 제안한 뒤 재검사합니다. 의도적으로 만든 로컬 샘플만 사용하고 실행 환경을 제한합니다.

## 과제 명세

### 입력

- 알려진 취약점이 포함된 로컬 샘플
- Coding Agent가 생성한 patch
- 예상 finding과 보안·회귀 테스트
- 컨테이너 권한·네트워크·자원 제한

### 필수 구현

- 정적 분석 실행과 finding 구조화
- 중복·오탐 후보 분류와 수정 우선순위
- 제한된 patch 생성 또는 수정 제안
- 정적 분석 재실행
- 보안 테스트와 기존 기능 회귀 테스트
- 잔여 위험과 승인·차단 결과 생성

### 산출물

- 보안 분석 Agent
- finding·수정·재검사 기록
- 보안·회귀 테스트 결과
- 탐지율·수정 성공률·오탐 비교표
- 통합 시스템이 사용할 승인 또는 차단 결과

### 포함 범위

- SQL injection, 경로 순회, 하드코딩 비밀값 등 로컬 샘플
- 제한된 컨테이너에서의 정적 분석과 테스트
- Coding Agent patch의 추가 검증

### 제외 범위

- 외부 시스템 스캔·공격·취약점 악용
- `--privileged` 실행과 Docker socket 전달
- 정적 분석·테스트 없이 LLM 판단만으로 승인

## 권장 기술

- Semgrep CE
- Python은 Bandit·pip-audit, Node는 npm audit 등 생태계 도구
- Docker 또는 동등한 격리 환경
- pytest 등 회귀·보안 테스트 도구
- Git diff와 dependency 변경 검사

## 디렉터리 사용

- `shared/`: 취약 샘플, 예상 finding, 보안 테스트와 격리 정책
- `implementations/ukkhnn/`: `ukkhnn`의 탐지·수정 전략
- `implementations/us788/`: `us788`의 탐지·수정 전략

## 평가 기준

| 지표 | 측정 방법 | 목표 |
| --- | --- | --- |
| 탐지율 | 알려진 취약점과 비교 | 100% 시도 |
| 수정 성공률 | 재검사·보안 테스트 | 80% 이상 |
| 회귀 | 기존 기능 테스트 | 전체 통과 |
| 오탐 | 정답 finding과 비교 | 기록·분석 |
| 격리 | 네트워크·host 접근 위반 | 0회 |

## 완료 조건

- [x] 알려진 취약 샘플을 공통 조건으로 검사함
- [x] 수정 후 정적 분석과 보안 테스트를 재실행함
- [x] 기존 기능 회귀 여부를 확인함
- [x] 외부 대상 접근과 과도한 권한을 차단함
- [x] 통합 시스템에 승인·차단·잔여 위험을 반환할 수 있음

## 구현 비교

| 참여자 | 분석·수정 구성 | 탐지율 | 수정 성공률 | 오탐 | 특징 |
| --- | --- | ---: | ---: | ---: | --- |
| `@ukkhnn` | Semgrep·Bandit·pytest·격리 Docker·참조 수정 replay | 100% | 100% | 0 | 08 patch 5개 추가 승인 |
| `@us788` | TBD | — | — | — | — |

## 결과

`@ukkhnn` 구현은 Python 로컬 fixture의 SQL injection 2건, 경로 순회 2건, 가짜 하드코딩 비밀값 2건을 Semgrep과 Bandit으로 정규화·중복 제거했다. 알려진 취약점 6건을 모두 찾고 정상 대조군 3개에서 finding을 만들지 않았다. 결정적 참조 수정 세트를 적용한 뒤 같은 정적 분석과 보안·기능 테스트를 다시 실행해 잔여 finding 0건과 전체 테스트 통과를 확인했다.

| 지표 | 결과 |
| --- | ---: |
| 알려진 취약점 탐지 | 6/6 (100%) |
| 수정 성공 | 6/6 (100%) |
| 정상 대조군 / 오탐 | 3 / 0 |
| 수정 후 잔여 finding | 0 |
| 격리 probe | 3/3 |
| Coding Agent handoff 승인 | 5/5 |

컨테이너는 네트워크 없음, 읽기 전용 root와 workspace, 모든 Linux capability 제거, `no-new-privileges`, 비-root 사용자, CPU·메모리·PID·시간 제한을 적용했다. 08의 5개 patch는 각 replay workspace에 독립 held-out 테스트를 다시 주입해 정적 분석과 전체 회귀 테스트를 통과한 경우에만 승인했다. 결과는 공통 `TaskRequest`, `AgentResult`, `ToolTrace`, `EvaluationRecord`와 통합용 승인 기록으로 보존한다.

이번 결과는 세 종류의 Python 취약점과 고정 참조 수정에 대한 보안 게이트 기준선이다. 전체 취약점 부재를 증명하지 않으며 dependency scan, 동적 보안 테스트, live LLM 수정 품질은 측정하지 않았다.

## 결론

- **적용 판단:** 제한된 patch 승인 게이트 `trial`, 자동 보안 수정 `hold`
- **판단 이유:** 탐지·수정·회귀·격리 기준과 08 handoff 5건은 모두 통과했지만 규칙 범위와 수정 입력이 결정적 기준선으로 제한된다.
- **적용 가능 범위:** 허용 취약점 범주와 결정적 테스트가 명확한 Python patch의 병합 전 보안 재검증
- **다음 행동:** Integration에서 08→09 승인 체인을 연결하고 dependency scan과 별도 취약 corpus를 추가한다.

## 변경 기록

### 초기 정의

- 변경: 보안 분석·수정·재검증 과제 정의
- 결과: `planned`
- 다음 행동: 두 분석 전략 선택

### 2026-09-26 — @ukkhnn 결정적 보안 게이트 검증 완료

- 변경: 취약 fixture, Semgrep·Bandit finding 정규화, 참조 수정, 격리 Docker 실행, 보안·회귀 테스트, 공통 계약과 08 handoff 재검증 구현
- 결과: 탐지 6/6, 수정 6/6, 오탐 0, 격리 probe 3/3, Coding Agent patch 승인 5/5
- 다음 행동: Integration에 승인 결과 연결, dependency·동적 검사와 별도 corpus 보강
