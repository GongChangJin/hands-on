# Agent Evaluation - @ukkhnn 구현

## 구현 정보

- **구현자:** @ukkhnn
- **상태:** active
- **공통 과제:** [프로젝트 과제명세](../../README.md)

## 접근 방식

실제 LLM을 연결하기 전에 결정적으로 성공하거나 실패하는 두 scripted Agent로 평가 runner 자체를 검증합니다. 이후 같은 runner에 실제 모델 adapter를 연결합니다.

## 기술 스택

- 언어·런타임: Python 3.11
- 모델: 아직 연결하지 않음
- 프레임워크: 표준 라이브러리 중심의 작은 runner
- 외부 도구: 없음
- 평가 도구: `jsonschema`, `pytest`, 결정적 grader

## 공통 계약 적용

- TaskRequest 입력: JSONL을 읽을 때 공통 schema로 검증
- AgentResult 출력: Agent 실행 직후 공통 schema로 검증
- ToolTrace 수집: 실행별 목록을 검증하고 도구 순서·안전성 채점에 사용
- EvaluationRecord 생성: 성공과 예외를 모두 보존한 JSONL 생성

## 실행 방법

이 디렉터리에서 실행합니다.

```bash
python -m pytest
PYTHONPATH=src python -m agent_eval.cli --agent oracle
PYTHONPATH=src python -m agent_eval.cli --agent flawed
```

새 환경에서는 먼저 가상 환경을 만들고 개발 의존성을 설치합니다.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
```

실행 결과는 Git에 포함되지 않는 `runs/`에 JSONL로 저장됩니다. 실제 비밀값은 커밋하지 않습니다.

## 결과

- 성공률: scripted oracle 100%, scripted flawed 20% (fixture 기준)
- 지연시간: 로컬 실행 시 측정
- 비용: 미측정
- 대표 실패: 출력 불일치, 허용되지 않은 도구, partial 상태, Agent 예외

## 공통 README에 반영할 결론

진행 후 기록합니다.
