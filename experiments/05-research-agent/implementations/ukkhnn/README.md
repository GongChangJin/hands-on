# AI Research Agent — @ukkhnn 구현

## 구현 정보

- **구현자:** `@ukkhnn`
- **상태:** 구현·live 평가 완료, 적용 보류
- **공통 과제:** [프로젝트 과제명세](../../README.md)
- **Python:** 3.11+
- **모델:** DeepSeek `deepseek-flash`만 허용
- **검색원:** Semantic Scholar Academic Graph, Crossref REST, arXiv API
- **관측:** Phoenix / OpenTelemetry, project `05-research-agent`

## 무엇을 구현했나

파이프라인은 `query.expand → paper.search → identifier.validate → paper.deduplicate → content.fetch → evidence.extract → report.synthesize → evaluation.deterministic` 순서로 실행된다. 각 단계는 실패를 구조화해 남기고 부분 실패를 성공으로 바꾸지 않는다.

- 고정 질문·검색 전략·필터·JSON Schema·평가 task를 실행 전에 검증한다.
- 공식 API adapter에 bounded pagination, timeout, retry/backoff, 식별 가능한 User-Agent를 적용한다.
- DOI, arXiv ID, Semantic Scholar paperId를 정규화하고 DOI → arXiv ID → paperId → 보수적 제목 유사도 순으로 중복을 제거한다.
- 공개 초록은 최대 600자 excerpt만 저장한다. PDF 경로는 HTTPS, DNS/IP, redirect, MIME, signature, byte/page 한도를 모두 통과해야 한다.
- DeepSeek JSON 응답에서 논문별 claim을 만들고, 모든 claim을 paper ID·출처 URL·근거 위치와 연결한다.
- 논문 claim과 Agent 해석·후속 가설을 서로 다른 필드와 schema로 강제한다.
- `TaskRequest`, `AgentResult`, `ToolTrace`, `EvaluationRecord` 공통 계약을 생성하고 결정론적 grader로 검증한다.
- `--offline`은 커밋된 synthetic fixture만 사용하고 네트워크·모델 호출을 하지 않는다.

## 설치

```bash
cd experiments/05-research-agent/implementations/ukkhnn
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
```

`.env.example`에는 변수 이름만 있다. 실제 비밀값은 파일이나 Git에 넣지 않는다.

```bash
export DEEPSEEK_API_KEY='실제 키를 현재 프로세스에 주입'
export PHOENIX_COLLECTOR_ENDPOINT='http://localhost:6006/v1/traces'
```

macOS Keychain과 shell profile에 이미 등록했다면 새 shell에서 profile을 불러온 뒤 실행한다. Phoenix만 Docker로 실행했고 research agent와 DeepSeek 호출은 host Python에서 실행했다. 격리된 실행 환경은 macOS Keychain 값을 자동으로 상속하지 않을 수 있다.

## 실행

공통 입력과 schema만 먼저 확인한다.

```bash
./run-research-agent prepare
./run-research-agent validate-shared
```

두 live 조건을 검색부터 비교까지 실행한다.

```bash
./run-research-agent run-all --output results/live
```

개별 단계도 재실행할 수 있다.

```bash
./run-research-agent search \
  --condition semantic-scholar-only \
  --output results/manual-semantic

./run-research-agent validate-corpus results/manual-semantic

./run-research-agent analyze \
  --condition semantic-scholar-only \
  --input results/manual-semantic \
  --output results/manual-semantic-analysis

./run-research-agent evaluate \
  --condition semantic-scholar-only \
  --input results/manual-semantic-analysis \
  --output results/manual-semantic-evaluation
```

네트워크나 비용 없이 end-to-end 구조를 확인한다.

```bash
./run-research-agent run-all \
  --offline \
  --no-phoenix \
  --output results/offline-smoke
```

테스트는 다음과 같이 실행한다.

```bash
python -m pytest
```

## DeepSeek 고정 설정과 비용

