# 04. Multimodal Agent

> 이미지와 텍스트를 함께 사용하면 UI 오류를 일관된 구조로 분석할 수 있는가?

## 프로젝트 정의

- **상태:** 구현·로컬 검증·DeepSeek live 비교·adaptive 보완 완료
- **참여자:** `@ukkhnn`, `@us788`
- **역할:** 이미지·화면 상태를 해석하는 전문 Agent
- **선행 프로젝트:** Agent Evaluation
- **후행 프로젝트:** Computer-use Agent, LLM Router

UI 스크린샷의 오류 유형, 심각도, 화면 근거, 불확실성과 수정 방향을 구조화한다. 같은 이미지의 `image-only`와 사용자 설명·축약 DOM·축약 accessibility snapshot을 더한 `image-with-context` 결과를 고정 라벨로 비교한다.

## 고정 공통 데이터

`shared/`는 두 구현자가 독립 구현 전에 함께 고정한 데이터다.

- 합성 UI PNG 24장: 결함 20장, 정상 4장, 모두 1280×720 RGB
- 오류 taxonomy: `layout_break`, `element_clipping`, `invalid_state`, `error_message`, `accessibility_issue`
- 이미지별 SHA-256, 기대 오류, 심각도, 화면 근거, 허용 불확실성
- 개인정보가 없는 사용자 설명, 축약 DOM과 accessibility snapshot
- 두 조건을 짝지은 공통 `TaskRequest` 48개

실제 개인정보, 사내 화면, 인증 정보나 비밀값은 fixture에 없다. `prepare`가 이 데이터를 재현 가능하게 생성하고 `validate-fixtures`가 signature/MIME, 크기, metadata, SHA-256, 개인정보 패턴, label과 task 연결을 검증한다.

## 구현된 흐름

```text
TaskRequest
  → 허용 경로·symlink·크기·signature·MIME·hash 검사
  → RGB 1280×720 metadata-free PNG 정규화
  → 무결성에 묶인 visible text와 선택 context 개인정보 검사
  → DeepSeek deepseek-v4-flash-vision-exp
  → 엄격한 JSON parsing과 AgentResult 검증
  → 고정 라벨 deterministic grader
  → EvaluationRecord와 JSONL/CSV/JSON/Markdown
```

이미지는 개인정보 검사에 통과하기 전에는 모델 호출에 도달하지 않는다. 허용된 `shared/fixtures/` 밖의 파일, symlink 이탈, hash 불일치, 상한 초과, 개인정보·비밀 형태 문자열은 `blocked`로 남긴다. JSON parsing, timeout, rate limit, 인증 실패는 삭제하지 않고 실패 유형으로 보존한다.

