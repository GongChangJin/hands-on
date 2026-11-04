# Session Persistence — @ukkhnn

Node 22.19+와 기본 라이브러리만 필요하다. `npm test`, `npm run evaluate`로 재현한다. 평가 상태는 운영체제 임시 폴더에 만들고 종료 시 지운다. `node src/evaluate.mjs --out /tmp/session-results`로 출력 위치를 지정할 수 있다.

## 공개 API

```js
import { SessionStore } from './src/store.mjs';
const store = new SessionStore('/tmp/example-session-lab/state.json');
try {
  store.createTask({ id: 'task-a', projectId: 'project-a', ownerId: 'owner-a' });
  const event = store.appendEvent('task-a', { type: 'instruction.queued', payload: { messageId: 'message-a' } });
  store.events('task-a', 0); // Includes event.seq
  store.getTask('task-a'); // Deep copy
  store.listTasks(); // Deep copy, for startup reconciliation
} finally { store.close(); }
```

`events(id, afterSeq=0)`는 해당 작업의 `seq > afterSeq` 이벤트를 반환한다. 순번은 저장소 전체 기준이라 한 작업에서 1,3처럼 건너뛸 수 있다. 모르는 task 조회·이벤트 추가는 거부한다. `createTask`의 같은 ID/owner/project 반복은 성공하며 다른 신원으로 덮어쓰기는 거부한다. 모든 공개 반환값은 복사본이다.

## 구현

- `validation.mjs`: 식별자, cursor, JSON·크기·깊이 검증
- `snapshot.mjs`: schema, checksum, 참조·이벤트 순번 검증
- `atomic.mjs`: writer lock, private file, fsync/rename
- `store.mjs`: 작업·이벤트 API와 변경 전 복사, 쓰기 결과 불확실 시 재사용 거부
- `scenarios.mjs`: 오류 주입과 실제 별도 프로세스 재시작

`close()` 후에만 같은 파일을 다른 인스턴스로 연다. 동시 writer는 `EEXIST`로 거부한다. lock 소유권이 바뀌면 삭제하지 않는다. 비정상 종료의 stale lock은 자동으로 회수하지 않으며, 프로세스 종료를 확인하고 수동 복구해야 한다. 파일의 checksum만으로 공격자의 변경을 막을 수는 없다.

## 결과와 다음 연결

평가 12/12, 테스트 14/14. [보고서](results/report.md)는 task identity, 깊은 복사, cursor, 프로세스 재시작, 손상, 쓰기 실패 결과를 구분한다. 12는 이 저장소를 실제로 import해 지시 상태 전이를 보존한다. 애플리케이션 권한 인증, 저장 암호화, migration·백업·전원 장애 검증은 구현하지 않았다.

[Node.js 22 공식 fs 문서](https://nodejs.org/docs/latest-v22.x/api/fs.html)를 참고했다. 실행 대상 파일시스템의 rename과 sync 동작을 별도로 검증해야 한다.
