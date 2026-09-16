# Verified RAG research report

- Condition: `semantic-scholar-only`
- Question: RAG 시스템에서 query rewriting, reranking, corrective retrieval, self-reflective retrieval 기법은 검색 품질과 답변의 faithfulness를 어떤 조건에서 개선하며, latency·비용·구현 복잡도 측면에서 어떤 trade-off를 만드는가?
- Search started: 2026-09-16T03:56:12.929339+00:00
- Verified papers: 18
- Evidence claims: 75
- Model status: `executed`

## Search and verification

Sources: semantic_scholar. Requests: {'semantic_scholar': 22}. Deduplicated: 0. Identifier failures: 0.

## Claim–evidence

| Claim ID | Paper | Claim | Locator |
| --- | --- | --- | --- |
| claim-001 | A Self-Reflective Retrieval Augmented Generation System to Eliminate Hallucination in LLM Generation | In a Retrieval Augmented Generation system, the possibility of hallucination is ever prevalent. | abstract excerpt |
| claim-002 | A Self-Reflective Retrieval Augmented Generation System to Eliminate Hallucination in LLM Generation | It has been increasingly common for an AI model to produce inaccurate generations given an input. | abstract excerpt |
| claim-003 | A Self-Reflective Retrieval Augmented Generation System to Eliminate Hallucination in LLM Generation | Inaccurate generations can become increasingly more devastating for a RAG system due to its node-like generation. | abstract excerpt |
| claim-004 | A Self-Reflective Retrieval Augmented Generation System to Eliminate Hallucination in LLM Generation | We introduced a series of self-reflective nodes, creating a self-RAG model. | abstract excerpt |
| claim-005 | A Self-Reflective Retrieval Augmented Generation System to Eliminate Hallucination in LLM Generation | We established a series of nodes that utilized ChatGPT for generation as well as the Langchain python library and its workflow functions to piece together the nodes. | abstract excerpt |
| claim-006 | Self-Reflective Retrieval-Augmented Generation (Self-RAG) in Analytical Systems | Traditional analytical systems often struggle with efficiently querying and interpreting vast datasets. | abstract excerpt |
| claim-007 | Self-Reflective Retrieval-Augmented Generation (Self-RAG) in Analytical Systems | Self-RAG presents a promising solution. | abstract excerpt |
| claim-008 | Self-Reflective Retrieval-Augmented Generation (Self-RAG) in Analytical Systems | It examines existing literature on Self-RAG and its application in similar fields. | abstract excerpt |
| claim-009 | Self-Reflective Retrieval-Augmented Generation (Self-RAG) in Analytical Systems | It presents the findings of research conducted on how Self-RAG can enhance data analysis in distributed systems by improving information retrieval accuracy, generat... | abstract excerpt |
| claim-010 | EvaRAG: Evaluating Advanced RAG Techniques With Indexing and Distance Metrics | Retrieval Augmented Generation (RAG) has emerged as a powerful paradigm for enhancing large language models (LLMs) with external knowledge. | abstract excerpt |
| claim-011 | EvaRAG: Evaluating Advanced RAG Techniques With Indexing and Distance Metrics | The performance of RAG pipelines is susceptible to design choices across retrieval, similarity metrics, indexing, and reranking. | abstract excerpt |
| claim-012 | EvaRAG: Evaluating Advanced RAG Techniques With Indexing and Distance Metrics | Despite growing adoption, little systematic work has explored the trade-offs between retrieval quality, semantic accuracy, computational efficiency, and cost in RAG systems. | abstract excerpt |
| claim-013 | EvaRAG: Evaluating Advanced RAG Techniques With Indexing and Distance Metrics | This study addresses this gap by conducting a comprehensive evaluation of RAG configurations across multiple dimensions. | abstract excerpt |
| claim-014 | EvaRAG: Evaluating Advanced RAG Techniques With Indexing and Distance Metrics | We propose a benchmarking frame... | abstract excerpt |
| claim-015 | Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection | Despite their remarkable capabilities, large language models (LLMs) often produce responses containing factual inaccuracies due to their sole reliance on the parametric knowledge they encapsulate. | abstract excerpt |
| claim-016 | Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection | Retrieval-Augmented Generation (RAG), an ad hoc approach that augments LMs with retrieval of relevant knowledge, decreases such issues. | abstract excerpt |
| claim-017 | Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection | Indiscriminately retrieving and incorporating a fixed number of retrieved passages, regardless of whether retrieval is necessary, or passages are relevant, diminishes LM versatility or can lead to unhelpful response generation. | abstract excerpt |
| claim-018 | Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection | We introduce a new framework c... | abstract excerpt |
| claim-019 | MEMERAG: A Multilingual End-to-End Meta-Evaluation Benchmark for Retrieval Augmented Generation | Automatic evaluation of retrieval augmented generation (RAG) systems relies on fine-grained dimensions like faithfulness and relevance, as judged by expert human annotators. | abstract excerpt |
| claim-020 | MEMERAG: A Multilingual End-to-End Meta-Evaluation Benchmark for Retrieval Augmented Generation | Meta-evaluation benchmarks support the development of automatic evaluators that correlate well with human judgement. | abstract excerpt |
| claim-021 | MEMERAG: A Multilingual End-to-End Meta-Evaluation Benchmark for Retrieval Augmented Generation | Existing benchmarks predominantly focus on English or use translated data, which fails to capture cultural nuances. | abstract excerpt |
| claim-022 | MEMERAG: A Multilingual End-to-End Meta-Evaluation Benchmark for Retrieval Augmented Generation | A native approach provides a better representation of the end user experience. | abstract excerpt |
| claim-023 | MEMERAG: A Multilingual End-to-End Meta-Evaluation Benchmark for Retrieval Augmented Generation | In this work, we develop a Multilingual End-to-end Meta-Evaluation RAG benchmark (MEMERAG). | abstract excerpt |
| claim-024 | A Unified Evaluation Framework for Grounded LLM Architectures: Comparative Analysis of RAG, Self-RAG, and Agentic RAG | RAG grounds large language models with external knowledge. | abstract excerpt |
| claim-025 | A Unified Evaluation Framework for Grounded LLM Architectures: Comparative Analysis of RAG, Self-RAG, and Agentic RAG | Self-RAG is a self-reflective retrieval refinement variant. | abstract excerpt |
| claim-026 | A Unified Evaluation Framework for Grounded LLM Architectures: Comparative Analysis of RAG, Self-RAG, and Agentic RAG | Agentic RAG is a multi-step reasoning and tool orchestration variant. | abstract excerpt |
| claim-027 | A Unified Evaluation Framework for Grounded LLM Architectures: Comparative Analysis of RAG, Self-RAG, and Agentic RAG | Self-RAG and Agentic RAG aim to boost factuality, reasoning depth, and adaptability. | abstract excerpt |
| claim-028 | A Unified Evaluation Framework for Grounded LLM Architectures: Comparative Analysis of RAG, Self-RAG, and Agentic RAG | The unified evaluation framework compares the three paradigms under matched conditions for the first time. | abstract excerpt |
| claim-029 | A Unified Evaluation Framework for Grounded LLM Architectures: Comparative Analysis of RAG, Self-RAG, and Agentic RAG | Matched conditions include the same base model, the same hybrid retriever, and identical domain constraints. | abstract excerpt |
| claim-030 | A Unified Evaluation Framework for Grounded LLM Architectures: Comparative Analysis of RAG, Self-RAG, and Agentic RAG | The multi-task benchmark spans factual recall, multi-hop reasoning, and domain-specific Q&A in insurance. | abstract excerpt |
| claim-031 | DynamicRAG: Leveraging Outputs of Large Language Model as Feedback for Dynamic Reranking in Retrieval-Augmented Generation | RAG systems combine large language models with external knowledge retrieval, making them highly effective for knowledge-intensive tasks. | abstract excerpt |
| claim-032 | DynamicRAG: Leveraging Outputs of Large Language Model as Feedback for Dynamic Reranking in Retrieval-Augmented Generation | The reranker is a crucial but often under-explored component of RAG systems. | abstract excerpt |
| claim-033 | DynamicRAG: Leveraging Outputs of Large Language Model as Feedback for Dynamic Reranking in Retrieval-Augmented Generation | Irrelevant documents in RAG systems can mislead the generator. | abstract excerpt |
| claim-034 | DynamicRAG: Leveraging Outputs of Large Language Model as Feedback for Dynamic Reranking in Retrieval-Augmented Generation | The reranker plays a vital role in refining retrieved documents to enhance generation quality and explainability. | abstract excerpt |
| claim-035 | DynamicRAG: Leveraging Outputs of Large Language Model as Feedback for Dynamic Reranking in Retrieval-Augmented Generation | It is challenging to determine the appropriate number of documents (k) that the reranker should select. | abstract excerpt |
| claim-036 | DynamicRAG: Leveraging Outputs of Large Language Model as Feedback for Dynamic Reranking in Retrieval-Augmented Generation | Too few selected documents may result in missing critical information. | abstract excerpt |
| claim-037 | Evaluating retriever reranker pairings in RAG based on quality and efficiency trade-offs | Large language models are the core of many Artificial Intelligence systems. | abstract excerpt |
| claim-038 | Evaluating retriever reranker pairings in RAG based on quality and efficiency trade-offs | One of the key problems with these systems is hallucination (i.e., making up facts). | abstract excerpt |
| claim-039 | Evaluating retriever reranker pairings in RAG based on quality and efficiency trade-offs | RAG solves this problem by grounding responses in external knowledge sources, thereby improving the factual accuracy of the response. | abstract excerpt |
| claim-040 | Evaluating retriever reranker pairings in RAG based on quality and efficiency trade-offs | The RAG system consists of two core components: the information retrieval component (retriever and rerankers) and the text generation component (LLM). | abstract excerpt |
| claim-041 | Evaluating retriever reranker pairings in RAG based on quality and efficiency trade-offs | The efficacy of a RAG system depends on the retrieval strategies, reranking mechanisms, and generation mod | abstract excerpt |
| claim-042 | An Empirical Evaluation of Open-Source LLMs for Philippine Labor Law Question Answering Using Retrieval-Augmented Generation | This study evaluates the effectiveness of open-source large language models for answering questions about the Philippine Labor Code using a Retrieval-Augmented Generation framework. | abstract excerpt |
| claim-043 | An Empirical Evaluation of Open-Source LLMs for Philippine Labor Law Question Answering Using Retrieval-Augmented Generation | Three instruction-tuned models—LLaMA 3.1 8B, Qwen2.5 7B, and Gemma 2 9B—were deployed within an identical hybrid retrieval pipeline combining BM25, dense embeddings, reciprocal rank fusion, and cross-encoder reranking. | abstract excerpt |
| claim-044 | An Empirical Evaluation of Open-Source LLMs for Philippine Labor Law Question Answering Using Retrieval-Augmented Generation | Evaluation was conducted on 30 benchmark queries (27 in-scope and 3 out-of-scope) using metrics including semantic similarity, faithfulness, answer relevancy, citation accuracy, LLM-as-a-... | abstract excerpt |
| claim-045 | Optimizing Retrieval-Augmented Generation: Analysis of Hyperparameter Impact on Performance and Efficiency | Large language models achieve high task performance yet often hallucinate or rely on outdated knowledge. | abstract excerpt |
| claim-046 | Optimizing Retrieval-Augmented Generation: Analysis of Hyperparameter Impact on Performance and Efficiency | Retrieval-augmented generation (RAG) addresses these gaps by coupling generation with external search. | abstract excerpt |
| claim-047 | Optimizing Retrieval-Augmented Generation: Analysis of Hyperparameter Impact on Performance and Efficiency | We analyse how hyperparameters influence speed and quality in RAG systems, covering Chroma and Faiss vector stores, chunking policies, cross-encoder re-ranking, and temperature. | abstract excerpt |
| claim-048 | Optimizing Retrieval-Augmented Generation: Analysis of Hyperparameter Impact on Performance and Efficiency | We evaluate six metrics: faithfulness, answer correctness, answer relevancy, context precision, context recall, and answer similarity. | abstract excerpt |
| claim-049 | Optimizing Retrieval-Augmented Generation: Analysis of Hyperparameter Impact on Performance and Efficiency | Chroma processes queries 13% faster, whereas Faiss yields higher retrieval ... | abstract excerpt |
| claim-050 | eSapiens: A Real-World NLP Framework for Multimodal Document Understanding and Enterprise Knowledge Processing | eSapiens is a unified question-answering system designed for enterprise settings that bridges structured databases and unstructured textual corpora via a dual-module architecture. | abstract excerpt |
| claim-051 | eSapiens: A Real-World NLP Framework for Multimodal Document Understanding and Enterprise Knowledge Processing | The system combines a Text-to-SQL planner with a hybrid RAG pipeline, enabling natural language access to both relational data and free-form documents. | abstract excerpt |
| claim-052 | eSapiens: A Real-World NLP Framework for Multimodal Document Understanding and Enterprise Knowledge Processing | To enhance answer faithfulness, the RAG module integrates dense and sparse retrieval, commercial reranking, and a citation verification loop that ensures grounding consistency. | abstract excerpt |
| claim-053 | eSapiens: A Real-World NLP Framework for Multimodal Document Understanding and Enterprise Knowledge Processing | eSapiens is evaluated on the RAGTruth benchmark. | abstract excerpt |
| claim-054 | ReflectiveRAG: Rethinking Adaptivity in Retrieval-Augmented Generation | RAG systems degrade sharply under extreme noise, where irrelevant or redundant passages dominate. | abstract excerpt |
| claim-055 | ReflectiveRAG: Rethinking Adaptivity in Retrieval-Augmented Generation | Current methods—fixed top-k retrieval, cross-encoder reranking, or policy-based iteration—depend on static heuristics or costly reinforcement learning, failing to assess evidence sufficiency, detect subtle mismatches, or reduce redundancy, leading to hallucinations and poor grounding. | abstract excerpt |
| claim-056 | ReflectiveRAG: Rethinking Adaptivity in Retrieval-Augmented Generation | ReflectiveRAG is a lightweight yet reasoning-driven architecture that enhances factual grounding through two complementary mechanisms: Self-Reflective Retrieval (SRR) and [truncated]. | abstract excerpt |
| claim-057 | MARA: A Multimodal Adaptive Retrieval-Augmented Framework for Document Question Answering | Retrieval-based multimodal document QA aims to identify and integrate relevant information from visually rich documents with complex multimodal structures. | abstract excerpt |
| claim-058 | MARA: A Multimodal Adaptive Retrieval-Augmented Framework for Document Question Answering | While RAG has shown strong performance in text-based QA, its extensions to multimodal documents remain underexplored and face significant limitations. | abstract excerpt |
| claim-059 | MARA: A Multimodal Adaptive Retrieval-Augmented Framework for Document Question Answering | Current approaches rely on query-agnostic document representations that overlook salient content and use static top-k evidence selection, which fails to adapt to the uncertain distribution of relevant information. | abstract excerpt |
| claim-060 | A Handbook-Grounded Retrieval-Augmented Generation Chatbot for Family Planning: Comparative Evaluation of Qwen3-4B and Llama-3.1-8B | The study presents a handbook-grounded RAG chatbot for evidence-based family planning question answering using the Philippine Family Planning Handbook (2023 Edition) as a closed knowledge source. | abstract excerpt |
| claim-061 | A Handbook-Grounded Retrieval-Augmented Generation Chatbot for Family Planning: Comparative Evaluation of Qwen3-4B and Llama-3.1-8B | The system employs page-aware PDF extraction, overlapping chunking, and a hybrid BM25–FAISS retrieval pipeline with cross-encoder reranking to assemble page-attributed evidence. | abstract excerpt |
| claim-062 | A Handbook-Grounded Retrieval-Augmented Generation Chatbot for Family Planning: Comparative Evaluation of Qwen3-4B and Llama-3.1-8B | A controlled comparison evaluates Qwen3-4B-Instruct-2507 and Llama-3.1-8B-Instant as generator backends within the identical architecture. | abstract excerpt |
| claim-063 | A Handbook-Grounded Retrieval-Augmented Generation Chatbot for Family Planning: Comparative Evaluation of Qwen3-4B and Llama-3.1-8B | Results across ten domain-specific queries show that [truncated]. | abstract excerpt |
| claim-064 | PetNutriBot: A Retrieval-Augmented, Extractive Conversational Architecture for Grounded Veterinary Nutrition Question Answering | Accessing precise and reliable veterinary nutrition information remains challenging due to the fragmented and technical nature of authoritative sources. | abstract excerpt |
| claim-065 | PetNutriBot: A Retrieval-Augmented, Extractive Conversational Architecture for Grounded Veterinary Nutrition Question Answering | PetNutriBot is a domain-specific question-answering system that integrates a hybrid RAG pipeline with extractive transformer-based models to deliver accurate and grounded responses for cat and dog nutrition queries. | abstract excerpt |
| claim-066 | PetNutriBot: A Retrieval-Augmented, Extractive Conversational Architecture for Grounded Veterinary Nutrition Question Answering | The system leverages dense retrieval using MiniLM embeddings, lexical retrieval via BM25, rank fusion, and cross-encoder reranking to identify relevant evidence, followed by answer [truncated]. | abstract excerpt |
| claim-067 | RankCoT: Refining Knowledge for Retrieval-Augmented Generation through Ranking Chain-of-Thoughts | LLMs still encounter challenges in effectively utilizing the knowledge from retrieved documents, often being misled by irrelevant or noisy information. | abstract excerpt |
| claim-068 | RankCoT: Refining Knowledge for Retrieval-Augmented Generation through Ranking Chain-of-Thoughts | RankCoT is a knowledge refinement method that incorporates reranking signals in generating CoT-based summarization for knowledge refinement based on given query and all retrieval documents. | abstract excerpt |
| claim-069 | RankCoT: Refining Knowledge for Retrieval-Augmented Generation through Ranking Chain-of-Thoughts | During training, RankCoT prompts the LLM to generate Chain-of-Thought (CoT) candidate summaries. | abstract excerpt |
| claim-070 | Faithfulness-Aware Multi-Objective Context Ranking for Retrieval-Augmented Generation | Existing ranking methods in RAG pipelines primarily optimize for document-query relevance, neglecting crucial factors for generation quality such as factual consistency and information coverage. | abstract excerpt |
| claim-071 | Faithfulness-Aware Multi-Objective Context Ranking for Retrieval-Augmented Generation | We propose a novel multi-objective ranking framework that explicitly models three critical dimensions: relevance, coverage, and faithfulness support. | abstract excerpt |
| claim-072 | Faithfulness-Aware Multi-Objective Context Ranking for Retrieval-Augmented Generation | Our method introduces a utility-based scoring mechanism that evaluates these dimensions. | abstract excerpt |
| claim-073 | Demo: Guide-RAG: Evidence-Driven Corpus Curation for Retrieval-Augmented Generation in Long COVID | We developed and evaluated six Retrieval-Augmented Generation (RAG) corpus configurations for Long COVID (LC) clinical question answering, ranging from expert-curated sources to large-scale literature databases. | abstract excerpt |
| claim-074 | Demo: Guide-RAG: Evidence-Driven Corpus Curation for Retrieval-Augmented Generation in Long COVID | Our evaluation employed an LLM-as-a-judge framework across faithfulness, relevance, and comprehensiveness metrics using LongCOVID-CQ, a novel dataset of expert-generated clinical questions. | abstract excerpt |
| claim-075 | Demo: Guide-RAG: Evidence-Driven Corpus Curation for Retrieval-Augmented Generation in Long COVID | Our RAG corpus configuration combining clinical gui... | abstract excerpt |

