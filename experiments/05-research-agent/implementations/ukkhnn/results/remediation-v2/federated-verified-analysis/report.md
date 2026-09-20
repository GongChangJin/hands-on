# Verified RAG research report

- Condition: `federated-verified`
- Question: RAG 시스템에서 query rewriting, reranking, corrective retrieval, self-reflective retrieval 기법은 검색 품질과 답변의 faithfulness를 어떤 조건에서 개선하며, latency·비용·구현 복잡도 측면에서 어떤 trade-off를 만드는가?
- Search started: 2026-09-20T07:45:31.229866+00:00
- Verified papers: 18
- Evidence claims: 53
- Model status: `executed`

## Search and verification

Sources: semantic_scholar, crossref, arxiv. Requests: {'arxiv': 9, 'crossref': 11, 'semantic_scholar': 37}. Deduplicated: 82. Identifier failures: 1.

## Claim–evidence

| Claim ID | Paper | Claim | Locator |
| --- | --- | --- | --- |
| claim-001 | A Self-Reflective Retrieval Augmented Generation System to Eliminate Hallucination in LLM Generation | In a Retrieval Augmented Generation system, the possibility of hallucination is ever prevalent, as it has been increasingly common for an AI model to produce inaccurate generations given an input, which can become increasingly more devastating for a RAG system due to its node-like generation. | abstract excerpt |
| claim-002 | A Self-Reflective Retrieval Augmented Generation System to Eliminate Hallucination in LLM Generation | To solve this problem, we introduced a series of selfreflective nodes, creating a self-RAG model. | abstract excerpt |
| claim-003 | A Self-Reflective Retrieval Augmented Generation System to Eliminate Hallucination in LLM Generation | To create our program, we established a series of nodes that utilized ChatGPT for generation as well as the Langchain python library and its workflow functions to piece together the nodes. | abstract excerpt |
| claim-004 | GRPO++: A Controlled Differentiable Reinforcement Learning Reranking Method for Retrieval-Augmented Generation | The performance of retrieval-augmented generation (RAG) systems heavily depends on the quality of the re-ranking module, yet existing methods face challenges such as training instability, unreasonable reward design, and insufficient confidence calibration. | abstract excerpt |
| claim-005 | GRPO++: A Controlled Differentiable Reinforcement Learning Reranking Method for Retrieval-Augmented Generation | This paper proposes GRPO++, an end-to-end re-ranking framework based on reinforcement learning, which collaboratively optimizes five core modules: Soft Normalized Discounted Cumulative Gain (Soft-nDCG) to achieve a differentiable ranking objective; Critical Reweighting for Importance (CRI) to enhance Top-K position optimization; Evi | abstract excerpt |
| claim-006 | Candidate Evidence Reranking and Risk-Aware Answer Selection in Multi-Hop Retrieval-Augmented Generation | Multi-hop retrieval-augmented generation (RAG) can fail to fully exploit useful evidence even after it has entered the candidate pool, because ranking and limited context budgets determine which documents are actually exposed to the reader. | abstract excerpt |
| claim-007 | Candidate Evidence Reranking and Risk-Aware Answer Selection in Multi-Hop Retrieval-Augmented Generation | Candidate answers produced by multiple retrieval trajectories can likewise be misselected when answer frequency does not align with correction value. | abstract excerpt |
| claim-008 | Candidate Evidence Reranking and Risk-Aware Answer Selection in Multi-Hop Retrieval-Augmented Generation | Building on the SQL-Retrieval Augmented Generation (SAG) backbone, we develop a two-layer framework for candidate utilization. At the evidence layer, candidate evidence reranking (CAPE) combines traje | abstract excerpt |
| claim-009 | Self-Reflective Retrieval-Augmented Generation (Self-RAG) in Analytical Systems | This research explores the application of Self-Reflective Retrieval-Au’gmented Generation (Self-RAG) within analytical systems, specifically focusing on data distribution systems. | abstract excerpt |
| claim-010 | Self-Reflective Retrieval-Augmented Generation (Self-RAG) in Analytical Systems | While traditional analytical systems often struggle with efficiently querying and interpreting vast datasets, Self-RAG presents a promising solution. | abstract excerpt |
| claim-011 | Self-Reflective Retrieval-Augmented Generation (Self-RAG) in Analytical Systems | It then presents the findings of research conducted on how Self-RAG can enhance data analysis in distributed systems by improving information retrieval accuracy, generat | abstract excerpt |
| claim-012 | MMCRAG-Resp: a multi-modal corrective retrieval-augmented generation framework for explainable respiratory disease reasoning | Standard Retrieval-Augmented Generation (RAG) systems only use semantic similarity to retrieve information, and since this method is quite limiting, it may find clinically irrelevant evidence and produce outputs that are unsafe or hallucinated. | abstract excerpt |
| claim-013 | MMCRAG-Resp: a multi-modal corrective retrieval-augmented generation framework for explainable respiratory disease reasoning | This drawback is particularly important in respiratory care, where the diagnosis relies heavily on very accurate physiological indicators such as spirometry patterns and symptom profiles. | abstract excerpt |
| claim-014 | MMCRAG-Resp: a multi-modal corrective retrieval-augmented generation framework for explainable respiratory disease reasoning | We propose MMCRAG-Resp., a clinically grounded, physiology-aware corrective RAG framework for respiratory intelligence. The system harmonizes 17,516 | abstract excerpt |
| claim-015 | Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection | LLMs often produce responses containing factual inaccuracies due to their sole reliance on parametric knowledge. | abstract excerpt |
| claim-016 | Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection | Retrieval-Augmented Generation decreases such issues. | abstract excerpt |
| claim-017 | Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection | Indiscriminately retrieving and incorporating a fixed number of retrieved passages, regardless of whether retrieval is necessary or passages are relevant, diminishes LM versatility or can lead to unhelpful response generation. | abstract excerpt |
| claim-018 | Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection | We introduce a new framework c | abstract excerpt |
| claim-019 | A Unified Evaluation Framework for Grounded LLM Architectures: Comparative Analysis of RAG, Self-RAG, and Agentic RAG | Retrieval-Augmented Generation (RAG) grounds large language models with external knowledge, while two recent variants—Self-RAG (self-reflective retrieval refinement) and Agentic RAG (multi-step reasoning and tool orchestration)—aim to boost factuality, reasoning depth, and adaptability. | abstract excerpt |
| claim-020 | A Unified Evaluation Framework for Grounded LLM Architectures: Comparative Analysis of RAG, Self-RAG, and Agentic RAG | We present a unified evaluation framework that, for the first time, compares these three paradigms under matched conditions: the same base model, the same hybrid retriever, and identical domain constraints. | abstract excerpt |
| claim-021 | A Unified Evaluation Framework for Grounded LLM Architectures: Comparative Analysis of RAG, Self-RAG, and Agentic RAG | Our multi-task benchmark spans factual recall, multi-hop reasoning, and domain-specific Q&A in insurance, | abstract excerpt |
| claim-022 | LawRAG: Indonesian legal document retrieval-augmented generation with specialized chunking and reranking strategies | Enhancing Question-Answering accuracy on new law documents by using Retrieval-Augmented Generation (RAG)-Large Language Models . | abstract excerpt |
| claim-023 | LawRAG: Indonesian legal document retrieval-augmented generation with specialized chunking and reranking strategies | The proposed method is built on a RAG design for Indonesian new law documents, incorporating a specific data chunking method and a reranker model. | abstract excerpt |
| claim-024 | LawRAG: Indonesian legal document retrieval-augmented generation with specialized chunking and reranking strategies | The proposed method, which segments legal data by focusing on the document title, article, and paragraph, outperforms the sequential chunking method in terms of accuracy. | abstract excerpt |
| claim-025 | LawRAG: Indonesian legal document retrieval-augmented generation with specialized chunking and reranking strategies | This research demonstrates that the completeness of a sentence in the data set used during | abstract excerpt |
| claim-026 | Understanding Retrieval Pitfalls: Challenges Faced by Retrieval Augmented Generation (RAG) models | Large language models (LLMs) like GPT-4, the engine of products like ChatGPT, have taken centre stage in recent years due to their astonishing capabilities. | abstract excerpt |
| claim-027 | Understanding Retrieval Pitfalls: Challenges Faced by Retrieval Augmented Generation (RAG) models | Yet, they are far from perfect. | abstract excerpt |
| claim-028 | Understanding Retrieval Pitfalls: Challenges Faced by Retrieval Augmented Generation (RAG) models | Many of us have since learnt — perhaps when asking ChatGPT a question or employing it to write our reports — that LLMs can hallucinate. | abstract excerpt |
| claim-029 | The Impact of Query Decomposition and Cross-Encoder Reranking in Multi-Hop Retrieval-Augmented Generation | Retrieval-Augmented Generation (RAG) has emerged as a promising paradigm for open-domain question answering. | abstract excerpt |
| claim-030 | The Impact of Query Decomposition and Cross-Encoder Reranking in Multi-Hop Retrieval-Augmented Generation | However, standard single-hop retrieval often fails on complex, multi-hop queries where the answer requires synthesizing information from disparate documents. | abstract excerpt |
| claim-031 | The Impact of Query Decomposition and Cross-Encoder Reranking in Multi-Hop Retrieval-Augmented Generation | In this work, we propose an enhanced Multi-Hop RAG pipeline augmented with Cross-Encoder Reranking to address the challenges of reasoning across multiple documents. | abstract excerpt |
| claim-032 | The Impact of Query Decomposition and Cross-Encoder Reranking in Multi-Hop Retrieval-Augmented Generation | Our approach decomposes complex queries into self-contained sub-questions and employs a Cross-Encoder to rerank candidates at each retrieval step, mitigating the "seman | abstract excerpt |
| claim-033 | GHP: Hardening Graph‐Based Reranking Defense for Poisoned Retrieval‐Augmented Generation | Graph-based reranking defense remains vulnerable when poisoned passages form small structures. | abstract excerpt |
| claim-034 | GHP: Hardening Graph‐Based Reranking Defense for Poisoned Retrieval‐Augmented Generation | Under poisoned retrieval, adversarial passages may survive ranking and enter the final prompt, creating a reliability risk even when the generator itself is unchanged. | abstract excerpt |
| claim-035 | RETRIEVAL AUGMENTED GENERATION SYSTEM FOR EDUCATIONAL TEXTBOOK QUERY ASSISTANCE | The system employs a combination of natural language processing techniques to facilitate textbook query assistance. | abstract excerpt |
| claim-036 | RETRIEVAL AUGMENTED GENERATION SYSTEM FOR EDUCATIONAL TEXTBOOK QUERY ASSISTANCE | The system disassembles and categorizes textbook contents, converts them into a searchable format, and uses a language model to generate responses. | abstract excerpt |
| claim-037 | Performance VS Cost: A Modular Architecture for Cost-Aware Adaptive Retrieval in Retrieval-Augmented Generation Systems | Choosing the most suitable retrieval strategy is no simple task. | abstract excerpt |
| claim-038 | Performance VS Cost: A Modular Architecture for Cost-Aware Adaptive Retrieval in Retrieval-Augmented Generation Systems | Lexical and dense retrievers are efficient and inexpensive, while reasoning-based retrievers can improve effectiveness on complex questions at substantially higher computational cost. | abstract excerpt |
| claim-039 | Performance VS Cost: A Modular Architecture for Cost-Aware Adaptive Retrieval in Retrieval-Augmented Generation Systems | CARE is a modular architecture for query-adaptive and cost-aware retrieval. | abstract excerpt |
| claim-040 | ReflectiveRAG: Rethinking Adaptivity in Retrieval-Augmented Generation | RAG systems degrade sharply under extreme noise, where irrelevant or redundant passages dominate. | abstract excerpt |
| claim-041 | ReflectiveRAG: Rethinking Adaptivity in Retrieval-Augmented Generation | Current methods depend on static heuristics or costly reinforcement learning, failing to assess evidence sufficiency, detect subtle mismatches, or reduce redundancy, leading to hallucinations and poor grounding. | abstract excerpt |
| claim-042 | ReflectiveRAG: Rethinking Adaptivity in Retrieval-Augmented Generation | ReflectiveRAG is a lightweight yet reasoning-driven architecture that enhances factual grounding through two complementary mechanisms: Self-Reflective Retrieval (SRR) and another mechanism. | abstract excerpt |
| claim-043 | MARA: A Multimodal Adaptive Retrieval-Augmented Framework for Document Question Answering | Retrieval-based multimodal document QA aims to identify and integrate relevant information from visually rich documents with complex multimodal structures. | abstract excerpt |
| claim-044 | MARA: A Multimodal Adaptive Retrieval-Augmented Framework for Document Question Answering | Current approaches rely on query-agnostic document representations that overlook salient content and use static top-k evidence selection, which fails to adapt to the uncertain distribution of relevant information. | abstract excerpt |
| claim-045 | MARA: A Multimodal Adaptive Retrieval-Augmented Framework for Document Question Answering | MARA is a multimodal adaptive retrieval-augmented framework for document question answering. | abstract excerpt |
| claim-046 | Retrieval-Augmented Generation with Low-Latency Deployment for Vertical Domains Question Answering: A Case Study on Economic Resource Platforms | The paper presents an optimized domain-specific question-answering framework that combines normalized Dense Retrieval and BM25 fusion, DistilBERT-based candidate re-ranking, and evidence-constrained T5-small generation within a retrieval-augmented generation pipeline. | abstract excerpt |
| claim-047 | Retrieval-Augmented Generation with Low-Latency Deployment for Vertical Domains Question Answering: A Case Study on Economic Resource Platforms | Deployment of generative chatbots in vertical domains such as policy documents and economic resource platforms faces challenges in retrieval accuracy, answer faithfulness, latency control, and scalable service readiness. | abstract excerpt |
| claim-048 | SCIM: Self-Correcting Iterative Mechanism for Retrieval-Augmented Generation | Standard Retrieval-Augmented Generation (RAG) models are limited by their “one-shot” nature, failing to assess or improve answer quality dynamically. | abstract excerpt |
| claim-049 | SCIM: Self-Correcting Iterative Mechanism for Retrieval-Augmented Generation | SCIM operates on a lightweight Flan-T5-base model (250M parameters) and requires no fine-tuning, challenging the industry’s reliance on 7B+ parameter models. | abstract excerpt |
| claim-050 | SCIM: Self-Correcting Iterative Mechanism for Retrieval-Augmented Generation | Experimental results across four major benchmarks show that SCIM yields a 17.2% improvement over sta[ndard baselines]. | abstract excerpt |
| claim-051 | Faithfulness-Aware Multi-Objective Context Ranking for Retrieval-Augmented Generation | Existing ranking methods in RAG pipelines primarily optimize for document-query relevance, neglecting crucial factors for generation quality such as factual consistency and information coverage. | abstract excerpt |
| claim-052 | Faithfulness-Aware Multi-Objective Context Ranking for Retrieval-Augmented Generation | The paper proposes a novel multi-objective ranking framework that explicitly models three critical dimensions: relevance, coverage, and faithfulness support. | abstract excerpt |
| claim-053 | Faithfulness-Aware Multi-Objective Context Ranking for Retrieval-Augmented Generation | The method introduces a utility-based scoring mechanism that evaluates [the three dimensions]. | abstract excerpt |

