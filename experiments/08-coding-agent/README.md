# 08. Coding Agent

> Agent가 Issue를 분석하고 제한된 범위의 코드를 수정한 뒤 테스트로 결과를 검증할 수 있는가?

## 프로젝트 정의

- **상태:** `planned`
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

- [ ] Issue 5개 이상을 공통 조건으로 실행함
- [ ] 기존 테스트와 신규 회귀 테스트가 통과함
- [ ] 요구와 무관한 변경을 검사함
- [ ] 실패와 중단 이유를 결과에 포함함
- [ ] Cybersecurity Agent에 patch와 검증 결과를 전달할 수 있음

## 구현 비교

| 참여자 | 모델·도구 구성 | 성공률 | 평균 반복 | 비용 | 특징 |
| --- | --- | ---: | ---: | ---: | --- |
| `@ukkhnn` | TBD | — | — | — | — |
| `@us788` | TBD | — | — | — | — |

## 결과

진행 후 기록합니다.

## 결론

- **적용 판단:** 미정
- **판단 이유:**
- **적용 가능 범위:**
- **다음 행동:** 샘플 저장소와 Issue 세트 확정

## 변경 기록

### 초기 정의

- 변경: Issue→patch→test 과제와 권한 경계 정의
- 결과: `planned`
- 다음 행동: 구현 도구 조합 선택
