# Tool Adapter

Agent가 호출하는 검색·계산·브라우저·코드·보안 도구의 공통 규칙을 관리합니다.

각 도구는 입력 schema, 출력 schema, timeout, 오류 형식, 허용 범위와 부작용 여부를 선언하고 실행 결과를 `ToolTrace`로 남겨야 합니다.