## Method, results, limitations, and trade-offs

### query_rewriting

['Standard single-hop retrieval often fails on complex multi-hop queries requiring synthesis across disparate documents; decomposing complex queries into self-contained sub-questions is proposed to address this.', "An enhanced Multi-Hop RAG pipeline augmented with Cross-Encoder Reranking decomposes complex queries into self-contained sub-questions and reranks candidates at each retrieval step, mitigating a 'semantic' issue (truncated)."]

Supporting claims: claim-030, claim-031, claim-032

Trade-offs: ['Query decomposition adds latency and computational cost due to multiple retrieval steps and sub-question processing.', 'Implementation complexity increases with the need for a decomposition module and integration with reranking at each step.']

### reranking

['RAG performance heavily depends on re-ranking quality, but existing methods face training instability, unreasonable reward design, and insufficient confidence calibration.', 'GRPO++ is an end-to-end reinforcement learning re-ranking framework that collaboratively optimizes five core modules, including Soft-nDCG for differentiable ranking and CRI for Top-K position optimization.', 'In multi-hop RAG, useful evidence may not be fully exploited after entering the candidate pool due to ranking and context budget constraints; candidate evidence reranking (CAPE) is part of a two-layer framework to improve candidate utilization.', 'Candidate answers from multiple retrieval trajectories can be misselected when answer frequency does not align with correction value.', 'Graph-based reranking defenses remain vulnerable when poisoned passages form small structures; under poisoned retrieval, adversarial passages may survive ranking and enter the final prompt, creating a reliability risk even when the generator is unchanged.', 'Existing ranking methods primarily optimize document-query relevance, neglecting factual consistency and information coverage; a multi-objective ranking framework models relevance, coverage, and faithfulness support using a utility-based scoring mechanism.', 'A domain-specific QA framework combines normalized Dense Retrieval and BM25 fusion with DistilBERT-based candidate re-ranking and evidence-constrained T5-small generation.', 'LawRAG incorporates a specific data chunking method and a reranker model; segmenting legal data by document title, article, and paragraph outperforms sequential chunking in accuracy.', 'Current methods like fixed top-k retrieval, cross-encoder reranking, or policy-based iteration depend on static heuristics or costly reinforcement learning, failing to assess evidence sufficiency, detect subtle mismatches, or reduce redundancy, leading to hallucinations and poor grounding.']

