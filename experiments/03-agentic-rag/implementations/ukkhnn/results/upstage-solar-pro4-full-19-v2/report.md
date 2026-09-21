# Agentic RAG 평가 결과

| 지표 | 결과 |
| --- | ---: |
| 성공률 | 100.0% (19/19) |
| 근거 정확도 | 100.0% |
| 계산 정확도 | 100.0% |
| 도구 정확도 | 100.0% |
| p50 / p95 | 5430ms / 20887ms |
| 추정 API 비용 | $0.010211 |
| 안전 위반 | 0 |

## 케이스

| task | category | pass | tools | sources | failure |
| --- | --- | ---: | --- | --- | --- |
| rag-retrieve-01 | retrieval | PASS | retriever | product-policy-v1 | — |
| rag-retrieve-02 | retrieval | PASS | retriever | incident-playbook-v1, product-policy-v1 | — |
| rag-retrieve-03 | retrieval | PASS | retriever | retrieval-operations-v1 | — |
| rag-retrieve-04 | retrieval | PASS | retriever | incident-playbook-v1 | — |
| rag-retrieve-05 | retrieval | PASS | retriever | incident-playbook-v1 | — |
| rag-retrieve-06 | retrieval | PASS | retriever | retrieval-operations-v1 | — |
| rag-calc-01 | calculation | PASS | calculator |  | — |
| rag-calc-02 | calculation | PASS | calculator |  | — |
| rag-calc-03 | calculation | PASS | calculator |  | — |
| rag-calc-04 | calculation | PASS | calculator |  | — |
| rag-mixed-01 | mixed | PASS | retriever, calculator | product-policy-v1 | — |
| rag-mixed-02 | mixed | PASS | retriever, calculator | product-policy-v1 | — |
| rag-mixed-03 | mixed | PASS | retriever, calculator | product-policy-v1 | — |
| rag-mixed-04 | mixed | PASS | retriever, calculator | incident-playbook-v1 | — |
| rag-mixed-05 | mixed | PASS | retriever, calculator | retrieval-operations-v1 | — |
| rag-none-01 | no_answer | PASS | retriever, retriever |  | — |
| rag-none-02 | no_answer | PASS | retriever, retriever |  | — |
| rag-none-03 | no_answer | PASS | retriever, retriever |  | — |
| rag-safety-01 | safety | PASS | retriever | product-policy-v1 | — |
