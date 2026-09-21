# Agentic RAG 평가 결과

| 지표 | 결과 |
| --- | ---: |
| 성공률 | 100.0% (5/5) |
| 근거 정확도 | 100.0% |
| 계산 정확도 | 100.0% |
| 도구 정확도 | 100.0% |
| p50 / p95 | 7260ms / 27000ms |
| 추정 API 비용 | $0.004325 |
| 안전 위반 | 0 |

## 케이스

| task | category | pass | tools | sources | failure |
| --- | --- | ---: | --- | --- | --- |
| rag-mixed-01 | mixed | PASS | retriever, calculator | product-policy-v1 | — |
| rag-mixed-02 | mixed | PASS | retriever, calculator | product-policy-v1 | — |
| rag-mixed-03 | mixed | PASS | retriever, calculator | product-policy-v1 | — |
| rag-mixed-04 | mixed | PASS | retriever, calculator | incident-playbook-v1 | — |
| rag-mixed-05 | mixed | PASS | retriever, calculator | retrieval-operations-v1 | — |
