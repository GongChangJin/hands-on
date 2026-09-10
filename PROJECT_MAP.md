# AI Hands-on 프로젝트 맵

## 목적

9개 핸즈온 프로젝트의 정의, 선행·후행 관계, 공통 계약과 최종 통합 구조를 설명합니다. 세부 과제와 평가 기준은 각 프로젝트 README를 기준으로 합니다.

## 전체 구조

```text
                         ┌→ 02 Local LLM ──────────┐
                         ├→ 03 Agentic RAG ────────┤
01 Agent Evaluation ─────┼→ 04 Multimodal Agent ──┼→ 06 LLM Router
                         └→ 05 Research Agent ─────┘       │
                                                           ├→ 07 Computer-use
                                                           └→ 08 Coding Agent
                                                                    │
                                                                    ▼
                                                        09 Cybersecurity Agent
                                                                    │
                                                                    ▼
                                                               Integration
```

Agent Evaluation은 모든 프로젝트가 사용하는 기반입니다. Local LLM과 세 전문 Agent는 공통 계약이 준비되면 서로 독립적으로 구현할 수 있습니다. Router는 이 프로젝트들의 실측 결과를 이용해 모델과 Agent를 선택합니다. Coding Agent의 결과는 Cybersecurity Agent를 거쳐 통합 시스템에 연결됩니다.

## 프로젝트 관계표

| 번호 | 프로젝트 | 역할 | 직접 선행 | 직접 후행 |
| ---: | --- | --- | --- | --- |
| 01 | [Agent Evaluation](experiments/01-agent-evaluation/) | 공통 계약·평가·관측 | 없음 | 전체 프로젝트 |
| 02 | [Local/Open-weight LLM](experiments/02-local-llm/) | 로컬 모델 백엔드와 성능 기준 | 01 | 06, Integration |
| 03 | [Agentic RAG](experiments/03-agentic-rag/) | 문서 검색·계산 전문 Agent | 01 | 06, Integration |
| 04 | [Multimodal Agent](experiments/04-multimodal-agent/) | 이미지·화면 이해 전문 Agent | 01 | 06, 07 |
| 05 | [AI Research Agent](experiments/05-research-agent/) | 논문 검색·검증·비교 Agent | 01 | 06, Integration |
| 06 | [LLM Router](experiments/06-llm-router/) | 모델·전문 Agent 선택과 fallback | 01~05 | 07, 08, Integration |
| 07 | [Computer-use Agent](experiments/07-computer-use-agent/) | 제한된 브라우저 행동 실행 | 01, 04, 06 | Integration |
| 08 | [Coding Agent](experiments/08-coding-agent/) | Issue 기반 코드 변경과 테스트 | 01, 06 | 09, Integration |
| 09 | [Cybersecurity Agent](experiments/09-cybersecurity-agent/) | 코드 변경의 보안 재검증 | 01, 08 | Integration |

## 구축 전후관계

### 기반

먼저 Agent Evaluation에서 공통 요청, 결과, 도구 실행과 평가 레코드 형식을 정의합니다. 다른 프로젝트는 이 계약을 사용해야 서로 비교하고 연결할 수 있습니다.

### 모델·전문 Agent

다음 네 프로젝트는 서로 독립적으로 진행할 수 있습니다.

- Local/Open-weight LLM: 로컬 모델 실행과 API 기준선 비교
- Agentic RAG: 문서 검색·계산·근거 생성
- Multimodal Agent: 이미지와 화면 상태 분석
- AI Research Agent: 논문 검색·검증·비교

각 프로젝트는 자신의 capability와 품질·비용·지연시간 결과를 Router에 제공합니다.

### 오케스트레이션

LLM Router는 앞선 결과를 바탕으로 논리 모델과 전문 Agent를 선택합니다. Router는 전문 업무를 직접 처리하지 않고 선택 이유, confidence와 fallback을 반환합니다.

### 실행

Computer-use Agent와 Coding Agent는 외부 상태를 변경할 수 있는 실행형 Agent입니다. 두 프로젝트는 Router의 선택 결과를 사용하며 더 강한 권한·범위·반복 제한을 적용합니다.

### 보안 검증

Cybersecurity Agent는 Coding Agent의 patch를 정적 분석, 보안 테스트와 회귀 테스트로 재검증합니다. LLM의 판단만으로 코드 변경을 승인하지 않습니다.

### 통합

Integration은 검증된 구현을 연결합니다. 개별 Agent를 다시 구현하지 않으며 공통 계약 호환성, Router 선택, 권한 제한, fallback과 end-to-end 평가를 검증합니다.

## 프로젝트별 정의

### 01 Agent Evaluation

모든 프로젝트가 같은 방식으로 결과를 제출하고 비교할 수 있게 하는 기반입니다.

- 입력: 평가 태스크, 기대 결과, AgentResult, ToolTrace
- 출력: EvaluationRecord, 비교표, 실패 유형
- 핵심 판단: 결과가 재현 가능하고 서로 공정하게 비교되는가

### 02 Local/Open-weight LLM

로컬 모델을 API 모델과 비교하고 공통 LLM adapter로 제공합니다.

- 입력: 공통 프롬프트, 로컬 모델 설정, API 기준선
- 출력: 모델 adapter, 품질·속도·자원 지표
- 핵심 판단: 어떤 작업을 로컬 경로로 보낼 수 있는가