## Method, results, limitations, and trade-offs

### query_rewriting

No verified claim in the supplied records directly evaluates query rewriting as a standalone technique. The closest evidence concerns adaptive retrieval decisions: indiscriminately retrieving a fixed number of passages regardless of necessity or relevance diminishes LM versatility and can lead to unhelpful response generation (claim-017). Static top-k evidence selection fails to adapt to the uncertain distribution of relevant information (claim-059), and current methods such as fixed top-k retrieval depend on static heuristics that fail to assess evidence sufficiency or detect subtle mismatches (claim-055). These findings imply that query-time adaptivity, including deciding whether and what to retrieve, is a recognized gap, but the supplied records do not isolate query rewriting or report its independent effects.

Supporting claims: claim-017, claim-055, claim-059

Trade-offs: The supplied claims do not report latency, cost, or implementation-complexity trade-offs specific to query rewriting. Related evidence indicates that static retrieval heuristics are cheap but brittle (claim-055), while adaptive alternatives are motivated by failures of static top-k (claim-059), but no verified claim quantifies the cost of adding a rewriting step.

### reranking

Reranking is described as a crucial but often under-explored component of RAG systems (claim-032). Irrelevant documents can mislead the generator (claim-033), and the reranker plays a vital role in refining retrieved documents to enhance generation quality and explainability (claim-034). A central difficulty is choosing the appropriate number of documents k for the reranker to select: too few may miss critical information (claim-036), while the appropriate k is hard to determine (claim-035). RAG efficacy depends on retrieval strategies, reranking mechanisms, and generation models (claim-041), and RAG performance is susceptible to design choices across retrieval, similarity metrics, indexing, and reranking (claim-011). Existing ranking methods primarily optimize document-query relevance while neglecting factual consistency and information coverage (claim-070); a proposed multi-objective ranking framework explicitly models relevance, coverage, and faithfulness support (claim-071) using a utility-based scoring mechanism (claim-072). RankCoT incorporates reranking signals into CoT-based summarization for knowledge refinement (claim-068). In deployed pipelines, cross-encoder reranking appears alongside hybrid retrieval in multiple systems (claim-043, claim-061, claim-066), and commercial reranking is combined with a citation verification loop to enhance answer faithfulness (claim-052).

