# 13 Approval Boundary

> 승인한 사람·작업·행동·revision이 모두 일치할 때만 일회성 실행 권한을 소비할 수 있는가?

- 상태: `validated` — 로컬 결정적 경계 평가 완료
- 참여자: `@ukkhnn`
- 학습 세션 라벨: 2026-10-20. 실제 구현·평가 실행 시각은 결과의 `executed_at`을 따른다.
- 선행: 10~12의 작업·이벤트 기반, 06 Router의 정책 경계
- 후행: 16 Central Session Client, 17 Personal AI 연결

08/09가 코드 변경의 실행·보안 적합성을 다룬다면 이 과제는 **사람의 동의를 특정 요청에 묶는 것**을 다룬다. 인증된 호출자가 owner와 현재 시간을 전달한다는 전제에서, 승인 원장을 디스크에 저장하고 재시작 후에도 재사용을 차단한다.

## 구현과 평가

요청은 불변 JSON snapshot과 SHA-256 fingerprint로 기록한다. task/owner/revision/action이 다른 응답, 기한이 지난 응답, 재사용을 거절한다. 같은 작업·소유자에게 더 높은 revision이 등록되면 이전 대기 요청은 superseded가 된다. 다른 scope의 잘못된 시도는 원래 요청을 소비하지 않는다.

| 검증 | 결과 |
| --- | --- |
| 독립 fixture 10건 | 10/10 |
| 경계 테스트 | 14/14 |
| 기대하지 않은 승인 | 0 |

재현 명령은 [구현 README](implementations/ukkhnn/README.md)에 있다. [평가 결과](implementations/ukkhnn/results/report.md), [개별 레코드](implementations/ukkhnn/results/records.jsonl)를 함께 검토한다. 평가 레코드는 기존 `EvaluationRecord`의 필드 형식을 사용한다. 진행 상태는 기존 최종 `AgentResult`에 섞지 않는다.

## 적용 판단과 한계

`trial`: 서버 내부의 인증된 결정 경계에 적용할 수 있다. **승인과 외부 부작용은 하나의 transaction이 아니다.** 소비 직후 crash가 발생하면 실행 여부가 불명확해질 수 있으므로 외부 도구에는 별도의 idempotency/receipt 설계가 필요하다. 이 실험은 외부 발송이나 변경을 실행하지 않는다.

원장 파일과 상위 디렉터리, 호출자의 owner/time은 신뢰해야 한다. 프로세스 간 exclusive lock은 충돌을 차단하지만 crash로 남은 lock은 자동 회수하지 않는다. 악의적인 원장 편집, 멀티 호스트 저장소, 전원 손실까지의 내구성은 보장하지 않는다.

## 구현 근거

- Node 공식 [파일 시스템 문서](https://nodejs.org/docs/latest-v22.x/api/fs.html): exclusive `wx` 생성, 동기 기록과 rename 사용. 원자적 갱신과 충돌 차단을 구분한다.
- Node 공식 [Crypto 문서](https://nodejs.org/docs/latest-v22.x/api/crypto.html): `createHash('sha256')`로 정규화한 JSON을 식별한다. hash는 사용자 인증을 대신하지 않는다.
