# Agent Evaluation with Phoenix - @ukkhnn

## 구현 정보

- **구현자:** @ukkhnn
- **상태:** completed
- **공통 과제:** [프로젝트 과제명세](../../README.md)
- **협업 방식:** @ukkhnn과 @us788이 각각 독립 구현하고, 실행 결과와 학습 결론을 공유해 비교

## 무엇을 익히는 구현인가

평가 runner를 직접 만드는 데 집중하지 않고 실제 Agent 실행을 Phoenix로 관측한 뒤, 같은 Dataset으로 모델과 Agent 구조를 한 변수씩 비교한다.

```text
DeepSeek / Upstage
  → OpenAI Agents SDK (tools, handoffs)
  → OpenInference + OpenTelemetry (traces)
  → Phoenix (Dataset, Experiment, CODE/LLM evaluations)
  → EvaluationRecord (JSONL, CSV, Markdown)
```

## 기술 스택

- Python 3.11, `jsonschema`, pytest
- OpenAI Agents SDK: Agent loop, function tools, handoffs
- 모델 API: Upstage Solar / DeepSeek OpenAI 호환 Chat Completions
- 관측: OpenInference, OpenTelemetry, Arize Phoenix
- 평가: Phoenix Dataset / Experiment / CODE evaluator / 선택적 LLM evaluator
- 실행 환경: Docker Compose

## 공통 계약 적용

저장소의 `common/contracts` 원본을 직접 읽어 Draft 2020-12 JSON Schema로 검증한다.

- `TaskRequest`: Phoenix example 업로드 전에 변환·검증
- `AgentResult`: Agent 성공·실패 출력을 모두 검증
- `ToolTrace`: tool call/output을 연결해 검증하고 실제 시간은 Phoenix span에서 조회
- `EvaluationRecord`: Experiment 결과를 내보내기 전에 검증

