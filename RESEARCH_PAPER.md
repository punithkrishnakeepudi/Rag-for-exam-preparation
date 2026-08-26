# StudyLens-EAGS: Evidence-Gated Adaptive Retrieval for Exam Preparation

## Abstract

Large language model study assistants can summarize course material, answer questions, and generate practice tests, but fluent answers may be unsupported by the learner's documents and fixed question generators do not model what the learner knows. This paper proposes StudyLens-EAGS, an educational retrieval-augmented generation system that couples evidence verification with adaptive study activity selection. The system retrieves document passages, reranks them, maps answer claims to evidence spans, and either answers, requests clarification, or abstains when support is insufficient. A learner model estimates concept mastery from verified explanations and quiz attempts, then selects the next activity according to the learner's weakest concepts and target difficulty. We describe an OpenRouter-backed implementation, an evaluation dataset design, baselines, metrics, ablations, and reproducibility requirements. The central hypothesis is that evidence gating improves groundedness while mastery-aware activity selection improves learning efficiency. No performance numbers are claimed until the proposed experiments are run.

**Keywords:** educational AI, retrieval-augmented generation, grounded generation, adaptive learning, mastery estimation, citation verification, exam preparation

## 1. Introduction

Students often need three kinds of support from the same course material: a trustworthy explanation, a way to check understanding, and a plan for what to study next. Conventional document chat addresses the first task but may produce answers that are only plausibly related to the source. Quiz generation addresses the second task but often produces repeated, uncalibrated, or weakly supported questions. A study planner addresses the third task but requires a model of learner knowledge.

StudyLens is an open-source notebook application that already supports document ingestion, dense retrieval, streaming chat, summaries, quizzes, mind maps, and slides. This paper extends that foundation with a testable design rather than treating the collection of UI features as the contribution. The proposed Evidence-Gated Adaptive Study Loop, or EAGS, joins two controls: an evidence gate for answer reliability and a mastery loop for activity selection.

The research questions are:

1. Does evidence gating reduce unsupported claims compared with standard dense RAG?
2. Does hybrid retrieval and reranking improve evidence recall and citation accuracy?
3. Does mastery-aware activity selection improve post-test performance and reduce the number of questions needed to reach a target mastery level?
4. What are the accuracy, latency, and cost trade-offs across routed language models?

The intended contribution is a reproducible educational RAG evaluation and system design. It is not a claim that document chat, adaptive learning, citation grounding, or quiz generation are individually new.

## 2. Related Work

Retrieval-augmented generation combines parametric language models with retrieved external memory and established the basic retrieve-then-generate pattern [1]. Self-RAG introduced a framework in which the model learns to retrieve and critique its own generations [2]. Corrective RAG added a retrieval evaluation and correction step for noisy retrieval results [3]. Ragas proposed automated evaluation dimensions for RAG pipelines, including context relevance, faithfulness, and answer relevance [4]. These works motivate separating retrieval quality and generation quality instead of treating a fluent answer as evidence of correctness.

Educational question generation with retrieval and in-context learning has been studied for automatic assessment [5]. Personalized learning support with RAG has also been explored as a feasibility direction [6]. Graph-based retrieval has been proposed for learner understanding of concepts in MOOCs [7]. These studies establish that educational RAG and adaptive support are active areas. The proposed boundary is the explicit evaluation of a combined policy that uses source support to control answer behavior and uses verified interactions to choose the next learning activity.

Before publication, the authors must update this section through a systematic search and add any work that overlaps with evidence gating, mastery modeling, citation verification, or adaptive tutoring.

## 3. System Overview

### 3.1 Current implementation

The current StudyLens baseline performs the following operations:

1. Extract text from a document.
2. Split the text into fixed word windows with overlap.
3. Generate document embeddings and store them in ChromaDB.
4. Embed a question and retrieve the nearest chunks.
5. Insert the chunks into a prompt.
6. Stream a response to the frontend.
7. Generate summaries, quizzes, slides, and mind maps from document text.

The backend now uses OpenRouter for chat completions and embeddings. The model and embedding IDs are configurable through environment variables. Streaming parses Server-Sent Events and ignores OpenRouter keep-alive comments. JSON-producing flows use OpenRouter JSON mode, with application-level repair and validation retained as a defensive layer.

### 3.2 Proposed EAGS pipeline

For a question q and document collection D:

1. Construct lexical and dense query representations.
2. Retrieve a candidate set C using hybrid search.
3. Rerank C and select evidence E with diversity constraints.
4. Generate a draft answer A with explicit evidence references.
5. Split A into claims c1...cn.
6. Verify each claim against evidence spans.
7. Compute retrieval confidence and support confidence.
8. Apply a response policy: answer, answer with warning, ask clarification, or abstain.
9. Update concept mastery from the verified interaction.
10. Select the next activity using concept weakness, difficulty target, and spaced-repetition timing.

### 3.3 Evidence gate

Let r be retrieval confidence, s be the fraction of answer claims supported by evidence, and x be a contradiction indicator. A simple policy is:

- answer when r >= tau_r, s >= tau_s, and x = 0;
- answer with an uncertainty notice when support is partial and the question is answerable;
- ask a clarification question when the query is ambiguous;
- abstain when evidence is absent, contradictory, or below the support threshold.

The thresholds must be tuned only on a development set and then frozen for the test set.

### 3.4 Mastery loop

Represent each concept k with a mastery estimate m_k in [0, 1]. After a question attempt with correctness y, difficulty d, and confidence estimate p, update m_k using a transparent rule or a Bayesian knowledge-tracing variant. A simple starting rule is:

