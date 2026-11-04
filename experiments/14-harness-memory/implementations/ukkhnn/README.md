# Harness and Memory — ukkhnn

Node 22, 외부 의존성·API 호출 없음.

```sh
cd hands-on/experiments/14-harness-memory/implementations/ukkhnn
node --test
node src/evaluate.mjs
```

평가는 메모리 안에서 합성 자료를 다루며 결과 파일만 쓴다. 실제 사용자 기억을 수집하지 않는다.

## Snapshot 인터페이스

`src/snapshot.mjs`는 `HARNESS_VERSION`, `HARNESS_FIELDS`, `createHarnessSnapshot(template, { capabilities })`, alias `createSnapshot`을 export한다. 입력 예시는 [harness.json](../../shared/harness.json)을 기준으로 한다.

반환값은 `{ version: 1, fingerprint, template }`이며 전체가 불변이다. template은 `version`과 여섯 필드를 정확히 요구한다. model/skill/tool의 capability가 runtime 선언에 없으면 거절한다. configured tool만 permissions에 넣을 수 있고 부작용 도구를 허용하려면 `allowWrites: true`가 필요하다. 그 이후의 도구 호출 집행은 runner 책임이다.

## Memory 인터페이스

`src/memory.mjs`:

- `createMemoryRecord(record)`: 출처·시간·revision 형식 검증과 불변 사본.
- `selectMemory(records, { projectId, now, limit = 20 })`: 프로젝트별 최신 유효 기억. 전체 기록 체인이 필요하다.
- `memoryForHarness(snapshot, records, now)`: memory가 꺼져 있으면 빈 목록, 켜져 있으면 snapshot의 프로젝트로 선택.

```js
const record = {
  id: 'style', projectId: 'project-a', revision: 1, supersedes: null,
  text: 'Keep notes concise', deleted: false,
  source: { uri: 'fixture://note/1', hash: 'a'.repeat(64), observedAt: 1000 },
  expiresAt: 3000,
};
selectMemory([record], { projectId: 'project-a', now: 2000 });
```

시간은 epoch milliseconds, `expiresAt: null`은 만료 없음이다. revision 1의 supersedes는 null, 후속은 직전 기록의 revision이다. 같은 revision의 완전히 동일한 복제는 중복 제거하지만 서로 다른 내용은 `conflicting_revision`으로 중단한다. `deleted: true`는 논리 삭제이며 최신 tombstone이 만료되어도 이전 값을 복구하지 않는다.

## 결과와 적용 경계

17개 테스트와 10개 독립 시나리오가 통과했다. [records.jsonl](results/records.jsonl)은 기대값과 관측 오류를 남긴다. 대표 실패는 `missing_model_capability`, `conflicting_revision`, `missing_provenance`다. 최신 기억을 먼저 선택한 다음 만료를 적용하는 순서가 중요하다. 이 순서를 바꾸면 오래된 사실이 다시 선택될 수 있다.

현재 selector는 작은 배열을 매번 검증한다. 대규모 검색, 인증 서버, 기억 자동 생성 및 사실성 평가는 구현하지 않았다. `memoryForHarness`의 snapshot은 신뢰하는 설정 경계에서 `createHarnessSnapshot`으로 생성한 값을 전달한다.
