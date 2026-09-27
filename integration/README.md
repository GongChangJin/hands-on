# Integrated Agent System

Hands-on 01~09에서 검증된 구현을 공통 계약으로 연결하는 CLI 검증 harness입니다. 개별 Agent의 기능을 다시 만들지 않고 Router, 전문 Agent, 실행 Agent와 Security gate 사이의 경계를 검사합니다.

## 실행

```bash
cd integration
uv sync --all-extras
./run-integration replay
uv run --frozen pytest
```

`replay`는 06 Router를 subprocess로 실제 실행하고 나머지 프로젝트의 커밋된 검증 결과를 adapter로 읽습니다. 외부 API를 호출하지 않습니다.

```bash
./run-integration live-smoke
```

`live-smoke`는 03 RAG 1건, 07 Browser 전체 로컬 suite, 08 Coding 1건과 09 Docker Security gate를 실행합니다. Upstage 키는 macOS Keychain의 `UPSTAGE_API_KEY` service에서 실행 프로세스에만 주입합니다. 05 Research는 DeepSeek 키가 없으면 deterministic offline corpus로 실행되며 결과에 명시됩니다.

## 처리 흐름

```text
TaskRequest
→ 06 Router subprocess
→ 02 model 또는 03/04/05/07/08 adapter
→ Coding이면 09 Security gate 필수
→ AgentResult + ToolTrace + EvaluationRecord
```

## 구성

- `scenarios/replay-v1.jsonl`: 정상 7건과 fail-closed 3건
- `src/integrated_agent/`: 계약, subprocess/artifact adapter, orchestration, 평가 CLI
- `tests/`: 계약, local-only, 보안 게이트, end-to-end 회귀 테스트
- `results/replay-v1/`: 외부 호출 없는 재현 결과
- `results/live-smoke-v1/`: 실제 실행 요약; 중복 raw 산출물은 Git 제외

## 범위

### 포함

- 공통 계약 호환성 검증과 route/agent 일치
- local-only 외부 adapter 차단
- downstream timeout·형식 오류 fail-closed
- Coding → Security gate 강제
- replay와 live-smoke 결과 분리

### 제외

- 개별 프로젝트의 핵심 로직 재구현
- 평가되지 않은 구현 연결
- 실제 서비스의 결제·발송·보호 브랜치 변경

## 완료 조건

- replay 10/10, route/agent/status 10/10
- Coding 경로의 Security gate 우회 불가
- 오류 주입 3건이 예상된 failed/blocked 상태로 종료
- live-smoke 4/4와 공통 계약 기록 생성

현재 결과와 개별 Hands-on 대비 판단은 [`results/report.md`](results/report.md)에 정리했습니다.
