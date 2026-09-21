# LangGraph Agentic RAG - @ukkhnn

## 구현 정보

- **구현자:** `@ukkhnn`
- **상태:** completed
- **공통 과제:** [프로젝트 과제명세](../../README.md)
- **협업 방식:** `@us788`과 설계·코드를 맞추지 않고 각자 독립 구현한 뒤, 동일 데이터의 실행 결과와 학습 결론만 공유한다.

## 학습 목표와 구조

일반적인 “항상 검색한 뒤 답변” RAG가 아니라 모델이 검색과 계산 필요성을 고르고, 검색 결과가 부족하면 질의를 한 번 고쳐 다시 검색하는 bounded Agent를 구현했다.

```text
TaskRequest
  → plan ───────────────→ calculator ──────────→ answer
      │                       ↑                      │
      └→ retriever → grade ───┤                      └→ AgentResult
                       │       │
                       ├→ rewrite → retriever (최대 1회)
                       └→ no_answer
```

- `plan`: `search`, `calculate`, `search_then_calculate`, `direct` 중 하나 선택
- `retriever`: 로컬 multilingual embedding으로 Qdrant cosine 검색
- `grade`: 질문에 직접 답할 chunk와 문서 내부 명령을 구분
- `rewrite`: 근거가 없을 때 질의를 한 번만 재작성
- `formulate` / `calculator`: 문서 규칙을 안전한 산술식으로 바꾸고 AST evaluator로 결정적 계산
- `answer`: 사용한 문서 ID·원문 줄과 계산식을 `AgentResult.evidence`에 보존

## 기술 구성

- Python 3.11, LangGraph 1.x
- LLM: Upstage `solar-pro4` 또는 DeepSeek `deepseek-v4-flash`
- 로컬 embedding: FastEmbed + `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`
- vector store: Qdrant local persistent mode, `agentic-rag-v1` collection
- 관측: OpenInference LangChain instrumentation + OpenTelemetry + 기존 Phoenix
- 평가: 공통 JSON Schema와 결정적 grader, JSONL·CSV·Markdown export

`langchain-openai`는 두 provider의 OpenAI-compatible protocol client로만 사용한다. 실제 endpoint는 `https://api.upstage.ai/v1` 또는 `https://api.deepseek.com`으로 고정되어 있으며 OpenAI API key나 OpenAI endpoint 경로는 없다.

## 공통 계약

- `TaskRequest`: 실행 전에 저장소의 `common/contracts/task-request.schema.json`으로 검증한다.
- `AgentResult`: 성공, 답 없음, 오류를 모두 같은 계약으로 반환한다.
- `ToolTrace`: 검색 질의·시도 횟수·chunk ID·score와 계산식·결과·지연·오류를 기록한다.
- `EvaluationRecord`: 사실 포함, 근거 문서/위치, 계산 결과, 도구 집합, 안전성과 상태를 결정적으로 판정한다.

`AgenticRAG.run(task)`가 Router 연결용 인터페이스다. 입력과 반환값이 공통 계약을 그대로 사용하므로 별도 CLI parsing 없이 호출할 수 있다.

## 설치와 색인

```bash
cd experiments/03-agentic-rag/implementations/ukkhnn
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
```

모델 가중치는 최초 색인 때 로컬 `artifacts/models/`로 내려받는다. 문서와 질의의 embedding은 로컬 ONNX runtime에서 계산되며 embedding API로 전송하지 않는다.

```bash
./run-agentic-rag index
```

색인을 다시 실행하면 collection을 다시 만들고, 문서 3개의 18개 chunk와 corpus fingerprint를 출력한다. Qdrant 데이터와 모델 가중치는 `artifacts/` 아래에 있어 Git에 포함되지 않는다.

## provider와 Phoenix

실제 키는 파일에 저장하지 않고 현재 터미널에만 설정한다.

```bash
export UPSTAGE_API_KEY='...'
# 또는
export DEEPSEEK_API_KEY='...'
```

새 Phoenix를 만들지 않고 `01-agent-evaluation`의 volume과 collector를 재사용한다.

```bash
docker compose -f ../../../01-agent-evaluation/implementations/ukkhnn/compose.yaml up -d
```

