# LLM Router - @us788 구현

## 구현 정보

- **구현자:** @us788
- **상태:** `active`
- **공통 과제:** [프로젝트 과제명세](../../README.md)
- **구현 이름:** 규칙 · LLM · 하이브리드 비교

## 접근 방식

세 가지 라우팅 전략을 같은 인터페이스로 만들어 동일 태스크셋에 돌립니다.

- **rule** — 길이, 난이도 마커, 민감도, 코드 포함 여부로 판정. 비용 0, 지연 0에 가깝습니다. 도구 필요 여부(`tool`)와 줄 수(`multiline`) 신호도 계산하지만 **현재 라우트 선택에 기여하지 않습니다** — `tool`은 `easy` 분기의 부정 조건으로만 쓰이고 `multiline`은 어디에도 쓰이지 않습니다.
- **llm** — 경량 모델이 등급을 고릅니다.
- **hybrid** — 규칙이 확신하면(`confidence >= 0.6`) 규칙으로 끝내고, 애매할 때만 LLM을 부릅니다.
- **all_frontier** — 비교 기준선.

실험 규칙 세 가지를 구조로 강제했습니다.

- 모델 ID를 코드에 고정하지 않습니다. 논리 라우트(`small`/`balanced`/`frontier`/`local`)만 다루고 실제 ID는 `models.yaml`에 있습니다.
- 라우터 자체 비용을 제외하지 않습니다. `RoutedResponse.total_cost_usd = 모델 비용 + 라우터 비용`입니다. **다만 `router_cost_usd`가 0으로 고정이라 이 규칙이 아직 지켜지지 않습니다** — `llm`·`hybrid`는 분류를 위해 실제 모델을 호출하는데 그 비용이 0으로 집계되어, 비용 비교가 하이브리드에 구조적으로 유리하게 왜곡됩니다. 이 상태의 비용 수치로는 절감률을 결론지을 수 없습니다.
- 품질 평가 없이 비용만 비교하지 않습니다. 비교는 evalkit의 grader를 거칩니다. **다만 라우팅 정확도를 재는 grader가 아직 없습니다** — `tasks/routing.jsonl`이 `contains`를 걸고 있는데 이 grader는 모델 답변 텍스트만 보고 선택된 라우트는 보지 않습니다. `meta.expected_route`와 `logical_route`를 비교하는 `route_match` grader를 추가해야 프로젝트 평가 기준의 라우팅 정확도를 측정할 수 있습니다.

폴백은 timeout·장애·낮은 confidence를 한 체인으로 다룹니다. `small` 실패 시 `balanced → frontier`, `local` 실패 시 `small → balanced` 순입니다. **다만 `timeout_s`가 실제 지연을 줄이지 못합니다** — `ThreadPoolExecutor`는 실행 중인 호출을 취소할 수 없고 `with` 블록을 빠져나갈 때 완료를 기다리므로, 기록되는 실패 사유만 바뀌고 전체 소요 시간은 그대로입니다. 모델 클라이언트의 HTTP 타임아웃으로 옮겨야 합니다.

## 기술 스택

- 언어·런타임: Python 3.11+
- 모델: 논리 라우트 4종. provider는 `models.yaml`에서 지정
- 프레임워크: LangChain `init_chat_model`
- 저장소·외부 도구: JSONL 태스크
- 평가 도구: [01 Agent Evaluation](../../../01-agent-evaluation/implementations/us788/)의 `evalkit`

## 공통 계약 적용

현재는 `evalkit`의 자체 스키마를 씁니다. `common/contracts/` 대응 관계는 다음과 같습니다.

- `TaskRequest` 입력: `tasks/routing.jsonl`을 `evalkit.Task`로 읽습니다. 라우팅 정답 라벨은 `meta`에 넣어두었고, 계약의 `task_type: "routing"`과 `metadata`로 옮길 수 있습니다.
- `AgentResult` 출력: `RoutedResponse`로 선택 라우트·confidence·폴백 여부·`total_cost_usd`를 반환합니다. 계약의 `actions[]`에 선택 이유와 폴백 경로를, `limitations[]`에 낮은 confidence를 넣는 배선이 남았습니다.
- `ToolTrace` 수집: Router는 도구를 직접 호출하지 않아 현재 비어 있습니다. 전문 Agent 위임을 붙이면 그 호출을 `ToolTrace`로 기록합니다.
- `EvaluationRecord` 생성: `compare.py`가 전략별로 `evalkit.RunRecord`를 만듭니다. `logical_route`·`provider`·`model_id`는 계약의 `metadata`로 넘길 항목입니다.

## 디렉터리

```text
router/
├── classify.py  rule · llm · hybrid · all_frontier
├── fallback.py  timeout / 장애 폴백 체인
└── client.py    분류 → 호출 → 폴백 → 계측
compare.py           전략별 비교 실행
eval_agent.py        run_eval.py 어댑터
evalkit_bridge.py    01 Agent Evaluation의 evalkit 경로 참조
tasks/routing.jsonl  라우팅 정답이 붙은 질문
```

## 실행 방법

```bash
pip install -r requirements.txt
cp .env.example .env

python compare.py --tasks tasks/routing.jsonl --strategies all_frontier rule hybrid --repeats 3
```

## 실험 결과

- 성공률: 미측정
- 평균 지연시간: 미측정
- 비용: 미측정
- 도구 정확도: 미측정
- 안전 위반: 미측정

규칙 분류기만 API 없이 확인했습니다. 샘플 질문 4개(easy / hard / tool / sensitive)에서 기대 라우트와 4/4 일치했습니다. 다만 tool 케이스는 `confidence 0.45`로, 하이브리드였다면 LLM 판정으로 넘어갔을 경계입니다.

## 한계

- 라우팅 정답 라벨이 4건뿐입니다. 실험 목표인 20건 이상으로 늘려야 의미가 있습니다.
- `router_cost_usd`가 아직 0으로 고정입니다. LLM 분류 호출의 토큰을 더하는 배선이 남았습니다.
- 규칙 마커가 한국어 표현에 맞춰져 있습니다. 영어 질문 비중이 늘면 재조정이 필요합니다.
- 폴백 체인이 하드코딩입니다. 장애 주입 테스트로 검증해야 합니다.
- 선행 프로젝트(02·03·04·05)의 실측값이 아직 없어 선택 근거가 규칙에만 의존합니다. 특히 02 Local LLM이 미착수라 `local` 라우트에는 대상 모델이 없습니다.
- 라우팅 정확도를 측정할 grader가 없어 프로젝트 평가 기준의 첫 항목을 재지 못합니다.
- `timeout_s`가 실제 지연 상한으로 동작하지 않아 fallback 항목도 검증되지 않았습니다.
- `AgentResult.extra`에 담은 `planned_route`·`confidence`·`fallbacks`가 `RunRecord`에 전달되지 않아, 완료 조건인 "선택 이유와 비용이 metadata에 기록됨"이 미충족입니다.
- `llm_classify`가 응답에서 라우트를 부분문자열로 찾아 `ROUTES` 순서에 의존합니다. 모델이 문장으로 답하면 오판할 수 있습니다.

## 공통 README에 반영할 결론

미정. 공통 질문셋과 모델군이 확정되면 기준선 대비 품질 저하 5% 이내 / 비용 30% 절감 목표로 측정합니다.
