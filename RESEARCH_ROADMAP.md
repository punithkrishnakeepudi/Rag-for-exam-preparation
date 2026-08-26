# StudyLens: Next-Step Roadmap and Research Positioning

## 1. Current system

StudyLens is a notebook-scoped educational RAG application with:

- PDF, DOCX, TXT, Markdown, and URL ingestion
- fixed word-window chunking and Chroma cosine retrieval
- streaming grounded chat with document-level source labels
- document summaries, MCQ generation, mind maps, and slide decks
- SQLite persistence for notebooks, documents, and chat history
- OpenRouter generation and embedding calls through one backend client

This is a useful product foundation, but the current system is not yet a strong research contribution. Its main limitations are fixed chunking, dense-only retrieval, weak source attribution, no abstention policy, no learner model, no experiment harness, and no answer-quality telemetry.

## 2. Proposed central contribution

Use the working name **EAGS: Evidence-Gated Adaptive Study Loop**.

EAGS is a two-loop educational RAG design:

1. **Evidence loop:** retrieve, rerank, and verify source spans. If evidence is weak or contradictory, the system asks a clarifying question or abstains instead of guessing.
2. **Learning loop:** estimate mastery by concept and use verified evidence to choose the next explanation, hint, quiz item, or spaced-repetition review.

The research claim should be narrow:

> Compared with a standard dense RAG tutor, an evidence-gated adaptive study loop can improve groundedness and learning efficiency under the same model and document budget, while reducing unsupported answers and poorly targeted questions.

Do not claim that the entire product is novel. RAG tutors, MCQ generators, personalized learning systems, graph RAG, and citation-aware systems already exist. The defensible contribution is the evaluated coupling of evidence support, abstention, learner-state updates, and next-action selection for exam preparation.

## 3. Feature expansion paths

| Path | Feature | Product value | Research value | Priority |
|---|---|---:|---:|---:|
| Ingestion | layout-aware PDF parsing, tables, equations, OCR, page coordinates | High | High | P0 |
| Retrieval | hybrid BM25 + dense search, parent-child chunks, query expansion | High | High | P0 |
| Retrieval | cross-encoder reranking and diversity selection | High | Medium | P0 |
| Evidence | exact span citations, claim-to-source mapping, contradiction detection | Very high | Very high | P0 |
| Evidence | retrieval confidence, answer support score, abstain/clarify policy | Very high | Very high | P0 |
| Learning | concept inventory and prerequisite graph | High | High | P1 |
| Learning | mastery estimation from quiz attempts and chat signals | Very high | Very high | P1 |
| Assessment | Bloom-level controls, difficulty calibration, distractor validation | High | High | P1 |
| Assessment | spaced repetition and exam-date study planner | Very high | High | P1 |
| Personalization | learner language, pace, preferred explanation style, accessibility modes | High | Medium | P1 |
| Multimodal | figure/table/image retrieval, formula explanations, diagram questions | High | High | P1 |
| Agents | planner -> retriever -> tutor -> verifier workflow with bounded tools | Medium | Medium | P2 |
| Evaluation | question bank, golden citations, regression tests, LLM judge plus human labels | Medium | Very high | P0 |
| Observability | latency, tokens, cost, model, retrieval scores, refusal rate | Medium | High | P0 |
| Privacy | local encrypted document store, redaction, provider policy controls | High | High | P1 |
| Collaboration | instructor authoring, shared notebooks, cohort analytics | High | Medium | P2 |
| Deployment | model routing, fallback models, rate limits, job queue, Docker | High | Medium | P2 |

## 4. Recommended build sequence

### Phase 0: make the baseline measurable

- Add a stable question/evidence evaluation dataset from 3-5 open educational documents.
- Store page number, chunk ID, character offsets, retrieval scores, model ID, latency, and token usage.
- Replace document-name citations with exact source spans.
- Add a support verifier that labels each answer claim as supported, unsupported, or contradicted.
- Add an abstain threshold and a visible reason when evidence is insufficient.
- Add mocked OpenRouter contract tests and a provider health check.

### Phase 1: improve RAG quality

- Parse page-aware blocks rather than only whitespace windows.
- Add hybrid lexical and dense retrieval.
- Rerank the top 20 candidates and pass the best diverse 4-6 chunks to the model.
- Add query rewriting for ambiguous exam questions.
- Add parent-child retrieval so a small child chunk retrieves a larger context window.
- Add a re-index command when the embedding model changes.

