# 10 — 실행 엔진 어댑터

> 모델과 Agent 선택 결과를 특정 실행 엔진에 연결하면서 제품의 상태·권한 경계를 유지할 수 있는가?

- **상태:** `validated` — 로컬 HTTP fixture 범위
- **참여자:** `@ukkhnn`
- **선행:** 01 평가 계약, 06 Router, Integration v1
- **후행:** 11 세션 보존, 12 지시 대기열, 17 Personal AI 인계
- **학습 슬롯:** 2026-10-05. 2026-11-04에 재구성·구현·평가한 자료이며, 과거 실험 실행을 주장하지 않는다. 실제 시각은 결과의 `executedAt`에 기록한다.

## 검증할 질문과 배경

기존 Router는 어디로 보낼지를 선택했고 Integration v1은 CLI 결과를 공통 계약으로 연결했다. 지속적으로 쓰는 개발 작업공간에는 세션 생성, 비동기 지시 접수, 진행 조회, 중단이 추가로 필요하다. 이 단계는 도구 API가 제품의 작업 ID·완료 판단·권한 설정을 직접 결정하지 않도록 경계를 실험한다.

## 과제와 범위

입력은 작업 이름, 자체 메시지 ID와 텍스트, 요구 capability다. 출력은 외부 세션 ID, 접수 결과, 정규화한 snapshot과 민감정보 없는 전송 trace다. 허용 endpoint만 호출하고 응답 형식·크기·시간 제한·세션 소유권을 검사한다.

Node 22 기본 HTTP 서버로 OpenCode 공식 HTTP API의 작은 부분을 재현했다. 실제 TCP/HTTP 통신을 실행하지만 **실제 OpenCode 프로세스·모델·사용자 계정은 실행하지 않는다.** 모델 품질, 실제 배포 버전 호환성, SSE, permission API, 도구 실행과 다중 호스트 연결은 범위 밖이다. 비동기 HTTP 204는 접수이며 완료가 아니다.

## 공통 계약 적용

기존 `TaskRequest`의 사용자 의도는 상위 coordinator가 유지한다. 이 실험은 제품 연결용 `RuntimeSession`과 `RuntimeSnapshot`을 추가하고, 도구 trace는 HTTP 작업명·상태·지연시간만 남긴다. 모델 답변 품질을 측정하지 않으므로 기존 `AgentResult`·`EvaluationRecord`의 품질 점수를 꾸며 넣지 않는다. 대신 별도 시나리오 평가에 `evidenceMode: local-fixture`를 명시한다.

## 실행과 평가

```sh
cd hands-on/experiments/10-runtime-adapter/implementations/ukkhnn
npm test
npm run evaluate
```

의존성 설치 없이 실행한다. 로컬 포트 개방을 제한하는 환경에서는 임시 `127.0.0.1` 서버 허용이 필요하다. 원격 주소를 허용하는 방식으로 우회하지 않는다.

| 검증 | 목표 | 결과 |
|---|---:|---:|
| 공통 시나리오 | 전부 통과 | 12/12 |
| 자동 테스트 | 전부 통과 | 14/14 |
| unsupported·허용 밖 endpoint | HTTP 요청 0회 | 통과 |
| timeout·redirect | 자동 재시도·redirect follow 0회 | 통과 |
| 실제 모델 호출 / 비용 | 0회 / $0 | 0회 / $0 |

결과는 [실행 보고서](implementations/ukkhnn/results/report.md)와 [원시 평가 레코드](implementations/ukkhnn/results/records.jsonl)에 있다. 반복 실행 지연시간은 성능 보장이 아닌 로컬 측정값이다.

## 실패 사례와 적용 판단

문자열 `healthy: "yes"`, 잘못된 JSON, 64KiB를 넘는 응답, 다른 세션의 메시지, 알려지지 않은 상태가 모두 명시적 오류로 끝났다. timeout은 전달 결과가 불확실할 수 있으므로 이 어댑터가 재시도하지 않는다. 이후 12에서 저장된 메시지 ID와 함께 조정한다.

**판단: `trial`.** 제품 상태와 실행 엔진 연결을 분리하는 구조에 적용할 수 있다. `personal-ai/agent-workspace/app/src/opencode.js`의 책임과 연결되지만 그 파일을 가져오거나 수정하지 않았다. 실제 OpenCode 채택 판단에는 해당 설치 버전의 `/doc` 계약과 유료 실행을 별도 확인해야 한다.

## 참고

- [OpenCode 공식 Server 문서](https://opencode.ai/docs/server/) — health, session, status, message, prompt_async, abort 및 Basic 인증 규약. 2026-11-04 확인. 이 실험은 해당 API의 최소 부분집합이며 전체 서버 호환성 선언이 아니다.
- 구현별 API와 후속 연결 예시는 [구현 README](implementations/ukkhnn/README.md)를 참고한다.
