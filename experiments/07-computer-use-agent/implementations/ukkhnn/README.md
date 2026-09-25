# Computer-use Agent - @ukkhnn 구현

## 구현 정보

- **상태:** validated
- **방식:** 정책 선검사 + 결정적 browser planner + 실패 시 screenshot 증거·접근성 fallback
- **런타임:** Python 3.11 이상, Playwright, Pydantic 2, JSON Schema, `uv`
- **브라우저:** headless Google Chrome(Playwright Chromium API)
- **공통 과제:** [프로젝트 과제명세](../../README.md)

## 접근 방식

허용된 localhost fixture만 열고 태스크마다 새 browser context를 만든다. Planner는 DOM/accessibility 상태에서 구조화된 click·fill·select·check·scroll·wait action을 만든다. 실행 전에 origin, action, submit, step과 복구 횟수를 검사하고 외부 request·popup·download를 차단한다.

두 조건을 같은 12개 태스크에 두 번씩 실행한다.

- `dom-accessibility`: DOM 상태와 고정 selector만 사용한다.
- `adaptive-screenshot`: action 오류가 발생한 시점에만 screenshot hash를 trace에 기록하고 접근성 이름으로 selector 변경을 복구한다.

두 번째 조건은 screenshot을 vision model로 해석하지 않는다. 캡처는 실패 시점의 감사 증거이고, 실제 fallback은 접근성 이름을 사용한다. 일반 웹 탐색 능력보다 격리, 권한 제한, 상태 검증과 복구 경계를 확인하는 결정적 baseline이다.

## 공통 계약과 통합 경계

- `TaskRequest`: 목표, 입력, 허용 도구, 금지 행동과 최대 step을 기록한다.
- `AgentResult`: 최종 DOM 값, evidence, action 목록, 실패 한계와 context ID를 반환한다.
- `ToolTrace`: navigation과 각 action의 입력 요약, 결과, 지연시간, 복구 여부와 screenshot hash를 기록한다.
- `EvaluationRecord`: 성공, 품질, 도구 정확도, 비용, 안전 위반과 실패 유형을 기록한다.
- Router capability는 `web_navigation`이며 API 비용은 발생하지 않는다. 로컬 장비·운영 비용은 산정하지 않았다.

## 환경 준비와 실행

```bash
cd experiments/07-computer-use-agent/implementations/ukkhnn

uv venv --python 3.11 .venv
uv pip install '.[dev]'
uv run --extra dev pytest
./run-computer-use
```

Google Chrome 위치가 기본 macOS 경로와 다르면 `CHROME_PATH` 또는 `--chrome-path`로 지정한다. 실행은 `results/playwright-local-site/`에 조건별 원본 trace, 공통 계약 레코드, 요약과 비교 보고서를 생성한다.

## 결과

| 조건 | 성공 | 평균 action | 복구 | p50 / p95 | screenshot 관측 |
| --- | ---: | ---: | ---: | ---: | ---: |
| DOM/accessibility | 22/24 (91.7%) | 1.75 | 4/6 (66.7%) | 1,275.8 / 2,243.1ms | 0 |
| 실패 시 screenshot 증거 + 접근성 fallback | 24/24 (100.0%) | 1.83 | 6/6 (100.0%) | 1,373.8 / 2,268.8ms | 4 |

- 안전 probe: 6/6 통과, 실제 외부 navigation 0회
- 격리 context: 조건별 24개
- 회귀 테스트: 18/18 통과
- 대표 실패: DOM 전용 조건에서 `changed-ui-001`의 변경된 ID를 두 반복 모두 찾지 못해 `planner_exhausted`로 종료
- 보완 결과: 실패 시 screenshot 증거를 남긴 뒤 `Save draft` 접근성 이름으로 재탐색해 같은 두 건을 복구

## 적용 판단

허용 origin과 최종 DOM assertion이 명확한 내부 테스트 및 되돌릴 수 있는 작업에 `trial`로 적용한다. 임의 사이트, 로그인 상태, 실제 제출, 결제·발송과 장기 browser task에는 적용하지 않는다. 단일 합성 사이트와 결정적 planner 결과이므로 실제 UI 일반화를 검증하려면 독립 task corpus와 vision/accessibility 기반 모델 비교가 추가로 필요하다.
