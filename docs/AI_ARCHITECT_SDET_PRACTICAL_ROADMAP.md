# AI Architect / SDET Practical Roadmap

## Quick navigation

- [Outcomes and current boundaries](#outcomes-to-demonstrate)
- [Target architecture](#target-demonstration-architecture)
- [Technology choices](#technology-choices-learn-the-concepts-choose-tools-deliberately)
- [16-week learning sequence](#suggested-pace-and-working-method)
- [Portfolio artifacts](#portfolio-artifacts-to-produce)
- [Interview preparation](#interview-answer-framework)
- [Role-focused checklist](#role-focused-preparation-checklist)

## Purpose

This guide turns the current mobile automation framework into a portfolio of
small, demonstrable AI engineering capabilities. The goal is to gain working
knowledge by building, testing, measuring, and explaining a system—not by
installing a long list of AI libraries or memorizing interview definitions.

The repository is currently a Python 3.14, pytest-BDD, Appium framework for
Android and iOS, with page objects, a shared platform-aware XPath catalog,
Allure reporting, BrowserStack support, unit tests, and GitHub Actions. Keep
those deterministic foundations. Add AI around them in bounded increments.

This roadmap can create credible evidence of AI architecture and SDET skills;
it cannot substitute for or manufacture 15 years of professional experience.
Describe your actual experience accurately, and use the working implementation,
trade-off decisions, measurements, and lessons learned as proof of hands-on
capability.

## Outcomes to demonstrate

By the end, be able to:

1. Explain when to use deterministic automation, an LLM feature, RAG, or an
   agent—and defend the trade-offs.
2. Implement structured model outputs, retrieval, bounded orchestration, tool
   contracts, safe execution, and meaningful human approval.
3. Measure retrieval, generation, agent, and automation quality separately.
4. Diagnose a failure across requirement, retrieval, model, tools, Appium, test
   data, device, and CI instead of blaming "the AI."
5. Demonstrate a requirement-to-test workflow on this mobile framework with
   traceable evidence and a clear audit trail.
6. Discuss security, cost, latency, reliability, rollout, and governance as
   first-class architecture concerns.

## Current framework: starting point and boundaries

Useful extension points already present:

| Existing capability | What it gives the AI project |
|---|---|
| `mobile_test_automation/pages/` | Reusable, deterministic page operations for the General Store app |
| `mobile_test_automation/services/locator_logic.py` | Strict platform-aware locator resolution and explicit configuration errors |
| `mobile_test_automation/resources/locators/locators.json` | Versioned locator source that can be documented/retrieved, not silently rewritten |
| `mobile_test_automation/config/runtime_config.py` | Existing environment-backed configuration and secret boundary |
| `tests/bdd/features/` and `tests/bdd/steps/` | Executable behavior and acceptance-test examples |
| `tests/unit/` | Device-independent place to test schemas, retrieval, policies, and orchestration |
| `mobile_test_automation/services/reporting.py` and `tests/conftest.py` | Screenshots/video and scenario lifecycle evidence |
| GitHub Actions and Allure | CI gates, reports, and a place to publish controlled artifacts |

Important boundaries:

- The current project is mobile Appium/Python, not Playwright/TypeScript or an
  API test suite. Use Appium for the first end-to-end showcase. Add web/API as
  separate adapters only when a target application and scenario justify them;
  the supplied EventHub and Postman materials are separate references, not
  current repository coverage.
- Keep assertions, authorization, locator catalog writes, and business rules
  deterministic. An LLM can propose or classify; ordinary code validates and
  enforces.
- Do not give a model unrestricted shell, filesystem, device, browser, or Jira
  credentials. The model proposes a typed action; an application policy
  decides whether it may run.
- Do not automatically rewrite a locator or weaken an assertion to make a test
  pass. Self-healing begins as an evidence-backed recommendation requiring
  review.
- Start with a local, synthetic/demo dataset. Do not send customer data, real
  credentials, or proprietary documents to an external model without approval.

## Target demonstration architecture

```text
First slice: post-run analysis
pytest/JUnit + approved evidence -> deterministic classification
  -> optional retrieval/model assist -> validation -> report or abstention

Later capability: test-plan drafting
approved requirement -> retrieval -> structured draft -> validation
  -> human review -> existing pytest/Appium execution
```

Keep the first slice a deterministic Python workflow; use a model only after
the evidence and evaluation baseline are ready. Add graph orchestration only
when conditional routing, checkpoint/resume, or approval pauses justify it.
The [implementation plan](AI_IMPLEMENTATION_PLAN.md) owns the exact workflow
contracts and acceptance gates.

## Technology choices: learn the concepts, choose tools deliberately

### Start with this practical stack

| Concern | Initial choice | Why / decision boundary |
|---|---|---|
| Language and test execution | Existing Python, pytest, pytest-BDD, Appium | Preserve the working framework and use its existing tests as the execution target |
| Model interface | One approved provider behind a small adapter | Keep provider-specific SDK types out of workflow and test code; choose a provider based on data policy, availability, cost, and latency |
| Contracts | Pydantic models; JSON Schema at service/tool boundaries if needed | Validate shape and constraints; remember valid JSON is not necessarily a correct answer |
| Orchestration | Plain Python first; evaluate Microsoft Agent Framework (MAF) as the current recommended direction, and compare LangGraph only if a real workflow needs it | Keep the runtime behind project contracts, run a compatibility spike, and select one orchestrator rather than adopting both |
| Retrieval | Approved local documents and a lexical baseline first | Add embeddings and one vector store only if the reviewed query set shows a measurable gap |
| Evaluation | Version-controlled golden cases plus deterministic Python assertions | Start with measurable business criteria; add RAGAS or DeepEval only for metrics they help answer |
| Prompt/model comparisons | promptfoo, optionally | Useful for repeatable prompt/model matrices; not a replacement for domain acceptance checks |
| Tool protocol | MCP Python SDK after the application has stable tool contracts | MCP standardizes tool/resource exposure; your application still owns identity, authorization, and validation |
| Observability | Structured logs and a workflow/run ID first; OpenTelemetry and Langfuse later | Be able to reconstruct one run; redact secrets and sensitive values |
| Persistence | JSONL/SQLite for a local learning prototype; PostgreSQL when multi-user durable service needs arise | Do not introduce a database before state, access, and retention needs are clear |
| CI and execution | Existing GitHub Actions; a restricted worker/container for generated artifacts | Treat model output as untrusted; do not execute arbitrary generated code in the CI control plane |

### Add only when the milestone needs it

- **Hybrid retrieval:** lexical/BM25 plus vector search when exact issue IDs,
  error codes, symbols, and product vocabulary matter alongside semantic
  similarity.
- **Reranking:** when measured top-k retrieval includes relevant content but
  orders it poorly, and quality improvement justifies added latency/cost.
- **PostgreSQL + pgvector:** when relational metadata, access rules, and vector
  records should share an operational store.
- **A second model or local model:** when evaluating quality/cost/privacy trade
  offs—not merely to increase the technology count.
- **Redis/queue/workers:** when measured concurrency, durability, or backpressure
  requires them.
- **Playwright:** when adding a web application adapter; keep it separate from
  the current Appium mobile adapter and share only appropriate orchestration,
  contracts, reporting, and policy layers.

## Suggested pace and working method

Use the phases below as a 16-week example at roughly 5–8 focused hours per
week. Stretch the calendar if needed; meet each phase's demo gate before
moving on. The implementation sequence follows the canonical
[AI implementation plan](AI_IMPLEMENTATION_PLAN.md): deterministic baseline,
evidence/reporting, evaluation, retrieval, then model and orchestration. The
plan owns detailed acceptance criteria and status; this roadmap focuses on
what to learn and demonstrate. Use synthetic data until data approval exists.

For every feature, answer four questions:

1. What failure or user need does it address?
2. What deterministic control verifies the model's output?
3. How will success and regressions be measured?
4. What evidence lets another engineer reproduce the result?

## Phase 0 — Establish the baseline (Week 1)

Run the device-independent suite, confirm BDD discovery, and map one failing
or synthetic scenario from feature through page object, locator, and report.
Record the deterministic failure categories and evidence already available.
Choose **post-run failure analysis** as the first AI use case; defer test-plan
generation until the first workflow has an evaluated baseline.

**Demo:** a reproducible baseline and a short failure/evidence map, with no AI
dependency.

## Phase 1 — Contracts, context, and deterministic capability (Weeks 2–3)

Learn typed inputs/outputs, provenance, redaction, trust boundaries, and
abstention. Define synthetic cases, run/evidence identifiers, and a bounded
context; build an offline Python classifier before calling an LLM.

**Demo:** malformed, conflicting, and unknown inputs return explicit safe
outcomes; existing Appium verdicts remain unchanged.

## Phase 2 — Read-only tools and failure analysis (Weeks 4–5)

Implement a small internal registry over run summaries, failed steps, locator
metadata, and evidence references. Add allowlists, output limits, and audit
events in application code. Learn MCP concepts, but keep protocol exposure
later than stable tool contracts.

**Demo:** a deterministic diagnosis can be reproduced from cited evidence;
unauthorized or unsupported requests abstain or fail explicitly.

## Phase 3 — Post-analysis and reviewable reports (Week 6)

Build a deterministic report from pytest/JUnit totals and validated failure
annotations. Separate test verdict from AI status, link evidence, and label
facts versus hypotheses. Treat BMAD-style briefs, decisions, and post-run
records as reviewed artifacts, not autonomous status updates.

**Demo:** report totals match the runner, and every claim is cited or marked
uncertain.

## Phase 4 — Evaluation and monitoring (Weeks 7–8)

Create a human-reviewed golden set and measure classification, evidence
support, abstention, false confident answers, tool reliability, latency, and
review outcomes separately. Add privacy-safe structured events and a small
offline regression check before considering hosted tracing.

**Demo:** a repeatable evaluation that catches a known regression and exposes
an abstention/error case.

## Phase 5 — Retrieval and grounding (Weeks 9–10)

Start with an allowlisted corpus and lexical search. Add source/version
metadata and access filters, then measure retrieval separately from answer
quality. Consider embeddings and one vector store only if a reviewed query set
shows lexical retrieval is insufficient.

**Demo:** queries return relevant, versioned sources and cannot retrieve
outside their approved scope.

## Phase 6 — One model and bounded orchestration (Weeks 11–13)

After data approval and a working deterministic baseline, add one provider
behind a typed interface. Compare against the same reviewed cases. Use plain
Python first; perform a MAF compatibility spike before selecting an
orchestrator. Use AutoGen only as an isolated, synthetic-data learning
exercise, not a production dependency.

**Demo:** provider errors, invalid output, budget exhaustion, and uncertainty
are explicit and never change the test verdict. Add requirement-to-test draft
generation as a second use case only after it has its own acceptance set.

## Phase 7 — Review-only locator proposals (Week 14)

Trigger only for confirmed locator failures. Rank candidates from approved
hierarchy/catalog evidence, validate them deterministically, and require
approval and regression before any catalog edit.

**Demo:** a plausible repair is proposed with evidence, while an ambiguous
case abstains and the original assertion remains intact.

## Phase 8 — Production readiness and integration decisions (Weeks 15–16)

Complete threat/data-flow review, retention and deletion rules, release
controls, rollback, unit economics, and a reproducible leadership demo. Add
MCP only if a real client/interoperability need remains after the internal
tool boundary is stable; select one hosted observability product only after
data approval.

**Demo:** an end-to-end, measured walkthrough with a success, an ambiguous
case, and a safe failure, plus a clear list of what is still planned.

## Portfolio artifacts to produce

Keep these concise, real, and based on the implementation:

- System/context and sequence diagrams.
- Versioned golden dataset and evaluation output.
- Typed state, tool contracts, and policy tests.
- Threat model covering prompt injection, excessive agency, data leakage,
  unsafe generated code, and external write duplication.
- A run trace showing requirement, retrieved evidence, generated plan,
  validation, approval, Appium run, and final outcome.
- A short architecture decision record for provider, vector store, orchestration,
  and MCP timing.
- A demo script with a successful case, an ambiguous case, and a failure case.
- A one-page case study with baseline, intervention, measured results,
  limitations, and next steps.

Do not publish proprietary documents, credentials, personal data, or
unreviewed generated output in a portfolio.

## Interview answer framework

Use this answer shape for architecture questions:

1. **Need and boundary:** what problem is being solved, and what should remain
   deterministic?
2. **Design:** components, data flow, state, trust boundaries, and contracts.
3. **Failure modes:** what can fail and how the system detects, bounds, retries,
   or escalates it.
4. **Measurement:** quality, safety, reliability, latency, and cost metrics.
5. **Trade-off and evidence:** alternatives considered and what your prototype
   or production evidence showed.

For experience questions, be precise about what you personally implemented,
what was a prototype, what was deployed, and what you would change. Do not
present roadmap items as completed production experience.

## Interview guides

The detailed question-and-answer material is maintained in two focused
references to avoid duplicating answers in this learning roadmap:

- [AI Automation Interview Guide](AI_AUTOMATION_INTERVIEW_GUIDE.md) covers
  LLM/GenAI, RAG, agent workflows, MCP, evaluation, safety, and AI operations.
- [Automation Framework Interview Guide](AUTOMATION_FRAMEWORK_INTERVIEW_GUIDE.md)
  covers deterministic framework design, Appium, web, API, CI, and quality
  engineering.

Use the guides as evidence-based speaking points. This roadmap remains the
source for hands-on learning phases and portfolio milestones; do not describe
planned features as completed experience.

For concept-by-concept labs based on the supplied AI-engineering images, see
the [AI Engineer Concept-to-Practice Roadmap](AI_ENGINEER_CONCEPT_TO_PRACTICE_ROADMAP.md).

## Role-focused preparation checklist

Before interviews, verify that you can do—not merely describe—the following:

- [ ] Explain the current mobile framework and point to its real extension
  points.
- [ ] Implement and test a typed model response with explicit abstention.
- [ ] Ingest a small approved corpus and return source-linked retrieval results.
- [ ] Debug a retrieval miss separately from a generation error.
- [ ] Run a golden set and explain at least one regression it caught.
- [ ] Show state, bounded retries, stop conditions, and human approval.
- [ ] Demonstrate that authorization is enforced outside model instructions.
- [ ] Execute an approved plan through existing pytest/Appium and inspect
  artifacts.
- [ ] Classify a failure with evidence and propose—but do not silently apply—a
  locator repair.
- [ ] Explain the design alternatives, cost/latency/safety trade-offs, and what
  you would change at higher scale.
- [ ] Separate what is implemented, evaluated, deployed, and still planned.

## Final principle

An architect-level showcase is not the number of AI products integrated. It is
the ability to select a small useful problem, preserve deterministic quality
controls, measure the result, handle failure safely, and explain why the design
is appropriate. Build the phases in order and let each demo earn the next
capability.