Supporting claims: claim-004, claim-005, claim-006, claim-007, claim-008, claim-033, claim-034, claim-051, claim-052, claim-053, claim-046, claim-023, claim-024, claim-041

Trade-offs: ['Reranking improves retrieval quality but adds latency and computational cost, especially with complex models like cross-encoders or reinforcement learning-based rerankers.', 'Training instability and reward design challenges in RL-based reranking increase implementation complexity.', 'Multi-objective ranking may require additional computation for evaluating multiple dimensions.', 'Graph-based reranking defenses may be vulnerable to adversarial attacks, requiring additional hardening.']

### corrective_retrieval

['Standard RAG systems rely solely on semantic similarity, which is limiting and can lead to clinically irrelevant evidence and unsafe or hallucinated outputs; this is particularly critical in respiratory care where diagnosis depends on accurate physiological indicators.', 'MMCRAG-Resp is a clinically grounded, physiology-aware corrective RAG framework for respiratory intelligence that harmonizes 17,516 [truncated].', "SCIM is a self-correcting iterative mechanism for RAG that operates on a lightweight Flan-T5-base model (250M parameters) without fine-tuning, challenging the industry's reliance on 7B+ parameter models; it yields a 17.2% improvement over standard baselines on four major benchmarks.", "Standard RAG models are limited by their 'one-shot' nature, failing to assess or improve answer quality dynamically."]