## 환경 준비

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
docker compose up -d
```

실제 키는 파일이나 Git에 저장하지 않고 실행하는 터미널에만 설정한다.

```bash
export UPSTAGE_API_KEY='...'
# 또는
export DEEPSEEK_API_KEY='...'
```

기본 모델은 Upstage `solar-pro4`, DeepSeek `deepseek-v4-flash`이며 `--model`로 바꿀 수 있다.

## 실행 흐름

### 1. trace 읽기

```bash
./run-agent --provider upstage
```

Phoenix의 `Projects > 01-agent-evaluation > Traces`에서 workflow → Agent → LLM → Tool 계층과 입력·출력·지연을 확인한다.

### 2. 20개 Dataset 업로드

```bash
./upload-dataset
```

`agent-tool-use-golden-v1`은 계산 10개, 프로젝트 조회 5개, 두 도구 결합 5개로 구성된다. 정답, 필수 도구, handoff 목표 Agent를 실행 전에 고정한다.

### 3. 한 모델 또는 구조 실행

```bash
./run-experiment --provider upstage --architecture single
./run-experiment --provider upstage --architecture handoff
```

`--repetitions 3`처럼 반복 수를 늘릴 수 있다. DeepSeek은 본 실험 전에 model-list 요청으로 연결과 인증을 확인하며 example을 순차 실행한다.

### 4. Agent 구조 자동 비교

```bash
./run-comparison --provider upstage --repetitions 1
```

같은 provider, model, Dataset, evaluator를 유지하고 `single`과 `handoff`만 바꾼다.

- `single`: Agent 하나가 두 function tool을 직접 선택
- `handoff`: Triage Agent가 Calculator / Project / Combined Specialist 중 하나로 제어권 전달
- handoff 입력에서는 이전 tool history를 제거해 전문 Agent가 transfer tool을 다시 호출하는 회귀를 줄임

### 5. 선택적 LLM judge

```bash
./run-experiment --provider upstage --architecture single --llm-judge
```

LLM judge는 `kind=LLM` annotation으로만 기록한다. `task_success`는 아래 CODE evaluator만으로 결정하므로 LLM 판정이 성공 여부를 뒤집지 않는다.

| evaluator | kind | 확인 내용 |
| --- | --- | --- |
| `answer-contains-required-text` | CODE | 필수 사실 포함 |
| `tool-accuracy` | CODE | 누락·추가·중복 도구 호출 |
| `safe-tool-use` | CODE | 허용되지 않은 도구 호출 |
| `tool-execution-success` | CODE | 도구 실행 오류 |
| `handoff-route-correct` | CODE | handoff 구조의 최종 전문 Agent |
| `semantic-quality-llm` | LLM | 답변의 직접성·기대 사실과의 모순 여부 |

## 결과 파일

각 Experiment는 다음 파일을 자동 생성한다.

- `records.jsonl`: 공통 `EvaluationRecord` 전체
- `records.csv`: 표 분석용 평탄화 결과
- `summary.json`: 성공률, p50/p95, usage, 추정 비용, 실패 유형
- `report.md`: 사람이 읽는 실행별 표
- `comparison.md`: 두 구조를 나란히 비교한 표

실제 결과는 [`reports/`](reports/)에 보존한다. 실패와 예외도 삭제하지 않는다.

## 실험 결과

### 모델 교체 학습용 첫 실험

초기 3개 example에서 두 모델은 CODE 평가를 모두 통과했다. 작은 1회 표본이므로 모델의 일반적인 우열이 아니라 provider 교체와 Phoenix 비교 흐름 확인용이다.

| provider / model | 통과 | 평균 latency | 평균 tokens |
| --- | ---: | ---: | ---: |
| DeepSeek / `deepseek-v4-flash` | 6/6 | 2.0초 | 1,169 |
| Upstage / `solar-pro4` | 6/6 | 3.5초 | 866 |

### Agent 구조 비교 — 20개 example, Upstage `solar-pro4`

최종 v2 결과는 [`comparison.md`](reports/upstage-solar-pro4-architecture-v2/comparison.md)에 있다.

| architecture | 성공률 | p50 | p95 | tokens | Agent 호출 추정 비용 | 안전 위반 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| single | 100% (20/20) | 2,071ms | 3,564ms | 18,661 | $0.006528 | 0 |
| handoff | 95% (19/20) | 2,651ms | 3,927ms | 24,046 | $0.008477 | 0 |

handoff는 single보다 p50이 약 28%, token이 약 29%, 추정 비용이 약 30% 늘었다. 이 문제처럼 도구가 두 개뿐이고 라우팅이 단순한 경우에는 전문 Agent 분리의 추가 모델 호출 비용이 이득보다 컸다.

handoff 실패 1건(`calc-divide`)은 Calculator Specialist까지 도달하고 정답 12도 답했지만 `calculator`를 호출하지 않았다. 답변 문자열만 보면 통과할 수 있는 회귀를 tool trace 평가가 잡아냈다.

### LLM judge 분리 확인

[`upstage-solar-pro4-single-llm-judge`](reports/upstage-solar-pro4-single-llm-judge/) 실행에서 CODE 성공 20/20과 LLM `PASS` 20/20을 별도 annotation으로 확인했다. 보고서의 비용은 Agent task 호출만 추정하며 evaluator 호출 비용은 제외한다.

## 비용 해석

usage의 input, cached input, output token을 provider의 공개 단가에 적용한 추정치다. 알 수 없는 `--model` override는 가격을 추측하지 않고 `N/A`로 남긴다.

- Upstage Solar Pro 4: [공식 API 가격](https://www.upstage.ai/pricing/api)
- DeepSeek V4 Flash: [공식 모델·가격](https://api-docs.deepseek.com/quick_start/pricing/)

DeepSeek은 UTC 평일 peak/off-peak 배율을 반영한다. 실제 청구액은 provider 콘솔을 최종 기준으로 삼는다.

## 회귀와 완료 확인

- exploratory run에서 handoff의 tool 생략, transfer tool 반복, 모호한 tool argument를 발견하고 결과를 보존했다.
- handoff history filter, 전문 Agent 지시 강화, 안전한 `^`/프로젝트 별칭 정규화를 적용했다.
- 최종 suite는 25개 로컬 테스트로 Dataset 개수, 네 계약, evaluator, 실패 보존, 비용, p50/p95, 세 형식 export를 검증한다.

```bash
python -m pytest
```

## 결론

- 현재 범위에는 `single` Agent를 기본으로 적용한다.
- handoff는 전문 영역이 실제로 독립적이고 복합 orchestration의 이득이 추가 latency·token보다 클 때 다시 평가한다.
- 이후 핸즈온도 같은 `TaskRequest → Phoenix Experiment → EvaluationRecord` 흐름을 재사용한다.
- 종료는 `docker compose down`을 사용한다. `down -v`는 보존된 Phoenix 데이터를 지우므로 사용하지 않는다.
