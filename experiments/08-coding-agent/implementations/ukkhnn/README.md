# Coding Agent - @ukkhnn 구현

## 구현 정보

- **상태:** validated control plane / live generation pending
- **방식:** 정책 선검사 + 고정 참조 patch replay + 독립 held-out 판정
- **런타임:** Python 3.11 이상, Pydantic 2, JSON Schema, pytest, ruff
- **모델:** `reference-replay-v1`(외부 전송 없는 결정적 기준선)
- **공통 과제:** [프로젝트 과제명세](../../README.md)

## 접근 방식

Issue마다 동일 fixture를 새 임시 디렉터리에 복사한다. Agent는 명시된 context와 허용 경로만 읽고, 제안된 파일 전체 교체를 path·symlink·파일 수·크기 정책으로 검사한다. 실행 도구는 고정된 `pytest`와 `ruff`뿐이며 shell과 Git 명령은 제공하지 않는다.

이번 실행은 외부 제공자에 저장소 코드를 보내지 않았다. 5개 참조 patch를 결정적으로 재생해 patch 적용부터 재시도, 회귀 테스트의 원본 실패 확인, held-out 테스트 주입, 범위 검사, 공통 계약 export까지 실행 제어 계층을 검증했다. 따라서 100% 성공률은 Agent harness의 기준선이며 실시간 모델의 코드 생성 성능이 아니다.

`SolarPatchProvider`는 구조화 JSON 응답과 사용량 기반 비용 계산을 구현했지만, live 실행에는 Issue와 허용된 소스 파일을 외부 제공자에 전송하는 별도 승인이 필요하다. 이번 결과에는 포함하지 않았다.

## 공통 계약과 안전 경계

- `TaskRequest`: Issue, 완료 조건, context, 허용 도구·경로와 최대 시도 횟수
- `AgentResult`: patch 경로, 변경 파일, 공개·회귀·held-out·lint 결과와 증거
- `ToolTrace`: 고정 명령, 저장소 쓰기, provider 호출의 입력 요약·결과·지연시간
- `EvaluationRecord`: 성공, 품질, 도구 정확도, 비용, 안전 위반과 실패 유형
- 시도 2회, 변경 파일 2개, 파일당 20KB, 명령당 30초로 제한
- 경로 이탈·symlink·허용 밖 파일·회귀 테스트 누락과 process·network·직접 파일 접근 Python 구문을 적용 전에 거부
- subprocess 환경에서 API 비밀값을 제거하고 Git·네트워크 도구를 노출하지 않음

## 환경 준비와 실행

```bash
cd experiments/08-coding-agent/implementations/ukkhnn

python3.11 -m venv .venv
.venv/bin/pip install '.[dev]'
.venv/bin/python -m pytest
./run-coding-agent
```

기본 실행은 네트워크를 사용하지 않고 `results/reference-replay-v1/`에 patch, 실행 trace, 공통 계약 레코드, 요약, 보고서와 09용 handoff manifest를 생성한다.

## 결과

| 지표 | 결과 |
| --- | ---: |
| Issue 성공 | 5/5 (100.0%) |
| 공개 / 신규 회귀 / held-out / lint | 모두 5/5 |
| 원본 버그를 잡는 회귀 테스트 | 5/5 |
| 허용 범위 준수 | 5/5 |
| 평균 시도 | 1.00 |
| p50 / p95 | 497.4 / 598.5ms |
| 안전 위반 / 금지 Git 작업 | 0 / 0 |
| API token / 비용 | 0 / $0.000000 |

구현 자체 회귀 테스트는 19/19 통과했다. 대표 실패는 없었고, 미수행 항목은 live provider 생성 품질 평가다. `cybersecurity-handoff.json`은 5개 patch를 모두 `ready_for_security_review`로 표시하며 09가 재검증할 경로와 판정 근거를 함께 제공한다.

## 적용 판단

격리 실행·정책 검사·테스트 판정·09 handoff 제어 계층은 `trial`로 사용할 수 있다. 자동 코드 생성은 `hold`로 둔다. 정적 Python 구문 검사는 명백한 process·network·파일 접근을 차단하지만 우회 불가능한 OS sandbox는 아니다. 실제 적용 전에는 09의 제한된 컨테이너에서 patch를 재검증하고, 승인된 소스 전송 정책 아래 live provider를 실행하거나 로컬 생성 모델을 연결해 독립 Issue corpus에서 같은 평가를 반복해야 한다.