모델 adapter는 OpenAI-compatible Python client를 사용하지만 endpoint는 `https://api.deepseek.com`, provider는 `deepseek`, 요청 모델은 `deepseek-v4-flash-vision-exp`로 고정한다. thinking은 명시적으로 비활성화하며 실제 응답 model alias는 `deepseek-flash`로 관측됐다. `OPENAI_API_KEY`와 OpenAI endpoint를 읽지 않는다. 모델과 vision 입력 형식, 가격 근거는 [DeepSeek Vision guide](https://api-docs.deepseek.com/guides/vision/)와 [DeepSeek Models & Pricing](https://api-docs.deepseek.com/quick_start/pricing/)을 따른다.

## 관측과 평가

새 Phoenix를 만들지 않고 `01-agent-evaluation/implementations/ukkhnn/compose.yaml`의 container와 volume을 재사용한다. Phoenix project는 `04-multimodal-agent`다. 한 `multimodal.workflow` trace 아래에서 다음 span을 확인할 수 있다.

- `image.preprocess`
- `privacy.scan`
- `deepseek.vision`
- `output.parse`
- `evaluation.deterministic`

trace에는 상대 파일 경로, 이미지 hash·크기·MIME, 입력 조건, 실제 provider/endpoint, 모델, token usage와 latency만 기록한다. API key, base64 원문, 마스킹 전 개인정보와 전체 DOM은 기록하지 않는다. OpenAI-compatible protocol 때문에 UI가 provider를 `openai`로 해석하더라도 `protocol_provider=openai-compatible`, `actual_endpoint_provider=deepseek`, `actual_endpoint=api.deepseek.com` metadata로 실제 경계를 구분한다.

분류는 기대/예측 taxonomy 집합의 정확 일치, 근거는 고정 영역과 claim token overlap, 개인정보와 안전은 model-call gate 상태로 결정한다. LLM 자기평가는 성공 판정에 쓰지 않는다. 보고서는 성공률, 분류·schema·근거·심각도 정확도, 전체 latency p50/p95, provider-reported token, 공개 요율 기반 계산 비용과 실패 사례를 보존한다.

## 검증 결과

| 항목 | 결과 |
| --- | --- |
| fixture / paired tasks | 24 / 48 |
| 결함 / 정상 | 20 / 4 |
| fixture 개인정보·metadata finding | 0 / 0 |
| 로컬 회귀 테스트 | 37 passed |
| 기존 Phoenix container / health | running / OK |
| Phoenix live trace | 98 workflow roots / 583 spans / orphan 0 |
| 실제 DeepSeek 단일 smoke | 성공, schema 준수, 1,063 tokens |
| image-only v2 live 평가 | 24건, 성공 29.2%, 분류 54.2%, p50/p95 1.59s/2.04s |
| adaptive-context 반복 평가 | 각 24건, 성공 37.5~45.8%, 분류 75.0~87.5% |
| adaptive context 사용량 / p95 | 14~15건 / 4.43~4.58s |
| 개인정보 노출 / 안전 위반 | 두 조건 모두 0 / 0 |

최초 비교 뒤 taxonomy·severity prompt와 정상 화면 evidence grader를 보완하고, image-only가 실패·무오류이거나 접근성/상태 판단을 내렸을 때만 compact context를 재호출하는 adaptive 조건을 추가했다. 두 번의 adaptive 실행에서 성공률은 37.5~45.8%, 분류 정확도는 75.0~87.5%였고 context는 24건 중 14~15건에만 사용됐다. 두 실행 모두 schema 100%, 개인정보·안전 위반 0, p95 5초 이내였다. 전체 record와 비교표는 `implementations/ukkhnn/results/`에 있고 mock 측정은 없다.

## 구현 비교

| 참여자 | 입력 구성 | 모델 | 정확도 | 비용 | 특징 |
| --- | --- | --- | ---: | ---: | --- |
| `@ukkhnn` | image-only / adaptive-context | `deepseek-v4-flash-vision-exp` | 54.2% / 75.0~87.5% 분류 정확도 | $0.006357 / $0.006288~0.008469 관측값 | privacy gate, selective context retry, fixed-label grader |
| `@us788` | 독립 구현 후 기록 | 독립 구현 후 기록 | — | — | 공통 데이터·schema만 공유 |

## 완료 조건

- [x] 24개 합성 fixture와 두 조건 입력을 구현함
- [x] 모든 로컬 결과를 네 공통 schema로 검증함
- [x] 오류 근거, 불확실성과 수정 제안을 구조화함
- [x] 개인정보·경로·symlink·크기·request body 안전 경계를 구현함
- [x] JSONL, CSV, JSON, Markdown과 조건 비교 생성기를 구현·테스트함
- [x] 실제 DeepSeek로 단일 smoke와 두 조건 전체 평가를 완료함
- [x] live 수치로 Computer-use Agent 입력 형식을 결정함

## 독립 협업 규칙

`@ukkhnn`과 `@us788`은 `shared/`의 이미지, label, context, task와 저장소 공통 schema만 공유한다. 구현 코드, prompt, 전처리 방식과 중간 Phoenix trace는 공유하지 않는다. 각자 독립 구현 뒤 조건별 성공률·분류 정확도, schema 준수율, 근거 정확도, p50/p95, token·비용, 개인정보·안전 위반, 대표 실패, 적용/보류 결론만 공유한다.

## 결론

- **적용 판단:** 이 합성 UI 범위에서는 adaptive-context를 제한적 기본값으로 적용
- **판단 이유:** context를 58.3~62.5%의 요청에만 사용하면서 성공률과 분류·근거·심각도 정확도를 모두 개선했고 p95 5초 예산을 지켰음
- **적용 가능 범위:** 합성 UI 회귀 데이터, 사전 안전 검사, Router용 `TaskRequest → AgentResult`, 실제 DeepSeek 호출과 Phoenix 관측
- **다음 행동:** 더 넓은 UI corpus와 실제 Computer-use 화면에서 같은 5초 p95 예산과 선택 조건을 재검증한 뒤 확대 적용

## 변경 기록

### 2026-09-13

- 변경: 공용 합성 데이터, DeepSeek vision workflow, privacy gate, Phoenix 관측, deterministic 평가와 보고서 구현
- 결과: 로컬 검증 완료, live 평가 미실행
- 다음 행동: 실제 두 조건 평가 후 적용 판단 갱신

### 2026-09-15

- 변경: DeepSeek thinking 비활성화, empty response usage 보존, 동일 taxonomy 복수 finding 허용
- 결과: 단일 smoke, 두 조건 24건씩, 비교표, Phoenix live trace와 35개 회귀 테스트 검증 완료
- 판단: image-only 기본 적용, compact context는 선택적 보강으로 제한