Supporting claims: claim-012, claim-013, claim-014, claim-048, claim-049, claim-050

Trade-offs: ['Corrective retrieval can improve accuracy and safety but may introduce additional latency due to iterative correction steps.', 'Implementation complexity increases with the need for correction mechanisms and domain-specific adaptations.', 'Lightweight models like Flan-T5-base reduce computational cost but may have lower capacity than larger models.']

### self_reflective_retrieval

['Hallucination is a common and potentially severe issue in RAG systems because of their node-like generation process; self-reflective nodes were introduced to create a self-RAG model aimed at solving hallucination.', 'The self-RAG program was built using nodes that employed ChatGPT for generation and the Langchain Python library with its workflow functions to connect the nodes.', 'Self-RAG is explored in analytical systems, specifically data distribution systems, where traditional systems struggle with efficiently querying and interpreting vast datasets; findings suggest Self-RAG can enhance data analysis by improving information retrieval accuracy and generation [truncated].', 'LLMs often produce factual inaccuracies due to sole reliance on parametric knowledge; RAG decreases such issues, but indiscriminately retrieving a fixed number of passages diminishes LM versatility or leads to unhelpful responses.', 'Self-RAG (self-reflective retrieval refinement) and Agentic RAG (multi-step reasoning and tool orchestration) aim to boost factuality, reasoning depth, and adaptability; a unified evaluation framework compares these paradigms under matched conditions.', 'ReflectiveRAG is a lightweight reasoning-driven architecture that enhances factual grounding through two mechanisms: Self-Reflective Retrieval (SRR) and another mechanism [truncated].', 'RAG systems degrade sharply under extreme noise; current methods depend on static heuristics or costly reinforcement learning, failing to assess evidence sufficiency, detect subtle mismatches, or reduce redundancy, leading to hallucinations and poor grounding.']

