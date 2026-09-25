# 공통 자료

작은 Python 패키지 `taskboard`와 5개 Issue, 실행 정책, 공개 테스트와 held-out 판정 테스트를 둡니다. 판정 테스트는 저장소에는 재현 자산으로 보존하지만 모델 prompt에는 포함하지 않고 patch 생성이 끝난 뒤 평가 runner가 별도로 주입합니다.

- `fixture/`: 모든 Issue가 시작하는 동일한 샘플 저장소와 공개 회귀 테스트
- `issues.jsonl`: 요구사항, 허용 경로, 모델에 제공할 context와 판정 테스트 연결 정보
- `policy.json`: 시도·파일·크기·시간 제한과 금지 Git 작업
- `judge/`: 모델 context에서 제외하는 Issue별 판정 테스트

각 Issue는 새 임시 작업공간에서 실행한다. Agent에는 임의 shell이나 Git 명령을 제공하지 않고, 허용 경로의 파일 교체와 고정된 `pytest`·`ruff` 명령만 제공한다. 성공은 공개·신규·held-out 테스트, lint, 변경 범위와 금지 작업을 모두 통과했을 때만 인정한다.
