# Approval Boundary — ukkhnn

Node 22 기본 모듈만 사용한다. npm 설치, 외부 API, 비밀값이 필요 없다.

```sh
cd hands-on/experiments/13-approval-boundary/implementations/ukkhnn
node --test
node src/evaluate.mjs
```

평가기는 OS 임시 디렉터리에 원장을 만들고 완료 후 삭제한다. `results/`에는 합성 task ID, 실제 실행 시각과 성공/실패 이유만 남긴다. 절대 임시 경로, 인증 정보와 사용자 자료는 기록하지 않는다.

## API

`src/approvals.mjs`의 모든 메서드는 동기식이다.

```js
const ledger = new ApprovalLedger('/owned-temporary-directory/approvals.json');
const request = {
  id: 'approval-1', taskId: 'task-1', ownerId: 'user-1',
  action: { tool: 'save_note', arguments: { body: 'reviewed draft' } },
  revision: 1, expiresAt: Date.now() + 60_000,
};
ledger.request(request);
const result = ledger.decide(request.id, { ...request, now: Date.now(), allow: true });
// result.allowed === true; a second decision returns already_consumed.
ledger.list('task-1');
```

`expiresAt`와 `now`는 양의 정수 epoch milliseconds다. 만료 시각과 같은 시각도 만료로 취급한다. revision은 0 이상의 정수다. `action`은 비어 있지 않은 JSON object이며 NaN, undefined, sparse array, getter, cycle을 거절한다. object key 순서는 fingerprint에 영향을 주지 않는다.

유효한 승인은 `allowed: true`, `status: approved`, `consumed: true`를 반환한다. 거절은 `allowed: false`와 `reason`을 반환한다. 파일 손상·lock 충돌은 예외로 중단한다. 저장 실패를 승인 성공으로 바꾸지 않는다. `list(taskId)`는 요청 snapshot을 반환하며 인증 필터가 아니다. 호출자는 task 접근 권한을 먼저 확인해야 한다.

## 재현 결과와 실패 해석

- `node --test`: 14개 통과. 재열기, 원본/반환값 변경, task/owner 혼동, stale/expired/reused, 손상 원장과 잠금 충돌을 포함한다.
- 평가: 10/10, 예상 밖 승인 0. [summary.json](results/summary.json)의 실제 실행일을 확인한다.
- 대표 실패: 검토 후 action의 본문을 바꾸면 `action_changed`; 더 높은 revision을 등록한 뒤 이전 요청을 승인하면 `superseded`.
- 소비된 권한을 되살리거나 lock을 강제로 삭제하는 기능은 제공하지 않는다.
