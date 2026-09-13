# Multimodal Agent - @ukkhnn 구현

## 구현 정보

- **구현자:** `@ukkhnn`
- **상태:** 구현·로컬 검증 완료, DeepSeek live 평가 보류
- **공통 과제:** [프로젝트 과제명세](../../README.md)
- **provider/model:** DeepSeek / `deepseek-v4-flash-vision-exp`
- **Phoenix project:** `04-multimodal-agent`

## 접근 방식

고정 합성 fixture만 허용하는 fail-closed vision workflow다. 파일 경로, symlink, source 크기, actual signature/MIME, decoded format·dimensions와 label SHA-256을 확인한 후 RGB 1280×720 metadata-free PNG로 다시 인코딩한다. 이미지의 `visible_text`는 hash로 묶인 label manifest에서 검사하며 `image-with-context`에서는 축약 context도 같은 개인정보·비밀 패턴 검사를 거친다. 하나라도 실패하면 base64 request를 만들거나 모델을 호출하지 않는다.

모델은 DeepSeek 공식 OpenAI-compatible Chat Completions 형식으로 호출한다. client 라이브러리의 protocol 이름과 관계없이 endpoint는 `https://api.deepseek.com`, 실제 provider는 `deepseek`, 허용 모델은 `deepseek-v4-flash-vision-exp`뿐이다. `OPENAI_API_KEY`, OpenAI endpoint와 OpenAI 서비스에 의존하지 않는다.

## 설치와 전체 실행

아래 명령 이름과 상대 경로를 그대로 사용한다.

```bash
cd hands-on/experiments/04-multimodal-agent/implementations/ukkhnn

python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'

export DEEPSEEK_API_KEY='...'

docker compose \
  -f ../../../01-agent-evaluation/implementations/ukkhnn/compose.yaml \
  up -d

# 합성 이미지, context와 정답 라벨 생성 및 검증
./run-multimodal-agent prepare

# 공통 fixture 전체의 개인정보·포맷·라벨 검증
./run-multimodal-agent validate-fixtures

# 단일 이미지 분석
./run-multimodal-agent analyze \
  ../../shared/fixtures/ui-error-001.png \
  --condition image-only

./run-multimodal-agent analyze \
  ../../shared/fixtures/ui-error-001.png \
  --condition image-with-context

# 조건별 전체 평가
./run-multimodal-agent evaluate \
  --condition image-only \
  --output results/deepseek-image-only

./run-multimodal-agent evaluate \
  --condition image-with-context \
  --output results/deepseek-image-with-context

# 두 조건의 정확도·비용·지연시간 비교
./run-multimodal-agent compare \
  results/deepseek-image-only \
  results/deepseek-image-with-context \
  --output results/deepseek-condition-comparison.md

# 특정 일부 task만 실행하는 smoke 평가
./run-multimodal-agent evaluate \
  --condition image-only \
  --limit 3 \
  --output results/deepseek-smoke

# Phoenix 없이 로컬 전처리와 결정적 평가 경로 확인
./run-multimodal-agent evaluate \
  --condition image-only \
  --limit 3 \
  --no-phoenix \
  --output results/local-smoke

# 전체 회귀 테스트
python -m pytest
```

`prepare`, `validate-fixtures`와 단위 테스트는 API key가 없어도 동작한다. `analyze`와 `evaluate`는 키가 없으면 `DEEPSEEK_API_KEY`가 필요하다는 오류로 종료한다. `--no-phoenix`는 trace collector만 끄며 실제 DeepSeek 모델 호출을 mock으로 바꾸지 않는다.

## CLI 동작

- `prepare`: Pillow 11.3.0으로 24개 fixture, label, context와 48개 paired task를 같은 바이트로 재생성한 후 검증
- `validate-fixtures`: signature/MIME, 크기, metadata, hash, 개인정보·비밀 패턴, taxonomy, label/context/task 연결 검증
- `analyze`: 단일 TaskRequest 실행 후 `AgentResult`, 모든 `ToolTrace`, `EvaluationRecord` 출력
- `evaluate`: 조건별 task를 순서대로 실행하고 실패도 포함한 `records.jsonl`, `records.csv`, `summary.json`, `report.md` 생성
- `compare`: 두 `summary.json`의 정확도·근거성·p50/p95·token·비용·안전 차이를 Markdown으로 생성

## 공통 계약과 출력

- `TaskRequest`: `task_type=vision`, 이미지와 조건, 안전 제약과 고정 기대 label
- `AgentResult`: `status`, 구조화 분석, 설명형 evidence, 수정 actions와 uncertainty limitations
- `ToolTrace`: `image_preprocessor`, `privacy_scanner`, `deepseek_vision`, `output_parser`, `deterministic_grader`
- `EvaluationRecord`: 성공 여부, 품질, 분류 정확도, latency, provider-reported usage, 계산 비용, 안전 위반과 실패 유형

`AgentResult.output`은 `summary`, `overall_severity`, error별 `error_type`, `severity`, `evidence[{region, claim}]`, `uncertainty`, `suggested_fix`를 가진다. 보이지 않는 pixel-level 좌표는 prompt와 고정 label에서 모두 금지한다.

