# 재현 환경과 검증 경계

신규 10~17은 Node.js 22.19.0과 로컬 Git으로 실행한다. 모든 영속 상태와 실험용 Git 저장소는 테스트가 만든 임시 폴더에 두며, 사용자 작업 저장소나 Personal AI 코드를 수정하지 않는다. HTTP fixture는 `127.0.0.1`의 임시 포트만 사용한다. 제한된 실행 환경에서 포트 listen이 금지되면 로컬 실행 권한이 필요하다.

## 실제 날짜와 학습 순서

지정된 2026년 10월의 8개 날짜는 학습·커밋 배치 슬롯이다. 구현·검증은 2026-11-04에 수행했고 측정 파일에 실제 UTC 시각을 보존했다. 모델 호출 품질, Mac mini 배포, 실제 두 기기의 접속을 수행한 것으로 기록하지 않는다.

## 기존 Integration v1 환경 확인

2026-11-04 현재 MacBook에서 기존 `integration`의 Python 회귀 검증도 확인했다. 18개는 통과했고, Router subprocess를 호출하는 E2E 1개는 `06-llm-router/implementations/ukkhnn/.venv/bin/python`이 없어 실행하지 못했다. 소스 변경으로 기존 테스트를 건너뛰거나 성공으로 처리하지 않았다.

기존 `integration/.venv/bin/python`도 현재 호스트에서 사용할 수 없어 이 확인에는 설치된 Python 3.11.9를 사용했다. 이전 머신의 가상환경 경로는 Git의 소스 전달만으로 복구되지 않는다. 기존 v1 전체 재현에는 각 Python 구현 README의 환경 설치 절차가 별도로 필요하다. 신규 10~17의 Node 검증은 이 Python 가상환경에 의존하지 않는다.

## 새 실험 결과의 의미

- HTTP·저장·재시작·임시 Git 조작은 실제 로컬 입출력이다.
- 실행 엔진은 합성 fixture이며 실제 OpenCode/LLM 호출을 대체한 제품 검증이 아니다.
- 정상 종료 후 상태를 다시 여는 검증과 강제 종료·전원 장애 복구는 다르다. 남은 lock은 수동 확인이 필요하다.
- 인증 토큰은 테스트용이다. 운영 인증·비밀 저장·TLS·만료·회수·원격 접근은 후속 검증이다.
- 여러 파일 저장소를 하나의 transaction으로 묶지 않는다. 지시·승인 저장 후 audit만 실패하면 저장된 영수증과 `audit_recorded: false`를 반환하며, 누락 이벤트 자동 재구성은 구현하지 않았다.

## 공통 결과 형식 검사

Python 3.11 이상과 `integration/pyproject.toml`의 `jsonschema` 의존성이 있는 환경에서 실행한다.

```sh
python3 integration/validate-workspace-contracts.py
```

17의 요청·결과·도구 trace·평가 레코드와 소스 인계 계획을 기존 JSON Schema로 검사한다. Node 실험의 실행 자체에는 Python이 필요하지 않다.
