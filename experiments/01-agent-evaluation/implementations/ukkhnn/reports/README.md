# Experiment reports

## 보존된 실행

- `pilot-upstage-solar-pro4-architecture-v1/`: 20개 Dataset 첫 exploratory run. 구조와 evaluator의 빈틈을 발견한 기록이며 최종 비교값으로 사용하지 않는다.
- `upstage-solar-pro4-architecture-v2/`: prompt와 handoff 입력 경계를 고정한 최종 single/handoff 비교.
- `upstage-solar-pro4-single-llm-judge/`: CODE 평가와 선택적 LLM 평가의 분리 확인.

모든 디렉터리는 Phoenix가 반환한 실행 결과로부터 생성한 JSONL, CSV, JSON, Markdown을 보존한다. 실패 결과도 삭제하지 않는다.

## 해석 규칙

- `task_success`는 CODE evaluator만으로 계산한다.
- LLM evaluator는 진단 annotation이며 성공 여부를 변경하지 않는다.
- 비용은 Agent task의 공개 단가 기반 추정치이고 LLM evaluator 호출 비용은 포함하지 않는다.
- pilot과 v2는 evaluator 구성이 다르므로 수치를 직접적인 전후 성능 향상률로 사용하지 않는다.