Gateway는 `https://api.deepseek.com/chat/completions`와 `deepseek-flash`만 허용한다. `OPENAI_API_KEY`, 다른 endpoint, fallback 모델은 읽지 않는다. 가격은 2026-09-16에 확인한 [DeepSeek 공식 가격표](https://api-docs.deepseek.com/quick_start/pricing/)를 코드에 고정했다.

| 시간대 | cache hit input | cache miss input | output |
| --- | ---: | ---: | ---: |
| off-peak, USD / 1M tokens | $0.003 | $0.15 | $0.60 |
| peak, USD / 1M tokens | $0.006 | $0.30 | $1.20 |

Peak는 공식 문서 기준 평일 UTC 01:00–04:00, 06:00–10:00이다. 결과 비용은 provider usage에 이 요율을 적용한 계산값이며 invoice가 아니다.

## Live 결과

실행일은 2026-09-16 UTC다. 최종 산출물은 [`results/final/`](./results/final/)에, 요약 판정은 [`results/verification-status.json`](./results/verification-status.json)에 있다.

| 지표 | Semantic Scholar only | Federated verified |
| --- | ---: | ---: |
| 검색 시작–종료 | 17.85s | 30.81s |
| 원시 레코드 / 검증 논문 | 40 / 18 | 165 / 18 |
| 제거 중복 / 식별자 실패 / 잔존 중복 | 0 / 0 / 0 | 75 / 0 / 0 |
| claims / claim이 있는 논문 | 75 / 18 | 47 / 14 |
| evidence coverage | 100% | 77.8% |
| citation / locator / schema / hypothesis separation | 각 100% | 각 100% |
| 검색 요청 | S2 22 | S2 24 + Crossref 10 + arXiv 8 |
| 분석 모델 요청 | 5 | 5 |
| 조건별 API 요청 | 27 | 47 |
| input / cached / output tokens | 27,432 / 512 / 16,552 | 15,975 / 0 / 15,764 |
| total tokens | 43,984 | 31,739 |
| 모델 latency p50 / p95 | 11,777.52 / 14,820.07ms | 10,696.36 / 14,498.74ms |
| 계산 비용 | $0.027941472 | $0.023709300 |
| 결정론적 판정 | 통과 | 실패 |

공유 query expansion은 1회, 248 tokens, peak $0.0001257이었다. 처음 생성된 federated 결과의 Semantic Scholar 요청 수 46은 앞 조건의 22회를 포함한 누적값이었다. 코드가 조건 시작 시 counter를 snapshot하도록 수정했고, 실제 federated 값 `46 - 22 = 24`와 전체 `24 + 10 + 8 + 5 = 47`의 derivation을 [`request-attribution-correction.json`](./results/request-attribution-correction.json)에 기록했다. 당시 개별 검색 latency sample은 보존되지 않아 과거 검색 요청 p50/p95는 수정하지 않았고, 위 표에는 영향받지 않은 모델 호출 p50/p95만 제시했다.

### 관찰된 실패와 한계

- Semantic Scholar HTTP 429: 단독 6건, federated 8건. 재시도 한도 후 실패 레코드로 보존했다.
- Federated 후보 중 제목은 유사하지만 강한 ID가 없는 6쌍은 false positive를 피하려고 병합하지 않았다. 최종 18편 안의 잔존 중복은 0건이다.
- Federated 분석에서 4편은 모델이 schema를 만족하는 claim을 내지 않아 논문 단위 coverage가 77.8%였다.
- 분석은 공개 abstract excerpt 기반이다. 초록이 보고하지 않은 수치·구현 복잡도는 추정하지 않으며, 직접 실험 적합성은 후속 수동 screening 대상이다.
- 초기 중단 실행과 smoke 결과는 최종 결과로 세지 않는다. `final/`과 최상위 verification 파일만 판정 기준이다.

## Phoenix 검증

기존 Phoenix 19.10.0 인스턴스의 project `05-research-agent`를 재사용했다. 최종 live trace는 `5749d2fd4ffcd4e8b8cbbd32d00e4376`, root span은 `research.workflow`다. 필수 8단계가 root의 직접 자식으로 확인됐고, token span 5개와 rate limit·unresolved duplicate·partial model failure·deterministic threshold failure가 UI/API에서 관찰됐다.

저장소의 기존 Compose와 volume을 그대로 시작하고 `http://localhost:6006`에서 project를 선택한다. 새 Phoenix 환경은 만들지 않는다.

```bash
docker compose \
  -f ../../../01-agent-evaluation/implementations/ukkhnn/compose.yaml \
  up -d
```

[`results/phoenix-verification.json`](./results/phoenix-verification.json)의 prohibited scan은 API key, Authorization, raw prompt/response, 전체 초록, PDF body 모두 `false`다. span 속성은 모델·endpoint provider·hostname·token/cost/latency·result count·failure type 등 allowlist만 사용한다.

## 독립 협업

공통 기준은 `../../shared/`만 사용한다. 이 구현의 코드와 `results/`는 `@ukkhnn` 소유이며 `@us788` 디렉터리와 README는 수정하지 않는다. 비교 표에는 양쪽에 실제 결과가 있을 때만 참가자 간 수치를 추가한다.

## Router 계약

`ResearchRouter`는 연구 탐색·논문 비교형 요청만 이 구현으로 보낸다. 비연구 요청은 adapter나 모델을 호출하기 전에 거절한다. 성공과 실패 모두 공통 `AgentResult` 계약으로 반환하고, 실패 유형은 `timeout`, `rate_limit`, `authentication`, `connection`, `validation`, `model_parsing`, `deterministic_threshold_failed`처럼 구조화한다.

## 적용 판단

**품질 또는 안전 기준 미달로 적용 보류.** 비밀·출처·식별자·중복·schema·가설 분리는 기준을 통과했지만, federated 조건의 evidence coverage 100% 요구를 만족하지 못했다. Semantic Scholar rate limit을 줄이고 누락 batch의 추출 재시도를 추가한 다음 동일한 고정 corpus와 grader로 재평가해야 한다.
