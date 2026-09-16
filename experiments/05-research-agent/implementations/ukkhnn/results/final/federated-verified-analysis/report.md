# Verified RAG research report

- Condition: `federated-verified`
- Question: RAG 시스템에서 query rewriting, reranking, corrective retrieval, self-reflective retrieval 기법은 검색 품질과 답변의 faithfulness를 어떤 조건에서 개선하며, latency·비용·구현 복잡도 측면에서 어떤 trade-off를 만드는가?
- Search started: 2026-09-16T03:57:27.938947+00:00
- Verified papers: 18
- Evidence claims: 47
- Model status: `executed`

## Search and verification

Sources: semantic_scholar, crossref, arxiv. Requests: {'arxiv': 8, 'crossref': 10, 'semantic_scholar': 46}. Deduplicated: 75. Identifier failures: 0.

## Claim–evidence

| Claim ID | Paper | Claim | Locator |
| --- | --- | --- | --- |
| claim-001 | Corrective Retrieval Augmented Generation | LLMs inevitably exhibit hallucinations because the accuracy of generated texts cannot be secured solely by parametric knowledge. | abstract excerpt |
| claim-002 | Corrective Retrieval Augmented Generation | RAG relies heavily on the relevance of retrieved documents, raising concerns about model behavior if retrieval goes wrong. | abstract excerpt |
| claim-003 | Corrective Retrieval Augmented Generation | CRAG is proposed to improve the robustness of generation. | abstract excerpt |
| claim-004 | Corrective Retrieval Augmented Generation | A lightweight retrieval evaluator is designed to assess the overall quality of retrieved documents. | abstract excerpt |
| claim-005 | A Self-Reflective Retrieval Augmented Generation System to Eliminate Hallucination in LLM Generation | In a Retrieval Augmented Generation system, the possibility of hallucination is ever prevalent, as it has been increasingly common for an AI model to produce inaccurate generations given an input, which can become increasingly more devastating for a RAG system due to its node-like generation. | abstract excerpt |
| claim-006 | A Self-Reflective Retrieval Augmented Generation System to Eliminate Hallucination in LLM Generation | To solve this problem, we introduced a series of selfreflective nodes, creating a self-RAG model. | abstract excerpt |
| claim-007 | A Self-Reflective Retrieval Augmented Generation System to Eliminate Hallucination in LLM Generation | To create our program, we established a series of nodes that utilized ChatGPT for generation as well as the Langchain python library and its workflow functions to piece together the nodes. | abstract excerpt |
| claim-008 | A Self-Reflective Retrieval Augmented Generation System to Eliminate Hallucination in LLM Generation | A major challenge f (truncated). | abstract excerpt |
| claim-009 | GRPO++: A Controlled Differentiable Reinforcement Learning Reranking Method for Retrieval-Augmented Generation | The performance of retrieval-augmented generation (RAG) systems heavily depends on the quality of the re-ranking module, yet existing methods face challenges such as training instability, unreasonable reward design, and insufficient confidence calibration. | abstract excerpt |
| claim-010 | GRPO++: A Controlled Differentiable Reinforcement Learning Reranking Method for Retrieval-Augmented Generation | This paper proposes GRPO++, an end-to-end re-ranking framework based on reinforcement learning, which collaboratively optimizes five core modules. | abstract excerpt |
| claim-011 | GRPO++: A Controlled Differentiable Reinforcement Learning Reranking Method for Retrieval-Augmented Generation | Soft Normalized Discounted Cumulative Gain (Soft-nDCG) to achieve a differentiable ranking objective. | abstract excerpt |
| claim-012 | GRPO++: A Controlled Differentiable Reinforcement Learning Reranking Method for Retrieval-Augmented Generation | Critical Reweighting for Importance (CRI) to enhance Top-K position optimization. | abstract excerpt |
| claim-013 | Candidate Evidence Reranking and Risk-Aware Answer Selection in Multi-Hop Retrieval-Augmented Generation | Multi-hop retrieval-augmented generation (RAG) can fail to fully exploit useful evidence even after it has entered the candidate pool, because ranking and limited context budgets determine which documents are actually exposed to the reader. | abstract excerpt |
| claim-014 | Candidate Evidence Reranking and Risk-Aware Answer Selection in Multi-Hop Retrieval-Augmented Generation | Candidate answers produced by multiple retrieval trajectories can likewise be misselected when answer frequency does not align with correction value. | abstract excerpt |
| claim-015 | Candidate Evidence Reranking and Risk-Aware Answer Selection in Multi-Hop Retrieval-Augmented Generation | Building on the SQL-Retrieval Augmented Generation (SAG) backbone, we develop a two-layer framework for candidate utilization. | abstract excerpt |
| claim-016 | Candidate Evidence Reranking and Risk-Aware Answer Selection in Multi-Hop Retrieval-Augmented Generation | At the evidence layer, candidate evidence reranking (CAPE) combines traje (truncated). | abstract excerpt |
| claim-017 | Self-Reflective Retrieval-Augmented Generation (Self-RAG) in Analytical Systems | Traditional analytical systems often struggle with efficiently querying and interpreting vast datasets, while Self-RAG presents a promising solution. | abstract excerpt |
| claim-018 | Self-Reflective Retrieval-Augmented Generation (Self-RAG) in Analytical Systems | Self-RAG can enhance data analysis in distributed systems by improving information retrieval accuracy and generation. | abstract excerpt |
| claim-019 | MMCRAG-Resp: a multi-modal corrective retrieval-augmented generation framework for explainable respiratory disease reasoning | Standard Retrieval-Augmented Generation (RAG) systems only use semantic similarity to retrieve information, and since this method is quite limiting, it may find clinically irrelevant evidence and produce outputs that are unsafe or hallucinated. | abstract excerpt |
| claim-020 | MMCRAG-Resp: a multi-modal corrective retrieval-augmented generation framework for explainable respiratory disease reasoning | This drawback is particularly important in respiratory care, where the diagnosis relies heavily on very accurate physiological indicators such as spirometry patterns and symptom profiles. | abstract excerpt |
| claim-021 | MMCRAG-Resp: a multi-modal corrective retrieval-augmented generation framework for explainable respiratory disease reasoning | We propose MMCRAG-Resp., a clinically grounded, physiology-aware corrective RAG framework for respiratory intelligence. | abstract excerpt |
| claim-022 | MMCRAG-Resp: a multi-modal corrective retrieval-augmented generation framework for explainable respiratory disease reasoning | The system harmonizes 17,516 [excerpt truncated]. | abstract excerpt |
| claim-023 | Understanding Retrieval Pitfalls: Challenges Faced by Retrieval Augmented Generation (RAG) models | Large language models (LLMs) like GPT-4, the engine of products like ChatGPT, have taken centre stage in recent years due to their astonishing capabilities. | abstract excerpt |
| claim-024 | Understanding Retrieval Pitfalls: Challenges Faced by Retrieval Augmented Generation (RAG) models | Yet, they are far from perfect. | abstract excerpt |
| claim-025 | Understanding Retrieval Pitfalls: Challenges Faced by Retrieval Augmented Generation (RAG) models | Many of us have since learnt — perhaps when asking ChatGPT a question or employing it to write our reports — that LLMs can hallucinate. | abstract excerpt |
| claim-026 | LawRAG: Indonesian legal document retrieval-augmented generation with specialized chunking and reranking strategies | Enhancing Question-Answering accuracy on new law documents by using Retrieval-Augmented Generation (RAG)-Large Language Models. | abstract excerpt |
| claim-027 | LawRAG: Indonesian legal document retrieval-augmented generation with specialized chunking and reranking strategies | The proposed method is built on a RAG design for Indonesian new law documents, incorporating a specific data chunking method and a reranker model. | abstract excerpt |
| claim-028 | LawRAG: Indonesian legal document retrieval-augmented generation with specialized chunking and reranking strategies | The proposed method, which segments legal data by focusing on the document title, article, and paragraph, outperforms the sequential chunking method in terms of accuracy. | abstract excerpt |
| claim-029 | LawRAG: Indonesian legal document retrieval-augmented generation with specialized chunking and reranking strategies | This research demonstrates that the completeness of a sentence in the data set used during [truncated]. | abstract excerpt |
| claim-030 | The Impact of Query Decomposition and Cross-Encoder Reranking in Multi-Hop Retrieval-Augmented Generation | Standard single-hop retrieval often fails on complex, multi-hop queries where the answer requires synthesizing information from disparate documents. | abstract excerpt |
| claim-031 | The Impact of Query Decomposition and Cross-Encoder Reranking in Multi-Hop Retrieval-Augmented Generation | The proposed approach decomposes complex queries into self-contained sub-questions and employs a Cross-Encoder to rerank candidates at each retrieval step. | abstract excerpt |
| claim-032 | RETRIEVAL AUGMENTED GENERATION SYSTEM FOR EDUCATIONAL TEXTBOOK QUERY ASSISTANCE | The system facilitates and simplifies communication between students and their textbooks by allowing queries in casual language and providing responses based on textbook material. | abstract excerpt |
| claim-033 | RETRIEVAL AUGMENTED GENERATION SYSTEM FOR EDUCATIONAL TEXTBOOK QUERY ASSISTANCE | The system employs a combination of natural language processing techniques: disassembling and categorizing textbook contents, converting them into a searchable format, and using a language model to generate responses. | abstract excerpt |
| claim-034 | Performance VS Cost: A Modular Architecture for Cost-Aware Adaptive Retrieval in Retrieval-Augmented Generation Systems | Retrieval is a critical component of RAG systems, but choosing the most suitable retrieval strategy is not simple. | abstract excerpt |
| claim-035 | Performance VS Cost: A Modular Architecture for Cost-Aware Adaptive Retrieval in Retrieval-Augmented Generation Systems | Lexical and dense retrievers are efficient and inexpensive, while reasoning-based retrievers can improve effectiveness on complex questions at substantially higher computational cost. | abstract excerpt |
| claim-036 | Performance VS Cost: A Modular Architecture for Cost-Aware Adaptive Retrieval in Retrieval-Augmented Generation Systems | The authors introduce CARE (Cost-aware Adaptive REtrieval), a modular architecture for query-adaptive retrieval. | abstract excerpt |
| claim-037 | Retrieval-Augmented Generation with Low-Latency Deployment for Vertical Domains Question Answering: A Case Study on Economic Resource Platforms | Generative chatbots have improved access to public information, yet their deployment in vertical domains such as policy documents and economic resource platforms still faces challenges in retrieval accuracy, answer faithfulness, latency control, and scalable service readiness. | abstract excerpt |
| claim-038 | Retrieval-Augmented Generation with Low-Latency Deployment for Vertical Domains Question Answering: A Case Study on Economic Resource Platforms | The paper presents an optimized domain-specific question-answering framework that combines normalized Dense Retrieval and BM25 fusion, DistilBERT-based candidate re-ranking, and evidence-constrained T5-small generation within a retrieval-augmented generation pipeline. | abstract excerpt |
| claim-039 | Retrieval-Augmented Generation with Low-Latency Deployment for Vertical Domains Question Answering: A Case Study on Economic Resource Platforms | DistilBERT is used as an encoder and relevance component. | abstract excerpt |
| claim-040 | SCIM: Self-Correcting Iterative Mechanism for Retrieval-Augmented Generation | Standard Retrieval-Augmented Generation (RAG) models are limited by their 'one-shot' nature, failing to assess or improve answer quality dynamically. | abstract excerpt |
| claim-041 | SCIM: Self-Correcting Iterative Mechanism for Retrieval-Augmented Generation | SCIM is a framework featuring multi-dimensional evaluation and adaptive retrieval. | abstract excerpt |
| claim-042 | SCIM: Self-Correcting Iterative Mechanism for Retrieval-Augmented Generation | SCIM operates on a lightweight Flan-T5-base model (250M parameters) and requires no fine-tuning, challenging the industry’s reliance on 7B+ parameter models. | abstract excerpt |
| claim-043 | SCIM: Self-Correcting Iterative Mechanism for Retrieval-Augmented Generation | Experimental results across four major benchmarks show that SCIM yields a 17.2% improvement over sta | abstract excerpt |
| claim-044 | Faithfulness-Aware Multi-Objective Context Ranking for Retrieval-Augmented Generation | Retrieval-Augmented Generation (RAG) has emerged as a dominant paradigm for enhancing Large Language Models (LLMs) with external knowledge. | abstract excerpt |
| claim-045 | Faithfulness-Aware Multi-Objective Context Ranking for Retrieval-Augmented Generation | Existing ranking methods in RAG pipelines primarily optimize for document-query relevance, neglecting crucial factors for generation quality such as factual consistency and information coverage. | abstract excerpt |
| claim-046 | Faithfulness-Aware Multi-Objective Context Ranking for Retrieval-Augmented Generation | We propose a novel multiobjective ranking framework that explicitly models three critical dimensions: relevance, coverage, and faithfulness support. | abstract excerpt |
| claim-047 | Faithfulness-Aware Multi-Objective Context Ranking for Retrieval-Augmented Generation | Unlike traditional IR-centric approaches, our method introduces a utilitybased scoring mechanism that evalu | abstract excerpt |