### Phase 2: build the learning loop

- Extract concepts and prerequisites from source documents.
- Maintain a mastery score per concept with a transparent update rule.
- Generate questions only from verified evidence spans.
- Calibrate question difficulty using attempt history, not only the model's self-label.
- Recommend the next activity: explain, hint, practice, mixed review, or spaced repetition.

### Phase 3: evaluate and package the research system

- Run component ablations and model/provider comparisons.
- Measure groundedness and learning outcomes separately.
- Conduct a small controlled user study with consent and a pre/post test.
- Publish code, prompts, configuration, anonymized evaluation data, and a reproducible run script.

## 5. Research questions

- **RQ1:** Does evidence gating reduce unsupported claims compared with standard dense RAG?
- **RQ2:** Does hybrid retrieval plus reranking improve citation recall and answer correctness?
- **RQ3:** Does mastery-aware activity selection improve delayed post-test performance compared with random quiz selection?
- **RQ4:** What is the quality, latency, and cost trade-off across OpenRouter model choices?
- **RQ5:** When should the system abstain, ask for clarification, or answer directly?

## 6. Experimental design

### Systems to compare

- **B0:** LLM without document retrieval.
- **B1:** Current StudyLens dense top-k RAG.
- **B2:** Hybrid BM25 + dense retrieval with reranking.
- **B3:** B2 plus exact citations and answer verification.
- **EAGS:** B3 plus evidence gating, concept mastery, and adaptive next-activity selection.

Keep the generation model, prompt budget, document set, and maximum context length fixed within each comparison. Change one component at a time for ablations.

### Dataset

Use openly licensed course material from at least three subjects, for example computer networks, machine learning, and operating systems. Create a held-out question set containing:

- direct fact questions
- multi-hop explanation questions
- comparison questions
- numerical or formula questions
- questions whose answer is absent
- questions with conflicting source passages
- ambiguous questions that require clarification

For every question, annotate gold evidence spans, expected answer points, acceptable abstention behavior, and concept IDs. Have two human annotators label a subset and report agreement.

### Metrics

- Retrieval: Recall@k, MRR, nDCG, evidence coverage.
- Generation: exactness, answer correctness, citation precision, citation recall, supported-claim ratio, contradiction rate, abstention precision, abstention recall.
- Learning: pre/post-test gain, delayed retention gain, question efficiency, mastery calibration, time-on-task.
- Operations: p50/p95 latency, tokens, cost per session, error rate, stream completion rate.
- User experience: SUS or UMUX-Lite, perceived trust, explanation usefulness, cognitive load.

Never report only an LLM judge score. Use human labels for a statistically meaningful sample and report confidence intervals, sample size, and the judge prompt/model.

## 7. Threats to validity and ethics

- Model upgrades and OpenRouter routing can change results; pin model IDs and record provider metadata.
- LLM judges can share biases with the evaluated model; use human adjudication.
- Synthetic questions can make the system look better than it is; include real exam-style questions.
- A higher refusal rate is not automatically better; evaluate helpful clarification and learning outcomes.
- Student data is sensitive; minimize collection, obtain consent, redact identifiers, and document provider data handling.
- Do not make claims about improved grades without a controlled study.
- The phrase "first" or "novel" requires a systematic search across papers, patents, products, and repositories before publication.

## 8. Originality checklist

Before submitting the paper:

- Search Semantic Scholar, Google Scholar, ACL Anthology, arXiv, IEEE Xplore, and ACM Digital Library using combinations of `educational RAG`, `adaptive tutoring`, `citation grounded QA`, `evidence gating`, `abstention`, `mastery learning`, `graph RAG`, and `MCQ generation`.
- Build a comparison table with task, data, retrieval method, learner model, evaluation, and code availability.
- Run a repository and product search for overlapping feature combinations.
- Use a plagiarism/similarity checker for the manuscript, but treat its result as a screening signal, not proof of originality.
- Rephrase all borrowed ideas, cite the original work, and publish the exact novelty boundary.
- If a similar system appears, change the claim to an empirical comparison, reproducible benchmark, or new dataset rather than hiding the overlap.

## 9. Definition of done for the next level

A strong v1 research prototype should make one answer auditable end to end:

`question -> query -> retrieved spans -> reranked evidence -> support labels -> response/refusal -> concept update -> next activity`

If the system cannot log that chain, it is a demo, not yet a research instrument.
