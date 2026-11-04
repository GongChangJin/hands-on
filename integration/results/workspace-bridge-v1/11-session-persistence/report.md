# 11-session-persistence 실행 결과

- 실제 평가 시각: 2026-11-04T14:25:22.825Z
- 재구성 학습 슬롯: 2026-10-06 (실행일 주장 아님)
- 결과: 12/12, 실패 0
- 실행 환경: v22.19.0
- 범위: Real temporary filesystem and separate Node restart process; no production data.
- 외부 모델 호출: 0, API 비용: $0

| 시나리오 | 결과 | 직접 확인한 동작 |
|---|---|---|
| task-identity | PASS | Repeated creation preserves identity; another owner is rejected. |
| immutable-reads | PASS | Input and returned payload mutation cannot alter persisted state. |
| monotonic-cursors | PASS | Global cursor is monotonic while task queries preserve isolation. |
| restart-process | PASS | A separate Node process appends after restart without resetting cursors. |
| malformed-json | PASS | Corrupted JSON is refused and original bytes remain available for recovery. |
| checksum-corruption | PASS | Valid JSON with an accidentally changed owner fails its checksum. |
| unknown-schema | PASS | Unsupported schemas are rejected rather than guessed or overwritten. |
| invalid-payload | PASS | Non-JSON, oversized and prototype-like payloads produce no events. |
| writer-lock | PASS | Concurrent writer is refused; orderly close releases ownership. |
| atomic-failure | PASS | Failure before rename leaves the committed snapshot intact and cleans the temporary file. |
| private-files | PASS | Snapshot and writer-lock files are owner-readable/writable only. |
| unknown-task | PASS | Unknown task and path-like identities are rejected before mutation. |

## 판단과 한계

제한된 로컬 실행 경계의 trial 근거다. 기대한 차단도 검증 성공에 포함된다. 모델 품질, 실제 OpenCode 버전 호환성, Mac mini 운영, 다중 기기 실사용, 전원 장애 복구 완료를 뜻하지 않는다.
실패는 숨기거나 pass로 대체하지 않는다. 원시 상태는 운영체제 임시 폴더에 만들고 정리하며, 기록에는 사용자 경로·메시지·인증정보를 넣지 않는다.
