# AI for Automation and Quality Engineering: Interview Guide

## How to use this guide

Use the answers as evidence-led speaking points, not scripts. Tailor the depth
to the role and support claims with a design, test, metric, or reviewed
prototype. Distinguish **implemented**, **evaluated**, **deployed**, and
**planned** capabilities.

The current repository is a deterministic Python 3.14, pytest-BDD, and Appium
framework. It has no production LLM, agent, RAG, MCP, AI evaluation, or
self-healing runtime. Its drivers, page objects, locator catalog, Allure
evidence, GitHub Actions, and synthetic starter cases are foundations, not
implemented AI. The separate EventHub, Postman, skills, images, and AutoGen
folders supplied for this review are reference material; they are not part of
this repository's runtime.

For framework design, mobile/web/API execution, and test engineering questions,
use the separate [Automation Framework Interview Guide](AUTOMATION_FRAMEWORK_INTERVIEW_GUIDE.md).

## Quick navigation

- [AI fundamentals](#1-ai-product-and-system-fundamentals)
- [AI for test engineering](#2-ai-applied-to-test-engineering)
- [Retrieval and grounding](#3-retrieval-and-knowledge-grounding)
- [Agents, tools, and protocols](#4-agents-tools-orchestration-and-protocols)
- [Evaluation and operations](#5-evaluation-observability-and-model-operations)
- [Security and leadership](#6-security-delivery-and-leadership-scenarios)
- [Applied source topics](#7-applied-questions-from-the-supplied-reference-set)
- [Out-of-scope alternatives](#8-out-of-scope-capabilities-and-closest-alternatives)

## 1. AI product and system fundamentals

### AI-01. What problem should AI solve in an automation framework?
**Answer:** I would target expensive, language-heavy work such as turning
approved requirements into reviewable test drafts, retrieving relevant
framework knowledge, and explaining failures from evidence. I would not use an
LLM to decide whether an assertion passed, replace deterministic validation,
or run unrestricted device actions.

### AI-02. How do you distinguish AI, generative AI, an agent, and an agentic workflow?
**Answer:** AI is the broad field; generative AI creates content; an agent can
select tools toward a bounded goal; an agentic workflow adds state, routing,
limits, and approval. A deterministic workflow that invokes one model at one
step can be more reliable and cheaper than a multi-agent system.

### AI-03. How does an LLM produce an answer, and why can it be wrong?
**Answer:** An LLM predicts token sequences from its input and learned
parameters. Tokenization affects how text uses the context window and budget;
embeddings can represent semantic similarity for retrieval, but do not prove
truth. Transformer attention weighs relationships among tokens; it does not
verify facts either. I ground outputs in approved evidence and validate them
independently.

### AI-04. What is the difference between prompting and context engineering?
**Answer:** A prompt gives instructions and a task; context engineering selects,
labels, orders, redacts, and bounds the evidence needed for that task. For
failure analysis, I would send the failed step, exception family, platform,
locator key, and authorized evidence references—not a full repository dump.

### AI-05. How do you separate instructions, project knowledge, context, memory, and cache?
**Answer:** Instructions define reviewed behavior and policy; project
knowledge holds versioned stable facts; runtime context is evidence for one
task/run; operational memory is a curated, governed continuity feature; cache
reuses a computation and must expire or invalidate. A screenshot from today's
failure is context, not durable memory.

### AI-06. How do you reduce hallucinations?
**Answer:** I use an approved corpus, source IDs, typed outputs, deterministic
validation, explicit uncertainty, and abstention when evidence is missing.
Schema validity proves only shape, and a citation proves only that a source
was referenced; neither alone proves a claim is correct.

### AI-07. When would you use an LLM rather than ordinary code?
**Answer:** I use ordinary code for parsing JUnit, counting results,
authorization, selector validation, and exact business assertions. I use an
LLM for bounded synthesis or classification where language variation matters,
such as summarizing conflicting failure evidence. I compare both against a
baseline before adding a model.

### AI-08. How do you select a model or provider?
**Answer:** I compare task quality, structured-output support, privacy and
residency terms, availability, latency, cost, rate limits, and operational
support using the same reviewed evaluation set. I put provider-specific SDKs
behind an interface and pin the model version; I do not select by benchmark
rank or popularity alone. A local or smaller model is an option when policy,
offline use, latency, or measured cost justifies its hosting and quality
trade-offs. Quantization or specialized serving is relevant only when we own
that inference layer and have a measured need.

## 2. AI applied to test engineering

### AI-09. How would you generate test scenarios from requirements?
**Answer:** I retrieve the approved requirement and business rules, draft
scenario records with requirement IDs, preconditions, steps, expected results,
priority, and suggested test layer, then validate the schema and source links.
A reviewer edits or rejects the draft before it becomes executable.

### AI-10. Why should an LLM generate a test plan instead of test code?
**Answer:** A typed test-plan format is reviewable and language-neutral. A
deterministic compiler or human then maps approved cases to existing steps and
page/API operations. This avoids executing arbitrary model-generated code and
makes changes diffable and auditable.

### AI-11. How do you ensure generated tests are traceable?
**Answer:** Every case must cite an approved requirement, rule, or discovered
behavior and retain stable IDs through design, execution, and report. If the
source is missing or contradictory, the generator should mark the case
unresolved instead of inventing expected behavior.

### AI-12. How can AI help with test data?
**Answer:** It can propose boundary and combinatorial cases or synthetic data
that conforms to a validated schema. A deterministic generator should create
unique values and enforce constraints. I never send real credentials or
personal data to a model or use a generated value as an authorization
credential.

### AI-13. How can AI help prioritize regression tests?
**Answer:** First establish deterministic signals: changed modules, dependency
graph, prior failures, criticality, and platform coverage. A model may explain
or rank candidates, but selection must be evaluated for missed critical tests
and compared with running the full required gate. It cannot silently skip a
mandatory test.

### AI-14. How would you classify a failed test?
**Answer:** I start with deterministic categories such as product/assertion,
test-or-locator, app/device/environment, infrastructure/provider, and
unknown. A model can propose a cause with evidence IDs and confidence. The
report preserves the test result and exposes unknown or conflicting evidence
for review.

### AI-15. What is useful in an AI post-run report?
**Answer:** Machine results supply authoritative totals. The report adds
failure group, cited scenario/step/evidence, uncertainty, probable owner, and
recommended next action. It labels facts separately from hypotheses and does
not turn a failing run into a pass. A reproducible bundle also records the
source revision, test and evidence IDs, sanitized artifacts, and model,
prompt, or dataset versions when those were actually used.

### AI-16. How do you detect flaky tests with AI?
**Answer:** I first collect first-attempt, retry, duration, device, build,
environment, and error-family history. Deterministic rules identify repeated
patterns; an LLM may summarize them. A retry pass remains a recovered/flaky
outcome, not a clean first-attempt pass, and no diagnosis is accepted without
the underlying run evidence.

### AI-17. What does safe self-healing mean?
**Answer:** It is a locator-change proposal after a confirmed locator failure,
not an automatic pass. The system can rank trusted candidates, then
deterministic checks verify platform, uniqueness, visibility, and expected
context. A person approves the patch; the original assertion and targeted
regression still run.

### AI-18. When is screenshot or multimodal analysis useful?
**Answer:** It can help explain visual layout or ambiguous UI state, but I
prefer accessibility hierarchy, DOM, resource IDs, and logs for precise
evidence. Images need authorization, redaction, retention controls, and a
human-readable artifact link; visual similarity alone cannot prove business
correctness.

## 3. Retrieval and knowledge grounding

### AI-19. What is RAG, and when would you use it?
**Answer:** Retrieval-augmented generation finds relevant approved sources at
request time and supplies them to the model. I would use it to ground answers
in versioned test conventions, feature rules, locators, and sanitized
runbooks. It is not required for the first offline classifier or a small,
well-defined prompt.

### AI-20. RAG versus fine-tuning: which comes first?
**Answer:** RAG is usually the better first choice for facts that change and
need citations. Fine-tuning changes model behavior and needs a lawful,
reviewed dataset and a measured gap that prompting/RAG cannot address. Neither
is a substitute for application authorization.

### AI-21. How would you build a safe RAG corpus?
**Answer:** Ingest only approved sources; retain source path, commit/version,
owner, access class, platform, and effective date; remove secrets and
irrelevant data; and apply access filters at retrieval time. Deletion or
permission changes must propagate to indexes and caches.

### AI-22. How do you choose chunking and metadata?
**Answer:** I chunk on semantic boundaries such as a test rule, endpoint, or
runbook section, preserve headings and stable source offsets, and attach
version/access metadata. I tune chunk size against a reviewed query set rather
than assuming a universal token size.

### AI-23. When do you use hybrid search or reranking?
**Answer:** Lexical search is strong for exact test IDs, exception names, and
endpoint paths; vector search helps paraphrases. I add hybrid retrieval and
then reranking only when evaluation shows a measurable recall or ranking
problem worth the latency, cost, and operational complexity.

### AI-24. How do you evaluate retrieval?
**Answer:** I use human-reviewed queries and relevant-source labels to measure
recall@k, precision@k, ranking quality, citation correctness, stale-source
rate, and latency. I review misses separately from generation errors and
include access-control tests.

### AI-25. How would you implement agent memory safely?
**Answer:** I would begin without persistent memory. If continuity proves
valuable, store typed, scoped records with provenance, owner, status, review
date, expiry/supersession, and deletion. Only an authorized review path can
write memory; retrieved text or a model response never writes itself.

### AI-26. How is cache different from memory?
**Answer:** Cache optimizes repeated work and can be discarded; memory is
curated knowledge meant to influence a later task. Cache keys need model,
prompt, evidence, corpus, and policy versions where relevant. Neither may
cross access scopes, and stale cached output never outranks current source
evidence.

## 4. Agents, tools, orchestration, and protocols

### AI-27. What agents would you build for QA?
**Answer:** I would keep evidence collection, policy checks, output
validation, report arithmetic, and test execution deterministic. A bounded
failure analyst or test-design analyst can use an LLM when needed. A
supervisor routes work, and a human approves consequential changes.

### AI-28. When is multi-agent architecture justified?
**Answer:** Only when independently useful roles, permissions, or workflows
need separation and measured collaboration improves outcomes. I first compare
a deterministic single-agent workflow with a multi-agent baseline; extra
agents otherwise add latency, token cost, failure modes, and harder debugging.

### AI-29. How do you bound an agent's execution loop?
**Answer:** I define typed state, allowed transitions, turn/tool/time budgets,
approval pauses, and terminal states before selecting an orchestration
library. Timeout, malformed output, denied tools, and provider outage must end
in a visible error, abstention, or human review—not another unbounded retry.

### AI-30. What is your AutoGen versus Microsoft Agent Framework decision?
**Answer:** The supplied AutoGen examples illustrate assistant/team,
multimodal, web, and MCP workbench patterns; they are not production
integrations. AutoGen is archived, so the project plan recommends a
compatibility spike for Microsoft Agent Framework (MAF) before a production
choice. I keep orchestration behind project contracts and do not claim either
runtime is installed here.

### AI-31. How do you choose an orchestration or AI integration framework?
**Answer:** I start with plain Python. LangChain is an integration layer for
models/tools/retrieval, LangGraph supports stateful graph workflows, MAF is
the proposed Microsoft orchestration candidate here, and LangFlow can help
prototype visually. They are not interchangeable. I compare only candidates
that solve a demonstrated need, run a compatibility spike, and select one
production orchestrator; graph features are justified by routing,
checkpoint/resume, or approval requirements, not by framework popularity.

### AI-32. What is a tool contract?
**Answer:** It is a named operation with a typed input/output schema,
validation, permission, timeout, size limit, error semantics, and audit event.
For example, `get_run_summary(run_id)` is safer than exposing shell access or
arbitrary filesystem reads.

### AI-33. What is MCP, and what does it not do?
**Answer:** MCP standardizes how compatible clients discover and call tools
or resources. It does not automatically authenticate a user, authorize a
request, sanitize data, or make a tool safe. The server and application must
enforce identity, allowlists, limits, and audit.

### AI-34. How do MCP, REST APIs, and agent-to-agent protocols differ?
**Answer:** REST is an application integration style; MCP provides a
standardized model-context tool/resource interface; agent-to-agent protocols
support communication between agent systems. I use the simplest contract that
solves the integration. A protocol never replaces business authorization.

### AI-35. How would you scope MCP servers?
**Answer:** I would start with read-only knowledge and run-evidence tools,
then add CI or test-management read access only if needed. Write actions use a
separate identity and server, explicit confirmation, idempotency, and audit.
No generic shell, arbitrary URL, all-device-control, or broad database tool is
exposed. The supplied REST/SQL/spreadsheet workbenches are examples to study,
not trusted services or current project integrations.

### AI-36. What are skills, and are they agents?
**Answer:** A skill is reusable task guidance and domain knowledge, such as
scenario-design lenses or Playwright conventions. It can instruct an agent
what process to follow, but it is not an executable permission boundary.
Authorization and validation remain in code and service identity policy. The
supplied skills can inform a draft-and-review workflow; they do not prove that
the framework has those agents or tool permissions installed.

### AI-37. How do you handle long-running work and recovery?
**Answer:** I persist only minimal, versioned workflow state and artifact
references, use explicit checkpoints for approval or resume, and make
repeated tool operations idempotent where possible. Resume revalidates
authorization, evidence freshness, and budgets instead of blindly replaying
old state.

## 5. Evaluation, observability, and model operations

### AI-38. What does a good AI evaluation strategy look like?
**Answer:** It has a versioned, human-reviewed golden set; deterministic
schema and policy checks; task-specific quality measures; adversarial cases;
and an offline CI gate. Model-judge scores are calibrated against human
labels and never serve as the only oracle. Libraries such as DeepEval or
RAGAS can help measure selected LLM/retrieval behaviors, but they do not
provide ground truth. For user-facing tasks, include relevant safety,
fairness, and harmful-output checks in the evaluation design.

### AI-39. How do you evaluate generated test plans?
**Answer:** I measure requirement coverage and traceability, valid
preconditions/steps/assertions, duplicate and unsupported cases, risk-layer
appropriateness, and reviewer accept/edit/reject outcomes. I compare against a
human baseline and check that critical negative/security cases are not omitted.

### AI-40. How do you measure failure-analysis quality?
**Answer:** I track per-category precision/recall and confusion matrix,
evidence support, unsupported-claim rate, calibrated confidence, abstention
quality, false confident diagnoses, reviewer correction, and downstream
triage time. Overall agent completion rate is not a quality metric by itself.

### AI-41. What belongs in an LLM/agent test harness?
**Answer:** Deterministic fake-model tests cover output contracts, policy,
tool permissions, state transitions, budgets, timeouts, retries, injection,
and resume behavior. A separately marked provider test checks the live SDK
integration; the ordinary unit suite must not depend on network access or
model judgment.

### AI-42. What is LLM observability?
**Answer:** It is correlated, redacted tracing of run/agent/tool steps, model
and prompt versions, validation outcomes, latency, token usage, errors, and
review decisions. LangSmith or Langfuse may be selected later; neither is
currently implemented, and raw evidence should not be uploaded without
approval.

### AI-43. How do you handle model upgrades?
**Answer:** A model change is a behavior migration. I pin exact model and
prompt versions, run old/new against the same golden and adversarial cases,
diff outputs and tool behavior, review token and latency changes, then use a
small canary with rollback criteria. A version bump alone is not validation.

### AI-44. Which metrics are meaningful to leaders?
**Answer:** I report useful, auditable outcomes: diagnosis acceptance and
correction, escaped/false-heal indicators, triage time, evidence completeness,
latency, provider/tool reliability, and cost per accepted diagnosis. I
establish a baseline and avoid unmeasured ROI or accuracy claims.

### AI-45. How do you reduce token and model cost?
**Answer:** Route deterministic cases without a model, send compact
failure-specific context, retrieve a small evaluated top-k, use one suitable
model tier, cap output and tool calls, cache only safe versioned results, and
avoid agent fan-out. I measure cost per accepted outcome rather than optimize
tokens in isolation.

### AI-46. How should the test pipeline behave when a model provider fails?
**Answer:** The AI annotation should end in an explicit unavailable or error
state after bounded handling of transient faults. Pytest/JUnit execution and
its CI verdict continue independently; provider or tracing outages must not
convert test failures to passes or block the deterministic test lane.

## 6. Security, delivery, and leadership scenarios

### AI-47. How do you defend against prompt injection in app text or logs?
**Answer:** Treat page source, issue text, logs, retrieved documents, and
screenshots as untrusted data. Keep policy outside them, delimit and label
content, expose only allowlisted tools, validate every call in application
code, and test attacks that try to override system instructions or exfiltrate
data.

### AI-48. How do you protect privacy and secrets?
**Answer:** Classify inputs, minimize and redact fields before model/trace
boundaries, keep credentials in a secret manager, use least-privilege
identities, and set retention/deletion and provider-training terms. I do not
put real credentials, tokens, or unnecessary personal data in prompts,
fixtures, screenshots, memory, or reports.

### AI-49. How do you govern risky actions?
**Answer:** Keep model tools read-only initially. Jira writes, locator edits,
test reruns, code changes, and device actions require a separately authorized,
visible approval with arguments, evidence, identity, result, and timestamp.
The agent cannot approve itself or change the test verdict.

### AI-50. How do you release a model-backed feature safely?
**Answer:** I version the prompt, model, retrieval index, and policy; pass
offline evaluations and security checks; then use a non-blocking shadow or
small canary with explicit rollback thresholds. Provider/model services need
health monitoring, bounded concurrency, managed secrets, and artifact access
controls. Deployment should never gate or rewrite the deterministic test
verdict on its own.

### AI-51. How would you demonstrate this to leadership?
**Answer:** I would show one end-to-end case: requirement and source evidence,
a reviewable test draft or failure diagnosis, deterministic execution, cited
evidence, explicit human decision, and a measured report. I would also show an
ambiguous or injected case where the system abstains, and disclose which
capabilities are still planned.

### AI-52. What would you build first in this repository?
**Answer:** I would build offline contracts, redacted run context, read-only
evidence tools, a deterministic failure classifier, and a report whose totals
match pytest/JUnit. Only after evaluation and data approval would I add one
model provider, retrieval, workflow orchestration, or a proposed locator
repair.

## 7. Applied questions from the supplied reference set

### AI-53. How can AI help classify tests as trusted, review, refactor, or retire?
**Answer:** It can combine ownership, requirement links, assertion strength,
failure history, flakiness, duplicate behavior, and change impact to recommend
a status. Deterministic rules and owners validate the evidence; the model
does not delete tests or downgrade required release coverage automatically.

### AI-54. What does BMAD-style reporting add to an AI engineering workflow?
**Answer:** It organizes reviewed delivery evidence into artifacts such as a
brief, requirements, architecture decision, implementation story, test
strategy, risk log, and post-run report. In this repository it is a
documentation practice, not an installed BMAD product; generated text is
reviewed and linked to source evidence.

### AI-55. How would you use the supplied EventHub and API materials as AI test inputs?
**Answer:** I would treat them as separate web/API reference systems and
build a sanitized evaluation corpus from reviewed business rules, source
behavior, API contracts, and expected test-plan fields. I would record
provenance and resolve conflicting claims against the active source of truth.
Sample accounts, database rows, or Postman variables are neither evaluation
labels nor approved credentials.

## 8. Out-of-scope capabilities and closest alternatives

These are scope boundaries for the **current executable repository**, not
claims that the concepts have no future value. The alternatives help explain
the same engineering goal while keeping the implementation status honest.

| Not currently in the executable scope | Closest implemented or supplied alternative | What is not equivalent / remains out of scope |
|---|---|---|
| LLM-based test planning, failure analysis, and autonomous agents | Deterministic pytest/Appium execution, existing Allure evidence, and the synthetic offline cases in `tests/fixtures/ai_qa/starter_cases.json` | Fixtures exercise data contracts; they do not call a model, evaluate model quality, or provide an agent runtime |
| RAG, vector database, and persistent agent memory | Version-controlled project documentation and synthetic fixtures provide reviewable facts for people and offline tests | No runtime semantic retrieval, vector index, or governed operational-memory store exists |
| AI self-healing and visual interpretation | `mobile_test_automation/services/locator_logic.py` resolves known platform-specific locator keys; screenshots/video can be attached through `mobile_test_automation/services/reporting.py` | Locator resolution is strict, not a repair recommendation; media is evidence, not AI vision or visual regression |
| MCP servers and agent tool execution | Existing pytest/CI boundaries are extension points; the implementation plan proposes an internal typed tool registry before MCP exposure | No MCP server, tool authorization service, or model-triggered action is implemented |
| LLM trace, cost, and quality dashboards | GitHub Actions logs plus pytest/Allure results provide deterministic run status and test evidence | They do not measure model tokens, spend, retrieval quality, or agent behavior |
| AI-generated Jira tests or automatic test-management updates | `scripts/generate_general_store_test_plan.py` creates a Jira-import-oriented manual test workbook; synthetic cases support offline examples | Workbook generation is not AI generation, a Jira API integration, or a model evaluation dataset |
| AI across browser, API, and mobile channels | The supplied EventHub, Playwright, Postman, and MCP materials offer separate reference patterns; current Appium BDD flows cover mobile behavior | Those references are not connected to this repository; no browser/API execution or cross-channel AI workflow is present |

When presenting these alternatives, describe them as the **nearest current
analogue**, not as partial AI delivery. The detailed implementation order and
future acceptance gates remain in the [AI implementation plan](AI_IMPLEMENTATION_PLAN.md).

## Source-coverage index

| Supplied source | Covered areas |
|---|---|
| 34 images | AI fundamentals; test generation and validation; agent roles/orchestration; MCP; RAG and embeddings; multimodal UI evidence; self-healing; evaluation; cost; observability; security; deployment and leadership demonstration |
| Existing AI implementation and SDET roadmaps | Project status, MAF/AutoGen decision, phase order, BMAD, governance, memory/context/cache, and evidence-based interview framing |
| AutoGen prototype | Assistant/team patterns, multimodal/web examples, MCP workbenches, and prototype-versus-production boundaries |
| Supplied skills | Domain grounding, scenario-design lenses, test-strategy mapping, generation/review workflow, and the distinction between skills and tool authorization |
| EventHub, Postman, SQL, and spreadsheet references | Separate web/API domain, test-data and source-of-truth checks, tool integration patterns, and credential/data isolation |

Image and social-post technology lists are treated as prompts for topics, not
as verified standards, market data, or proof that a named product belongs in
this project's stack. The existing roadmap remains authoritative for current
implementation status and tool-selection decisions.

## References in this repository

- [AI implementation plan](AI_IMPLEMENTATION_PLAN.md) — implementation status,
  AI concepts, architecture decisions, evaluation, security, cost, and phases.
- [Unified mobile automation architecture](UNIFIED_MOBILE_AUTOMATION_ARCHITECTURE.md)
  — current system boundaries and target execution/evidence flows.
- [AI Architect / SDET practical roadmap](AI_ARCHITECT_SDET_PRACTICAL_ROADMAP.md)
  — hands-on learning sequence and portfolio guidance.
- [Automation framework interview guide](AUTOMATION_FRAMEWORK_INTERVIEW_GUIDE.md)
  — test framework and cross-channel execution questions.
