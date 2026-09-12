# Agent Evaluation with Phoenix - @ukkhnn

## 구현 정보

- **구현자:** @ukkhnn
- **상태:** active
- **공통 과제:** [프로젝트 과제명세](../../README.md)

## 접근 방식

평가 runner를 직접 만드는 대신 실제 Agent 실행을 Arize Phoenix로 관측하고, trace를 Dataset과 Experiment로 전환해 모델·프롬프트·Agent 구성을 비교합니다.

첫 번째 학습 흐름은 다음과 같습니다.

```text
DeepSeek / Upstage → OpenAI Agents SDK → OpenInference → OpenTelemetry → Phoenix
```

## 기술 스택

- 언어·런타임: Python 3.11
- Agent: OpenAI Agents SDK
- 모델 API: Upstage Solar 또는 DeepSeek의 OpenAI 호환 Chat Completions API
- 모델 교체: `--provider`와 `--model` 옵션
- 관측: OpenInference, OpenTelemetry
- 평가·실험: Arize Phoenix
- 실행 환경: Python 3.11, Docker Compose

## 공통 계약 적용

- TaskRequest 입력: 다음 단계에서 Phoenix Dataset example로 매핑
- AgentResult 출력: Agent 최종 출력과 run items를 공통 형식으로 변환 예정
- ToolTrace 수집: OpenInference span으로 자동 수집
- EvaluationRecord 생성: Phoenix Experiment 결과를 공통 형식으로 export 예정

## 실행 방법

### 1. 환경 준비

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
```

실제 API 키는 파일이나 Git에 저장하지 않고 실행할 터미널에만 설정합니다. 둘 중 사용할 키 하나만 있으면 됩니다.

```bash
export UPSTAGE_API_KEY='...'
# 또는
export DEEPSEEK_API_KEY='...'
```

### 2. Phoenix 실행

```bash
docker compose up -d
```

브라우저에서 `http://localhost:6006`을 엽니다.

### 3. trace 생성

```bash
./run-agent --provider upstage
```

기본 질문은 계산 도구와 프로젝트 조회 도구를 모두 사용하도록 구성되어 있습니다. 다른 입력과 모델도 지정할 수 있습니다.

```bash
./run-agent "15의 제곱을 계산해줘" --provider deepseek
```

기본 모델은 Upstage의 `solar-pro4`, DeepSeek의 `deepseek-v4-flash`입니다. `--model`로 계정에서 사용할 수 있는 다른 모델 ID를 지정할 수 있습니다.

### 4. Dataset 업로드

```bash
./upload-dataset
```

Phoenix의 `Datasets & Experiments > agent-tool-use-golden-v1`에서 입력, 기대 결과, metadata로 구성된 3개 example을 확인합니다.

### 5. Experiment 실행

```bash
./run-experiment --provider upstage
```

각 example마다 실제 Agent를 실행하고 두 code evaluator를 적용합니다.

- `answer-contains-required-text`: 정답의 필수 내용 확인
- `required-tools-used`: 기대한 도구가 실제 trace에 존재하는지 확인

같은 Dataset에 `--provider deepseek`을 사용하면 모델만 바꾼 비교 Experiment가 됩니다.

DeepSeek 실행은 본 실험 전에 과금 없는 model-list 요청으로 연결과 인증을 확인하고, API 연결 안정성을 위해 example을 하나씩 순차 실행합니다. 모델 호출이 실패하면 긴 traceback 대신 `error` 필드에 짧은 원인을 보존합니다.

### 6. 확인과 종료

- Phoenix의 `Projects > 01-agent-evaluation > Traces`에서 Agent, LLM, Tool span을 확인합니다.
- `Datasets & Experiments > agent-tool-use-golden-v1 > Experiments`에서 example별 점수와 실행을 비교합니다.
- 종료할 때 `docker compose down`을 실행합니다. 데이터는 Docker volume에 유지됩니다.
- 데이터까지 지우는 `docker compose down -v`는 이 핸즈온에서 사용하지 않습니다.

## 결과

- Phoenix 서버: Docker Compose로 로컬 실행 확인
- trace 연결: `01-agent-evaluation` 프로젝트에 smoke trace 수집 확인
- 실제 Agent trace: Upstage `solar-pro4`, 2.3초, 921 tokens, Tool 2개 호출 확인
- Dataset: `agent-tool-use-golden-v1`에 3개 example 업로드 확인
- Experiment: `upstage-solar-pro4`, `deepseek-deepseek-v4-flash` 실행 완료
- 평가: 모델별 3개 task × 2개 code evaluator, 양쪽 모두 6/6 통과

| example | latency | tokens | 답변 내용 | 필수 도구 |
| --- | ---: | ---: | ---: | ---: |
| 계산 | 1.4초 | 814 | 1.00 | 1.00 |
| 프로젝트 조회 | 5.4초 | 860 | 1.00 | 1.00 |
| 두 도구 결합 | 3.6초 | 924 | 1.00 | 1.00 |
| **평균** | **3.5초** | **866** | **1.00** | **1.00** |

### 모델 비교

Phoenix의 같은 Dataset과 evaluator로 두 Experiment를 나란히 비교했다.

| provider / model | 통과율 | 평균 latency | 평균 tokens |
| --- | ---: | ---: | ---: |
| DeepSeek / `deepseek-v4-flash` | 6/6 (100%) | 2.0초 | 1,169 |
| Upstage / `solar-pro4` | 6/6 (100%) | 3.5초 | 866 |

- 이 실행에서는 답변 내용과 필수 도구 사용 품질이 동률이었다.
- DeepSeek은 평균 latency가 약 43% 짧았고, 표시된 token 수는 약 35% 많았다.
- provider마다 tokenizer가 다를 수 있으므로 token 수는 비용의 직접 비교값이 아니다. Phoenix에 제3자 모델 가격을 설정하지 않았으므로 화면의 비용도 비교하지 않는다.
- example 3개를 각 1회 실행한 학습용 결과이므로 모델의 일반적인 우열로 해석하지 않는다. 반복 횟수와 Dataset 범위를 늘려야 변동성과 실패율을 비교할 수 있다.

이번 단계의 핵심은 모델명을 바꾸는 것보다, **Dataset·Agent 구조·evaluator를 고정한 상태에서 한 변수만 교체하고 trace와 점수를 함께 읽는 실험 방식**을 익힌 것이다.

## 첫 번째 체크포인트

첫 Agent 실행 뒤 Phoenix에서 아래 내용을 직접 확인합니다.

1. 하나의 요청이 Agent, LLM, Tool span으로 나뉘는가?
2. `calculator`와 `lookup_project_status`가 모두 호출됐는가?
3. 각 span의 입력·출력과 지연시간을 확인할 수 있는가?

이 단계에서는 trace 구조를 먼저 읽습니다. 이후 같은 입력을 Dataset으로 고정하고 모델 비교 Experiment를 진행합니다.

모델 비교가 끝난 다음 단계에서는 모델과 Dataset을 고정하고 Agent 구조만 바꿔 비교합니다.

## 공통 README에 반영할 결론

진행 후 기록합니다.