## Method, results, limitations, and trade-offs

### Corrective Retrieval-Augmented Generation (CRAG)

CRAG is proposed to improve generation robustness by using a lightweight retrieval evaluator to assess retrieved document quality. It addresses the problem that RAG relies heavily on document relevance and that LLMs inevitably hallucinate due to parametric knowledge limitations.

Supporting claims: claim-001, claim-002, claim-003, claim-004

Trade-offs: Introduces additional evaluation step (lightweight evaluator) which may add latency and complexity, but aims to improve robustness. Specific latency/cost impacts are not detailed in the available abstracts.

### Self-Reflective Retrieval-Augmented Generation (Self-RAG)

Self-RAG introduces self-reflective nodes to eliminate hallucination in LLM generation. It is implemented using ChatGPT for generation and Langchain for workflow orchestration. Self-RAG is also presented as a solution for analytical systems to improve information retrieval accuracy and generation in distributed systems.

Supporting claims: claim-005, claim-006, claim-007, claim-017, claim-018

Trade-offs: Involves multiple self-reflective nodes and workflow orchestration, which may increase implementation complexity and latency. However, it aims to reduce hallucination and improve retrieval accuracy. Specific cost/latency metrics are not provided in the available abstracts.

### Re-ranking with Reinforcement Learning (GRPO++)