실행 후 [Phoenix](http://localhost:6006)의 `03-agentic-rag` project에서 다음 계층을 확인한다.

```text
03-agentic-rag.workflow (AGENT)
  └─ LangGraph (CHAIN)
      ├─ plan / retrieve / grade / rewrite / formulate / answer
      ├─ agent.<node> (LLM generation)
      ├─ retriever.search (RETRIEVER)
      └─ tool.calculator (TOOL)
```

Phoenix의 protocol metadata에는 client 구현 때문에 `openai`라는 값이 보일 수 있지만, 같은 span의 `metadata.provider`와 workflow의 `agent.provider`가 실제 `upstage` 또는 `deepseek` endpoint를 식별한다.

## 실행

```bash
./run-agentic-rag ask 'Team 요금제를 1년 선납할 때 할인 후 금액을 계산해줘.'
./run-agentic-rag ask '회사의 서울 사무실 주소는 어디야?'
./run-agentic-rag ask '17 곱하기 23을 계산해줘.' --allowed-tools calculator
```

일시적으로 trace 전송을 끄려면 `--no-phoenix`, 다른 provider는 `--provider deepseek`를 사용한다. 검색 상한은 2회, 계산 도구는 질문당 1회이며 `TaskRequest.max_tool_calls`도 함께 적용된다.

## 평가

공통 세트는 검색 6, 계산 4, 혼합 5, 답 없음 3, 문서 내부 프롬프트 인젝션 1의 총 19개다.

```bash
./run-agentic-rag evaluate
./run-agentic-rag evaluate --provider deepseek
./run-agentic-rag evaluate --category calculation
python -m pytest
```

각 실행은 `results/<provider>-<model>/`에 `records.jsonl`, `records.csv`, `summary.json`, `report.md`를 만든다. 실패도 삭제하지 않으며 `failure_type`을 사실, 근거, 계산, 도구, 안전, 상태로 분류한다.

## 확인한 결과

- 로컬 회귀 테스트: 12/12 통과
- 실제 Upstage 혼합 경로: `retriever → grade → formulate → calculator → answer` 성공, 73,000원과 문서 ID/줄·계산식 보존
- 실제 Upstage 전체 평가: 19/19 통과, 근거·계산·도구 정확도 100%, p50 5,430ms, p95 20,887ms, 추정 비용 $0.010211, 안전 위반 0
- Phoenix REST 확인: `03-agentic-rag.workflow → LangGraph → agent.plan/answer + tool.calculator`가 한 trace ID에 저장됨
- 첫 전체 실행에서 `rag-mixed-05`가 문서 정책값을 질문에 주어진 숫자로 오인해 `calculate`로 직행한 실패를 보존했다. 계산식의 모든 숫자가 질문에 근거하지 않으면 검색이 허용된 요청을 `search_then_calculate`로 승격하도록 보완한 뒤 전체 세트를 재실행했다.

최종 결과 원본은 [`results/upstage-solar-pro4-full-19-v2/`](results/upstage-solar-pro4-full-19-v2/)에 있다. 최초 전체 실행과 혼합형 회귀 결과도 각각 `results/upstage-solar-pro4-full-19-v1/`, `results/upstage-solar-pro4-mixed-v2/`에 보존했다.

## 안전성과 한계

- 검색 문서는 untrusted data로 표시하며 문서 안의 명령을 계획·채점·답변 instruction으로 사용하지 않는다.
- calculator는 숫자와 `+ - * / // % **`만 허용하고 함수, 이름, 속성 접근, 과도한 지수와 긴 식을 거부한다.
- 검색 score만으로 답을 확정하지 않고 LLM relevance grade를 거치며, 근거가 없으면 제한된 재검색 후 답 없음으로 종료한다.
- 작은 합성 corpus의 결과다. 실제 문서 적용 전에는 chunk 크기, 0.45 threshold와 top-k를 별도 Dataset으로 다시 보정해야 한다.
- 가격은 알려진 기본 모델만 추정한다. 실제 청구는 provider console을 기준으로 한다.

## `@us788`과 공유할 결과와 결론

코드, prompt, graph 구성, 중간 trace는 공유하지 않는다. 아래 표 한 행과 대표 실패/학습 결론만 공통 README에 합친다.

- 결과: 동일 19개 task의 성공률, 근거 정확도, 계산 정확도, 도구 정확도, p50/p95, 비용, 안전 위반
- 결론: bounded retry와 결정적 계산을 유지하고, 검색 threshold는 embedding 모델별로 보정해야 한다.
- 비교 전제: 공통 `shared/documents`와 `shared/evals/tasks.jsonl`은 수정하지 않고 실행한다.

현재 판단은 `trial`이다. 전체 19개 live 평가를 통과했으므로 구조와 관측은 후속 Router에 연결할 수 있다. 독립 구현 비교는 별도 후속 작업으로 남긴다.
