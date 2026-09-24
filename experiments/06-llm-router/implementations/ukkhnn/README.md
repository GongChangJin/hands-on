# LLM Router - @ukkhnn 구현

## 구현 정보

- **상태:** validated
- **방식:** policy-first hybrid router
- **런타임:** Python 3.11 이상, Pydantic 2, `uv`
- **모호 요청 분류기:** Upstage `solar-pro4`
- **공통 과제:** [프로젝트 과제명세](../../README.md)

## 접근 방식

명시적인 privacy·complexity·risk·capability 신호는 규칙으로 처리한다. 신호가 불완전한 요청만 소형 구조화 분류 단계로 보내 필요한 전문 Agent를 추론한다. 모델 ID, 품질, 비용과 지연시간은 정책 코드와 분리된 `shared/project-metrics.json`에서 읽는다.

선택 결과는 논리 모델, 실제 모델, Agent, confidence, 선택 이유, fallback 원인, 분류 비용과 지연시간을 구조화해서 남긴다. 분류기 timeout·provider/schema 오류·낮은 confidence는 결정론적 추론으로 복구한다. local-only 요청에서 로컬 모델이 없으면 외부 API로 보내지 않고 `blocked`로 반환한다.

## 실행

```bash
cd experiments/06-llm-router/implementations/ukkhnn

# 테스트와 네트워크 없는 재현 평가
./run-router evaluate --classifier heuristic --output results/offline-replay
./run-router fallback --output results/fallback-suite
uv run --extra dev pytest

# 실제 Solar 분류기 평가
export UPSTAGE_API_KEY="$(security find-generic-password -s UPSTAGE_API_KEY -a "$USER" -w)"
./run-router evaluate --classifier solar --output results/hybrid-solar-pro4
```

비밀값은 결과와 로그에 기록하지 않는다. `UPSTAGE_BASE_URL`과 `ROUTER_CLASSIFIER_MODEL`은 환경 변수로 바꿀 수 있다.

## 결과

| 항목 | 하이브리드 Router | all-frontier 기준선 |
| --- | ---: | ---: |
| 라우팅 정확도 | 39/40 (97.5%) | 해당 없음 |
| 모델 / Agent 정확도 | 100% / 97.5% | 해당 없음 |
| projected 품질 | 89.73% | 93.52% |
| 모델+라우팅 비용 | $0.000786 | $0.000879 |
| 비교 가능한 전체 비용 | $0.099255 | $0.099476 |
| projected p50 | 573.6ms | 520.9ms |
| projected p95 | 10,696.4ms | 10,696.4ms |

- 실제 분류기 호출: 4회, $0.000171
- 모델+라우팅 비용 절감: 10.52%
- 전체 비용 절감: 0.22%. Research Agent 비용이 총비용의 대부분이라 절감 효과가 희석됐다.
- 품질 차이: 3.79%p로 목표 5%p 이내
- 품질·비용·지연 projection coverage: 82.5%. 미측정 browser/coding과 이들이 함께 선택된 요청은 제외했다.
- fallback: timeout, provider 오류, schema 오류, 낮은 confidence, circuit open, 로컬 모델 장애 7/7 통과
- 회귀 테스트: 19/19 통과

실패 1건은 `hybrid-002` 연구 요청에서 `research`와 함께 `browser`를 추가 선택한 경우다. 실행은 가능하지만 기대 경로보다 도구가 하나 많아 과다 라우팅으로 판정했다.

## 적용 판단

`trial`로 적용한다. 규칙으로 판별되는 36건은 별도 모델 호출 없이 처리했고, 모호한 4건에만 분류 비용이 발생했다. 다만 현재 로컬 7.6B의 p50이 Solar Pro 4보다 느려 지연시간 최적화 수단으로는 사용할 수 없다. local route는 데이터 경계와 외부 비용 회피를 위한 선택으로 한정한다.

Browser와 coding은 07·08 실측치가 들어오기 전까지 실행 비용·품질 최적화 대상에서 제외한다. `balanced`와 `frontier`도 실제 모델이 하나뿐이므로 새 모델을 평가한 뒤 매핑을 분리해야 한다.

## 산출물

- `results/hybrid-solar-pro4/`: 실제 Solar 분류 결과, 행별 route와 비교 보고서
- `results/offline-replay/`: 네트워크 없는 결정론적 재현 결과
- `results/fallback-suite/`: 7개 장애·안전 경계 결과
