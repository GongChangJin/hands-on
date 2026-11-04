# 14 Harness and Scoped Memory

> 실행 설정을 고정하고 출처 있는 기억만 프로젝트·revision·유효기간에 맞춰 선택할 수 있는가?

- 상태: `validated`
- 참여자: `@ukkhnn`
- 학습 세션 라벨: 2026-10-21. 실제 실행일은 결과 `executed_at`에 기록한다.
- 선행: 10 실행 엔진 연결, 11 영속 상태, 13 승인 경계
- 후행: 17 Personal AI 연결

03 RAG의 검색·답변 성능과 다른 질문을 다룬다. 이 실험은 모델을 호출하지 않고 **prompt/model/skills/tools/memory/permissions 여섯 항목의 실행 snapshot**, capability 호환성, 기억의 소유 범위와 변경 이력을 검증한다.

## 구현

버전 1 template을 검증하고 정규화 JSON의 SHA-256과 깊게 동결한 사본을 만든다. 호출자가 원본 template을 바꿔도 실행 중 snapshot은 변하지 않는다. 권한에 없는 도구를 추가 실행하는 runner는 포함하지 않는다. runner가 snapshot의 허용 도구와 쓰기 권한을 반드시 집행해야 한다.

기억에는 project ID, source URI/hash/관측 시각, revision과 supersedes, 만료 시각, 삭제 상태가 있다. project를 먼저 고르고 revision chain을 검증한 후 최신 기억에 만료·삭제를 적용한다. 최신 사실이 만료되거나 삭제되어도 과거 사실이 되살아나지 않는다. 같은 revision의 상반된 값은 선택하지 않고 실패한다.

| 평가 | 결과 |
| --- | --- |
| 독립 시나리오 | 10/10 |
| 경계 테스트 | 17/17 |
| 프로젝트 기억 혼합 | 0 |

[구현·재현 명령](implementations/ukkhnn/README.md), [결과](implementations/ukkhnn/results/report.md), [기억 계약](shared/memory.schema.json)을 제공한다. `EvaluationRecord` 형식으로 평가하며 기존 공통 계약을 수정하지 않는다.

## 적용 판단

설정 재현성과 기억 수명 관리에는 `trial`. capability 선언은 모델의 실제 성능을 증명하지 않으며, 출처 hash도 내용의 진위를 증명하지 않는다. 전체 revision chain을 가진 작은 합성 메모리만 평가했다. 인증, 저장소, 벡터 검색, LLM 기억 추출, 대량 기억 성능은 별도 과제다. 정정 기록을 보존하는 tombstone은 개인정보의 물리적 삭제 절차가 아니다.

Node 공식 [Crypto 문서](https://nodejs.org/docs/latest-v22.x/api/crypto.html)의 SHA-256 API와 [기본 모듈 문서](https://nodejs.org/docs/latest-v22.x/api/fs.html)를 참조했다. JSON 정규화와 객체 불변성은 실험 내부 규칙으로 구현하며 외부 표준 서명 형식이라고 주장하지 않는다.