GRPO++ is an end-to-end re-ranking framework based on reinforcement learning that collaboratively optimizes five core modules, including Soft-nDCG for differentiable ranking and Critical Reweighting for Importance (CRI) to enhance Top-K position optimization. It addresses challenges in existing re-ranking methods such as training instability, unreasonable reward design, and insufficient confidence calibration.

Supporting claims: claim-009, claim-010, claim-011, claim-012

Trade-offs: Reinforcement learning-based re-ranking may require significant training resources and complexity, but aims to improve ranking quality and RAG performance. Specific latency and cost implications are not detailed in the available abstracts.

### Candidate Evidence Reranking and Risk-Aware Answer Selection (CAPE)

A two-layer framework built on SQL-Retrieval Augmented Generation (SAG) backbone addresses the issue that multi-hop RAG may fail to exploit useful evidence due to ranking and context budgets. The evidence layer includes candidate evidence reranking (CAPE) that combines trajectory information. It also addresses misselection of candidate answers when answer frequency does not align with correction value.

Supporting claims: claim-013, claim-014, claim-015, claim-016

Trade-offs: Adds a two-layer framework for candidate utilization, which may increase computational overhead and complexity. However, it aims to improve evidence utilization and answer selection. Specific trade-off metrics are not available in the abstracts.

