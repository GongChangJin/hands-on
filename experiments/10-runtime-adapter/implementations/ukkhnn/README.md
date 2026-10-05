# Runtime Adapter — @ukkhnn

Node.js 22.19+ 기본 라이브러리만 사용한다. `npm test`는 14개 검증을, `npm run evaluate`는 12개 공통 사례를 실행한다. `node src/evaluate.mjs --out /tmp/runtime-adapter-results`로 평가 결과 위치를 바꿀 수 있다.

## API

```js
import { RuntimeAdapter } from './src/adapter.mjs';
import { startFixture } from './src/fixture.mjs';
const fixture = await startFixture();
try {
  const runtime = new RuntimeAdapter(fixture.url, { password: fixture.password });
  runtime.require(['create', 'send', 'snapshot', 'abort']);
  const { runtimeId } = await runtime.create('sample task');
  await runtime.send(runtimeId, { id: 'msg_1', text: 'fixture instruction' });
  // Accepted is not completed; snapshot first reports running.
  await runtime.snapshot(runtimeId);
  fixture.complete(runtimeId);
  const completed = await runtime.snapshot(runtimeId);
  console.log(completed.status); // idle, with completed assistant message
} finally { await fixture.close(); }
```

`require(['permissions'])` 등 미지원 요구는 호출 전에 거부한다. `abort(id)`는 요청 확인만 반환하고 실제 중단 여부는 후속 `snapshot(id)`로 확인한다. `snapshot`은 `{runtimeId,status,messages}`이며 `status`는 `idle|running|retrying`이다. 메시지는 텍스트와 식별자만 정규화하고 원본 provider 설정은 반환하지 않는다.

## 파일과 실행 경계

- `contracts.mjs`: 입력·capability 계약
- `transport.mjs`: loopback·endpoint 허용 목록, 인증, redirect 거부, 시간·응답 크기 제한
- `adapter.mjs`: OpenCode 부분 HTTP 규약을 제품 관점의 작은 API로 변환
- `fixture.mjs`: 합성 비밀번호와 메모리 상태를 쓰는 임시 HTTP 서버
- `scenarios.mjs`, `tests/`: 정상 흐름·오류 주입·정보 노출 경계
- `evaluate.mjs`, `results/`: 실제 평가 시각과 관찰 결과

브라우저나 운영 서버에 공개하지 않는다. fixture는 인증정보를 외부에서 읽지 않으며 포트와 비밀번호는 출력 기록에 포함하지 않는다. 전송 trace에는 본문·헤더·자격증명을 남기지 않는다. 현재 `trace`의 `received`는 HTTP 응답 수신을 뜻하며, 이후 어댑터 schema 검사가 성공했음을 뜻하지 않는다.

## 결과와 한계

시나리오 12/12, 자동 테스트 14/14. [보고서](results/report.md)에서 실패 주입이 어떻게 차단됐는지 확인할 수 있다. 실제 네트워크를 거친 로컬 protocol fixture 증거이며 OpenCode 실프로세스나 모델 답변의 증거는 아니다. HTTP 요청 이후 연결이 끊기면 전달 여부가 모호할 수 있어 재시도 없이 오류를 올린다. 12의 durable queue에서 해당 상태를 다룬다.

[공식 OpenCode HTTP 규약](https://opencode.ai/docs/server/)을 참고하되 runtime ID의 내부 표현이나 모든 이벤트 종류가 고정되어 있다고 가정하지 않는다. 제품 도입 전 실제 설치 버전의 OpenAPI를 비교해야 한다.