Supporting claims: claim-011, claim-032, claim-033, claim-034, claim-035, claim-036, claim-041, claim-043, claim-052, claim-061, claim-066, claim-068, claim-070, claim-071, claim-072

Trade-offs: The supplied claims identify a quality trade-off in selecting k: too few documents may omit critical information (claim-036), while determining the appropriate k is challenging (claim-035). Reranking is presented as improving generation quality and explainability (claim-034), but no verified claim in the supplied records quantifies latency or monetary cost of reranking. The multi-objective ranking framework adds coverage and faithfulness-support objectives beyond relevance (claim-071), implying additional scoring complexity, but the records do not report its computational overhead.

### corrective_retrieval

The supplied records contain limited direct evidence on corrective retrieval. A citation verification loop that ensures grounding consistency is integrated into a RAG module to enhance answer faithfulness (claim-052), which is the closest described corrective mechanism. More broadly, RAG systems degrade sharply under extreme noise where irrelevant or redundant passages dominate (claim-054), and current methods fail to assess evidence sufficiency, detect subtle mismatches, or reduce redundancy, leading to hallucinations and poor grounding (claim-055). LLMs are often misled by irrelevant or noisy information in retrieved documents (claim-067). These findings establish the failure modes that corrective retrieval is intended to address, but the supplied claims do not report a controlled evaluation of a corrective-retrieval technique.

