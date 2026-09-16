# Verified RAG research report

- Condition: `federated-verified`
- Question: RAG 시스템에서 query rewriting, reranking, corrective retrieval, self-reflective retrieval 기법은 검색 품질과 답변의 faithfulness를 어떤 조건에서 개선하며, latency·비용·구현 복잡도 측면에서 어떤 trade-off를 만드는가?
- Search started: 2026-09-16T04:01:29.603954+00:00
- Verified papers: 12
- Evidence claims: 12
- Model status: `offline_mock_not_live`

## Search and verification

Sources: semantic_scholar, crossref, arxiv. Requests: {}. Deduplicated: 3. Identifier failures: 0.

## Claim–evidence

| Claim ID | Paper | Claim | Locator |
| --- | --- | --- | --- |
| offline-claim-001 | Offline Fixture Corrective Retrieval Study 07 | Offline fixture evidence for Offline Fixture Corrective Retrieval Study 07 | offline fixture abstract excerpt |
| offline-claim-002 | Offline Fixture Cross Encoder Reranker Study 05 | Offline fixture evidence for Offline Fixture Cross Encoder Reranker Study 05 | offline fixture abstract excerpt |
| offline-claim-003 | Offline Fixture Self RAG Study 09 | Offline fixture evidence for Offline Fixture Self RAG Study 09 | offline fixture abstract excerpt |
| offline-claim-004 | Offline Fixture Adaptive Retrieval Study 11 | Offline fixture evidence for Offline Fixture Adaptive Retrieval Study 11 | offline fixture abstract excerpt |
| offline-claim-005 | Offline Fixture Self Reflective Retrieval Study 10 | Offline fixture evidence for Offline Fixture Self Reflective Retrieval Study 10 | offline fixture abstract excerpt |
| offline-claim-006 | Offline Fixture Passage Reranking Study 06 | Offline fixture evidence for Offline Fixture Passage Reranking Study 06 | offline fixture abstract excerpt |
| offline-claim-007 | Offline Fixture Query Reformulation Study 02 | Offline fixture evidence for Offline Fixture Query Reformulation Study 02 | offline fixture abstract excerpt |
| offline-claim-008 | Offline Fixture Reranking Study 04 | Offline fixture evidence for Offline Fixture Reranking Study 04 | offline fixture abstract excerpt |
| offline-claim-009 | Offline Fixture Faithful Retrieval Pipeline Study 12 | Offline fixture evidence for Offline Fixture Faithful Retrieval Pipeline Study 12 | offline fixture abstract excerpt |
| offline-claim-010 | Offline Fixture Retrieval Correction Study 08 | Offline fixture evidence for Offline Fixture Retrieval Correction Study 08 | offline fixture abstract excerpt |
| offline-claim-011 | Offline Fixture Query Rewriting Study 01 | Offline fixture evidence for Offline Fixture Query Rewriting Study 01 | offline fixture abstract excerpt |
| offline-claim-012 | Offline Fixture Multi Query Retrieval Study 03 | Offline fixture evidence for Offline Fixture Multi Query Retrieval Study 03 | offline fixture abstract excerpt |

## Method, results, limitations, and trade-offs

### offline fixture

Synthetic evidence confirms only that the offline pipeline is wired correctly.

Supporting claims: offline-claim-001, offline-claim-002, offline-claim-003, offline-claim-004, offline-claim-005, offline-claim-006, offline-claim-007, offline-claim-008, offline-claim-009, offline-claim-010, offline-claim-011, offline-claim-012

Trade-offs: No live research conclusion may be drawn.

## Agent hypotheses (not paper conclusions)

- **offline-hypothesis-001**: The same pipeline should preserve provenance when connected to live APIs.
  - Derived from: offline-claim-001
  - Falsification test: Run the live workflow and check every output contract and locator.
  - Confidence: 0.2

## Representative failures

- None observed.

## Limitations

- Extraction uses bounded public abstract excerpts; claims are not full-text findings unless explicitly marked.
- Search API ranking and metadata can change after the recorded retrieval timestamp.
- Calculated API cost uses provider-reported usage and published rates; it is not an invoice.
- Offline output is synthetic and must not be presented as live research.

## Usage and calculated cost

Provider-reported usage: `{'input_tokens': 0, 'output_tokens': 0, 'cached_input_tokens': 0, 'total_tokens': 0, 'requests': 0}`. Calculated cost: `$0.00000000`. This is a calculation from published rates, not an invoice.