### Multi-Modal Corrective RAG (MMCRAG-Resp)

MMCRAG-Resp is a clinically grounded, physiology-aware corrective RAG framework for respiratory intelligence. It addresses the limitation that standard RAG uses only semantic similarity, which can retrieve clinically irrelevant evidence and produce unsafe or hallucinated outputs. The system harmonizes a large dataset (17,516 items, truncated).

Supporting claims: claim-019, claim-020, claim-021, claim-022

Trade-offs: Incorporates multi-modal and physiology-aware components, likely increasing implementation complexity and computational cost. However, it aims to improve clinical relevance and safety. Specific latency/cost trade-offs are not detailed in the available abstracts.

### Query Decomposition and Cross-Encoder Reranking

The approach decomposes complex queries into self-contained sub-questions and employs a Cross-Encoder to rerank candidates at each retrieval step. It addresses the failure of standard single-hop retrieval on complex, multi-hop queries that require synthesizing information from disparate documents.

Supporting claims: claim-030, claim-031

Trade-offs: Query decomposition and cross-encoder reranking add computational overhead and latency due to multiple retrieval steps and reranking. However, they improve effectiveness on multi-hop queries. Specific cost/latency metrics are not provided in the available abstracts.

### Specialized Chunking and Reranking (LawRAG)

