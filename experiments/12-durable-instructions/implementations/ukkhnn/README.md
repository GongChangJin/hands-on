# Durable Instructions — @ukkhnn

Node.js 22.19+ 기본 라이브러리와 선행 실험 11의 SessionStore를 사용한다. npm 의존성은 없다. `npm test`는 15개 테스트, `npm run evaluate`는 13개 공통 시나리오를 실행한다.

## API와 의미

```js
import { InstructionQueue } from './src/queue.mjs';
const queue = new InstructionQueue('/tmp/example-instruction-lab/queue.json');
try {
  queue.ensureTask('task-a'); // Explicit empty task creation; reads do not create tasks.
  queue.enqueue('task-a', { id: 'message-a', text: 'implement feature' });
  const message = queue.next('task-a'); // Durable sending BEFORE runtime call.
  // Send message, then inspect runtime evidence of actual completion.
  queue.acknowledge('task-a', message.id);
} finally { queue.close(); }
```

| 호출 | 의미 |
|---|---|
| `ensureTask(taskId)` | 메시지 없는 queue 작업을 명시적으로 만들거나 동일 작업 반환 |
| `enqueue(taskId,{id,text})` | 같은 ID/내용 중복 제거, 다른 내용이면 충돌; 없는 task 생성 |
| `next(taskId)` | sending 저장 후 메시지 반환; 중단·미해결·빈 queue면 null |
| `acknowledge(taskId,id)` | runtime **완료 확인**; HTTP 접수 확인으로 사용 금지 |
| `markUncertain(taskId,id)` | 결과 불확실·pause 저장, 자동 재발송 금지 |
| `stop(taskId)` | 발송 중단, active ID 반환; 실제 runtime 중단 보장 없음 |
| `resolve(taskId,id,{outcome,evidence})` | uncertain의 완료 또는 취소 근거 기록 |
| `resume(taskId)` | active/uncertain이 없을 때만 다음 지시 허용 |
| `list(taskId)` / `status(taskId)` | 복사된 메시지 / paused 포함 projection 조회 |
| `close()` | writer lock 해제 |

resolve의 outcome은 `completed|cancelled`만 지원한다. `retry`는 제공하지 않는다. cancelled는 운영자가 확인한 결과를 기록하는 것이며 이 호출 자체가 원격 실행을 취소하지 않는다. queue file은 전용 SessionStore 형식이며 임의의 기존 task/event 저장소와 혼용하지 않는다.

## 전달 불확실성 예

```js
queue.enqueue('task-a', { id: 'message-b', text: 'follow up' });
queue.next('task-a');
queue.markUncertain('task-a', 'message-b');
queue.next('task-a'); // null
// queue.resume('task-a') throws: unresolved work remains.
queue.resolve('task-a', 'message-b', {
  outcome: 'completed', evidence: 'Runtime history confirms message-b finished.'
});
queue.resume('task-a');
```

실제로 존재하는 runtime 근거를 넣어야 한다. 예제 문자열을 운영 확인 대신 사용하면 안 된다. 재시작 중 `sending`은 저장된 `uncertain` 이벤트로 바뀌며, 잘못된 상태 전이는 projection 단계에서 거부된다.

## 결과와 한계

[보고서](results/report.md)에 13개 시나리오와 실제 평가 시각이 있다. 모든 테스트의 상태 파일은 임시 디렉터리에 생성·삭제한다. 서로 다른 Node 프로세스가 같은 완료 기록을 읽고 뒤의 대기 건만 dispatch하는 흐름도 확인했다. 외부 부작용의 exactly-once 보장은 하지 않으며, 전송과 원격 실행을 하나의 트랜잭션으로 만들지 않았다. 11의 용량·단일 writer·stale lock 제약을 그대로 상속한다.

비동기 전송이 곧 완료를 뜻하지 않는다는 구분은 [OpenCode 공식 HTTP 문서](https://opencode.ai/docs/server/)에 따라 명시했다. 개인 AI 제품의 실제 엔진 상태·승인·질문과 결합하는 부분은 16/17 및 프로젝트 구현에서 검증한다.
