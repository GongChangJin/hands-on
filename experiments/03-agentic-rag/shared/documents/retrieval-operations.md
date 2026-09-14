---
document_id: retrieval-operations-v1
title: Agentic RAG 검색 운영 기준
version: 2026-09-01
---

# 수집과 분할

승인된 지식 문서는 매일 02:00 KST에 증분 수집한다. 원문이 바뀌면 문서 버전과 corpus fingerprint를 갱신한 뒤 색인을 다시 만든다.

기본 분할 크기는 500 tokens이고 겹침은 80 tokens이다. 제목, 문서 ID, 원문 줄 범위를 각 chunk의 metadata에 보존한다.

# 검색과 재검색

첫 검색은 cosine 유사도 상위 4개 chunk를 반환한다. Agent가 근거가 부족하다고 판정하면 질의를 한 번 고쳐서 재검색할 수 있다. 따라서 한 질문의 검색 호출 상한은 2회이다.

검색 적합성 참고 임곗값은 0.55이다. 임곗값을 넘는 근거가 없거나 관련 문서에 답이 없으면 추측하지 않고 “공통 문서에서 확인할 수 없음”으로 답한다.

# 저장소와 관측

로컬 개발은 Qdrant의 `agentic-rag-v1` collection을 사용한다. 임베딩은 로컬 multilingual 모델로 계산하며 문서 내용이나 질의를 외부 임베딩 API로 보내지 않는다.

Phoenix project 이름은 `03-agentic-rag`이다. 한 workflow trace 아래에 LangGraph node, LLM generation, `retriever.search`, `tool.calculator` span을 연결하고 검색 질의, chunk ID, score, 계산식을 기록한다. 비밀 키와 원문 전체는 span attribute에 기록하지 않는다.
