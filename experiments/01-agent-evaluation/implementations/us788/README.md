# Agent Evaluation - @us788 구현

## 구현 정보

- **구현자:** @us788
- **상태:** `active`
- **공통 과제:** [프로젝트 과제명세](../../README.md)
- **구현 이름:** evalkit — 공통 평가 하네스

## 접근 방식

03 Agentic RAG와 06 LLM Router가 같은 계측 기록을 남기도록, 평가 하네스를 이 프로젝트 한 곳에만 두고 나머지 프로젝트는 경로로 참조합니다(`evalkit_bridge.py`). 같은 코드를 프로젝트마다 복제하지 않기 위해서입니다.

grader는 세 계층으로 나눕니다.

- **결정적 검사** — `exact`, `json_valid`, `tool_used`
- **규칙 기반 검사** — `contains`, `regex`, `cited`, `no_forbidden`
- **LLM grader** — `llm`

실험 규칙대로 `llm` grader 단독으로 성공을 판정하지 않습니다. 항상 결정적 grader와 함께 걸고, 불일치는 리포트에 남깁니다.

## 기술 스택

- 언어·런타임: Python 3.11+
- 모델: `models.yaml`에서 논리 라우트(`small`/`balanced`/`frontier`/`local`)로 지정. 코드에 모델 ID를 고정하지 않습니다.
- 프레임워크: LangChain `init_chat_model` — provider 문자열만 바꾸면 Anthropic·OpenAI·Google·Ollama로 그대로 옮겨갑니다.
- 저장소·외부 도구: JSONL (태스크·실행 기록)
- 평가 도구: 자체 구현 (`evalkit`)

## 공통 계약 적용

`common/contracts/`의 공통 계약이 이 구현보다 나중에 들어와서, 현재 `evalkit`은 자체 dataclass를 씁니다. 아래가 대응 관계와 남은 간극입니다.

| 공통 계약 | `evalkit` 대응 | 남은 작업 |
| --- | --- | --- |
| `TaskRequest` | `schema.Task` (`task_id`·`prompt`·`expected`) | `task_type`, `constraints.allowed_tools`, `constraints.forbidden_actions` 필드 추가. `prompt` → `input`, `expected` → `expected_output` 개명 |
| `AgentResult` | `schema.AgentResult` (이름만 같고 형태가 다름) | `status`, `evidence[]`, `actions[]`, `limitations[]` 추가 |
| `ToolTrace` | `schema.ToolCall` | `task_id`, `result_summary` 추가. `name` → `tool_name`, `latency_ms` → `duration_ms` 개명 |
| `EvaluationRecord` | `schema.RunRecord` | `passed` → `task_success`, `implementation` → `implementation_id` 개명. `forbidden_actions`(횟수) → `safety_violations`(문자열 배열)로 형식 변경 |

계약 전환은 소비 측(03·06)과 함께 한 번에 바꿔야 해서 별도 작업으로 둡니다.

## 디렉터리

```text
evalkit/
├── schema.py    Task · ToolCall · Grade · AgentResult · RunRecord
├── loader.py    JSONL 태스크 로더 (중복 task_id 거부)
├── graders.py   grader 레지스트리
├── models.py    provider 비종속 모델 팩토리 + 비용 추정
├── runner.py    반복 실행 + telemetry 수집 (실패도 기록)
└── report.py    마크다운 리포트 (성공률 · p50/p95 · 비용 · 재현성)
agents/echo.py   API 키 없이 배관을 확인하는 더미 에이전트
run_eval.py      CLI
```

## 실행 방법

```bash
pip install -r requirements.txt
cp models.example.yaml models.yaml   # 실제 모델 ID 기입
cp .env.example .env                 # 키 기입

# 배관 점검 (API 호출 없음)
python run_eval.py --tasks tasks/sample.jsonl --agent agents.echo:build --repeats 2
```

`models.yaml`, `.env`, `runs/`는 커밋하지 않습니다.

## 실험 결과

- 성공률: 미측정
- 평균 지연시간: 미측정
- 비용: 미측정
- 도구 정확도: 미측정
- 안전 위반: 미측정

배관 점검은 통과했습니다. 더미 에이전트로 3개 태스크 × 2회 반복을 돌려 리포트 생성까지 확인했습니다.

## 한계

- `cited` grader가 정규식 기반이라 형식만 보고 근거의 진위는 보지 않습니다.
- 비용은 `models.yaml`의 단가표에 의존하는 추정치입니다. 실제 청구액과 대조가 필요합니다.
- 재현성은 성공/실패가 갈리는지만 봅니다. 출력 자체의 분산은 아직 측정하지 않습니다.
- 공통 계약(`common/contracts/`)으로의 전환이 남아 있습니다. 전환 전까지는 다른 참여자의 구현과 같은 표로 비교할 수 없습니다.
- `AgentResult.extra`를 `RunRecord`로 옮기지 않아 소비 측(03·06)이 담은 telemetry가 전량 유실됩니다. 프로젝트 평가 기준의 관측성(누락률 0%)에 걸립니다.
- `run_eval.py`가 cwd를 `sys.path`에 넣지 않아, 다른 프로젝트 디렉터리에서 `--agent`로 로컬 어댑터를 지정하면 import에 실패합니다. 호출 측에서 `PYTHONPATH=.`가 필요합니다.
- `Grade.score`의 의미가 grader마다 다릅니다. 대부분 0.0/1.0인데 `cited`는 인용 개수, `no_forbidden`은 위반 횟수를 담아 `EvaluationRecord.quality_score`(0~1)로 그대로 옮길 수 없습니다.
- 실행 기록을 append로 쌓아 같은 `--out`에 여러 번 실행하면 과거 기록이 섞입니다.
- 평가 태스크가 3건입니다. 프로젝트 완료 조건은 20건 이상입니다.

## 공통 README에 반영할 결론

미정. `run_id`·모델·tool call·token·latency를 담은 `RunRecord`를 `EvaluationRecord` 확장 후보로 제안합니다. 팀 합의가 되면 `common/contracts/`와 `common/evaluation/runner/`에 반영합니다.
