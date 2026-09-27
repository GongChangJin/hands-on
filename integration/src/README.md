# Integration Source

- `contracts.py`: 저장소 공통 JSON Schema 검증과 JSONL 출력
- `adapters.py`: 06 Router subprocess와 02~09 결과 adapter
- `orchestrator.py`: local-only와 Coding → Security 정책을 포함한 fail-closed 실행
- `evaluation.py`: replay 시나리오 평가와 공통 레코드 출력
- `live.py`: 실제 RAG·Browser·Coding·Security smoke 실행
- `cli.py`: `replay`, `live-smoke` 명령

각 Hands-on은 서로 다른 dependency 환경을 유지하므로 Python package를 직접 합치지 않고 subprocess/JSON 경계로 연결합니다.