Supporting claims: claim-001, claim-002, claim-003, claim-009, claim-010, claim-011, claim-015, claim-016, claim-017, claim-018, claim-019, claim-020, claim-021, claim-040, claim-041, claim-042

Trade-offs: ['Self-reflective retrieval can improve faithfulness and reduce hallucinations but adds latency due to iterative reflection steps.', 'Implementation complexity increases with the need for reflection mechanisms and integration with generation.', 'Cost may increase due to multiple LLM calls for reflection and generation.']

## Agent hypotheses (not paper conclusions)

- **hyp-001**: Query rewriting via decomposition into sub-questions improves retrieval quality for multi-hop queries but increases latency proportionally to the number of sub-questions.
  - Derived from: claim-030, claim-031, claim-032
  - Falsification test: Measure retrieval accuracy and latency for multi-hop queries with and without decomposition; if latency does not increase significantly or accuracy does not improve, hypothesis is falsified.
  - Confidence: 0.5
- **hyp-002**: Reinforcement learning-based reranking (e.g., GRPO++) improves ranking quality but introduces training instability and high implementation complexity, making it less suitable for low-resource settings.
  - Derived from: claim-004, claim-005
  - Falsification test: Compare training stability and resource requirements of RL-based reranking versus simpler rerankers; if RL-based reranking is stable and low-cost, hypothesis is falsified.
  - Confidence: 0.5
