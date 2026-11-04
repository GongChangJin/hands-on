# ukkhnn — 두 클라이언트와 중앙 세션

Node.js 22.19+, 외부 npm 패키지 없음. `npm test`, `npm run evaluate`로 재현한다. 상태는 테스트 소유 임시 디렉터리에만 만들며 종료 시 제거한다. 포트를 외부에 공개하지 않는다.

## 구성

- policy: 소유권, bearer 인증, host/origin과 입력 검증
- protocol: bounded JSON 요청 및 원문을 반사하지 않는 오류 응답
- server: 11/12/13의 저장소·대기열·승인을 연결하는 localhost HTTP
- client: 상대 경로 요청과 task별 단조 이벤트 커서
- scenarios: 고정 기대값으로 실행한 정상·실패 사례

## 관찰할 실패

다른 소유자의 task는 404로 감추고, 동일 message ID의 다른 내용은 409로 막는다. 전달 중 서버가 닫히면 재개 후 `uncertain`으로 남아 자동 재전송하지 않는다. `stop_requested`는 큐의 dispatch를 멈춘 상태이며 런타임 프로세스 종료 확인이 아니다.

## 적용 범위

trial. 이 실험은 한 컴퓨터의 두 클라이언트이다. 장치 간 통신, 운영 인증·세션 만료/회수, HTTPS, 오래 열린 연결, 부하, Tailscale은 별도 검증해야 한다. 세 저장소의 쓰기는 하나의 transaction이 아니므로 중간 장애에서 event projection과 queue/approval의 reconciliation이 제품화 과제로 남는다.

진행 기록 저장만 실패했을 때는 이미 저장한 지시·승인 영수증을 유지하고 `audit_recorded: false`를 반환한다. 이를 미접수로 해석해 새 ID로 재전송하면 안 된다. 같은 지시 ID로 조회·재조정하고 승인 장부의 소비 여부를 확인한다. 누락한 이벤트의 자동 복원은 구현하지 않았으며, 쓰기 오류 이후 저장소 재개에는 재시작·수동 확인이 필요할 수 있다.

학습 날짜 슬롯과 실제 실행일은 다르다. 실제 실행일·측정치·미검증 항목은 results/summary.json에 있다.