Supporting claims: claim-052, claim-054, claim-055, claim-067

Trade-offs: No verified claim in the supplied records quantifies latency, cost, or implementation complexity for corrective retrieval. The citation verification loop is described as part of a system that also uses dense and sparse retrieval and commercial reranking (claim-052), suggesting added pipeline components, but the records do not isolate its cost.

### self_reflective_retrieval

Self-RAG is described as a self-reflective retrieval refinement variant (claim-025) that aims to boost factuality, reasoning depth, and adaptability (claim-027). One paper introduced a series of self-reflective nodes to create a self-RAG model (claim-004), built using ChatGPT for generation and Langchain workflow functions to connect nodes (claim-005). Self-RAG is presented as a promising solution for analytical systems that struggle with efficiently querying and interpreting vast datasets (claim-006, claim-007), with reported research findings that it can enhance data analysis in distributed systems by improving information retrieval accuracy and generation (claim-009). ReflectiveRAG is introduced as a lightweight yet reasoning-driven architecture that enhances factual grounding through two complementary mechanisms, one being Self-Reflective Retrieval (SRR) (claim-056). A unified evaluation framework compares RAG, Self-RAG, and Agentic RAG under matched conditions including the same base model, same hybrid retriever, and identical domain constraints (claim-028, claim-029), across factual recall, multi-hop reasoning, and insurance domain Q&A (claim-030). The motivation for self-reflection includes the prevalence of hallucination in RAG (claim-001), the increasing commonness of inaccurate generations (claim-002), and the amplified impact of inaccurate generations in RAG due to node-like generation (claim-003).

