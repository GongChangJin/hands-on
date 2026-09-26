# 공통 자료

의도적으로 취약한 로컬 Python 샘플, 예상 finding, 참조 수정, 보안·기능 테스트와 Docker 격리 정책을 둡니다. 외부 대상 주소나 실제 인증정보는 포함하지 않습니다.

- `fixture/`: SQL injection 2건, 경로 순회 2건, 가짜 하드코딩 비밀값 2건과 정상 대조군 3개
- `fixed/`: 매개변수화 SQL, base 경로 containment, 런타임 환경 변수로 바꾼 결정적 참조 수정
- `expected-findings.json`: 위치·범주·식별자가 고정된 정답 finding
- `rules/semgrep.yml`: 실험 범위에 맞춘 로컬 Semgrep 규칙
- `policy.json`: 도구 버전, 허용 도구·범주, 자원 제한과 승인 임계값
- `container/Dockerfile`: Semgrep 1.178.0, Bandit 1.9.4, pytest 9.1.1 실행 이미지

취약 fixture의 기능 테스트는 수정 전에도 통과하고 보안 테스트는 실패한다. 참조 수정 뒤에는 정적 분석의 예상 finding이 모두 사라지고 기능·보안 테스트가 함께 통과해야 한다.
