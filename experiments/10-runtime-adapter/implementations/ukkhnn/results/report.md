# 10-runtime-adapter 실행 결과

- 실제 평가 시각: 2026-11-04T14:21:25.577Z
- 재구성 학습 슬롯: 2026-10-05 (실행일 주장 아님)
- 결과: 12/12, 실패 0
- 실행 환경: v22.19.0
- 범위: Local HTTP protocol fixture; no OpenCode process, model, account or API key.
- 외부 모델 호출: 0, API 비용: $0

| 시나리오 | 결과 | 직접 확인한 동작 |
|---|---|---|
| lifecycle-http | PASS | Real localhost HTTP carries create, asynchronous acceptance and later completion evidence. |
| abort-confirmation | PASS | Abort acknowledgement is followed by an independent idle snapshot. |
| unsupported-capability | PASS | Unsupported features fail before transport or credentials are used. |
| endpoint-allowlist | PASS | Configuration, credentials and arbitrary proxy requests never reach the fixture. |
| destination-boundary | PASS | Only an explicit literal loopback origin is accepted. |
| malformed-json | PASS | Broken JSON is a protocol failure, not an empty successful result. |
| schema-guard | PASS | Healthy as a string fails the response guard. |
| bounded-response | PASS | Response body consumption stops at the configured byte budget. |
| timeout-no-retry | PASS | Timeout returns an explicit uncertain transport failure and performs no retry. |
| redirect-no-follow | PASS | Redirects cannot forward fixture credentials to another route. |
| foreign-session-response | PASS | A response carrying another session ID fails closed. |
| unknown-runtime-state | PASS | Unrecognized runtime state is never treated as idle or completed. |

## 판단과 한계

제한된 로컬 실행 경계의 trial 근거다. 기대한 차단도 검증 성공에 포함된다. 모델 품질, 실제 OpenCode 버전 호환성, Mac mini 운영, 다중 기기 실사용, 전원 장애 복구 완료를 뜻하지 않는다.
실패는 숨기거나 pass로 대체하지 않는다. 원시 상태는 운영체제 임시 폴더에 만들고 정리하며, 기록에는 사용자 경로·메시지·인증정보를 넣지 않는다.
