# Common

모든 핸즈온 프로젝트가 공유하는 계약, 어댑터 규칙과 평가 기반을 관리합니다.

## 구성

- `contracts/`: 프로젝트 사이에서 교환하는 JSON Schema
- `adapters/llm/`: 로컬·API 모델을 같은 방식으로 호출하기 위한 규칙
- `adapters/tools/`: Agent 도구의 입력·출력·오류 처리 규칙
- `evaluation/datasets/`: 여러 프로젝트가 공통으로 사용하는 평가 데이터
- `evaluation/runner/`: 공통 평가 실행기와 결과 집계 규칙

프로젝트 하나에서만 사용하는 데이터와 코드는 해당 프로젝트의 `shared/`에 둡니다. 두 프로젝트 이상이 실제로 공유하기 전에는 `common/`으로 옮기지 않습니다.

## 공통 원칙

- 비밀값과 개인정보를 저장하지 않습니다.
- 계약 변경은 영향받는 프로젝트를 함께 기록합니다.
- 실행 결과는 `AgentResult`, 도구 호출은 `ToolTrace`로 표현합니다.
- 프로젝트별 지표는 `EvaluationRecord`로 변환할 수 있어야 합니다.
