# ukkhnn — source-only handoff

Node.js 22.19 이상과 로컬 Git을 사용한다. npm 패키지 설치, API 키, OpenCode 설치, 모델 호출은 필요 없다. 모든 쓰기는 OS 임시 폴더와 이 구현의 `results/`에 한정된다. `personal-ai`는 기준점 확인 시 읽기만 한다.

```sh
npm test
npm run evaluate
npm run evaluate -- --reference-root /path/to/personal-ai
```

`src/workflow.mjs`는 10–16의 소스를 직접 import한다. 이 폴더만 복사하면 실행되지 않으므로 hands-on 저장소를 함께 사용한다. `src/plan.mjs`는 소스 인계 manifest의 독립 검증기다. 인계 계획에는 소스 revision·상대 파일명·SHA-256, 완료 확인, 새 작업을 만들 절차만 들어간다.

공유 JSON Schema는 구조를 검증한다. 가져온 manifest의 경로 이동·민감 파일명·실행 상태 파일·중복 경로까지 거부하려면 `validateHandoffPlan`도 사용해야 한다. 파일 내용을 내보내지 않으므로 소스 내용의 비밀 검사까지 완료했다는 뜻은 아니다.

`records.jsonl`은 공통 EvaluationRecord, `task-requests.jsonl`은 TaskRequest, `agent-results.jsonl`은 AgentResult, `tool-traces.jsonl`은 ToolTrace 형식이다. `summary.json`은 실제 실행 시각과 모델 호출 0회, 원격 환경 미검증, 제품 준비 상태를 기록한다. `handoff-plan.json`은 테스트용 임시 저장소의 소스 계획이며 배포 지시나 실제 사용자 저장소의 인계 파일이 아니다.

학습 슬롯은 2026-10-30이지만 모든 테스트와 결과는 실제 실행 시각을 사용한다. fixture의 완료는 프로토콜 동작이며 모델의 코딩 능력 점수가 아니다. 테스트용 인증 정보·임시 절대경로·활성 세션 ID는 결과 파일에 기록하지 않는다.
