# Cybersecurity Agent - @ukkhnn 구현

## 구현 정보

- **상태:** validated deterministic security gate
- **방식:** 정적 분석 정규화 + 결정적 참조 수정 + 격리 재검사 + 08 handoff 승인
- **공통 과제:** [프로젝트 과제명세](../../README.md)

## 접근 방식

Semgrep과 Bandit 결과를 범주·경로·줄 단위로 합치고 `expected-findings.json`과 대조한다. 취약 fixture는 새 임시 workspace에 복사하며, 기능 기준선을 확인한 뒤 보안 테스트가 실제로 실패하는지 검사한다. 참조 수정은 SQL 매개변수화, 경로 containment, 환경 변수 기반 비밀값 주입으로 제한한다. 수정 후 동일 스캔과 전체 pytest를 다시 실행해 임계값, 잔여 finding, 회귀와 격리 probe가 모두 통과한 경우에만 승인한다.

08의 `cybersecurity-handoff.json` 5건은 각각 독립 workspace에 patch와 해당 held-out 테스트를 주입한다. Semgrep·Bandit finding이 없고 공개·회귀·held-out 테스트가 모두 통과하며 08의 선행 검증이 유효한 경우에만 `approve`를 반환한다.

## 기술 스택

- 언어·런타임: Python 3.11 이상
- 모델: 사용하지 않음(`deterministic-container-v1`)
- 프레임워크: Pydantic 2, JSON Schema
- 외부 도구: Docker, Semgrep 1.178.0, Bandit 1.9.4, pytest 9.1.1
- 평가 도구: 공통 계약 validator와 자체 security evaluation runner

## 공통 계약 적용

- `TaskRequest`: fixture 또는 08 source task, 허용 도구, 금지 행동과 평가 출력
- `AgentResult`: 승인·차단, finding·테스트 증거, 수행 action과 잔여 위험
- `ToolTrace`: Semgrep·Bandit·pytest 입력 요약, 종료 상태, 지연시간과 컨테이너 제한
- `EvaluationRecord`: 성공, 탐지·수정 품질, 도구 정확도, 비용과 안전 위반

## 실행 방법

```bash
cd experiments/09-cybersecurity-agent/implementations/ukkhnn
./run-security-agent
```

Docker Desktop 또는 호환 Docker 엔진이 필요하다. 실행기는 고정 버전 이미지를 만들고 `results/deterministic-container-v1/`에 finding, 수정 diff, 도구 trace, 격리 probe, 08 handoff 승인, 공통 계약 레코드, 요약과 보고서를 생성한다. 컨테이너에 실제 API 비밀값을 전달하지 않으며 fixture 값은 명시적으로 가짜다.

## 결과

| 지표 | 결과 |
| --- | ---: |
| 탐지율 | 6/6 (100%) |
| 수정 성공률 | 6/6 (100%) |
| 잔여 finding / 오탐 | 0 / 0 |
| 기능·보안 회귀 | 통과 |
| 격리 probe | 3/3 |
| 08 handoff 승인 | 5/5 |
| 모델 호출 / 비용 | 0 / $0.00 |

구현 자체 회귀 테스트는 19/19 통과했다. 결과 trace는 fixture 7개와 handoff 15개로 총 22개다. 대표 실패는 없었다. 규칙은 Python의 세 취약점 범주만 다루며 dependency·동적 검사는 제외한다. 참조 수정 replay는 게이트와 증거 체인을 검증하지만 live LLM의 수정 품질을 측정하지 않는다.

## 공통 README에 반영할 결론

허용 범주와 테스트가 명확한 Python patch의 병합 전 보안 승인 게이트는 `trial`로 적용한다. 자동 보안 수정은 별도 corpus와 live 생성 평가 전까지 `hold`로 둔다.