Supporting claims: claim-001, claim-002, claim-003, claim-004, claim-005, claim-006, claim-007, claim-009, claim-025, claim-027, claim-028, claim-029, claim-030, claim-056

Trade-offs: The supplied claims do not report quantitative latency, cost, or implementation-complexity trade-offs for self-reflective retrieval. The construction of self-reflective nodes using ChatGPT and Langchain workflow functions (claim-005) implies additional orchestration components, and ReflectiveRAG is described as lightweight (claim-056), but no verified claim compares its cost against standard RAG. The unified evaluation framework provides matched conditions for comparison (claim-028, claim-029) but the supplied records do not include its results.

### evaluation_and_measurement_context

Faithfulness and relevance are established fine-grained evaluation dimensions for RAG, judged by expert human annotators (claim-019), and meta-evaluation benchmarks support automatic evaluators that correlate with human judgment (claim-020). Existing benchmarks predominantly focus on English or use translated data, failing to capture cultural nuances (claim-021), motivating a multilingual end-to-end meta-evaluation benchmark (claim-023). Multiple systems report evaluation using faithfulness, answer relevancy, citation accuracy, semantic similarity, context precision, context recall, answer correctness, and answer similarity (claim-044, claim-048), and LLM-as-a-judge frameworks are used across faithfulness, relevance, and comprehensiveness (claim-074). RAG is widely characterized as grounding LLMs with external knowledge (claim-024) and as effective for knowledge-intensive tasks (claim-031), while hallucination remains a key problem (claim-038) that RAG mitigates by grounding responses in external knowledge sources (claim-039).