- **hyp-003**: Corrective retrieval frameworks like MMCRAG-Resp improve answer safety and relevance in domain-specific applications (e.g., respiratory care) but require domain-specific knowledge integration, increasing implementation complexity.
  - Derived from: claim-012, claim-013, claim-014
  - Falsification test: Evaluate MMCRAG-Resp in respiratory care versus standard RAG; if no significant improvement in safety/relevance or if implementation is straightforward, hypothesis is falsified.
  - Confidence: 0.5
- **hyp-004**: Self-reflective retrieval (e.g., Self-RAG) reduces hallucination and improves faithfulness but increases latency and cost due to iterative reflection and generation steps.
  - Derived from: claim-001, claim-002, claim-015, claim-016, claim-017, claim-018, claim-040, claim-041, claim-042
  - Falsification test: Measure hallucination rate, faithfulness, latency, and cost for Self-RAG versus standard RAG; if no trade-off exists (e.g., latency unchanged), hypothesis is falsified.
  - Confidence: 0.5
- **hyp-005**: Lightweight self-correcting mechanisms (e.g., SCIM with Flan-T5-base) can achieve significant improvements over standard RAG without fine-tuning, offering a favorable trade-off between performance and cost.
  - Derived from: claim-048, claim-049, claim-050
  - Falsification test: Reproduce SCIM on benchmarks and compare to standard RAG; if improvement is not significant or cost is high, hypothesis is falsified.
  - Confidence: 0.5

## Representative failures

- `rate_limit`: semantic_scholar returned HTTP 429
- `rate_limit`: semantic_scholar returned HTTP 429
- `rate_limit`: semantic_scholar returned HTTP 429
- `rate_limit`: semantic_scholar returned HTTP 429
- `rate_limit`: semantic_scholar returned HTTP 429
- `rate_limit`: semantic_scholar returned HTTP 429
- `rate_limit`: semantic_scholar returned HTTP 429
- `http_error`: arxiv returned HTTP 406
- `http_error`: arxiv returned HTTP 406
- `http_error`: arxiv returned HTTP 406
- `http_error`: arxiv returned HTTP 406
- `http_error`: arxiv returned HTTP 406

## Limitations

- Extraction uses bounded public abstract excerpts; claims are not full-text findings unless explicitly marked.
- Search API ranking and metadata can change after the recorded retrieval timestamp.
- Calculated API cost uses provider-reported usage and published rates; it is not an invoice.

## Usage and calculated cost

Provider-reported usage: `{'input_tokens': 18843, 'output_tokens': 12868, 'cached_input_tokens': 0, 'total_tokens': 31711, 'requests': 5}`. Calculated cost: `$0.01054725`. This is a calculation from published rates, not an invoice.