`m_k(next) = clip(m_k + alpha * (y - m_k) * w(d), 0, 1)`

where w(d) increases for harder questions. Activity selection chooses a concept with low mastery but sufficient prerequisite readiness, then selects explanation, hint, practice, or review according to the learner's recent errors and review interval.

## 4. Implementation

### 4.1 Provider layer

The OpenRouter client exposes four backend operations: `embed`, `generate`, `json_generate`, and `stream`. It sends system and user messages to the chat completions endpoint, sends document/query strings to the embeddings endpoint, validates the API key before requests, and preserves the frontend SSE contract. The embedding model must remain fixed for an index lifetime; changing it requires re-indexing.

### 4.2 Retrieval layer

The baseline uses Chroma cosine similarity with top-k retrieval. The proposed implementation adds BM25, dense retrieval, reciprocal-rank fusion, a reranker, parent-child context expansion, and exact page/character metadata. Retrieval logs should include query text hash, model ID, candidate IDs, scores, selected evidence, and latency.

### 4.3 Evidence layer

The answer prompt requires each factual claim to reference one or more evidence spans. A verifier classifies claims as supported, unsupported, or contradicted. The UI exposes source spans and the reason for refusal or uncertainty. The verifier must be evaluated independently; otherwise a model can simply agree with its own unsupported answer.

### 4.4 Learning layer

A concept extractor produces concept IDs and prerequisite edges. Quiz attempts, hints, and verified chat claims update the mastery state. The state is stored separately from raw chat text so that it can be inspected, reset, and evaluated.

## 5. Experimental Method

### 5.1 Baselines and ablations

- B0: language model without retrieval.
- B1: current dense top-k StudyLens RAG.
- B2: hybrid retrieval and reranking.
- B3: B2 with exact citations and claim verification.
- EAGS: B3 with evidence policy, mastery updates, and adaptive activity selection.

Ablations remove one component at a time: no reranker, no evidence gate, no verifier, no mastery model, and random activity selection.

### 5.2 Dataset and annotation

Construct a benchmark from openly licensed material in at least three subjects. For each held-out question, annotate the answer points, gold evidence spans, concept IDs, expected difficulty, and whether the correct behavior is to answer, clarify, or abstain. Include absent-answer and contradiction cases. Use two annotators on a subset and report agreement and adjudication rules.

### 5.3 Metrics

Retrieval metrics are Recall@k, MRR, nDCG, and evidence coverage. Generation metrics are answer correctness, citation precision, citation recall, supported-claim ratio, contradiction rate, abstention precision, and abstention recall. Learning metrics are pre/post-test gain, delayed retention, questions per mastered concept, and mastery calibration. System metrics are p50/p95 latency, token usage, cost, failure rate, and stream completion rate.

### 5.4 Statistical analysis

Report sample sizes, confidence intervals, per-subject results, and paired tests where the same questions are evaluated across systems. For user studies, preregister the primary outcome, randomization unit, exclusion rules, and stopping rule. Report effect sizes, not only p-values.

## 6. Expected Findings

The hypotheses are:

- H1: B3 and EAGS will have a higher supported-claim ratio and lower contradiction rate than B1.
- H2: hybrid retrieval and reranking will improve evidence recall on terminology-heavy and multi-hop questions.
- H3: EAGS will produce higher delayed post-test gain per minute than random quiz selection.
- H4: stronger models will not necessarily minimize cost per mastered concept because latency and token cost can dominate.

These are hypotheses, not results. The final paper must replace this section with measured values, uncertainty intervals, failure examples, and negative findings.

## 7. Reproducibility

Record the exact commit, Python version, dependency lock, OpenRouter model IDs, embedding model ID, temperature, retrieval parameters, prompt versions, dataset license, and evaluation scripts. Store API responses only when permitted and remove keys, personal data, and document content from logs. Include mocked provider tests so the pipeline can be checked without a live API key.

## 8. Limitations and Responsible Use

OpenRouter routing and upstream model updates can change behavior. Cloud inference introduces privacy, cost, and availability constraints that did not exist in the original local Ollama design. A support verifier can fail, and a mastery estimate is not a psychological measurement. The system should assist learning, not make high-stakes grading or admissions decisions. Students should be told when an answer is uncertain or based on incomplete evidence.

## 9. Conclusion

StudyLens is best advanced by turning its existing feature set into an auditable learning experiment. EAGS provides a concrete research boundary: evidence determines whether the tutor is allowed to answer, and verified interactions determine what the learner should do next. The contribution becomes credible only after comparison with strong baselines, human-labeled evidence, ablations, and a literature search that records overlapping work.

## References

[1] Lewis et al., "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks," 2020. https://arxiv.org/abs/2005.11401

[2] Asai et al., "Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection," 2023. https://arxiv.org/abs/2310.11511

[3] Yan et al., "Corrective Retrieval Augmented Generation," 2024. https://arxiv.org/abs/2401.15884

[4] Es et al., "Ragas: Automated Evaluation of Retrieval Augmented Generation," 2023. https://arxiv.org/abs/2309.15217

[5] "Leveraging In-Context Learning and Retrieval-Augmented Generation for Automatic Question Generation in Educational Domains," 2025. https://arxiv.org/abs/2501.17397

[6] "Exploring Personalized Learning Support through Retrieval Augmented Generation," 2024. https://aclanthology.org/2024.swisstext-1.12/

[7] "Leveraging Graph Retrieval-Augmented Generation to Support Learners' Understanding of Knowledge Concepts in MOOCs," 2025. https://arxiv.org/abs/2505.10074