LawRAG is a RAG design for Indonesian new law documents that incorporates a specific data chunking method (segmenting by document title, article, and paragraph) and a reranker model. It outperforms sequential chunking in terms of accuracy for question-answering on new law documents.

Supporting claims: claim-026, claim-027, claim-028, claim-029

Trade-offs: Specialized chunking and reranking may require domain-specific preprocessing and additional reranking step, increasing implementation complexity and possibly latency. However, it improves accuracy. Specific trade-off metrics are not available in the abstracts.

### Cost-Aware Adaptive Retrieval (CARE)

CARE is a modular architecture for query-adaptive retrieval that addresses the challenge of choosing the most suitable retrieval strategy. It recognizes that lexical and dense retrievers are efficient and inexpensive, while reasoning-based retrievers improve effectiveness on complex questions at substantially higher computational cost.

Supporting claims: claim-034, claim-035, claim-036

Trade-offs: CARE explicitly balances performance and cost by adaptively selecting retrieval strategies. It may introduce routing overhead but aims to optimize cost-effectiveness. Specific latency/cost savings are not quantified in the available abstracts.

### Low-Latency Deployment with Dense Retrieval, BM25 Fusion, DistilBERT Reranking, and T5-small Generation

An optimized domain-specific QA framework combines normalized Dense Retrieval and BM25 fusion, DistilBERT-based candidate re-ranking, and evidence-constrained T5-small generation within a RAG pipeline. It targets challenges in retrieval accuracy, answer faithfulness, latency control, and scalable service readiness for vertical domains.

Supporting claims: claim-037, claim-038, claim-039

Trade-offs: Uses lightweight models (DistilBERT, T5-small) to reduce latency and cost, but may sacrifice some performance compared to larger models. The fusion of dense and lexical retrieval adds complexity but aims to improve accuracy. Specific latency/cost metrics are not provided in the abstracts.

### Self-Correcting Iterative Mechanism (SCIM)

SCIM is a framework featuring multi-dimensional evaluation and adaptive retrieval that addresses the one-shot limitation of standard RAG. It operates on a lightweight Flan-T5-base model (250M parameters) without fine-tuning, challenging the reliance on 7B+ parameter models. Experimental results across four benchmarks show a 17.2% improvement over sta (truncated).

Supporting claims: claim-040, claim-041, claim-042, claim-043

Trade-offs: Uses a lightweight model and no fine-tuning, reducing cost and complexity. However, iterative self-correction may add latency due to multiple evaluation and retrieval cycles. The 17.2% improvement suggests effectiveness, but specific latency/cost trade-offs are not detailed in the available abstracts.

### Faithfulness-Aware Multi-Objective Context Ranking

A multi-objective ranking framework explicitly models relevance, coverage, and faithfulness support. It introduces a utility-based scoring mechanism that evaluates (truncated). It addresses the limitation that existing ranking methods optimize only document-query relevance, neglecting factual consistency and information coverage.

Supporting claims: claim-044, claim-045, claim-046, claim-047

Trade-offs: Multi-objective ranking may increase computational complexity and latency due to evaluating multiple dimensions. However, it aims to improve generation quality and faithfulness. Specific trade-off metrics are not available in the abstracts.

## Agent hypotheses (not paper conclusions)

- **hyp-001**: Corrective retrieval mechanisms (e.g., CRAG, MMCRAG-Resp) improve answer faithfulness and reduce hallucination primarily when the initial retrieval returns irrelevant or low-quality documents, but they introduce additional latency and computational cost due to the evaluation and correction steps.
  - Derived from: claim-001, claim-002, claim-003, claim-004, claim-019, claim-020, claim-021
  - Falsification test: Conduct experiments comparing CRAG/MMCRAG-Resp against standard RAG on datasets with controlled retrieval quality (e.g., varying relevance of retrieved documents). Measure faithfulness, hallucination rate, latency, and cost. If corrective mechanisms do not improve faithfulness when retrieval is poor, or if latency/cost increases without proportional benefit, the hypothesis is falsified.
  - Confidence: 0.5
