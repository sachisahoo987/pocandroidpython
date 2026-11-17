# AI Engineer: Concept-to-Practice Roadmap

## Quick navigation

- [How to use this guide](#how-to-get-value-from-the-map)
- [LLM fundamentals](#1-llm-fundamentals)
- [RAG](#2-retrieval-augmented-generation)
- [Agents](#3-ai-agents)
- [Evaluation and observability](#4-evaluation-and-observability)
- [AI system design](#5-ai-system-design-and-inference)
- [AI security](#6-ai-security)
- [Backend and APIs](#7-backend-and-api-engineering)
- [Deployment and operations](#8-deployment-and-operations)
- [Build sequence](#suggested-practical-build-sequence)
- [Source inventory](#source-inventory)

## What this guide is for

This is a hands-on learning map for the eight AI-engineering infographic
images in the supplied `aiengineer` folder. Each listed concept is connected
to this repository, a practical exercise, and an honest implementation
status. It is designed to help you learn the underlying idea by building and
measuring it in a real test-automation context—not by collecting libraries
or claiming that a technology is already integrated.

The images are a learning checklist, not a curriculum standard or a mandate
to install every named technology. In particular, model-serving techniques,
multi-tenant SaaS infrastructure, and distributed deployment concepts are
advanced specializations; many should remain small experiments unless a
measured project need justifies production work.

### Current project baseline

The repository is a deterministic Python 3.14, pytest-BDD, Appium mobile
automation framework. It already provides page objects, a platform-aware
locator catalog, pytest/JUnit and Allure results/evidence, GitHub Actions,
environment-backed settings, and a synthetic AI-QA starter fixture. It has
**no AI runtime**: no LLM provider, embeddings, RAG index, AI evaluation
runner, agent, MCP server, model trace, AI service API, vector store, or
AI-specific deployment.

The fixture at
[`tests/fixtures/ai_qa/starter_cases.json`](../tests/fixtures/ai_qa/starter_cases.json)
is synthetic input for offline development, not a reviewed benchmark. The
current Appium and test results remain the only execution/verdict authority.
Web and API examples supplied separately are references, not integrated
project components.

### Status legend

| Label | Meaning |
|---|---|
| **Foundation** | A deterministic project capability exists and can be reused; it is not AI. |
| **Planned** | The canonical [AI implementation plan](AI_IMPLEMENTATION_PLAN.md) defines a future capability or acceptance gate, but code is not implemented. |
| **Future** | An optional extension; learn it with a bounded lab and implement only when justified. |
| **Study** | Understand the concept and trade-offs; it is usually internal to a model/provider or unnecessary for this project's first production slice. |

Use the status on each row to track project implementation. A completed study
or notebook is not an implemented product capability.

## How to get value from the map

For every lab, keep a small evidence record: concept, hypothesis, baseline,
change, tests, metric, cost/latency, security boundary, result, and next
decision. A good learning loop is:

1. Explain the concept in your own words and draw the data flow.
2. Predict how it should change one measurable outcome.
3. Implement a small, isolated experiment using synthetic or approved data.
4. Test normal, invalid, ambiguous, and adversarial inputs.
5. Compare against a deterministic baseline and record when not to use it.
6. Link the experiment to the relevant framework module and acceptance test.

For a step-by-step build sequence, use the
[AI Architect / SDET Practical Roadmap](AI_ARCHITECT_SDET_PRACTICAL_ROADMAP.md).
The
[AI Implementation Plan](AI_IMPLEMENTATION_PLAN.md)
owns canonical status, priority, and exit criteria. This guide maps concepts
to experiments; it is not a second completion tracker.

## 1. LLM fundamentals

**Image:** `IMG_2309.jpeg` — 20 concepts.

| Concept | How it relates to this framework | Practical exercise and status |
|---|---|---|
| Tokenization | Prompt, retrieved evidence, and output consume model-specific tokens; character count is not a dependable budget. | Compare token counts for a failed-step summary versus a full log using a tokenizer for the selected model. Add a token-budget test to the planned context builder. **Planned** |
| Transformer architecture | The model is a probabilistic component behind the automation, not the test runner or source of truth. | Draw a high-level transformer data path and use a tiny educational notebook to inspect embeddings and attention. Keep model internals outside Appium page objects. **Study** |
| Self-attention | Helps explain how token relationships are represented; it does not guarantee reasoning, factuality, or source attribution. | Run a toy attention example on synthetic test sentences, then compare model-generated diagnoses against evidence-linked deterministic cases. **Study** |
| Context windows | A future diagnostic must fit a bounded slice of scenario, exception, locator metadata, and approved evidence. | Build the planned context assembler; test truncation order, source labels, redaction, and refusal when critical evidence is dropped. **Planned** |
| KV cache | A decoder optimization that reuses prior attention keys/values during generation; normally controlled by the inference provider. | Observe latency/usage behavior on repeated-prefix provider calls if supported. Do not build an application KV cache; distinguish it from response/prompt caching. **Study** |
| Temperature and top-p | Sampling controls can affect variation in test-plan drafts or explanations, but lower randomness does not prove correctness. | Run the same synthetic golden prompts across settings; compare schema validity, unsupported claims, output variation, and cost. Use deterministic validators regardless. **Future** |
| System prompts | Trusted task instructions should be versioned separately from untrusted app text, logs, retrieved documents, and screenshots. | Store prompt templates with version IDs; test injected instructions inside a synthetic failure log. Authorization must stay in Python policy, not the prompt. **Planned** |
| Few-shot prompting | Curated examples may teach the desired failure-analysis or test-plan shape, but add context cost and can bias results. | Compare zero-shot and a few reviewed examples on the same golden set; measure quality per token and ensure examples contain no secrets. **Future** |
| Chain of thought | A model's private reasoning is not an audit trail and should not be required for trustworthy output. | Request a concise rationale with evidence IDs and verifiable checks, not hidden reasoning. Assert every cited ID exists and separates facts from hypotheses. **Planned** |
| Reasoning models | A higher-effort model can help ambiguous synthesis but may add latency and cost; it still needs evidence and validation. | Route only ambiguous/high-impact synthetic failures to a reasoning-capable model and compare with a cheaper baseline. Keep explicit budget and abstention paths. **Future** |
| Structured outputs | Typed outputs make proposed diagnoses and plans parseable; schema validity alone does not establish truth. | Define Pydantic/JSON Schema contracts for `FailureAnalysis` and `TestPlanDraft`; test missing/extra fields, invalid IDs, malformed content, and provider errors. **Planned** |
| Prompt caching | Reusing a stable prompt prefix may reduce provider cost/latency; support and cache semantics are provider-specific. | Measure cached versus uncached calls after a provider is approved. Keep dynamic evidence after stable instructions and do not cache across access scopes. **Future** |
| Token pricing | Cost depends on model, input/output token mix, caching, and current provider pricing. | Record usage and pricing-source version in redacted evaluation reports; compute cost per accepted diagnosis. Never hard-code infographic prices. **Planned** |
| Hallucinations | A plausible but unsupported locator or root cause could mislead triage or weaken testing. | Include unanswerable/conflicting examples; require evidence IDs, validate references, track unsupported-claim rate, and abstain when evidence is insufficient. **Planned** |
| Multimodal inputs | Existing screenshots/video are evidence foundations, not image understanding; UI hierarchy is often more precise and cheaper. | Compare hierarchy-only diagnosis with approved, redacted screenshot analysis for a synthetic visual issue. Measure incremental accuracy and data exposure. **Future** |
| Fine-tuning with LoRA | Adapter training may help a repeated task/style, but does not refresh changing project facts or add authorization. | First demonstrate a measured quality gap after prompt/RAG baselines and obtain data approval. A separate disposable experiment can compare an adapter with prompting. **Study** |
| QLoRA | Quantized low-rank adaptation is a memory-saving fine-tuning method for operating/train-adapting an open model. | Study through a synthetic-data notebook only if model adaptation becomes a goal; compare quality, GPU memory, training effort, and license. No current project need. **Study** |
| Quantization | Lower-precision weights can reduce inference memory/cost, often with quality and hardware trade-offs. | Compare an approved small open model at two supported precisions on the same synthetic evaluation set before choosing local inference. **Study** |
| Distillation | A smaller student model can imitate a larger model for selected tasks; quality is bounded by the data and teacher labels. | Build a toy classification experiment only after a stable, human-reviewed labeled set exists; measure regression and abstention, not only average accuracy. **Study** |
| Open vs. closed models | Self-hosting offers different control/data/cost trade-offs than a managed API; neither is automatically safer or cheaper. | Score candidates against privacy, data residency, quality, latency, operating skills, licensing, availability, and total cost. No provider is selected in this repo. **Future** |

## 2. Retrieval-augmented generation

**Image:** `IMG_2310.jpeg` — 20 concepts.

| Concept | How it relates to this framework | Practical exercise and status |
|---|---|---|
| Embeddings | Could retrieve semantically similar framework docs or prior reviewed failures; they are not labels or truth. | Implement embeddings only after a lexical baseline and reviewed queries exist. Keep model/index version, source IDs, and access metadata. **Planned** |
| Cosine similarity | A vector comparison score ranks candidates but is not a calibrated probability of relevance. | Compare cosine-ranked results to human relevance labels; plot score distributions and inspect false positives. Do not present similarity as confidence. **Future** |
| Chunking strategies | Features, scenarios, headings, and code units provide natural boundaries for project knowledge. | Parse allowlisted docs/Gherkin by semantic section; test chunk overlap, duplicate removal, source offsets, and whether acceptance rules remain together. **Planned** |
| Vector databases | A vector store is an index, not the source of truth or a security policy. | Start with in-memory/local indexing; compare one store only when corpus size, concurrency, persistence, or measured retrieval quality requires it. **Future** |
| pgvector | Could store embeddings beside relational evaluation/run metadata in PostgreSQL. | Prototype only if a real relational service is approved and vector/ACL needs justify it; compare operational and access-control complexity with a local index. **Future** |
| HNSW indexes | Approximate-nearest-neighbor index balancing recall, memory, and latency for larger vector collections. | Use a synthetic corpus to compare exact search with HNSW recall/latency at increasing sizes. Do not tune an index for today's small corpus. **Study** |
| Metadata filtering | Retrieval must respect repository, version, platform, environment, data class, and access scope. | Add metadata to each document record and test that Android queries cannot return unapproved/iOS-only or restricted evidence. **Planned** |
| BM25 keyword search | Exact test IDs, locator keys, exception names, and API routes are often best found lexically. | Implement an allowlisted lexical baseline and measure Recall@k on exact-identifier and paraphrase queries. **Planned** |
| Hybrid search | Combining lexical and semantic retrieval may improve exact-match plus paraphrase recall. | Compare lexical-only, vector-only, and hybrid results on one fixed, human-labeled query set; adopt hybrid only for measured gains. **Future** |
| Reranking | A reranker reorders retrieved candidates; it cannot recover documents never retrieved. | Measure ranking quality before/after reranking with MRR/nDCG and include added latency/cost. **Future** |
| Query rewriting | A rewritten query can add synonyms/context but may alter IDs or user intent. | Keep the original query, produce a bounded rewrite, and compare retrieval recall; preserve exact IDs and test rewritten queries for scope leakage. **Future** |
| HyDE | Hypothetical-document embeddings may improve semantic retrieval but can amplify invented assumptions. | Treat it as an offline experiment; compare against ordinary retrieval and require source-grounded results. Do not use generated hypothetical text as evidence. **Study** |
| Contextual retrieval | Adding a section heading or parent context can disambiguate a chunk without replacing its source. | Store a short context field plus exact source offsets; verify that citations still point to the original document text. **Future** |
| Parent-child chunking | Small child chunks can retrieve precisely while their parent section supplies enough meaning to answer. | Retrieve child IDs, expand only to bounded parent text, and measure context precision and token cost. **Future** |
| Document parsing | Ingestion quality affects retrieval; arbitrary recursive filesystem ingestion risks secrets and generated artifacts. | Build an explicit source allowlist for selected docs/Gherkin/catalog metadata; test unsupported formats, stale files, and secret-like strings. **Planned** |
| Citations | A diagnosis or test draft should refer to a stable source/version/section, not merely include a plausible link. | Validate source IDs and commit/section metadata in every output; measure citation correctness and unsupported-claim rate. **Planned** |
| GraphRAG | A graph could connect requirement → scenario → step → page/locator → run/failure relationships. | Begin with deterministic IDs and a simple graph export; compare multi-hop question accuracy with lexical/vector baselines before adding a graph database. **Future** |
| Agentic RAG | An agent may refine a query or retrieve iteratively, increasing cost and attack surface. | Add only after single-pass retrieval is evaluated; cap retrieval rounds, tools, tokens, and time, and ensure the agent cannot broaden access. **Future** |
| Recall@k | Measures whether relevant labeled documents appear in the top k; does not measure answer correctness. | Create a reviewed query-to-document set and report Recall@k by query type and platform. **Planned** |
| MRR and nDCG | Ranking measures reward early relevant results or graded relevance; they complement recall. | Report MRR/nDCG alongside recall and inspect query-level failures; choose k/thresholds from the actual QA use case. **Planned** |

## 3. AI agents

**Image:** `IMG_2311.jpeg` — 20 concepts.

| Concept | How it relates to this framework | Practical exercise and status |
|---|---|---|
| Tool calling | Agents should call named application functions, not arbitrary shell/device/filesystem operations. | Define an internal typed, allowlisted registry for run summaries, failed steps, locator metadata, and evidence references. Test arguments, permissions, timeouts, output caps, and audit events. **Planned** |
| Agent loop | Repeated model → tool → observation cycles can fail, loop, or consume budget. | Implement a small deterministic supervisor with explicit states, maximum turns/tool calls, deadlines, and terminal results. **Planned** |
| ReAct pattern | Alternating action/observation can be useful, but exposing hidden reasoning is unnecessary. | Log concise action rationale, tool arguments, and observations; keep internal reasoning private and validate every action server-side. **Future** |
| Planning | Planning can decompose test-design or diagnosis tasks, but plans may be wrong or oversized. | Produce a short typed task plan with allowed steps, then validate each against capability policy and budget before execution. **Future** |
| Reflection | Self-review can catch omissions but repeated model critique can reinforce the same error. | First use deterministic schema/evidence validation. Compare an optional independent review against human labels and cost; do not let reflection approve its own output. **Future** |
| Short-term memory | Current task state, evidence IDs, and approval state belong in a bounded workflow record. | Implement an explicit transient state object; test run isolation and ensure data from one scenario cannot leak into another. **Planned** |
| Long-term memory | Durable facts need provenance, ownership, access, review, expiry, and deletion. | Defer persistence; later prototype typed, human-approved diagnostic patterns and test cross-scope access, expiry, supersession, and deletion. **Future** |
| MCP servers | MCP can expose stable tools/resources to compatible clients; it does not provide authorization by itself. | Add an MCP adapter only after the internal registry and policy are tested. Begin read-only with repository/run-scoped tools. **Planned** |
| MCP clients | A client discovers/calls an MCP server; client trust and server identity still matter. | Use an approved local client to test schema, server identity, consent, timeout, and error behavior; never connect the agent to arbitrary servers. **Future** |
| Agent skills | Reusable QA guidance can encode test-design steps, but is not an executable security boundary. | Convert the supplied scenario/test-strategy guidance into reviewed instructions and test them on synthetic requirements; keep authorization in code. **Future** |
| Multi-agent handoffs | Handoffs pass bounded state between specialist capabilities; unrestricted conversation is hard to audit. | Model a failure analyst → locator analyst handoff with typed payload, allowed scope, stop state, and provenance. Start with one agent and justify any second by eval gains. **Future** |
| Orchestrator-worker pattern | A supervisor can delegate independent bounded analysis and merge validated results. | Compare deterministic fan-out of independent evidence checks to a worker agent; cap workers and reject conflicting/unreferenced outputs. **Future** |
| LangGraph | A graph runtime can model state, conditional routes, checkpoints, and interrupts. | Keep plain Python initially; run a compatibility spike only when the workflow needs durable branching/resume, then choose one orchestrator. **Future** |
| OpenAI Agents SDK | One provider-specific option for agent/tool workflows, not a requirement or current dependency. | Evaluate only behind project contracts against MAF and other candidates; compare Python compatibility, data policy, tool controls, observability, and golden-set quality. **Study** |
| State and checkpoints | Checkpoints support recovery/approval pauses but may retain sensitive state and replay side effects. | Persist minimal versioned state and artifact references; re-check authorization/freshness on resume and make external operations idempotent. **Planned** |
| Human in the loop | People review generated plans and approve consequential locator, Jira, or execution actions. | Add an explicit review status and approver identity to future proposals; test reject, timeout, stale evidence, and re-approval paths. **Planned** |
| Context engineering | The workflow should select, label, order, redact, and bound trusted instructions and untrusted evidence. | Build the planned context builder from scenario, exception, locator key, and approved excerpts; test token/size budget and trust separation. **Planned** |
| Context compaction | Long runs need concise summaries without losing important provenance or constraints. | Compact only prior observations into a typed summary with source IDs; test it against the immutable original artifacts for omitted critical facts. **Future** |
| Stop conditions | Every workflow needs explicit completion, abstention, denial, budget, timeout, and error outcomes. | Enumerate terminal states in the contract and prove each with unit tests; never translate exhaustion into success. **Planned** |
| A2A protocol | Agent-to-agent interoperability is useful only when independently governed agents need to communicate across systems. | Learn the protocol conceptually; a local QA workflow should use internal typed calls first. Consider A2A only for a separately approved integration need. **Study** |

## 4. Evaluation and observability

**Image:** `IMG_2312.png` — 20 concepts.

| Concept | How it relates to this framework | Practical exercise and status |
|---|---|---|
| Golden datasets | The existing starter fixture is synthetic but not yet human-reviewed ground truth. | Version reviewed examples with source/provenance, expected class, evidence IDs, unknown cases, and adversarial cases. **Planned** |
| Error analysis | Aggregate metrics can conceal systematic misclassification, weak evidence, or platform-specific failure. | Inspect per-case false positives/negatives and confusion categories; document examples and root causes for each iteration. **Planned** |
| LLM as a judge | A model judge can score some qualities but is biased and not an independent oracle. | Calibrate a judge against human labels and deterministic rubric checks; track disagreement and never gate only on judge scores. **Future** |
| Pairwise comparison | A/B output comparisons can be easier for humans than assigning an absolute score. | Blindly compare prompt/model A vs B on identical synthetic cases; record preference, tie, rationale rubric, and judge/human disagreement. **Future** |
| Rubric scoring | A fixed rubric makes review more repeatable than a single vague quality rating. | Score evidence support, completeness, uncertainty, and action safety separately; train reviewers with examples and measure agreement. **Planned** |
| Faithfulness | A response should be supported by retrieved or supplied evidence. | Require source citations and use deterministic claim/source checks plus human review; measure unsupported claims separately from style. **Planned** |
| Answer relevance | Correct facts are not enough if the answer does not address the user's QA question. | Label expected answer intent and evaluate relevance separately from factuality and concision. **Future** |
| Context precision | Retrieved context should contain useful evidence rather than irrelevant or conflicting material. | Label relevant retrieved passages; measure relevant/total context and inspect failure categories before changing chunking or ranking. **Planned** |
| Tool-call accuracy | A tool call must use the right approved tool, valid arguments, and expected permission. | Build contract/policy tests for correct, malformed, denied, and unnecessary calls; never judge only by final prose. **Planned** |
| Trajectory evaluations | Multi-step agent behavior includes routing, tool choices, state, and stop conditions. | Record versioned traces and expected allowed transitions; evaluate tool sequence, budget compliance, evidence use, and terminal state. **Future** |
| Regression evals in CI | GitHub Actions exists, but no AI regression gate or model eval suite exists. | Add offline deterministic evals before any hosted model; run a stable smoke set in CI and publish sanitized case-level artifacts. **Planned** |
| A/B testing prompts | Prompt changes can shift quality/cost; live experimentation risks exposing users or affecting decisions. | Compare versions offline first. Use shadow/canary traffic only with privacy/security approval, rollback criteria, and no user-impacting action. **Future** |
| Human labeling | Human-reviewed expected results establish the evaluation reference. | Label a representative synthetic set with rubric, reviewer, adjudication, timestamp, and version; keep disagreement visible. **Planned** |
| Synthetic test data | Existing fixture data is synthetic and safe to use as an offline starting point, but is not ground truth. | Generate edge cases from schema/rules, then review labels and remove secrets/real PII; measure whether synthetic cases reflect real failure classes. **Foundation** |
| Tracing | Allure and CI provide deterministic test evidence; there are no model/agent traces. | Add redacted workflow/run/tool IDs and structured events; link to protected artifacts rather than copying raw page source into traces. **Planned** |
| Langfuse | Optional hosted/self-hosted LLM observability choice, not a current component. | Compare with LangSmith only after data approval; select at most one initial hosted trace platform and verify retention/redaction controls. **Future** |
| OpenTelemetry for LLMs | Standardized telemetry could correlate future provider/workflow spans with CI and Appium runs. | Instrument a local mock provider first; export only approved attributes and test that sensitive payloads are absent. **Future** |
| P95 latency | Tail latency affects CI wait and triage usefulness more than an average alone. | Record end-to-end p50/p95 including retrieval and provider timeouts; compare to the deterministic path and set a project-specific budget. **Planned** |
| Cost per request | Per-call cost is useful but accepted, correct outcomes are more meaningful. | Join token usage and approved pricing with outcome/reviewer labels; report cost per accepted diagnosis and per abstention. **Planned** |
| User feedback loops | Reviewer accept/edit/reject signals can improve prompts, data, and policy but must be governed. | Capture structured feedback with evidence and consent; review labels before adding to a golden set or memory. **Future** |

## 5. AI system design and inference

**Image:** `IMG_2317.jpeg` — 20 concepts.

| Concept | How it relates to this framework | Practical exercise and status |
|---|---|---|
| Model routing | Deterministic rules should handle obvious failures; only ambiguous cases may need a model. | Build a route table from failure category/impact and compare cost, quality, and abstention against one-model-for-all. **Future** |
| Model fallbacks | Provider failure must not change pytest/JUnit results; fallback models may differ in policy or output. | Simulate timeout/rate limit and test explicit AI-unavailable status; if fallback is later approved, re-run schema and safety validation. **Planned** |
| Semantic caching | Similarity-based answer reuse risks stale evidence and cross-scope leakage. | Defer until repeated-request data proves value; prototype with strict tenant, model, prompt, evidence, and policy keys plus freshness checks. **Study** |
| Prefix caching | Stable prompt prefixes may be cached by a provider to save repeated input processing. | Benchmark provider-reported cache use; keep secrets and tenant-specific content out of shared prefixes. **Future** |
| Token budgets | Every run needs bounded input/output and a visible budget-exhausted outcome. | Add per-run budgets to future context/provider contracts; test boundary conditions and report usage. **Planned** |
| Streaming responses | Streaming may improve perceived latency for an interactive UI but complicates partial output validation. | Not needed for current offline CLI/testing. If a review UI is added, stream only drafts; validate the completed structured object before enabling approval. **Future** |
| Time to first token | Useful for interactive applications; not the same as end-to-end workflow latency. | Measure only if an interactive model-backed feature is built; include retrieval and queue time separately. **Study** |
| Throughput vs latency | Higher concurrency may increase queueing, cost, provider throttling, and test-run interference. | Load-test a mock/provider adapter with bounded synthetic requests; choose concurrency from SLO and quotas, not an arbitrary number. **Future** |
| Inference serving with vLLM | A serving engine is relevant if the team self-hosts compatible models; the image label is partly obscured but appears to refer to vLLM. | Compare managed API vs one self-hosted small model only after policy/quality/volume analysis; document GPU, operations, security, and upgrade costs. **Study** |
| Continuous batching | Serving optimization combines concurrent requests to improve accelerator utilization. | Learn via a controlled serving benchmark if operating a model server; it does not belong in the Appium test process. **Study** |
| PagedAttention | Model-serving memory management for KV-cache blocks; an implementation detail of compatible inference infrastructure. | Study and benchmark only when deploying a compatible high-throughput model server. **Study** |
| Speculative decoding | A draft model proposes tokens that a larger model verifies, potentially reducing latency. | Compare latency and quality on representative prompts if self-hosting/serving; likely unnecessary for this project's first AI slice. **Study** |
| GPU vs API cost | Total cost includes engineering, operations, utilization, privacy, and reliability—not only GPU hourly price or token price. | Create a simple workload-based cost sheet with measured request volume, tokens, engineering/support, availability, and data constraints. **Future** |
| Batch inference | Offline evals and document embedding may be batchable, unlike interactive diagnosis. | Batch synthetic evaluations or approved document embedding with resumable IDs and per-item failures; never batch production data without approval. **Future** |
| Async job pipelines | Long-running analysis may need queue/job state, bounded retries, and a pollable result. | Keep current work in-process; prototype a queued job only after latency/concurrency requirements are measured and idempotency is designed. **Future** |
| Provider rate limits | External model calls have quotas and transient errors that must be distinguished from test failure. | Mock 429/5xx/timeouts; implement bounded backoff with jitter and circuit breaking in the future adapter. **Planned** |
| Multi-tenant design | This is currently a repository/framework, not a shared SaaS serving multiple organizations. | Do not add tenancy abstractions prematurely. If service is shared, enforce tenant-scoped identity, retrieval, caches, logs, keys, and deletion with isolation tests. **Study** |
| RAG vs fine-tuning | RAG supplies changing, citable project facts; fine-tuning changes task behavior and requires reviewed training data. | Establish prompt + lexical/RAG baseline first; consider tuning only for a measured persistent behavior gap and approved data rights. **Planned** |
| Context-window management | Context selection, ordering, and compaction affect accuracy and cost. | Test a token-aware context packer that prioritizes current run evidence, retrieved sources, and policy without silently dropping critical fields. **Planned** |
| Cost optimization | Optimize cost per accepted, supported result while preserving privacy and safety. | Start with deterministic routing, compact context, top-k evaluation, one model, bounded retries, and measured cost; add caching or routing only with evidence. **Planned** |

## 6. AI security

**Image:** `IMG_2314.png` — 20 concepts. The separate system-design image is
mapped in Section 5.

| Concept | How it relates to this framework | Practical exercise and status |
|---|---|---|
| Prompt injection | A malicious requirement or failure message could try to change policy or request tools. | Add synthetic direct-injection cases to future capability tests; prove tool authorization is independent of model text. **Planned** |
| Indirect prompt injection | Gherkin, logs, page source, screenshots, and retrieved docs are untrusted content. | Mark evidence as data, not instruction; test malicious text embedded in each source and verify it cannot trigger a tool or leak data. **Planned** |
| Jailbreaks | Prompt-only refusal behavior is not a security control. | Test a threat-model-derived adversarial suite and enforce policy outside the model; record refusal and bypass outcomes. **Future** |
| OWASP Top 10 for LLMs | A useful threat checklist for risks such as injection, data exposure, unsafe output, supply chain, and excessive agency. | Map relevant risks to project controls/tests in the canonical security plan; do not claim a checklist equals certification. **Planned** |
| Input guardrails | Inputs need size/type validation, classification, redaction, and scope checks before model/retriever boundaries. | Test oversized, malformed, secret-like, unsupported, and cross-run inputs in the context builder. **Planned** |
| Output validation | A valid JSON response may still cite unknown evidence or propose an unsafe action. | Validate schema, allowed IDs, policy, sizes, and deterministic business constraints; reject invalid output explicitly. **Planned** |
| PII redaction | Screenshots, logs, and user-entered test data may contain sensitive values. | Add test cases for known synthetic secret/PII patterns and verify redaction before provider/log/trace boundaries; never log raw values. **Planned** |
| Data leakage | Cross-run exposure, prompt echo, traces, and provider retention are material risks. | Document data flow/retention; use synthetic data until approved; test scope boundaries and inspect sanitized artifacts. **Planned** |
| Least-privilege tools | Agent identities should read only the specific run/repository data needed. | Define per-tool permissions and tests for denied run IDs, repositories, environments, and actions. **Planned** |
| Tool sandboxing | Generated code and broad shell/device actions must not execute in the CI control plane. | Keep tools named and read-only; any future generated artifact runs in a disposable, restricted worker with no production credentials. **Planned** |
| Secrets management | The repo already uses environment-backed configuration for automation credentials; AI secrets are not present/implemented. | Reuse managed secret injection for any approved provider; scan prompts, fixture files, traces, and logs for leaks. **Foundation** |
| API key rotation | Provider keys must be revocable and rotated without code changes. | Use a managed store and documented rotation test; the supplied reference folders have included credential-like samples, so rotate exposed values and do not copy them. **Planned** |
| Authorization for agents | Identity and server-side policy—not system prompts—must authorize each tool call. | Implement policy checks at the internal registry and test role/run scope; deny by default. **Planned** |
| Human approval for actions | Locator updates, Jira changes, reruns, or device actions have external effects. | Add explicit proposal/review/approved/rejected states and immutable audit records; no agent self-approval. **Planned** |
| Content moderation | The product/task may need policy checks for harmful or disallowed generated content; it is not a universal substitute for validation. | Define task-specific cases and escalation behavior; keep moderation separate from factuality, safety, and QA verdict checks. **Future** |
| Data poisoning | Malicious or poor-quality docs/labels can corrupt retrieval and evaluation. | Restrict corpus writers, preserve provenance/review, scan changes, version indexes, and test poisoned instructions in retrieved content. **Planned** |
| Access control in RAG | Retrieval must apply source permissions before content reaches a model, including caches and citations. | Include access metadata and negative cross-scope retrieval tests before indexing any non-public corpus. **Planned** |
| MCP server trust | A malicious or misconfigured server can expose data or accept unsafe operations. | Use approved server allowlists, authenticated identity, capability review, pinned dependencies, and read-only tool defaults. **Planned** |
| Audit logging | Actions and decisions need traceable IDs without recording sensitive payloads. | Log actor, run/tool IDs, permission result, evidence reference, decision, time, and redacted outcome; test log redaction and retention. **Planned** |
| Red teaming | Adversarial testing should cover the actual tools, context sources, identities, and failure modes. | Build an authorized synthetic red-team suite for injection, exfiltration attempts, cross-run access, tool abuse, and denial-of-wallet; track remediation. **Future** |

## 7. Backend and API engineering

**Image:** `IMG_2316.png` — 20 concepts. The current repository is an
automation framework, not an AI web service or application backend. These
topics become relevant if you build a separately deployable AI-analysis API,
evaluation service, or web/API adapter.

| Concept | How it relates to this framework | Practical exercise and status |
|---|---|---|
| REST APIs | Could expose a future analysis job or report endpoint, but no AI API exists today. | After the offline capability works, optionally wrap it in a small FastAPI service with explicit contracts and no direct device control. **Future** |
| HTTP and status codes | Clients need to distinguish invalid input, unauthorized access, accepted async work, provider failure, and internal errors. | Add contract tests for 2xx/4xx/5xx semantics in an optional service; never return a success-shaped response for an AI/provider failure. **Future** |
| Async and await | Async can improve I/O concurrency for providers/HTTP, but Appium and current tests have their own lifecycle. | Keep current synchronous framework unchanged; make a separate async provider experiment with explicit timeout/cancellation and cleanup. **Future** |
| Streaming with SSE | Server-sent events can stream progress from a long-running analysis service to a UI. | Only add for a real interactive consumer; stream progress/status, not partial unvalidated diagnoses or secrets. **Study** |
| WebSockets | Bidirectional communication may support live control/status but is unnecessary for current offline analysis. | Prefer ordinary request/job polling or SSE first; prototype WebSockets only for a demonstrated bidirectional requirement. **Study** |
| Authentication with JWT | JWTs can carry signed identity/claims but are not automatically authorization. | For an optional API, validate issuer, audience, expiry, signature, and scopes with an identity provider; never hand tokens to an LLM. **Future** |
| OAuth 2.0 | Delegated service/user access can scope future Jira/GitHub or AI-service operations. | Start with read-only scopes and managed identities; test token expiry, revocation, project allowlists, and write denial. **Future** |
| SQL vs NoSQL | Evaluation metadata and workflow state may be relational; document/vector content has different needs. | Compare local JSONL/SQLite experiments with a durable database only after querying, retention, access, and concurrency needs are clear. No database-backed AI state exists in this project. **Study** |
| Database indexing | Run/evaluation lookup by run, scenario, version, or timestamp may need indexes at scale. | If persistence is introduced, profile real query plans and add indexes from measured access patterns; do not index hypothetical workloads. **Future** |
| Transactions and ACID | Approval state, job state, and audit events may need atomic updates in a service. | In a disposable SQLite/PostgreSQL lab, test atomic approval+audit writes and rollback; never let a partial write appear approved. **Future** |
| Caching with Redis | Could support shared rate limits, job coordination, or short-lived cache; current tests use no Redis. | Add only after measured multi-worker needs; define TTL, key scope, invalidation, and outage behavior before production use. **Study** |
| Message queues | Useful for durable async analysis jobs and backpressure, not needed by a local single-run workflow. | Prototype a queue only after job volume/SLOs require it; ensure bounded retries, dead-letter handling, and idempotent consumers. **Study** |
| Background jobs | Long reports/evaluations may run independently from an HTTP request. | Separate job lifecycle: queued/running/succeeded/failed/cancelled, with durable IDs and safe resume. **Future** |
| Rate limiting | Protects provider budgets and future API/MCP endpoints from overload or abuse. | Add per-identity and per-run limits in any service; test 429 behavior and ensure retries do not amplify overload. **Planned** |
| Idempotency keys | Prevent duplicate external effects if a client retries a request after timeout. | Require idempotency before any future Jira write, rerun dispatch, or queued job creation; test duplicate submissions. **Planned** |
| Retries with backoff | Transient network/provider faults can recover; business/schema failures generally should not be retried unchanged. | Use small bounded exponential backoff with jitter for classified transient errors; test retry budget and visible terminal failure. **Planned** |
| File uploads to S3 | Screenshots/reports may use object storage in a hosted service; current artifacts stay in CI/local paths. | If external storage is approved, use scoped short-lived upload URLs, encryption, retention/deletion, content limits, and malware scanning. **Future** |
| Pagination | Run history, evaluation cases, and tool results should be bounded rather than returned as unbounded lists. | Add cursor/limit contracts to any future API; test stable ordering, maximum page size, authorization, and no cross-run records. **Future** |
| Input validation with Pydantic | Project currently has no Pydantic runtime dependency; typed request validation is proposed for the AI boundary. | Add only with a real contract; validate types, size, enums, IDs, and cross-field rules, then test invalid and adversarial values. **Planned** |
| Logging and monitoring | pytest/Allure/GitHub Actions provide existing test evidence, not AI service observability. | Add structured, redacted logs and health/error metrics to any optional service; correlate to test run IDs and separate AI status from test verdict. **Planned** |

## 8. Deployment and operations

**Image:** `IMG_2318.jpeg` — 20 concepts.

| Concept | How it relates to this framework | Practical exercise and status |
|---|---|---|
| Docker | Can package a future stateless AI service or reproducible eval runner; the existing Appium/device stack adds separate runtime requirements. | First containerize a small offline evaluator or provider mock, not the whole mobile/device toolchain. Pin base image and scan it. **Future** |
| Docker Compose | Useful for a local service + optional database/trace stack during development. | Build a disposable local lab only after those components exist; use synthetic data, health checks, and no committed secrets. **Future** |
| Kubernetes basics | Relevant to multi-service scale/availability, not a prerequisite for learning or a single QA workflow. | Learn deployments, services, config/secrets, probes, resource requests, and rollout concepts in a toy environment; do not deploy this project there without need. **Study** |
| CI/CD pipelines | GitHub Actions already runs deterministic project checks and device workflows; there is no AI-eval/model delivery pipeline. | Add offline AI contract/eval tests to CI when implemented; never require paid provider calls for ordinary unit CI. **Foundation** |
| GitHub Actions | Existing workflow infrastructure is a practical place for lint, tests, BDD discovery, and later offline eval gates. | Add a synthetic evaluation job after a reviewed corpus exists; publish sanitized artifacts and separate its status from device lane results. **Foundation** |
| Eval gates in CI | No AI evaluation gate exists today. | Gate prompt/retrieval/model changes with deterministic schemas, golden cases, security tests, and agreed thresholds; maintain a no-network mode. **Planned** |
| Environment configs | Existing QA/stage properties and environment-backed settings are a foundation; AI provider/model configs do not exist. | Add typed, non-secret model/prompt/feature-flag configuration only when a provider exists; fail explicitly on invalid environment. **Foundation** |
| Infrastructure as Code | Not needed for the current framework; may become relevant for hosted model services, databases, or telemetry. | Learn by describing one optional sandbox environment as code, including least privilege, secret references, logging, and teardown. **Study** |
| Serverless functions | Could handle isolated low-volume event/report tasks, but may have runtime, timeout, and dependency constraints. | Compare a serverless job with a container/queue using measured duration and data policy; avoid making Appium execution serverless by assumption. **Study** |
| GPU instances | Required only when serving/training selected models locally; creates cost, capacity, and operational work. | Price and benchmark a small approved workload before requesting GPU capacity; compare utilization and total cost with a provider API. **Study** |
| Ollama for local models | A developer-local learning option for some open models, not installed or production-configured here. | Use only synthetic cases for a local provider adapter experiment; evaluate model capability, license, privacy, performance, and reproducibility. **Study** |
| Autoscaling | A future service concern based on demand, queue depth, latency, and quota. | Simulate load and define scaling signals/limits before configuring autoscaling; avoid unbounded scaling that creates runaway model cost. **Study** |
| Load balancing | Routes service requests across healthy instances; irrelevant to the current single-process test framework. | Add only if a hosted service has multiple replicas; preserve auth context, health, rate limits, and trace correlation. **Study** |
| Canary releases | Gradual rollout can expose a prompt/model change to a small, monitored cohort. | First compare offline; then shadow/canary only with approved data and rollback thresholds. AI output must remain non-blocking until proven. **Future** |
| Feature flags | Can enable/disable future AI analysis independently from deterministic tests. | Add a default-off feature flag when AI runtime is introduced; test disabled, unavailable, and rollback paths without changing test verdicts. **Planned** |
| Prompt versioning | Prompt changes are behavior changes and need review/evaluation. | Store prompt templates/version/hash with outputs; make the golden evaluation compare current and candidate versions. **Planned** |
| Model versioning | Provider aliases may change behavior; a model/version must be recorded for reproducibility. | Pin explicit model identifiers where available; record provider/version and rerun evals before upgrade. **Planned** |
| Health checks | Existing workflows check code/build/test readiness; no AI provider health or AI service exists. | Add liveness/readiness separately from model availability; provider outage should report AI unavailable without blocking normal Appium tests. **Planned** |
| Alerts and dashboards | No AI quality/cost dashboard exists; current CI and Allure show deterministic results. | Alert on provider errors, budget exhaustion, evaluation regression, redaction failures, and false-heal reports after telemetry is approved. **Future** |
| Rollbacks | Prompt, model, index, tool, or policy rollout should have a known safe prior version. | Keep versioned artifacts and a tested rollback path; revert an AI release without reverting Appium or altering historical verdicts. **Planned** |

## Suggested practical build sequence

Follow the canonical phase tracker in the
[AI Implementation Plan](AI_IMPLEMENTATION_PLAN.md); this sequence is a
learning view of that plan:

1. **Understand the deterministic host:** trace a pytest-BDD scenario through
   page object, driver, locator resolution, JUnit/Allure, and GitHub Actions.
   Deliver a diagram and a repeatable baseline.
2. **Build offline AI contracts:** validate the existing synthetic fixture,
   add typed run/evidence/failure schemas, redaction, a deterministic failure
   classifier, and explicit unknown/abstain states. Deliver unit tests and a
   case-level report without a network or model key.
3. **Add controlled tools and reporting:** expose read-only run/evidence
   functions; enforce scope, schema, output caps, and audit. Build a report
   whose totals exactly match pytest/JUnit.
4. **Create evaluation discipline:** human-review labels, golden set,
   confusion matrix, evidence/citation correctness, abstention, and failure
   analysis. Add offline evaluation to CI before a provider call.
5. **Learn retrieval:** lexical BM25 baseline first, then embeddings/vector
   retrieval only if the query set demonstrates a gap. Record source versions,
   metadata filters, citations, Recall@k, MRR/nDCG, and latency.
6. **Add one model provider:** use a typed adapter, approved synthetic inputs,
   prompt/version tracking, budgets, timeouts, and explicit unavailable/error
   states. Compare to the deterministic baseline.
7. **Add an agent workflow only for a measured need:** start with a bounded
   supervisor and one capability. Add an MCP adapter only after tool contracts
   and policy tests pass; require review for all state-changing actions.
8. **Operationalize selectively:** add tracing, service APIs, containers,
   queues, local inference, or scaling only when data policy, workload, and
   measured SLOs justify them.

### Evidence for practical mastery

For each project milestone, keep a short engineering note with:

- The question/problem and the relevant concept(s).
- A diagram or code path in this framework that demonstrates the concept.
- The deterministic baseline and expected behavior.
- Tests for success, invalid input, ambiguity, timeout, and unauthorized use.
- Measured quality, cost, and latency results, including a failure example.
- The design decision, alternative rejected, reason, and next learning goal.

This gives you credible subject-matter depth: you can explain the concept,
show where it lives in the implementation, reproduce its behavior, interpret
its failure modes, and defend when not to use it. It does not imply mastery
merely because a tool is named in a roadmap.

## Source inventory

| Image | Area | Mapping |
|---|---|---|
| `IMG_2309.jpeg` | LLM | Section 1 |
| `IMG_2310.jpeg` | RAG | Section 2 |
| `IMG_2311.jpeg` | AI Agents | Section 3 |
| `IMG_2312.png` | Evals | Section 4 |
| `IMG_2314.png` | AI Security | Section 6 |
| `IMG_2316.png` | Backend | Section 7 |
| `IMG_2317.jpeg` | AI System Design | Section 5 |
| `IMG_2318.jpeg` | Deployment | Section 8 |

Image wording is treated as a topic prompt. For the partly
obscured inference-serving label in `IMG_2317.jpeg`, this guide uses the likely
reference to vLLM and marks it as an interpretation rather than a verified
project dependency.

## Related documentation

- [AI Implementation Plan](AI_IMPLEMENTATION_PLAN.md) — canonical project AI
  status, work order, governance, and acceptance criteria.
- [AI Architect / SDET Practical Roadmap](AI_ARCHITECT_SDET_PRACTICAL_ROADMAP.md)
  — staged learning sequence and portfolio milestones.
- [Unified Mobile Automation Architecture](UNIFIED_MOBILE_AUTOMATION_ARCHITECTURE.md)
  — current execution authority, boundaries, and future integration points.
- [AI Automation Interview Guide](AI_AUTOMATION_INTERVIEW_GUIDE.md) — concise,
  evidence-grounded AI interview questions and answers.
- [Automation Framework Interview Guide](AUTOMATION_FRAMEWORK_INTERVIEW_GUIDE.md)
  — deterministic framework, mobile, web/API, and CI interview topics.