Supporting claims: claim-019, claim-020, claim-021, claim-023, claim-024, claim-031, claim-038, claim-039, claim-044, claim-048, claim-074

Trade-offs: The supplied claims do not quantify the cost of evaluation itself. The use of expert human annotators for fine-grained dimensions (claim-019) and the development of automatic evaluators (claim-020) imply a trade-off between annotation cost and evaluator reliability, but no verified claim measures this trade-off.

## Agent hypotheses (not paper conclusions)

- **hyp-001**: Reranking improves answer faithfulness primarily when the initial retrieval set contains a mixture of relevant and irrelevant documents, and its benefit diminishes when the retriever already returns mostly relevant passages.
  - Derived from: claim-032, claim-033, claim-034, claim-054, claim-067
  - Falsification test: Compare a fixed retriever with and without a cross-encoder reranker across retrieval-noise levels. If the faithfulness gain from reranking is constant or larger at low noise than at high noise, the hypothesis is falsified.
  - Confidence: 0.5
- **hyp-002**: Self-reflective retrieval reduces hallucination more than standard RAG under multi-hop reasoning tasks, but at the cost of additional generation calls that increase latency and cost.
  - Derived from: claim-001, claim-004, claim-005, claim-027, claim-030, claim-056
  - Falsification test: Run standard RAG and self-reflective RAG on a multi-hop benchmark under matched base model and retriever. If self-reflective RAG does not reduce hallucination more than standard RAG on multi-hop tasks, or if it achieves the reduction with no measurable latency or cost increase, the hypothesis is falsified.
  - Confidence: 0.5
