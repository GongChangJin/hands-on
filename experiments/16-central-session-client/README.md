# Central Session Client

> 접속한 창이 바뀌거나 끊겨도 같은 작업을 이어 보면서 소유권과 승인 경계를 유지할 수 있는가?

- 상태: `validated`
- 참여자: `@ukkhnn`
- 학습 순서 슬롯: 2026-10-27
- 선행: 11 Session Persistence, 12 Durable Instructions, 13 Approval Boundary
- 후행: 17 Personal AI Handoff

## 배경

01~09의 CLI 결과만으로는 기기 전환 시 어떤 지시가 전달됐고 승인됐는지 알 수 없다. 중앙 상태를 읽는 두 클라이언트를 실제 localhost HTTP로 연결해 이 차이를 검증한다.

## 범위와 평가

Node.js 22.19 이상 기본 HTTP/fetch API와 앞선 세 실험을 조합한다. 같은 소유자의 두 클라이언트, 다른 소유자의 접근 거부, origin·host·입력 검사, 지시 중복 방지, 이벤트 커서 재접속, 중단 요청과 재시작 불확실성을 고정 fixture로 평가한다. shared/cases.json의 모든 기대값이 통과해야 한다.

맥미니·모바일·Tailscale·HTTPS는 이번 실행 범위에 없다. 토큰은 테스트 전용이며 실제 계정 인증을 흉내 낸 성공으로 확대하지 않는다. 프로세스 중단은 런타임이 확인해야 하므로 중단 요청 접수와 분리한다.

## 실행

```sh
cd implementations/ukkhnn
npm test
npm run evaluate
```

공통 AgentResult의 완료 상태와 별도로, 실행 중 이벤트·대기열 모델을 사용한다. 17에서 공통 integration 계약으로 최종 결과를 내보낸다.

## 결과와 적용

[실행 결과](implementations/ukkhnn/results/report.md)와 [구현 설명](implementations/ukkhnn/README.md)을 참고한다. personal-ai의 polling UI와 중앙 실행 방향에 연결되며, 영속 이벤트 커서는 제품의 향후 개선 후보다.

## 참고

- [Node HTTP](https://nodejs.org/api/http.html)
- [Node test runner](https://nodejs.org/api/test.html)
- [OpenCode Server](https://opencode.ai/docs/server/)
