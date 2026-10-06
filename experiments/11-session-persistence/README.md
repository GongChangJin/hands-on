# 11 — 세션·이벤트 보존

> 실행 엔진과 접속 기기가 바뀌어도 작업의 정체성과 진행 순서를 보존할 수 있는가?

- **상태:** `validated` — 임시 파일시스템·별도 프로세스 재시작 범위
- **참여자:** `@ukkhnn`
- **선행:** 01 공통 계약, Integration v1, 10 Runtime Adapter
- **후행:** 12 Durable Instructions, 16 중앙 세션, 17 인계
- **학습 슬롯:** 2026-10-06. 2026-11-04에 재구성·구현·평가했으며 실제 실행 시각은 `executedAt`에 남긴다.

## 배경과 과제

Integration v1의 요청·결과 파일만으로는 사용자가 어떤 프로젝트의 어떤 작업을 이어가는지 설명하기 어렵다. 상태의 기준을 프로세스 메모리에서 자체 저장소로 옮기고, 실행 엔진 ID와 독립된 task/project/owner 식별자를 유지한다.

작업 생성은 같은 식별자로 재요청해도 한 건을 유지한다. 다른 owner/project로 바꾸려는 요청은 거절한다. 이벤트는 전역 증가 순번을 사용하고 작업별 cursor 조회를 제공한다. 반환값을 수정해도 내부 저장값은 바뀌지 않는다. 이것은 인증 구현이 아니라 데이터 정합성 경계이며, 사용자 신원 확인은 호출하는 서버의 책임이다.

## 설계와 범위

Node 22 파일 API로 JSON snapshot을 저장한다. 새 파일에 쓰기·fsync 후 같은 디렉터리에서 rename하고 디렉터리를 fsync한다. 파일 권한은 0600이다. schema와 checksum, task 참조, 연속된 이벤트 순번을 검사하며 손상 시 기존 데이터를 덮어쓰지 않는다. 배타적 writer lock으로 동시에 쓰는 두 인스턴스를 거부한다.

단일 로컬 writer의 작은 데이터셋을 선택했다. 매 이벤트마다 전체 snapshot을 쓰므로 대용량 서비스에는 적합하지 않다. 최대 1,000 tasks·10,000 events·10MiB snapshot·64KiB payload를 허용한다. 전원 장애·하드웨어 고장 내구성, 분산 DB, schema migration, 자동 백업, 감사로그 위변조 방지는 범위 밖이다. checksum은 우발 손상 검출이며 보안 서명이 아니다.

## 계약과 실행

`TaskRequest`·`AgentResult`를 원문 대화로 대신하지 않고, lifecycle에 필요한 작은 task와 `{seq,taskId,type,payload}` 이벤트를 추가한다. 기존 통합 평가 계약을 변경하지 않는다. 이벤트의 업무 의미는 12와 상위 coordinator가 결정한다.

```sh
cd hands-on/experiments/11-session-persistence/implementations/ukkhnn
npm test
npm run evaluate
```

| 검증 | 결과 |
|---|---:|
| 공통 평가 | 12/12 |
| 자동 테스트 | 14/14 |
| 별도 Node 프로세스에서 이어쓰기 | 순번 1 → 2 보존 |
| 손상·유효하지 않은 payload·중복 writer | 기대대로 거부 |
| 외부 API / 실제 사용자 데이터 | 사용 없음 |

[실행 보고서](implementations/ukkhnn/results/report.md)와 [상세 API](implementations/ukkhnn/README.md)에 결과와 한계를 기록했다.

## 대표 실패와 판단

rename 직전 쓰기 오류를 주입했을 때 마지막 snapshot은 바뀌지 않았고 임시 파일은 제거됐다. 체크섬이 맞지 않는 데이터와 JSON 파싱 오류는 즉시 거부했다. 프로세스가 비정상 종료하면 lock이 남을 수 있으며, 이를 자동 삭제하지 않는다. 운영자는 원래 writer가 종료됐음을 확인한 뒤 lock과 마지막 snapshot을 검토해야 한다. 테스트는 정상 close 후 별도 프로세스 재시작과 rename 전 오류 주입이며, 강제 종료·전원 장애 전체 복구를 검증하지 않았다.

**판단: `trial`.** 자체 상태 저장과 오류 시 보존 원칙을 적용할 수 있다. `personal-ai/agent-workspace/app/src/store.js`의 원자 저장·schema 거부와 연결되며 제품의 백업/복구 완료를 뜻하지 않는다. 이벤트가 늘면 SQLite 트랜잭션과 migration을 다음 비교 대상으로 삼는다.

## 참고

- [Node.js 22 파일시스템 API](https://nodejs.org/docs/latest-v22.x/api/fs.html) — open, fsync, rename, 파일 권한 API. 운영체제·파일시스템이 제공하는 보장과 애플리케이션 복구 정책은 별도다.
