# 공통 자료

전용 로컬 테스트 사이트, 12개 공통 태스크, 허용 정책과 최종 DOM 판정 조건을 둡니다. 실제 계정 정보와 로그인 상태는 사용하지 않습니다.

- `site/index.html`: 검색·필터·폼·탭·스크롤·동적 요소·변경 UI와 prompt injection fixture
- `tasks.jsonl`: 태스크 목표, 입력, UI variant, 최종 DOM assertion
- `policy.json`: localhost 전용 origin, 허용 행동, step·복구·시간 한도와 외부 이동 차단

각 태스크는 새 browser context와 새 페이지에서 시작한다. 결과는 모델의 완료 선언 대신 `expected.selector`의 최종 DOM 값으로 판정한다.
