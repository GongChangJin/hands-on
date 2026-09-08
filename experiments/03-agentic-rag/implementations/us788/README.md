# Agentic RAG - @us788 구현

## 구현 정보

- **구현자:** @us788
- **상태:** `active`
- **공통 과제:** [프로젝트 과제명세](../../README.md)
- **구현 이름:** retriever + calculator

## 접근 방식

LangGraph로 `retrieve → grade_docs → (재검색) → calculate → answer` 흐름을 만들었습니다. 세 가지를 의도적으로 분리했습니다.

- **계산은 LLM에 맡기지 않습니다.** `calculator`가 AST로 직접 평가합니다. 이름·호출·첨자는 전부 거부해서, 계산 정확도 100% 목표를 모델 성능과 무관하게 만듭니다.
- **검색 결과는 데이터로만 취급합니다.** 문서를 `<document>` 태그로 감싸고, 그 안의 지시문은 따르지 않도록 시스템 프롬프트에 명시합니다. 주입 의심 문구가 문서에 있으면 `forbidden_actions`로 계수합니다.
- **관련성 판정 후 재검색**을 최대 2회까지 돌립니다.

근거는 `[문서ID:p페이지]` 형식으로 답변에 넣고, evalkit의 `cited` grader가 이 패턴을 검사합니다.

## 기술 스택

- 언어·런타임: Python 3.11+
- 모델: 논리 라우트 `balanced` (기본). `models.yaml`에서 변경
- 프레임워크: LangGraph + LangChain `init_chat_model`
- 저장소·외부 도구: JSONL 코퍼스 + 키워드 검색 (의존성 없음, 임베딩 검색으로 교체 가능하게 시그니처 고정)
- 평가 도구: [01 Agent Evaluation](../../../01-agent-evaluation/implementations/us788/)의 `evalkit`

## 공통 계약 적용

현재는 `evalkit`의 자체 스키마를 씁니다. `common/contracts/` 대응 관계는 다음과 같습니다.

- `TaskRequest` 입력: `evalkit.Task`로 받습니다. `constraints.allowed_tools`(`retrieve`·`calculate`)는 아직 그래프에 하드코딩되어 있어 계약 필드로 뺄 작업이 남았습니다.
- `AgentResult` 출력: 답변 문자열과 `forbidden_actions` 계수를 반환합니다. 답변 안의 `[문서ID:p페이지]` 인용이 `evidence[]`의 원본이므로, `source`·`location`·`claim` 구조로 분리하면 그대로 채울 수 있습니다.
- `ToolTrace` 수집: `evalkit.ToolCall`로 `retrieve`·`calculate` 호출을 기록합니다. `result_summary`와 `task_id` 필드가 빠져 있습니다.
- `EvaluationRecord` 생성: `run_eval.py`를 거쳐 `evalkit.RunRecord`로 만듭니다. 전환 계획은 [01 구현 README](../../../01-agent-evaluation/implementations/us788/README.md)에 정리했습니다.

## 디렉터리

```text
agent/
├── tools.py    retrieve() · calculate() · Doc.cite()
├── prompts.py  시스템 프롬프트 · 주입 마커
└── graph.py    LangGraph 파이프라인
corpus/sample.jsonl  점검용 샘플 문서 3건
run.py               단건 실행
eval_agent.py        run_eval.py 어댑터
evalkit_bridge.py    01 Agent Evaluation의 evalkit 경로 참조
```

## 실행 방법

```bash
pip install -r requirements.txt
cp .env.example .env

python run.py "약관에서 중도해지 위약금 조항을 근거와 함께 설명하라"

# 평가
python ../../../01-agent-evaluation/implementations/us788/run_eval.py \
  --tasks ../../../01-agent-evaluation/implementations/us788/tasks/sample.jsonl \
  --agent eval_agent:build \
  --experiment 03-agentic-rag
```

## 실험 결과

- 성공률: 미측정
- 평균 지연시간: 미측정
- 비용: 미측정
- 도구 정확도: 미측정
- 안전 위반: 미측정

도구 계층만 API 없이 확인했습니다. `retrieve("중도해지 위약금")`이 `[TERMS:p3]`를 집고, `calculate("10,000,000 * 0.04 * 3")`이 `1200000.0`을 반환하며, `__import__` 주입 시도는 거부됩니다.

## 한계

- 검색이 키워드 겹침 기반이라 동의어와 표현 차이에 약합니다. 임베딩 검색과 비교가 필요합니다.
- `grade_docs`가 아직 결정적 판정입니다. LLM 관련성 판정과의 차이를 측정해야 합니다.
- 재검색 질의 확장 방식이 단순합니다. 질의 재작성으로 교체할 여지가 있습니다.
- 코퍼스가 샘플 3건입니다. 공통 문서는 `shared/`에서 확정해야 합니다.

## 공통 README에 반영할 결론

미정. 공통 문서·평가 질문 확정 후 일반 RAG 기준선과 비교합니다.
