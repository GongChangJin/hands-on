# 12-durable-instructions 실행 결과

- 실제 평가 시각: 2026-11-04T14:25:23.708Z
- 재구성 학습 슬롯: 2026-10-07 (실행일 주장 아님)
- 결과: 13/13, 실패 0
- 실행 환경: v22.19.0
- 범위: Durable local queue and separate Node restart process; no model or remote side effect.
- 외부 모델 호출: 0, API 비용: $0

| 시나리오 | 결과 | 직접 확인한 동작 |
|---|---|---|
| empty-task-lifecycle | PASS | Explicit task creation permits empty state and controls; reads never create unknown tasks. |
| idempotent-enqueue | PASS | Retrying the same request ID preserves one instruction. |
| idempotency-conflict | PASS | A reused ID with different content cannot rewrite intent. |
| ordered-dispatch | PASS | Only completion of the active instruction permits the next dispatch. |
| followup-does-not-stop | PASS | A normal follow-up message leaves the active execution intact. |
| stop-preserves-queue | PASS | Stop pauses dispatch and preserves pending intent; it does not claim the remote process stopped. |
| uncertain-no-retry | PASS | Ambiguous delivery blocks both automatic retries and later instructions. |
| sending-restart | PASS | Recovery converts sending to uncertain before any new dispatch. |
| completed-restart-process | PASS | A new Node process resumes only pending work and never re-dispatches completed work. |
| explicit-resolution | PASS | Recorded completion evidence and explicit resume are both needed after uncertainty. |
| cross-task-acknowledgement | PASS | Acknowledgement cannot cross task ownership boundaries. |
| invalid-inputs | PASS | Path-like IDs, empty and oversized messages are rejected. |
| immutable-list | PASS | Returned message data cannot bypass durable transitions. |

## 판단과 한계

제한된 로컬 실행 경계의 trial 근거다. 기대한 차단도 검증 성공에 포함된다. 모델 품질, 실제 OpenCode 버전 호환성, Mac mini 운영, 다중 기기 실사용, 전원 장애 복구 완료를 뜻하지 않는다.
실패는 숨기거나 pass로 대체하지 않는다. 원시 상태는 운영체제 임시 폴더에 만들고 정리하며, 기록에는 사용자 경로·메시지·인증정보를 넣지 않는다.