- **hyp-003**: Dynamic selection of the number of documents k for reranking improves faithfulness compared with a fixed k, because fixed k either omits critical information or introduces noise depending on the query.
  - Derived from: claim-035, claim-036, claim-054, claim-059
  - Falsification test: Compare fixed-k reranking against a dynamic-k reranker on the same retriever and generator across queries with varying evidence distributions. If dynamic k does not improve faithfulness over the best fixed k, or if the best fixed k matches dynamic k on all query types, the hypothesis is falsified.
  - Confidence: 0.5
- **hyp-004**: Multi-objective reranking that includes coverage and faithfulness support improves answer faithfulness relative to relevance-only reranking, but adds scoring complexity that may increase latency.
  - Derived from: claim-070, claim-071, claim-072, claim-034
  - Falsification test: Compare relevance-only reranking against multi-objective reranking on the same retriever and generator, measuring faithfulness and latency. If multi-objective reranking does not improve faithfulness, or if it improves faithfulness with no latency increase, the hypothesis is falsified.
  - Confidence: 0.5
- **hyp-005**: Corrective retrieval mechanisms such as citation verification loops improve grounding consistency mainly in high-noise retrieval settings, and their benefit is smaller when retrieval precision is already high.
  - Derived from: claim-052, claim-054, claim-055, claim-067
  - Falsification test: Evaluate a RAG system with and without a citation verification loop across retrieval-noise levels. If the grounding-consistency gain is constant or larger at low noise than at high noise, the hypothesis is falsified.
  - Confidence: 0.25
- **hyp-006**: Query rewriting and adaptive retrieval decisions improve retrieval quality for ambiguous or underspecified queries, but provide little benefit for queries whose surface form already matches the indexed documents.
  - Derived from: claim-017, claim-055, claim-059
  - Falsification test: Compare a RAG pipeline with and without query rewriting on a set of ambiguous queries and a set of well-specified queries. If rewriting improves retrieval quality equally for both query sets, or if it does not improve ambiguous queries, the hypothesis is falsified.
  - Confidence: 0.25

## Representative failures

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

Provider-reported usage: `{'input_tokens': 27432, 'output_tokens': 16552, 'cached_input_tokens': 512, 'total_tokens': 43984, 'requests': 5}`. Calculated cost: `$0.02794147`. This is a calculation from published rates, not an invoice.