- **hyp-002**: Self-reflective retrieval (e.g., Self-RAG, SCIM) improves faithfulness and answer quality by iteratively evaluating and refining retrieval and generation, but this iterative process increases latency and implementation complexity, especially when multiple reflection cycles are required.
  - Derived from: claim-005, claim-006, claim-007, claim-040, claim-041, claim-042, claim-043
  - Falsification test: Compare Self-RAG/SCIM against standard RAG on benchmarks measuring faithfulness, latency, and complexity (e.g., number of model calls). If self-reflective methods do not improve faithfulness or if latency/complexity increases without commensurate gains, the hypothesis is falsified.
  - Confidence: 0.5
- **hyp-003**: Advanced reranking techniques (e.g., GRPO++, CAPE, cross-encoder reranking, faithfulness-aware ranking) improve retrieval quality and answer faithfulness by better selecting and ordering evidence, but they add computational overhead and may require training or fine-tuning, increasing cost and implementation complexity.
  - Derived from: claim-009, claim-010, claim-011, claim-012, claim-013, claim-014, claim-015, claim-016, claim-030, claim-031, claim-044, claim-045, claim-046, claim-047
  - Falsification test: Evaluate these reranking methods against simpler baselines (e.g., BM25, dense retrieval without reranking) on retrieval and generation metrics, while measuring latency and cost. If reranking does not improve faithfulness or if overhead outweighs benefits, the hypothesis is falsified.
  - Confidence: 0.5
- **hyp-004**: Query rewriting and decomposition (e.g., decomposing complex queries into sub-questions) improve retrieval and answer quality for multi-hop queries, but they increase latency and cost due to multiple retrieval and generation steps, and may introduce error propagation if sub-questions are poorly formed.
  - Derived from: claim-030, claim-031
  - Falsification test: Compare query decomposition against single-hop retrieval on multi-hop QA benchmarks, measuring accuracy, latency, and cost. If decomposition does not improve accuracy or if latency/cost increases without benefit, or if error propagation significantly degrades performance, the hypothesis is falsified.
  - Confidence: 0.5
- **hyp-005**: Cost-aware adaptive retrieval (e.g., CARE) can reduce latency and cost while maintaining or improving answer quality by dynamically selecting retrieval strategies based on query complexity, but it requires a routing mechanism that adds implementation complexity and may misroute queries, leading to suboptimal performance.
  - Derived from: claim-034, claim-035, claim-036
  - Falsification test: Implement CARE and compare against always using a single retriever (cheap or expensive) on a mixed-complexity query set. Measure quality, latency, and cost. If CARE does not achieve a better trade-off or if misrouting causes significant quality drops, the hypothesis is falsified.
  - Confidence: 0.5
- **hyp-006**: Domain-specific adaptations (e.g., specialized chunking, multi-modal inputs, physiology-aware components) improve retrieval accuracy and answer faithfulness in vertical domains, but they increase implementation complexity and may require domain expertise, limiting generalizability and increasing development cost.
  - Derived from: claim-019, claim-020, claim-021, claim-022, claim-026, claim-027, claim-028, claim-029, claim-037, claim-038, claim-039
  - Falsification test: Apply domain-specific adaptations to out-of-domain datasets and compare against general-purpose RAG. If domain-specific methods do not outperform general methods in-domain, or if they fail to generalize and require excessive customization, the hypothesis is falsified.
  - Confidence: 0.5

## Representative failures

- `rate_limit`: semantic_scholar returned HTTP 429
- `rate_limit`: semantic_scholar returned HTTP 429
- `rate_limit`: semantic_scholar returned HTTP 429
- `rate_limit`: semantic_scholar returned HTTP 429
- `rate_limit`: semantic_scholar returned HTTP 429
- `rate_limit`: semantic_scholar returned HTTP 429
- `rate_limit`: semantic_scholar returned HTTP 429
- `rate_limit`: semantic_scholar returned HTTP 429

## Limitations

- Extraction uses bounded public abstract excerpts; claims are not full-text findings unless explicitly marked.
- Search API ranking and metadata can change after the recorded retrieval timestamp.
- Calculated API cost uses provider-reported usage and published rates; it is not an invoice.

## Usage and calculated cost

Provider-reported usage: `{'input_tokens': 15975, 'output_tokens': 15764, 'cached_input_tokens': 0, 'total_tokens': 31739, 'requests': 5}`. Calculated cost: `$0.02370930`. This is a calculation from published rates, not an invoice.
