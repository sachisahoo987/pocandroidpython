# AI and Agentic QA Implementation Plan

## Quick navigation

- [Current implementation snapshot](#current-implementation-snapshot)
- [Architecture and framework choices](#recommended-implementation-in-one-picture)
- [Concept-to-code map](#concept-to-code-map)
- [Memory and context boundaries](#context-instructions-memory-and-cache)
- [Agents, MCP, and cost controls](#multi-agent-design-and-mcp-server-plan)
- [Phased development plan](#development-plan-work-in-this-order)
- [Security and compliance](#corporate-security-privacy-and-compliance-baseline)
- [Measurement and reporting](#how-to-measure-progress-and-release-readiness)
- [Immediate backlog and decision rules](#immediate-development-backlog)

## Goal

Combine the earlier AI implementation plan and agentic QA roadmap into one
implementation source of truth for this Python 3.14, pytest-BDD, Appium
repository. The target is an AI-assisted mobile QA system in which bounded
agents collect approved context, use narrowly scoped tools, retrieve relevant
framework knowledge, analyze failed runs, recommend repairs, and produce
traceable reports.

The agent must **not** become the test oracle. Existing Appium actions,
assertions, pytest results, and CI gates remain authoritative. Generated test
plans and locator repairs start as proposals that a person reviews.

This is a development roadmap, not a claim that the AI components are already
running. The codebase currently has no LLM client, agent framework, RAG/vector
store, MCP server, or AI failure analysis. Existing Appium, page objects,
locators, Allure, CI, screenshots, and the synthetic input bundle are
foundations only.

The companion [Unified Mobile Automation Architecture](UNIFIED_MOBILE_AUTOMATION_ARCHITECTURE.md)
owns the repository's system boundaries, mobile execution/data flows, and
current-versus-target architecture. This plan owns AI choices, implementation
status, phases, evaluation, and acceptance criteria; do not duplicate its
roadmap tables in the architecture document.

The [AI Automation Interview Guide](AI_AUTOMATION_INTERVIEW_GUIDE.md) is the
canonical AI Q&A reference; the [Automation Framework Interview
Guide](AUTOMATION_FRAMEWORK_INTERVIEW_GUIDE.md) owns deterministic framework,
web, mobile, API, and CI interview topics.

The [AI Engineer Concept-to-Practice Roadmap](AI_ENGINEER_CONCEPT_TO_PRACTICE_ROADMAP.md)
maps the supplied AI-engineering image concepts to practical framework labs.
It is a learning companion; this plan remains the authority for implementation
status and acceptance criteria.

## Current implementation snapshot

| Capability | Status today | Evidence / boundary |
|---|---|---|
| Android/iOS Appium driver setup | Implemented foundation | `mobile_test_automation/drivers/driver_factory.py`; app-specific iOS selectors are null/unverified |
| Page objects and BDD General Store flows | Implemented foundation | `mobile_test_automation/pages/`, `tests/bdd/`; real device execution needs an installed app and configuration |
| Strict platform-aware locator catalog | Implemented | `mobile_test_automation/services/locator_logic.py`, `resources/locators/locators.json`; lookup is deterministic, not healing |
| Screenshots/video and Allure evidence | Implemented foundation | `services/reporting.py`, `tests/conftest.py`; capture is not AI vision or hosted tracing |
| CI, BrowserStack configuration, unit tests | Implemented foundation | `.github/workflows/`, `tests/unit/`; accounts, app references, and devices are externally configured |
| Synthetic QA starter dataset | Implemented | `tests/fixtures/ai_qa/starter_cases.json`; illustrative only, not real run data |
| Governed operational memory for an AI agent | Not implemented | No persistent agent memory store or read/write lifecycle exists |
| LLM, agents, AutoGen/MAF, MCP, RAG, DeepEval, tracing | Not implemented | No AI packages or runtime AI integration are present |
| AI failure analysis, post-analysis, self-healing | Not implemented | All future work; pytest/Appium remain verdict authority |

**AI runtime: not implemented.** Do not represent plans, diagrams, or installed
developer tools as working product capabilities. The starter fixture is not a
reviewed production evaluation set.

The starter data at
[`tests/fixtures/ai_qa/starter_cases.json`](../tests/fixtures/ai_qa/starter_cases.json)
contains synthetic requirements, failure observations, and a sample UI
hierarchy. Use it for offline contract/classifier tests only. It is not a live
app capture or an approved ground-truth benchmark; human-review labels before
using it to report model quality.

## Recommended implementation in one picture

```text
Gherkin + approved requirements + locator catalog + run artifacts
                              |
                 Context builder and redaction
                              |
            RAG retrieval (only if useful and evaluated)
                              |
       Failure-analysis / test-planning agent workflow
          MAF workflow + explicit limits
                              |
            Read-only typed tools via a registry
       Internal tool registry -> scoped MCP servers
                              |
         Structured output + deterministic validation
                              |
                Human review / approval
                 /                    \
       BMAD-style report        Approved action only
       and QA artifacts         Approved, deterministic actions
                 \                    /
              Allure + monitoring + evaluation
```

### Agent framework decision: AutoGen versus its successor

The request calls for AutoGen-style multi-agent development. However, the
official Microsoft AutoGen repository now marks AutoGen **archived and no
longer maintained**, and directs new projects to Microsoft Agent Framework
(MAF). For a corporate/production direction:

- Use **Microsoft Agent Framework for Python** as the proposed orchestration
  target, subject to a small compatibility, maturity, and dependency review
  against this project's Python 3.14 constraint before adding it.
- If learning AutoGen concepts is important, build a small disposable
  AutoGen AgentChat prototype against synthetic data, pin dependencies, and
  label it **learning-only**. Do not put an archived AutoGen runtime on the
  production dependency path.
- Migrate the useful concepts—agents, tools, handoffs, bounded workflows,
  human approval, checkpoints, and evaluation—to MAF rather than designing a
  production architecture around the archived package.
- Keep orchestration replaceable behind this project's own contracts so the
  Appium framework is not coupled to a vendor SDK.

This recommendation follows the official
[AutoGen repository](https://github.com/microsoft/autogen) and its
[AutoGen-to-Microsoft-Agent-Framework migration guide](https://learn.microsoft.com/en-us/agent-framework/migration-guide/from-autogen/).

Recommended first vertical slice: **post-run failure analysis on synthetic or
redacted evidence**. It uses the current test framework, needs no autonomous
device control, and can be evaluated before an external model, vector database,
or multi-agent conversation is introduced.

## Concept-to-code map

| Concept | Meaning to learn | Concrete implementation in this repository | First acceptance check |
|---|---|---|---|
| Context engineering | Select, minimize, order, and label the information a model needs; distinguish trusted instructions from untrusted app/log content | `mobile_test_automation/ai/context.py`: build a size-bounded, redacted run context from scenario, step, platform, exception, locator key, and evidence references | Unit tests prove irrelevant fields are excluded, secrets are redacted, and context limits are enforced |
| Capability / skill | A named, bounded QA responsibility with a contract, instructions, allowed tools, and completion criteria | `mobile_test_automation/ai/capabilities/`: start with `failure_analysis` and `test_plan_draft`; each declares inputs, output schema, allowed tools, and stop conditions | Each capability works with a fake model/offline fixture and refuses unsupported inputs |
| Tool building | Expose deterministic application functions with typed arguments/results; tools are not arbitrary model-generated code | `mobile_test_automation/ai/tools/`: read run summary, get scenario steps, read locator metadata, get approved screenshot/page-source summary, search test history, validate locator candidate | Tool schema tests, allowlist tests, bounded result size, audit event for every call |
| Agentic AI / multi-agent orchestration | A bounded workflow that assigns specialized work, chooses approved tools, and stops on completion, uncertainty, approval, or budget | Start with deterministic Python orchestration; use MAF workflow/agent APIs only after the single-agent slice works. AutoGen is learning-only because the project is archived | Max agents, turns, time, tool calls, retries, and spend are enforced; unknown cases abstain; no unapproved write tool exists |
| Generative AI / LLM | Generate a structured explanation or draft from evidence; output is probabilistic | `mobile_test_automation/ai/providers/`: one provider-neutral interface and one selected provider; model ID and prompt version are explicit configuration | Invalid JSON, unsupported IDs, missing citations, and provider outage never become success-shaped results |
| RAG | Retrieve relevant source passages at run time, then ground the generated response in those passages | `mobile_test_automation/ai/retrieval/`: initially lexical search over approved Gherkin, locator catalog, and sanitized runbooks; add embeddings/vector storage only after a retrieval benchmark | Golden query set measures recall@k, precision@k, and citation correctness; no invented locator/requirement is accepted |
| Evaluation / DeepEval | Repeatable measurement of model and retrieval quality against human-reviewed expected results | `tests/ai_eval/` plus `mobile_test_automation/ai/evaluation/`: golden cases, deterministic graders, optional DeepEval adapters | CI can run offline evals; thresholds detect regressions and report false positives separately |
| Workflow orchestration / MAF | Explicit state, conditional routes, retries, pause/resume, and checkpoints | Add MAF workflows only for the branching flow: collect evidence → retrieve → analyze → validate → review → report | Workflow terminates on every path; retries are bounded; rejected/unknown output cannot reach an action node |
| Chains / LangChain | Reusable prompt/model/retriever integrations and structured output helpers | Optional adapter inside provider/retrieval boundary; keep LangChain types out of page objects and core domain contracts | Core unit tests run without LangChain installed; provider integration tests are opt-in |
| Tracing / LangSmith | Inspect model and graph traces, prompts, tool calls, latency, and evaluation results | Optional integration in `mobile_test_automation/ai/observability/`; use project/run IDs and redaction | Trace contains no credentials/PII; a local/offline run still succeeds when tracing is disabled |
| LLM observability / Langfuse | Record model/prompt versions, input/output token usage, cost, latency, scores, and traces | Select LangSmith **or** Langfuse for the first hosted trace integration; optionally export standard OpenTelemetry metrics | A single run can be correlated from pytest scenario to agent trace and report without logging raw sensitive evidence |
| MCP | Standard protocol for exposing tools/resources to compatible clients | Later `mobile_test_automation/ai/mcp_server.py` wrapping the same internal tool registry; MCP must not bypass application policy | Tools are read-only by default, explicitly allowlisted, authenticated, audited, and input-validated |
| Self-healing | Recommend and validate a replacement interaction target after a locator failure | `mobile_test_automation/ai/healing/`: collect page source, rank existing catalog candidates, validate uniqueness/visibility, return a patch proposal | No assertion changes; no auto-write; ambiguous or unsafe candidates abstain; approved repair has regression evidence |
| Failure analysis | Classify product defect vs test/locator issue vs environment vs unknown, with supporting evidence | `mobile_test_automation/ai/failure_analysis.py`: deterministic baseline first, then optional model-assisted explanation | Golden-set category accuracy, abstention, evidence support, and false-positive rates are reported |
| Post-analysis | Summarize a completed run after execution and identify next steps without changing its verdict | `mobile_test_automation/ai/post_analysis.py` and report templates; consume pytest/Allure results and permitted evidence | Report agrees with machine test totals and links each finding to a case/evidence item |
| Monitoring | Observe system health and quality over time, not just individual answers | Structured events, counters, duration, provider health, tool errors, quality scores, and run correlation IDs | Dashboard/report distinguishes test failure, agent failure, provider outage, and telemetry failure |
| BMAD reports | For this plan, BMAD means a set of structured, reviewable delivery artifacts aligned to the BMAD method, not an installed reporting product | `reports/ai/` templates for brief/PRD, architecture/ADR, story, test strategy, implementation summary, risk/decision log, and post-run report | Each report is generated from source evidence, versioned, and reviewed; generated analysis does not silently alter Jira or test status |
| Guardrails / governance | Least privilege, privacy, explicit policy, human control, safe rollout | `mobile_test_automation/ai/policy.py`, redaction, model/prompt pinning, output schemas, tool allowlists, audit log | Negative tests prove prompt-injection text in logs cannot authorize a tool or change system policy |

### Tools: what to adopt, and when

| Tool | Recommendation for this project | Do not use it for |
|---|---|---|
| LangChain | Optional provider/prompt/retriever adapter after the first offline capability; useful if integrations save code | Owning the test verdict, unrestricted tool execution, or becoming a requirement for deterministic tests |
| Microsoft Agent Framework | Preferred Microsoft multi-agent/workflow target after an isolated compatibility spike; supports Python and MCP integration | Adding agents before a valuable, evaluated single-agent workflow |
| AutoGen | Use only for a short learning/migration prototype; the official repository is archived and advises new users to start with MAF | New production deployments or a long-lived dependency |
| DeepEval | Optional evaluation runner after a reviewed golden set exists; combine with deterministic schema/assertion tests | Treating an LLM judge as ground truth; calibrate it against human labels |
| LangSmith | Useful hosted trace/evaluation UI if data policy permits | Uploading raw screenshots, page source, credentials, or customer data without approval |
| Langfuse | Alternative LLM tracing/evaluation platform; choose instead of LangSmith initially | Running both observability products before there is a measured need |
| MCP Python SDK | Add multiple logical servers after internal tools, identities, and policy are stable | Permission enforcement; MCP standardizes interoperability, not authorization or trust |
| Pydantic / JSON Schema | Add for strict request/result contracts; validate every model/tool response | Assuming schema-valid output is factually correct |
| SQLite / JSONL | Start with local evaluation records and reproducible traces; redact and document retention | Multi-user production memory or unbounded retention |
| Chroma or Qdrant | Evaluate one local vector store only if lexical retrieval is insufficient; select one, not both | Adding a vector DB before approved documents and retrieval metrics exist |
| OpenTelemetry | Useful portable trace/metric export when local instrumentation grows | Sending sensitive payload attributes to a collector |
| promptfoo | Optional prompt/model regression matrix after an adapter and golden set exist | Replacing domain-specific assertions or manual review |
| Existing pytest, Allure, GitHub Actions | Keep as the deterministic test and CI foundation; publish sanitized evaluation artifacts | Claiming existing Allure reports are already AI traces |

Start with one model/provider, one failure-analysis capability, and a local
fixture corpus. Tool/framework selection should remain replaceable behind
interfaces. Do not install every named library at once.

## Context, instructions, memory, and cache

Treat these as separate logical concepts and data lifecycles, not as one
growing prompt or an unrestricted conversation transcript:

| Concept/store | Purpose | Appium-framework example | Lifecycle and authority |
|---|---|---|---|
| Instructions / policy | Define how the assistant is allowed and expected to work | Reviewed repository guidance, architecture, coding conventions, tool permissions, and validation rules | Version-controlled and changed through review; policy is trusted only from approved sources |
| Project knowledge | Provide stable, reusable facts about this repository | Python/pytest/Appium stack, page-object design, locator catalog contract, and supported run modes | Versioned docs/configuration; update when the project changes; retrieved knowledge does not itself grant tool authority |
| Runtime context | Supply evidence for the current task or run | Scenario/failed step, exception, app/build/platform, relevant logs, screenshot/page-source references, and acceptance criteria | Scoped to the current task/run and retained under artifact policy; temporary failures do not become permanent memory |
| Operational memory | Preserve a small set of approved facts or reviewed patterns that improve later tasks | A stable project preference or a human-confirmed recurring diagnostic pattern | Optional future capability; scoped, provenance-bearing, reviewable, replaceable, and deletable; not an event or evidence archive |
| Cache | Avoid recomputing a deterministic retrieval or provider result | Versioned retrieval result or safe summary keyed by content and policy versions | Performance optimization only; expire/invalidate on changed inputs or versions; never authoritative over source evidence |

If operational memory is later justified, use typed records rather than raw
transcripts. A record should include scope (project/repository/team/user),
type, key/value, source/provenance, status, creation and review timestamps,
review requirement, and expiry or supersession metadata. Enforce scope on
every read and write; provide review, replacement, and deletion mechanisms.
Exclude secrets, credentials, unnecessary personal data, one-off session IDs,
temporary failures, unverified model guesses, and raw logs/screenshots.
Retrieved content must never silently become durable memory: only an
authorized, validated, reviewable write path may create or update a record.

The current repository has no such persistent memory capability. Begin with
approved versioned project documentation plus per-run context and artifacts.
Add operational memory only after a concrete continuity need, data owner,
retention policy, and access model are established. Keep cache expiration and
invalidation separate from memory review and deletion. The architecture and
artifact data-flow boundaries are described in the
[Unified Mobile Automation Architecture](UNIFIED_MOBILE_AUTOMATION_ARCHITECTURE.md).

## Multi-agent design and MCP server plan

### Agent roles: specialized, not a debate swarm

Use the following logical roles in the design, but do not instantiate every
role as an LLM agent. Deterministic components are cheaper, easier to test, and
should own data collection, policy, verification, and report arithmetic.

| Role | Type | Responsibility | Model/tool access |
|---|---|---|---|
| Workflow supervisor | MAF workflow/controller, preferably deterministic routing | Own workflow state, deadlines, approval gates, agent selection, and terminal status | No broad tools; routes only from validated state |
| Evidence collector | Deterministic service/tool | Read pytest/JUnit/Allure metadata, scenario, locator definition, and allowlisted evidence | Read-only artifact and repository MCP |
| Failure analyst | One LLM-backed agent when needed | Propose failure category, evidence-backed explanation, uncertainty, and next diagnostic question | Read-only tools; no Jira write, Appium action, shell, or locator mutation |
| Locator analyst | Conditional LLM capability, not always invoked | Rank candidate locators from approved UI hierarchy and existing catalog after a confirmed locator failure | Read-only locator/UI evidence; emits proposal only |
| Test-design analyst | Separate capability, invoked only for a requirement-to-test request | Draft a schema-constrained, traceable test plan | Read-only requirement, feature, and locator metadata |
| QA reviewer / critic | Deterministic validators first; optional independent model only for high-risk findings | Check evidence references, supported IDs, contradictions, policy, and output completeness | No write/action tools; independent review must not simply repeat the same model call |
| Report builder | Deterministic renderer | Merge authoritative test totals with validated AI annotations into Markdown/JSON/Allure links | No LLM required; no ability to change test verdict |
| Human approver | Person | Approve Jira writes, locator changes, or any controlled test rerun | Explicit UI/PR approval and auditable identity |

**First deployable workflow:** one deterministic supervisor + evidence
collector + one failure-analysis agent + deterministic output validator and
report builder. Call the locator analyst only for locator-related failures and
the QA critic only when risk/uncertainty warrants its cost. Avoid autonomous
agent-to-agent discussion loops.

```text
pytest/JUnit result
      |
deterministic evidence collector
      |
read-only context/RAG tools
      |
failure analyst (bounded)
      |
schema + evidence + policy validation
      +---- invalid/uncertain ---> human review / abstain
      |
deterministic report builder
      +---- optional, approved action proposal ---> human approval
```

### MCP servers: separate trust and permission boundaries

MCP servers are adapters over the same internal typed tool registry; never
duplicate authorization rules in each server. Use distinct server processes or
deployments when permissions, credentials, data sensitivity, or network
boundaries differ. Start with the first two logical servers, not a large MCP
fleet.

| MCP server | Initial tools/resources | Permission | Build order |
|---|---|---|---:|
| `qa-knowledge` | Read approved Gherkin, locator catalog metadata, framework docs, synthetic/golden case IDs, and retrieval results with source/version | Read-only; repository allowlist; no arbitrary filesystem path | 1 |
| `qa-run-evidence` | Read run summary, JUnit/pytest result, failed step, screenshot/page-source metadata from an authorized run | Read-only; run-scoped authorization; default redact and return summaries/references rather than raw evidence | 2 |
| `qa-ci` | Read selected GitHub Actions run status, job summary, and approved artifact metadata | Read-only, repository and workflow allowlist; no dispatch/cancel/re-run initially | 3 |
| `qa-test-management` | Search Jira test/bug/project metadata and retrieve permitted issue fields | Read-only OAuth/service identity with project and field allowlists | 4 |
| `qa-controlled-actions` | Create a draft defect, request a rerun, or propose a locator patch | Separate server/identity; disabled by default; human confirmation, idempotency key, audit record, and allowlisted action required | 5 |

Never expose generic shell, arbitrary filesystem, unrestricted HTTP, all of
Appium, or unrestricted GitHub/Jira write operations as agent tools. A future
device server should provide named operations (for example, capture the
current screen or execute one approved existing scenario), not arbitrary
Appium scripts. MCP clients must connect only to authenticated, trusted
servers. Follow the MCP specification's consent, privacy, and tool-safety
guidance; protocol support is not a security certification.

### Token and model-cost minimization

Optimize **cost per accepted, evidence-supported outcome**, not merely tokens
per call. Multi-agent fan-out and repeated critique can increase cost without
increasing QA quality.

1. **Route without an LLM first.** Parse pytest/JUnit, classify obvious
   configuration/locator failures with deterministic rules, and invoke a model
   only when language/evidence synthesis adds value.
2. **Do not call every agent for every failure.** Use conditional roles:
   locator analysis only for locator failures, visual analysis only when
   hierarchy evidence is insufficient, and an independent reviewer only for
   low confidence/high impact.
3. **Set per-run budgets.** Configure maximum agent turns, agents invoked,
   tool calls, input/output tokens, wall-clock time, retries, and spend.
   Stop and return an explicit `budget_exhausted`/`needs_review` result at the
   limit; do not loop until a model claims certainty.
4. **Build compact context.** Send scenario ID, failed step, exception
   family, relevant locator, and short redacted evidence excerpts—not the
   entire repository, full logs, full page source, or full conversation.
   Store artifacts once and pass authorized IDs/links.
5. **Use retrieval before context expansion.** Filter by app, platform,
   scenario, version, and failure category; return a small top-k with snippets,
   source IDs, and commit/build version. Increase k only when retrieval
   evaluation shows missed evidence.
6. **Summarize hierarchically.** Keep a deterministic run summary and
   failure-specific evidence summary. Do not resend earlier agent dialogue;
   preserve immutable source evidence for audit.
7. **Choose model tiers by task.** Use rules or a small/low-cost model for
   classification and structured extraction; route ambiguous or high-impact
   cases to a stronger model. Measure both quality and cost on the same golden
   cases before routing.
8. **Constrain output.** Ask for only fields required by the schema, use
   structured output where available, cap result size, and avoid asking the
   model to repeat logs or cite long passages verbatim.
9. **Reuse stable prompts and cache safely.** Keep stable policy/instructions
   as a cacheable prefix when the provider supports prompt caching. Cache
   deterministic retrieval/index results and safe summaries by content hash;
   key model-response caches by model, prompt, evidence, and policy versions.
   Never reuse across tenants/access scopes or bypass freshness checks.
10. **Avoid wasteful retries and parallelism.** Retry only transient,
    classified provider errors with a small bounded count; do not retry invalid
    content unchanged. Parallelize only independent work whose latency benefit
    exceeds extra input/context cost.
11. **Minimize vision cost.** Use UI hierarchy/accessibility data first;
    capture/crop/resize only the relevant screen region when vision is
    necessary, and avoid sending the same screenshot to multiple agents.
12. **Track unit economics.** Record input/output tokens, cached tokens,
    model/provider, calls per run, cost per triaged failure, cost per accepted
    diagnosis, and human review time. Set budgets from measured baseline data,
    not guessed universal dollar thresholds.

Keep exact model/provider pricing in configuration or an approved pricing
source, not hard-coded assumptions in this plan. Re-evaluate cost and quality
whenever model, prompt, retrieval, or agent count changes.

## Proposed package structure

Create these modules incrementally; do not make placeholder directories for
phases that have not started.

```text
mobile_test_automation/
  ai/
    contracts.py             # typed input/output and evidence references
    context.py               # context assembly, token/size budget, redaction
    policy.py                # tool permissions, action limits, approval rules
    capabilities/
      failure_analysis.py    # initial capability
      test_plan_draft.py     # later, review-only test generation
    tools/
      registry.py            # named, typed, allowlisted tool registry
      run_evidence.py        # read-only pytest/Allure/evidence tools
      locator_catalog.py     # read-only catalog access and candidate validation
    retrieval/
      lexical.py             # initial local retrieval
      index.py               # later embedding/vector adapter, if justified
    providers/
      protocol.py            # provider-neutral model contract
      selected_provider.py   # one approved implementation, later
    workflow.py              # later, bounded MAF workflow adapter
    healing.py               # review-only locator repair proposal
    post_analysis.py         # post-run summary/report generation
    observability.py         # redacted trace/metric events
    reports/
      bmad.py                # BMAD-style artifacts from validated run data
tests/
  ai/
    unit/                    # contracts, policy, context, tools, parsers
    integration/             # mocked provider, graph, report pipeline
  ai_eval/
    golden_cases.jsonl       # human-reviewed, versioned expected outcomes
    test_failure_analysis.py # offline scores and quality gates
reports/
  ai/                        # generated, sanitized run reports; normally ignored
```

Keep AI code outside `pages/`, `drivers/`, and existing page actions. The AI
package may propose an action; the existing framework and a policy layer decide
whether a permitted deterministic action is executed.

## Development plan: work in this order

Check off a phase only after its exit criteria and tests pass. No AI runtime
phases below are currently implemented.

### Phase 0 — Baseline and contracts (next; P0)

- [ ] Run and record the existing unit suite and BDD collection baseline.
- [ ] Confirm the target public General Store app/build, Android package/version,
  allowed test environment, and whether screenshots/page source may be retained.
- [ ] Define stable identifiers for run, scenario, step, evidence, locator, and
  report; redact device IDs and secrets where required.
- [ ] Define typed `RunEvidence`, `FailureAnalysis`, `LocatorProposal`, and
  `TestPlanDraft` contracts before choosing orchestration libraries.
- [ ] Expand synthetic cases to include product, assertion, locator, app
  startup/environment, timeout, flaky/retry-recovered, conflicting-evidence,
  prompt-injection, and unknown examples.

**Exit:** fixtures and schemas can be checked offline; existing automation is
unchanged.

### Phase 1 — Context and capability (P0)

- [ ] Build a context assembler from pytest node/scenario, last failed step,
  exception type/message, platform, locator key, and safe evidence references.
- [ ] Add source labels and trust boundaries: system policy, project docs,
  test/run evidence, and untrusted app text are distinct fields.
- [ ] Keep runtime context transient and separate from any future operational
  memory; prohibit implicit writes from retrieved content or model output.
- [ ] Add truncation and redaction tests; never concatenate arbitrary page
  source into trusted instructions.
- [ ] Implement `failure_analysis` as a Python capability with declared input,
  typed output, allowed tools, success/abstention criteria, and max-step budget.

**Exit:** deterministic capability works on the synthetic corpus without a
device, network, model key, or external tracing service.

### Phase 2 — Tools and deterministic failure analysis (P0)

- [ ] Implement only read-only tools first: `get_run_summary`,
  `get_failed_step`, `get_locator_definition`, `get_evidence_metadata`, and
  `search_known_failures`.
- [ ] Validate tool name/arguments/result, cap output size, and record a
  redacted tool-call event.
- [ ] Add a deterministic baseline classifier:
  `product`, `test_or_locator`, `environment`, `unknown`.
- [ ] Return evidence IDs and confidence/abstention; low evidence means
  `unknown` plus `needs_human_review=true`.
- [ ] Keep defect creation, test reruns, device actions, and locator writes
  unavailable to the model.

**Exit:** unit tests cover valid, missing, conflicting, malformed, and
adversarial evidence; no false successful diagnosis on unknown input.

### Phase 3 — Post-analysis and BMAD reports (P1)

- [ ] Parse authoritative pytest/JUnit XML and Allure metadata for run totals;
  never ask a model to calculate the pass/fail count.
- [ ] Produce a structured post-run record: summary, test counts, failed cases,
  classification, cited evidence IDs, confidence, risks, and recommended next
  action.
- [ ] Generate reviewable BMAD-style artifacts:
  - **Brief / PRD:** problem, users, scope, non-goals, acceptance criteria.
  - **Architecture / ADR:** boundaries, data flows, tools, security decisions,
    provider/vector/orchestration choices and alternatives.
  - **Story / task:** user value, acceptance criteria, dependencies and test plan.
  - **Implementation report:** changed modules, tests/build evidence, known
    limitations, model/prompt versions.
  - **Post-run report:** authoritative execution totals, findings, linked
    evidence, unresolved questions, owner/next step.
- [ ] Store sanitized Markdown/JSON under `reports/ai/`; make retention and
  `.gitignore` policy explicit before storing real run artifacts.
- [ ] Link results to Allure; optionally add a small Markdown/JSON summary to
  the CI artifact. Keep report generation useful when AI is disabled.

**Exit:** report totals match JUnit/pytest data exactly, every diagnosis cites
evidence or abstains, and report creation cannot change test status.

### Phase 4 — Evaluation and monitoring (P1)

- [ ] Build a human-reviewed golden set and record dataset version and label
  provenance.
- [ ] Measure separately:
  - Input/output schema validity.
  - Failure-category precision, recall, and confusion matrix.
  - Evidence citation coverage and unsupported-claim rate.
  - Unknown-case abstention and incorrect confident-answer rate.
  - Locator candidate precision and ambiguous-match abstention.
  - Agent completion, max-step termination, and tool-call success.
  - p50/p95 latency, provider errors, retries, tokens/cost per run when
    available.
  - Human acceptance/edit/rejection rate and escaped-defect/false-heal rate.
- [ ] Start with local redacted JSONL metrics and CI artifacts. Add LangSmith
  **or** Langfuse only after the data path is approved.
- [ ] Add OpenTelemetry later if portable traces/metrics are needed across
  CI, Appium, and AI services.
- [ ] Alert on provider outage, schema/tool error spikes, latency/cost budget
  violations, evaluation regression, and false-healing events.

**Exit:** each evaluation run has reproducible inputs, versioned prompts/model
metadata when applicable, independent metrics, and no secret-bearing traces.

### Phase 5 — RAG (P2)

- [ ] Start with a small approved corpus: repository docs, active Gherkin,
  locator catalog metadata, and sanitized failure runbooks.
- [ ] Add stable document IDs, source path, version/commit, section, platform,
  and access metadata.
- [ ] Implement lexical search and a fixed query/golden relevance set first.
- [ ] Measure recall@k, precision@k, citation accuracy, stale-source rate, and
  retrieval latency.
- [ ] Add embeddings and one local vector store only if semantic retrieval
  improves measured results. Evaluate chunk size, overlap, metadata filtering,
  hybrid search, and optional reranking.
- [ ] Give every generated claim source IDs; refuse to invent missing locators,
  app behavior, or requirements.

**Exit:** retrieval beats or complements lexical baseline on reviewed queries
without exposing unapproved documents.

### Phase 6 — LLM and Microsoft Agent Framework (P2)

- [ ] Add a provider protocol with request, typed response, timeout, error,
  model ID, prompt version, token usage, and retry metadata.
- [ ] Select one approved model/provider from data policy, availability, cost,
  latency, structured-output support, and evaluation results.
- [ ] Keep a plain Python workflow until stateful routing, approval pause, or
  checkpoint/resume is necessary.
- [ ] Run a small MAF compatibility spike against this repository's Python
  version and pinned dependencies before selecting the production workflow
  APIs. Keep the provider/workflow contract isolated.
- [ ] Use MAF to orchestrate the bounded workflow only after the spike:
  `collect_evidence -> retrieve_context -> analyze_failure ->
  validate_output -> (needs_review | report)`.
- [ ] If AutoGen is used for learning, keep the prototype in a separate,
  optional dependency group and synthetic-only example; document the archive
  status and do not ship it in the runtime path.
- [ ] Enforce workflow limits: maximum agent turns/roles, tool calls, wall
  time, response size, provider retry count, and per-run spend.
- [ ] Treat provider/model changes as behavior migrations; pin versions and
  compare old/new on the golden set before rollout.

**Exit:** provider outage falls back to a visible AI-unavailable result and
does not fail or alter deterministic test execution.

### Phase 7 — Review-only self-healing (P3)

- [ ] Trigger only after a classified locator failure; preserve original error,
  screenshot/page-source metadata, app/platform, and locator key.
- [ ] Generate candidates from trusted sources in order: accessibility ID or
  resource ID, known catalog/platform selector, nearby UI hierarchy; use
  vision as additional evidence, not sole proof.
- [ ] Validate locator syntax and platform, uniqueness, visible/enabled state,
  and expected element context through deterministic code.
- [ ] Return a proposed patch with old/new selector, evidence, score, test
  impact, and rollback instructions.
- [ ] Require human approval before changing `locators.json`; run the original
  assertion and targeted regression after the change.
- [ ] Record approved/rejected proposals and outcomes to measure healing
  precision and false-heal rate.

**Exit:** zero automatic assertion weakening, zero silent catalog writes, and
ambiguous proposals abstain. A retry pass is reported as recovered/flaky, not
as an unqualified first-attempt pass.

### Phase 8 — Multiple MCP servers and controlled actions (P3/P4)

- [ ] Wrap the existing internal tool registry; do not create a second policy
  path in the MCP server.
- [ ] Build `qa-knowledge` and `qa-run-evidence` first; add `qa-ci` and
  `qa-test-management` only after repository/project access rules are approved.
- [ ] Require authenticated clients, per-tool authorization, argument
  validation, timeouts, rate limits, output caps, audit logs, and redaction.
- [ ] Keep write-capable `qa-controlled-actions` separate from read-only MCP
  servers. Disable Jira defect creation, locator updates, and reruns until
  explicit user approval, idempotency, and audit evidence are implemented.
- [ ] Add MCP protocol-version compatibility and server dependency updates to
  the CI/security maintenance plan.

**Exit:** permission tests prove unauthorized and prompt-injected requests
cannot invoke writes or access other runs.

## Corporate security, privacy, and compliance baseline

This roadmap is designed to support enterprise review, not to assert that the
repository or its future implementation is compliant, certified, or approved.
Applicable obligations depend on the organization, app data, geography,
deployment, and contracts. Engage security, privacy, legal, and platform
owners before production or external-model use.

Use the following as control references and map them to the organization's
actual policy:

- **NIST AI RMF:** document Govern, Map, Measure, and Manage activities for
  the AI use case, affected users, failure impacts, evaluation, monitoring,
  and ownership. NIST describes AI RMF as voluntary; it is not certification.
- **OWASP GenAI / LLM application security guidance:** threat-model prompt
  injection, sensitive information disclosure, supply-chain risk, improper
  output handling, excessive agency, and unbounded consumption. Apply
  controls to the agent and every connected MCP server.
- **Secure SDLC / organizational ISMS controls:** access review, change
  approval, dependency/SBOM management, vulnerability handling, secrets
  management, auditability, incident response, and retention. Map to the
  organization's chosen ISO 27001, SOC 2, or other control framework rather
  than claiming this code alone satisfies it.
- **Privacy and data residency:** classify every input and output; minimize
  collection; redact or tokenize identifiers; define purpose, location,
  retention, deletion, and provider-training/retention terms. Apply GDPR or
  other privacy obligations only where the data and jurisdiction make them
  applicable.
- **Model and prompt governance:** approved provider/model list, pinned
  identifiers, prompt version review, evaluation before rollout, rollback
  process, and a named business/technical owner.

Minimum controls before a corporate pilot:

1. Threat model covering system prompt, untrusted app text, indirect prompt
   injection in Gherkin/logs/page source, MCP server compromise, tool abuse,
   cross-run/tenant access, data exfiltration, and denial-of-wallet.
2. No secrets in prompts, source-controlled fixtures, MCP resources, traces, or
   generated reports; use managed secret stores and least-privilege service
   identities.
3. Authorization enforced by server-side policy on every tool call, not by
   agent instructions or MCP tool descriptions. Read-only and write-capable
   identities are separate.
4. Human approval and audit trail for Jira writes, locator changes, reruns, or
   any action that changes application/test state. Record requester, approver,
   arguments, evidence, result, and timestamp.
5. Encryption in transit/at rest as required by the hosting organization;
   bounded artifact retention; deletion path; private network/data residency
   review where applicable.
6. Dependency pinning, vulnerability scanning, software bill of materials,
   artifact provenance, code review, CI tests, and controlled rollout/rollback.
7. Incident runbook for provider outage, prompt injection, data exposure,
   runaway agent/cost, false healing, corrupted retrieval index, and MCP
   credential compromise.
8. Risk-based evaluation and explicit release approval; no agent or model can
   override deterministic assertions, access policy, or release gates.

## Explicit non-goals for the first production slice

| Non-goal | Reason | Revisit when |
|---|---|---|
| Production use of archived AutoGen | Official repository is archived and no longer maintained | Not recommended; use MAF successor. AutoGen may be a separate learning-only exercise |
| Autonomous multi-agent conversation/debate for every test | Extra turns increase cost, latency, and non-determinism | Golden evaluation proves specific agent collaboration improves outcomes |
| Model-generated code or shell execution | Unsafe execution boundary and unnecessary for failure triage | Separate sandboxed code-generation project with security approval |
| Automatic locator catalog writes or assertion changes | Can hide real product defects and create false passes | Keep review/approval and regression gates; do not remove assertion protection |
| Autonomous Jira writes, test reruns, or device control | External side effects require identity, consent, and audit | A specific action is approved, authorized, bounded, and independently tested |
| Company/customer-data RAG and external model calls | No corpus, access policy, data residency, or provider contract is currently approved | Data owners approve corpus, privacy/security review, and retrieval evaluation pass |
| Fine-tuning or training a model | No governed training corpus or demonstrated need | Prompt/RAG baseline fails and a reviewed cost/quality/data-rights case exists |
| Production-scale queue/cloud deployment | Workload, SLO, budget, concurrency, and operational ownership are unknown | Pilot measurements support a separate capacity/reliability design |
| Full iOS General Store AI coverage | iOS selectors and target app behavior are not verified | Authorized iOS app/build and verified accessibility selectors are supplied |
| Playwright/web testing added to this mobile project | Current system is Appium mobile automation | A real web SUT justifies a separate adapter and test plan |
| Claiming SOC 2/ISO/NIST certification or blanket "MAANG compliance" | A roadmap or code change cannot grant organizational certification | Only after applicable independent organizational audit/attestation |

## How to measure progress and release readiness

Track three separate scorecards:

| Scorecard | Example measures | Authority |
|---|---|---|
| Mobile test quality | Pass/fail/skip/retry counts, duration, flaky rate, evidence completeness, defect escape rate | pytest/JUnit and approved test-management records |
| AI quality | Schema validity, failure precision/recall, evidence support, abstention, hallucination/unsupported-claim rate, human accept/edit/reject, false-heal rate | Versioned, human-reviewed evaluation set and adjudication |
| Operations and cost | p50/p95 latency, provider/tool error rate, token and cost per run/accepted diagnosis, budget-exhaustion count, retention/redaction status | Redacted trace/metrics and provider billing data |

Do not use overall "agent success" as the only metric. A workflow that
confidently returns the wrong root cause is not successful. Establish baseline
and acceptance thresholds with the project owner before a pilot; never invent
accuracy, cost, or ROI figures.

## BMAD report examples and reporting split

Use "BMAD-style" here to mean engineering artifacts that make AI-assisted work
traceable. It is not a claim that a BMAD tool or plugin is installed.

### Development/reporting artifacts

1. **Project brief:** user problem, target users, outcomes, constraints,
   assumptions, and exclusions.
2. **PRD:** user stories, measurable acceptance criteria, data policy, and
   failure/approval behavior.
3. **Architecture decision records:** why this provider, why/when MAF,
   retrieval approach, observability destination, threat model, alternatives,
   and revisit triggers.
4. **Implementation story/report:** files changed, contract changes, test
   commands/results, evaluation version/scores, known gaps, and rollback.
5. **Risk/decision log:** unresolved app behavior, data approval, severity,
   owner, due date, and decision.

### Per-run QA post-analysis report

```text
Run ID / commit / environment / app build / platform / device
Execution totals (read from JUnit/pytest): passed, failed, skipped, retried
AI status: enabled/disabled; provider/model/prompt/dataset versions if used
Failure group: category, confidence, needs-human-review
Evidence: test/scenario/step IDs and links to approved artifacts
Analysis: facts separated from hypotheses; missing/conflicting evidence
Self-healing: proposal only; validation result; approval status; never hide source failure
Actions: recommended owner and next step; no ticket/write executed without approval
Quality: tool errors, latency, token/cost, eval scores, redaction status
```

Keep two verdicts separate: **test verdict** (pytest/JUnit) and **AI analysis
status** (success, abstained, unavailable, or error). An AI report must never
turn a failed test into a passed test.

## Monitoring and operational controls

- **Correlate:** `run_id`, `scenario_id`, `step_id`, `agent_trace_id`,
  `tool_call_id`, commit, environment, platform, model and prompt versions.
- **Record:** node start/end, tool name and validated arguments summary, result
  category, output validation, retry count, latency, token/cost if available,
  and reviewer decision.
- **Redact:** secrets, access keys, user-entered values, personal data, and
  raw screenshot/page source unless explicitly approved and access-controlled.
- **Separate failures:** test/product failure; Appium/device/environment
  failure; retrieval failure; model/provider failure; tool/policy failure;
  report/export failure.
- **Control budgets:** timeout, maximum agent steps, tool calls, response bytes,
  retries, concurrency, per-run token/cost budget, retention, and queue depth.
- **Gate changes:** prompt/model/retrieval/index changes run offline evaluation
  and produce a comparable report before merge.
- **Recover safely:** provider/observability outage does not block standard
  pytest execution; failed evidence capture is visible as missing evidence, not
  fabricated evidence.

## Immediate development backlog

Start with these small issues/PRs; do not begin with a multi-agent system.

1. **AI-01: Define contracts and synthetic golden set.** Add typed schemas,
   fixture validation, evidence IDs, label provenance, and prompt-injection/
   unknown examples. Done when all tests run offline and reject malformed data.
2. **AI-02: Build context and redaction.** Extract safe pytest/BDD metadata,
   set size limits, separate untrusted app text, redact secrets. Done when
   adversarial tests prove context cannot grant tool authority.
3. **AI-03: Build read-only tool registry.** Implement run summary, failure
   step, locator metadata, evidence metadata, and known-failure search. Done
   when schemas, allowlists, audit events, and output caps pass unit tests.
4. **AI-04: Implement deterministic failure analysis.** Classify the synthetic
   failure set with evidence IDs and abstention. Done when confusion matrix and
   unknown handling are reported; no external model required.
5. **AI-05: Generate post-analysis and BMAD-style artifacts.** Read JUnit/
   pytest as the verdict source; write sanitized Markdown/JSON with evidence
   links. Done when counts match and AI never changes the verdict.
6. **AI-06: Add golden evaluation and monitoring.** Establish human-reviewed
   labels, metrics, CI artifact, budgets, and regression thresholds.
7. **AI-07: Add one LLM provider and optional LangChain adapter.** Only after
   baseline, data approval, and schema validation exist; keep no-key mode
   supported.
8. **AI-08: Add RAG, then MAF workflow orchestration if branching is
   required.** Evaluate retrieval first; add explicit state, approval, and
   checkpoint behavior only when the failure-analysis flow requires it.
9. **AI-09: Add review-only self-healing.** Candidate → deterministic
   validation → human approval → targeted regression; never auto-merge.
10. **AI-10: Add LangSmith or Langfuse and later MCP.** Select observability
    after the data policy review. Add MCP only for a demonstrated client/tool
    interoperability need.

## Decision rules

- Use ordinary Python, pytest, and the synthetic fixture before adding a
  framework dependency.
- Use LangChain only if integrations reduce work; use Microsoft Agent
  Framework for production-oriented multi-agent workflows after a compatibility
  spike; use DeepEval for repeatable LLM-specific evaluation and MCP for
  interoperability. They solve different problems.
- Do not add both MAF and LangGraph to the initial stack. If the team already
  standardizes on LangGraph, compare it with MAF in an ADR and select one
  orchestration runtime.
- Use one of LangSmith/Langfuse first; both are not required.
- Use lexical RAG first; a vector database is justified by measured semantic
  retrieval improvement, not by popularity.
- Keep multi-agent decomposition, fine-tuning, autonomous test execution,
  production hosting, and cross-platform iOS parity out of the first release.
- Do not claim model accuracy, healing rate, or ROI until measured against
  reviewed cases and a deterministic baseline.

## Source material consolidated

This plan consolidates the earlier AI/SDET roadmap, agentic AI roadmap, and
the reviewed image collection. The 34 images covered LLM fundamentals and
hallucination, requirement-to-test generation, mobile test agents, failure
analysis, UI vision and self-healing, MCP, RAG/vector retrieval, evaluation
metrics, monitoring, production model migration, multi-agent system design,
AI project structure, and learning/technology stacks. Repeated social posts
and alternative technology stacks were deduplicated; pictured technologies
are recommendations, not evidence that the project uses them.

## References

- [Microsoft AutoGen repository and archive notice](https://github.com/microsoft/autogen)
- [Microsoft Agent Framework repository](https://github.com/microsoft/agent-framework)
- [AutoGen to Microsoft Agent Framework migration guide](https://learn.microsoft.com/en-us/agent-framework/migration-guide/from-autogen/)
- [Model Context Protocol specification](https://modelcontextprotocol.io/specification/2025-11-25)
- [OWASP GenAI Security Project / LLM Top 10](https://genai.owasp.org/llm-top-10/)
- [NIST AI Risk Management Framework](https://www.nist.gov/itl/ai-risk-management-framework)
- [AI Engineer Concept-to-Practice Roadmap](AI_ENGINEER_CONCEPT_TO_PRACTICE_ROADMAP.md) — image concepts mapped to framework labs and status.