### 03 Agentic RAG

질문에 따라 검색과 계산 도구를 선택하고 검증 가능한 근거를 반환합니다.

- 입력: 질문, 문서 집합, retriever와 calculator
- 출력: 근거·계산식이 포함된 답변과 ToolTrace
- 핵심 판단: 검색·계산·답 없음 처리를 안정적으로 구분하는가

### 04 Multimodal Agent

이미지와 보조정보를 이용해 UI 오류와 화면 상태를 구조화합니다.

- 입력: 마스킹된 스크린샷, 설명, 선택적인 DOM 정보
- 출력: 오류 종류·심각도·화면 근거·수정 제안
- 핵심 판단: Computer-use가 사용할 만큼 화면 상태를 정확히 표현하는가

### 05 AI Research Agent

연구 질문을 논문 검색·검증·비교 결과로 변환합니다.

- 입력: 연구 질문, 검색 조건, 초록 또는 원문
- 출력: 검증 논문 목록, claim-evidence 표, 출처 기반 요약
- 핵심 판단: 실제 논문 주장과 Agent 추론을 분리하는가

### 06 LLM Router

요청에 적합한 모델과 전문 Agent를 선택하는 오케스트레이션 계층입니다.

- 입력: TaskRequest, capability 목록, 프로젝트별 실측 결과
- 출력: 선택 모델·Agent, 선택 이유, confidence, fallback
- 핵심 판단: 품질을 유지하면서 비용이나 지연시간을 개선하는가

### 07 Computer-use Agent

허용된 테스트 사이트에서 화면을 해석하고 제한된 행동을 실행합니다.

- 입력: 브라우저 태스크, 화면 상태, 허용 정책
- 출력: 최종 DOM 상태, 행동 이력과 trace
- 핵심 판단: 범위 밖 행동 없이 작업을 완료하는가

### 08 Coding Agent

Issue를 분석하여 patch와 테스트 결과를 생성합니다.

- 입력: Issue, 샘플 저장소, 테스트와 변경 제한
- 출력: 코드 patch, 회귀 테스트, 실행 결과와 변경 요약
- 핵심 판단: 요구사항을 만족하면서 회귀와 불필요한 변경을 방지하는가

### 09 Cybersecurity Agent

취약 코드와 Coding Agent의 patch를 결정적 보안 도구로 재검증합니다.

- 입력: 로컬 취약 샘플, patch, 예상 finding과 보안 테스트
- 출력: 탐지·수정·재검사 결과와 잔여 위험
- 핵심 판단: 과도한 권한이나 외부 접근 없이 보안 문제를 줄이는가

## 공통 계약

계약 원본은 [`common/contracts/`](common/contracts/)에서 관리합니다.

| 계약 | 역할 |
| --- | --- |
| `TaskRequest` | 사용자 요청, 첨부자료, 허용 도구와 실행 제한 |
| `AgentResult` | 결과, 근거, 행동과 한계 |
| `ToolTrace` | 도구 입력·결과·지연시간·오류 |
| `EvaluationRecord` | 성공률, 품질, 도구 정확도, 비용과 안전 위반 |

## 프로젝트 간 데이터 흐름

| 생산 프로젝트 | 산출물 | 소비 프로젝트 |
| --- | --- | --- |
| 01 Agent Evaluation | schema·runner·평가 결과 | 전체 프로젝트 |
| 02 Local LLM | 모델 capability·성능 지표 | 06 Router |
| 03 Agentic RAG | 문서 질의 인터페이스·근거 | 06 Router, Integration |
| 04 Multimodal | 화면 분석 결과 | 06 Router, 07 Computer-use |
| 05 Research | 논문 검색·비교 결과 | 06 Router, Integration |
| 06 Router | 모델·Agent 선택 결과 | 07, 08, Integration |
| 07 Computer-use | 브라우저 행동·검증 결과 | 01 Evaluation, Integration |
| 08 Coding | 코드 patch·테스트 결과 | 09 Cybersecurity |
| 09 Cybersecurity | 승인·차단·잔여 위험 | Integration |

## 책임 경계

- Evaluation은 전문 Agent를 구현하지 않습니다.
- Router는 전문 업무를 직접 처리하지 않습니다.
- Agentic RAG는 일반 웹 리서치를 담당하지 않습니다.
- Research Agent는 브라우저 GUI를 조작하지 않습니다.
- Multimodal Agent는 화면을 분석하지만 클릭·입력하지 않습니다.
- Computer-use Agent는 허용된 테스트 환경 밖에서 행동하지 않습니다.
- Coding Agent는 보안 적합성을 최종 승인하지 않습니다.
- Cybersecurity Agent는 외부 시스템을 스캔하거나 공격하지 않습니다.
- Local LLM은 모델 학습보다 추론·연결·비교에 집중합니다.

## 통합 완료 조건

- 모든 연결 프로젝트가 공통 계약을 사용함
- Router의 선택 이유와 fallback이 기록됨
- 정보형 작업과 실행형 작업이 구분됨
- 실행형 작업에 권한·범위·검증 단계가 있음
- 코드 변경이 보안 재검증을 통과함
- 단일 프로젝트와 통합 결과를 같은 평가 형식으로 비교할 수 있음
