# 12 — 지시 대기열과 전달 불확실성

> 추가 지시·중단·재시작이 겹쳐도 같은 작업이 중복 실행되거나 사용자 의도가 사라지지 않는가?

- **상태:** `validated` — 저장된 queue·별도 프로세스 재시작 범위
- **참여자:** `@ukkhnn`
- **선행:** 10 Runtime Adapter, 11 Session Persistence
- **후행:** 13 승인 경계, 16 중앙 세션, 17 Personal AI 인계
- **학습 슬롯:** 2026-10-07. 2026-11-04에 재구성·구현·평가했으며 결과의 `executedAt`이 실제 시각이다.

## 배경과 질문

10의 HTTP 접수는 작업 완료와 다르다. 11의 저장만으로는 요청을 보낸 직후 응답이 끊겼을 때 다시 보내도 되는지 판단할 수 없다. 이 실험은 지시 ID와 상태 전이를 저장하고, 전달 여부를 모르는 요청을 자동 재실행하지 않는 쪽을 선택한다.

일반 메시지는 작업을 중단하지 않고 뒤에 대기한다. 중단은 별도 제어이며 대기 메시지를 지우지 않는다. HTTP timeout 이후 무조건 재시도하는 구현과 달리, 이 구현은 진행을 멈추고 확인 근거를 요구한다. 그 대가는 자동 복구율이 낮아지고 사람이 조정해야 한다는 점이다.

## 상태와 계약

```text
queued → sending → completed
             └──→ uncertain → completed / cancelled
```

`next(taskId)`는 **sending 상태를 저장한 뒤** 메시지를 반환한다. 같은 task에는 sending/uncertain을 하나만 허용한다. `acknowledge`는 runtime의 실제 완료를 확인했음을 의미한다. HTTP 접수 확인 직후 호출하면 안 된다. 새 프로세스가 sending을 발견하면 uncertain으로 전환하고 후속 발송을 막는다. 명시적 근거를 담은 resolve와 resume 없이는 다시 진행하지 않는다.

`stop`은 queue dispatch를 중단한다. 이 모듈은 원격 프로세스를 소유하지 않으므로 런타임 중단을 직접 실행하거나 완료했다고 주장하지 않는다. 상위 coordinator는 10의 abort와 후속 snapshot을 별도로 수행해야 한다. 대기 지시와 기존 결과는 유지한다.

11의 저장소를 그대로 사용하고 이벤트 payload에 지시 ID를 기록한다. 기존 `TaskRequest`와의 대응은 상위 coordinator가 맡는다. 각 `EvaluationRecord`를 LLM 품질 평가로 오해하지 않도록 별도 local-fixture 평가 결과를 기록한다.

## 실행과 평가

```sh
cd hands-on/experiments/12-durable-instructions/implementations/ukkhnn
npm test
npm run evaluate
```

11 폴더가 같은 저장소에 있어야 한다. 외부 의존성·모델·네트워크는 사용하지 않는다.

| 검증 | 결과 |
|---|---:|
| 공통 시나리오 | 13/13 |
| 자동 테스트 | 15/15 |
| 같은 지시 ID 재요청 | 1건 유지 |
| sending 재시작·전달 불확실성 | 자동 재시도 및 후속 dispatch 차단 |
| 완료된 지시 재시작 | 완료 건 제외, 대기 건만 발송 |
| 추가 지시와 stop 분리 | 진행 상태·대기 메시지 보존 |

## 실패 사례와 결론

runtime 호출 직후 응답을 잃은 상황에서는 queue가 `uncertain`이 되고 `resume`만 호출해도 거부된다. 사용자 확인을 포함한 근거로 completed/cancelled를 결정해야 한다. 이미 실행됐을 수 있는 지시를 자동으로 queued에 되돌리는 기능은 제공하지 않는다.

**판단: `trial`.** 저장 후 전송, 불확실성 명시, 추가 지시와 중단 분리가 `personal-ai/agent-workspace/app/src/workspace.js`의 queue 설계와 연결된다. 정확히 한 번의 외부 실행을 보장하는 실험은 아니다. 런타임이 별도로 보내는 중복 이벤트·서버 강제 종료·네트워크 분할은 추가 검증이 필요하다. 중단과 완료 사이 경합에는 런타임 증거를 확인해야 한다.

[실행 보고서](implementations/ukkhnn/results/report.md), [API·제약](implementations/ukkhnn/README.md), [11 저장소 원칙](../11-session-persistence/README.md)을 함께 본다. 공식 전송의 비동기 의미는 [OpenCode Server 문서](https://opencode.ai/docs/server/)의 `prompt_async` 응답 계약을 기준으로 했다.
