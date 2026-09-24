# Local/Open-weight LLM - @ukkhnn 구현

## 구현 정보

- **구현자:** @ukkhnn
- **상태:** validated
- **공통 과제:** [프로젝트 과제명세](../../README.md)

## 접근 방식

같은 24개 한국어 태스크를 Qwen 2.5 3B와 7.6B의 Q4_K_M 양자화 모델에 각각 3회 실행한다. Ollama의 JSON Schema structured output을 쓰되, 별도 `jsonschema` 검증과 결정적 정답 검사를 다시 수행한다. 결과 정확도와 구조 준수율을 분리하고, 첫 토큰·전체 지연·생성 속도·적재 메모리를 실제 provider counter에서 기록한다.

```text
TaskRequest 24개
  → 공통 prompt / response schema
  → Ollama 또는 OpenAI-compatible adapter
  → AgentResult + ToolTrace
  → EvaluationRecord
  → summary / report / comparison
```

## 기술 스택

- Python 3.11, `jsonschema`, pytest
- Ollama 0.22.0, Apple Metal 경로
- `qwen2.5:3b` 3.1B Q4_K_M
- `qwen2.5:latest` 7.6B Q4_K_M
- 선택적 API 기준선: Upstage `solar-pro4`

Ollama API의 `format`에 JSON Schema를 전달하고, 공식 응답의 `prompt_eval_count`, `eval_count`, `eval_duration`, `load_duration`을 사용한다. 첫 토큰 시간은 streaming 응답에서 첫 콘텐츠가 도착한 벽시계 시간이다. [Ollama Chat API](https://docs.ollama.com/api/chat), [Structured Outputs](https://docs.ollama.com/capabilities/structured-outputs), [running-model memory](https://docs.ollama.com/api/ps)를 구현 근거로 사용했다.

## 공통 계약 적용

- `TaskRequest`: 실행 전 24개 입력을 공통 schema로 검증
- `AgentResult`: 파싱 결과, raw 응답, 실패 한계를 보존
- `ToolTrace`: 모델 호출 지연, token, 첫 토큰과 생성 속도를 기록
- `EvaluationRecord`: schema·정답·안전 판정과 비용을 기록

## 환경 준비와 실행

```bash
uv venv --python 3.11 .venv
UV_CACHE_DIR=/tmp/gcj-local-llm-uv uv pip install '.[dev]'
source .venv/bin/activate

ollama serve
ollama pull qwen2.5:3b
ollama pull qwen2.5:7b

python -m pytest
./run-local-comparison
```

API 기준선은 실제 키를 파일에 저장하지 않고 실행 프로세스에만 주입한다.

```bash
export UPSTAGE_API_KEY='...'
local-llm evaluate \
  --adapter api \
  --model solar-pro4 \
  --repetitions 3 \
  --output results/solar-pro4-api
local-llm compare \
  results/qwen2.5-3b-q4_k_m/summary.json \
  results/qwen2.5-7b-q4_k_m/summary.json \
  results/solar-pro4-api/summary.json \
  --output results/full-comparison.md
```

## 로컬 실험 결과

기기는 M4 Pro 14-core, 64 GB unified memory다. 두 모델 모두 context 4,096에서 Ollama가 `100% GPU`를 보고했다. 세부 환경은 [`results/environment.md`](results/environment.md), 전체 실행은 [`results/local-comparison.md`](results/local-comparison.md)에 있다.

| model | 성공률 | JSON schema | p50 / p95 | 첫 토큰 p50 | 생성 속도 | loaded memory |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 3.1B Q4_K_M | 83.3% (60/72) | 100% | 370 / 757ms | 179ms | 89.1 token/s | 2.3 GB |
| 7.6B Q4_K_M | 95.8% (69/72) | 100% | 574 / 1,241ms | 336ms | 48.5 token/s | 4.8 GB |

3B는 7.6B보다 첫 토큰이 약 47% 빠르고 생성 속도는 약 1.84배였지만 정확도는 12.5%p 낮았다. 7.6B는 분류와 추출을 모두 맞혔고 짧은 질의에서 87.5%였다. 두 모델 모두 schema는 72/72로 지켜 structured output 용도는 안정적이었다.

## 대표 실패

- 3B는 혼합 감정을 `negative`로, `12×7-5`를 74로, 20% 할인 결과를 할인액 10,000으로, 단순 삼단논법을 `no`로 답했다. 네 유형이 세 반복에서 동일하게 재현됐다.
- 7.6B는 `12×7-5`를 47로 답했고 세 반복에서 동일했다.
- 모든 실패가 유효한 JSON이었으므로 schema 성공을 답의 정확성으로 취급하면 잡히지 않는다.
- 안전 위반과 adapter 오류는 없었다.

## 라이선스와 비용 경계

Qwen 공식 설명에 따르면 Qwen2.5 3B와 72B를 제외한 공개 모델은 Apache 2.0이다. 로컬 3B 가중치에 포함된 Qwen Research License는 비상업적 연구·평가만 허용하고 상업적 사용에는 별도 라이선스를 요구한다. 따라서 3B 결과는 학습·비교 목적으로만 사용하고 서비스 후보에서 제외한다. 7B는 Apache 2.0 후보지만 실제 배포 시 선택한 artifact의 라이선스 파일을 다시 확인한다. [Qwen2.5 공식 발표](https://qwenlm.github.io/blog/qwen2.5/)

로컬 request cost는 0달러지만 장비·전력·운영 비용은 미산정이다. API adapter는 2026-09-24 기준 공식 Solar Pro 4의 기간 한정 단가를 코드에 날짜와 함께 기록하고, 알 수 없는 모델의 단가는 추측하지 않는다. [Upstage 공식 가격](https://www.upstage.ai/pricing/api)

## API 기준선과 전체 비교

macOS Keychain에 저장된 키를 실행 프로세스에만 주입해 Upstage `solar-pro4`에 동일한 24개 태스크를 3회 실행했다. 키 값은 파일·명령 인자·결과에 저장하지 않았다. API 기준선은 72/72 정답과 schema를 통과했고 p50/p95는 521/955ms, 실제 usage 기반 추정 비용은 전체 72회에 $0.001582였다.

| model | 성공률 | p50 / p95 | API 호출비 | API 대비 정확도 차이 |
| --- | ---: | ---: | ---: | ---: |
| Qwen2.5 3.1B Q4_K_M | 83.3% | 370 / 757ms | $0 | -16.7%p |
| Qwen2.5 7.6B Q4_K_M | 95.8% | 574 / 1,241ms | $0 | -4.2%p |
| Solar Pro 4 API | 100% | 521 / 955ms | $0.001582 | 기준선 |

API adapter는 비스트리밍 호출을 사용했으므로 첫 토큰 시간과 생성 token/s는 측정하지 않았다. provider마다 tokenizer가 다르므로 token 수 자체를 모델 효율 비교값으로 사용하지 않는다. 전체 표는 [`results/full-comparison.md`](results/full-comparison.md), API 상세는 [`results/solar-pro4-api/report.md`](results/solar-pro4-api/report.md)에 있다.

## 적용 판단

- 7.6B Q4_K_M: `trial`. 저위험 분류·추출과 유효성 검사 앞단의 로컬 경로로 Router에 제공한다.
- 3B Q4_K_M: `hold`. 속도 이점은 크지만 정확도와 비상업 라이선스 때문에 연구 비교에만 둔다.
- 계산·논리: 두 로컬 모델 모두 결정적 오류가 있어 calculator 또는 API 모델로 fallback한다.
- Hands-on 02 전체: 로컬 2조건과 API 기준선을 같은 데이터로 검증했으므로 `validated`, 적용 판단은 제한 범위 `trial`이다.

## 검증

단위·통합 테스트 15개가 dataset 구성, 네 공통 계약, streaming metric, schema/정답 분리, 비밀값 비노출, 결과 export와 날짜별 API 비용 계산을 검증한다.