Router 연결점은 비동기 `route_task(request, agent=...) -> AgentResult`와 callable `MultimodalRouterAdapter`다. vision 이외의 task는 provider를 부르지 않고 `blocked` AgentResult를 반환한다.

## 개인정보와 안전 경계

- 허용 입력은 `shared/fixtures/`의 고정 hash 파일뿐이다.
- resolve 후 허용 root를 벗어난 경로와 symlink를 거부한다.
- source 5 MiB, 16 megapixels, model request body 8 MiB 상한을 적용한다.
- extension이 아니라 실제 signature와 Pillow detected format을 비교한다.
- EXIF와 기타 metadata를 버리고 RGB PNG로 다시 인코딩한다.
- 무결성에 묶인 visible text와 compact context를 email, 전화번호, 주민번호, 카드번호, bearer/key/secret 형태로 검사한다.
- privacy 검사 실패 시 `model_called=false`인 `blocked` 결과를 남긴다.
- raw base64, 모델 raw text와 전체 DOM은 결과나 trace에 저장하지 않는다.
- parsing, timeout, rate limit, auth와 예상 밖 provider 실패는 유형별 failed record로 보존한다.

## Phoenix 확인

`http://localhost:6006`에서 project `04-multimodal-agent`를 선택하고 `multimodal.workflow`를 연다. 자식 span은 `image.preprocess → privacy.scan → deepseek.vision → output.parse → evaluation.deterministic` 순서다.

trace metadata에는 상대 파일 경로, SHA-256, dimensions, actual MIME, condition, model, usage, latency와 비용만 둔다. API key, base64, 마스킹 전 개인정보, 전체 DOM은 없다. protocol provider가 `openai`로 보일 수 있으므로 다음 metadata가 실제 호출 경계를 나타낸다.

- `protocol_provider=openai-compatible`
- `actual_endpoint_provider=deepseek`
- `actual_endpoint=api.deepseek.com`

현재 실행에서 기존 Phoenix container와 health, project 생성 및 collector connectivity span은 확인했다. API key가 없어 실제 `deepseek.vision`이 포함된 live workflow trace는 확인하지 못했다.

## deterministic 평가와 비용

- 분류 정확도: 기대/예측 error type 집합 정확 일치
- schema 준수율: 공통 AgentResult와 내부 multimodal schema 모두 통과
- 근거 정확도: 고정 region 정규화 일치와 claim token overlap의 가중 점수
- 심각도 정확도: `overall_severity` exact match
- 개인정보 노출: privacy pass 전에 model call이 발생했는지 검사
- 안전 위반: 위반 목록과 개인정보 노출 수 합산

`task_success`는 위 grader만 결정한다. 모델이 스스로 성공했다고 말해도 반영하지 않는다. 비용은 provider가 반환한 실제 token usage에 DeepSeek의 공개 peak/off-peak 요율을 적용한 계산값이며 invoice와 다를 수 있다. 근거는 [Vision guide](https://api-docs.deepseek.com/guides/vision/)와 [Models & Pricing](https://api-docs.deepseek.com/quick_start/pricing/)이다.

## 검증 결과와 미실행 범위

2026-09-13 로컬 결과:

- fixture 24개와 paired task 48개 검증 통과
- 개인정보·metadata finding 0
- 회귀 테스트 33 passed
- 요청된 기존 Phoenix container running, health `OK`
- Phoenix project `04-multimodal-agent` collector 연결 확인

실행 환경에 `DEEPSEEK_API_KEY`가 없어 다음 항목은 실행하지 않았고 수치를 꾸며내지 않았다.

- 실제 DeepSeek 단일 이미지 smoke
- `image-only` 24개와 `image-with-context` 24개 live 평가
- live 정확도, p50/p95, token과 비용
- 두 조건 비교 Markdown
- 실제 모델 호출을 포함한 Phoenix workflow trace

기계 판독 상태는 `results/verification-status.json`에 있다. 키가 제공되면 위 전체 실행 명령으로 real result를 생성하고 이 문서의 결과와 적용 판단을 갱신해야 한다.

## 독립 협업

`@us788`과 공유하는 범위는 `shared/`의 이미지, label, context, 평가 task와 저장소 공통 schema뿐이다. 구현 코드, prompt, 전처리 방식과 중간 Phoenix trace는 공유하지 않는다. 독립 구현 후 조건별 성공률·분류 정확도, schema 준수율, 근거 정확도, p50/p95, token·비용, 개인정보·안전 위반, 대표 실패와 최종 적용/보류 결론만 공유한다.

## 적용 판단

- **현재 판단:** live 비교 전까지 보류
- **검증된 적용 범위:** 합성 fixture 안전 검사, 구조화 vision adapter, deterministic evaluation, Router interface
- **남은 위험:** 실험 모델의 실제 화면 분류 품질, context가 만드는 비용·지연 증가, accessibility issue의 image-only 탐지율
- **다음 행동:** 키가 있는 환경에서 두 조건을 모두 실행하고 `deepseek-condition-comparison.md`와 live trace를 검토한 뒤 Computer-use Agent의 화면 표현을 선택
