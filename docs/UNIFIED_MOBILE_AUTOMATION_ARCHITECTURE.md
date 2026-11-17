# Unified Mobile Automation and AI Architecture

## Purpose and authority

This document defines the **current repository architecture** and its
compatible target extension for agentic AI. It is specific to this Python 3.14,
pytest-BDD, and Appium project; it does not describe a separate Java/Gradle
product or claim unimplemented integrations as delivered.

The companion [AI Implementation Plan](AI_IMPLEMENTATION_PLAN.md) is the
single source of truth for AI concepts, framework/MCP choices, agent roles,
security and compliance controls, cost controls, implementation phases,
progress, and acceptance criteria. This document owns the end-to-end system
architecture and mobile/CI operational boundaries. Avoid copying phase tables
or the AI concept-to-code map here.

## Architecture status

| Area | Current repository | Compatible target |
|---|---|---|
| Mobile execution | Python, pytest, pytest-BDD, Appium; Android/iOS driver configuration | Keep the same deterministic execution authority; verify iOS app selectors before claiming iOS flow coverage |
| Application model | General Store page objects and BDD flows | Preserve page objects, fixtures, and scenario intent; AI proposes changes but does not replace them |
| Locator handling | Versioned JSON XPath catalog and strict platform-aware resolution | Add evidence-based candidate recommendation only after failure; approved changes still go through tests and review |
| Run evidence | Allure attachments, optional screenshots and Android video | Correlate artifacts to run/scenario/step/build; apply approved access, redaction, and retention |
| CI and cloud execution | GitHub Actions quality checks and optional/manual BrowserStack workflow configuration | Add explicit preflight, build identity, device-capacity checks, and AI analysis as separate status outcomes |
| AI runtime | Not implemented | Add the bounded capabilities and infrastructure in the companion plan |
| Jira, Slack, app crawler, API integration, dashboards | Not implemented as this repository's current end-to-end capabilities | Add only through separately authorized adapters and the staged plan |

Existing capabilities are the baseline, not a claim that every target concern
is fully productionized. In particular, configured BrowserStack support does
not imply valid account secrets or an available device; iOS configuration does
not imply verified iOS selectors; screenshots do not imply visual AI; and
Allure does not imply LLM tracing.

## System context

```text
Engineer / QA / approved CI trigger
                |
       Validated run request
                |
   Preflight: config, app/build, tools,
   platform, secrets-present, capacity
                |
        pytest + pytest-BDD
                |
     Appium driver and page objects
         /                 \
 Android session       iOS session
         \                 /
     Platform-aware locator catalog
                |
  JUnit/pytest + Allure + allowed media
                |
      Immutable run/evidence references
                |
  Optional bounded AI analysis workflow
   (see AI Implementation Plan for detail)
                |
   Validated report / proposal / abstention
         /                    \
 Human review             Existing CI verdict
         |
 separately approved Jira/locator action
```

The mobile test path and AI analysis path are separate. A test run can
complete when AI is disabled or unavailable. AI can annotate evidence or
propose a next action, but cannot change a pytest/JUnit result, bypass a CI
gate, approve a merge, or autonomously update a locator.

## Component boundaries

| Component | Responsibility | Current/target boundary |
|---|---|---|
| Configuration and profile loader | Resolve platform, local/BrowserStack mode, environment profile, app reference, device settings, and safe feature options | Current foundation in `mobile_test_automation/config/` and `drivers/`; validate inputs before opening sessions |
| Test definition | Gherkin feature intent, pytest-BDD bindings, test fixtures and tags | Current in `tests/bdd/`; keep expected outcomes and scenario steps human-reviewable |
| Page/action layer | Reusable form, catalog, cart, and modal interactions | Current in `mobile_test_automation/pages/`; deterministic behavior only |
| Driver/session layer | Create, scope, and tear down local or cloud Appium sessions | Current in `mobile_test_automation/drivers/`; one isolated session per worker/scenario as configured |
| Locator layer | Resolve known semantic page/key to the selected platform's configured XPath | Current in `services/locator_logic.py`; failures must retain locator key, platform, and error evidence |
| Evidence/reporting | Capture permitted screenshots/video and attach to Allure; collect test result files | Current foundation in `services/reporting.py` and `tests/conftest.py`; failures during capture must not hide the original test exception |
| CI orchestrator | Run deterministic quality checks, optional device suites, upload artifacts, and report infrastructure/test outcomes distinctly | Current GitHub Actions foundation; future preflight and device-lane controls must fail closed on missing required inputs |
| AI application layer | Context, retrieval, model adapter, policy, workflow, evaluation, and reporting annotations | Target only; persistent operational memory is not implemented and must remain distinct from runtime context and cache |
| MCP adapters | Expose narrowly authorized internal tools/resources over MCP | Target only; MCP is a protocol boundary, not an authorization system |
| External integrations | Jira, chat notifications, app/build systems, observability, or device cloud APIs | Target/optional; use scoped identities, contracts, audit, and explicit data approval |

AI modules must not import or mutate page-object internals as a shortcut.
They consume versioned evidence/contracts and may request only named tools
whose policy is enforced by application code.

Keep trusted instructions/policy, versioned project knowledge, per-run
evidence/context, optional curated operational memory, and disposable cache as
separate logical data classes. Runtime evidence must not become persistent
memory automatically, and cached results must not override source evidence.
The [AI Implementation Plan](AI_IMPLEMENTATION_PLAN.md#context-instructions-memory-and-cache)
defines their lifecycles and the proposed memory record governance.

## Mobile execution architecture

### Platform separation

Android and iOS share test intent and appropriate page behavior, but the
session, app identity, platform selectors, device capabilities, and validated
evidence remain platform-specific.

| Concern | Android | iOS | Shared contract |
|---|---|---|---|
| Appium automation | UiAutomator2 capabilities and Android app package/activity | XCUITest capabilities and bundle/app reference | Driver lifecycle and scenario boundary |
| Locator values | Android XPath values currently populated for General Store | iOS catalog values are currently null/unverified | Semantic page and locator key |
| Execution target | Local device/emulator or configured BrowserStack | Local simulator/device or configured BrowserStack | Environment profile and run metadata |
| Coverage statement | BDD flow may be run when app/device/configuration are supplied | Session wiring exists; verify app/build and selectors before claiming scenario support | Report platform result independently |

Never fall back from one platform's selectors to another platform's selectors.
Missing or unverified selectors should produce an explicit configuration
failure, not an inferred pass.

### Locator lifecycle and proposed self-healing

The current locator path is deterministic:

1. A page object requests a semantic key from the locator service.
2. The service validates the catalog and selected platform.
3. The service resolves the configured XPath and waits for the required
   visibility condition.
4. It returns the element or raises an explicit configuration/lookup error.

The future recommendation path is additive and review-only:

1. Preserve the original test failure and collect the permitted hierarchy,
   locator key, platform, app build, and evidence references.
2. Search trusted catalog and hierarchy evidence for candidate selectors.
3. Validate syntax and platform, then check uniqueness, visibility, and
   expected element context through deterministic code.
4. Emit old/new values, evidence, uncertainty, impact, and rollback guidance.
5. Require a human-approved change, run the original assertion, and execute
   targeted regression.

No locator suggestion can remove or weaken an assertion, change a test verdict,
or write directly to the catalog.

### Hybrid context and API extensions

Native-to-webview switching and API-assisted setup/cleanup are **extension
points**, not verified current General Store flows. If a target app needs them:

- Keep context discovery/switching in a shared mobile utility and use the same
  Appium session; validate the requested context and restore the prior/default
  context in a `finally` path.
- Fail explicitly on unavailable or unexpected webviews; do not silently
  create a new driver or reset the session.
- Keep API clients separate from page objects. Correlate API setup/cleanup
  with the same run ID, retrieve credentials from the approved secret store,
  document shared app state, and verify state before UI assertions.

## Run lifecycle and CI operations

### Run preflight

Before any device allocation, workflow should validate and report:

- Selected environment, platform, suite/tags, test configuration, and required
  non-secret settings.
- Presence of required secret references without printing or expanding secret
  values.
- Python/project dependency and runner readiness for the selected workflow.
- App artifact/reference availability and expected platform/build identity.
- Device/OS profile and requested parallelism against configured capacity.
- Evidence/output directory and artifact publication settings.

Preflight results should include check ID, status, safe diagnostic, impact,
remediation, and whether execution was blocked. Missing app/build or invalid
required configuration must stop the lane instead of allowing a stale app or
misleading test failure.

### Local and BrowserStack lanes

- Local and BrowserStack are distinct execution modes; resolve credentials
  only for the selected remote profile.
- A run manifest should record run ID, source revision, app identity/build,
  environment, platform, device/OS, suite, start/end time, and artifact
  references. Never store secret values in the manifest.
- Each parallel worker receives an isolated driver/session and mutable test
  state. Bound worker count by configured provider capacity.
- Publish platform/lane outcomes independently. An Android success must not
  mask an iOS upload or execution failure.
- Scheduled regression, trusted PR-build execution, and wider device-pool
  coordination are future workflow capabilities unless implemented in the
  repository's active workflows.

### Quality gates and failure semantics

CI stages should remain explicit:

1. Static checks, dependency/security checks, unit tests, BDD discovery, and
   catalog/schema validation.
2. Optional device preflight and smoke/regression execution.
3. Artifact/report publishing and optional AI post-analysis.
4. Human approval for any external write, locator change, merge, or release.

Report distinct statuses for code/test failure, app/device/environment
failure, provider outage, AI abstention/error, and report/notification failure.
A provider outage must not alter deterministic test execution. A
notification/reporting failure must be visible but must not overwrite the
actual test verdict.

Track first-attempt pass, passed-after-retry, exhausted failure, skip/block,
and retry attempts separately. Retried success is evidence of recovery or
flakiness; it is not the same as a first-attempt pass.

## Evidence, reporting, and post-run handoff

Every run should have stable correlation IDs for run, scenario, step, session,
and evidence. Artifact references should include provenance (source revision,
app build, platform, capture time, and applicable test case) and an access/
retention classification.

Current reporting uses Allure attachments and optional screenshots/video.
Future report adapters may publish approved summaries to Markdown/JSON, CI
artifacts, or an authorized Jira/chat integration. A canonical report must
separate:

- **Authoritative execution facts:** sourced from pytest/JUnit/Allure.
- **AI analysis:** category, evidence citations, confidence, abstention/error,
  and clearly labeled hypotheses.
- **Actions:** recommendations and approval state, not implied completion.

Do not duplicate raw screenshots, full device logs, page source, or large
videos into AI traces when a protected artifact reference and a short,
redacted excerpt are sufficient. Artifact retention, access, deletion, and
external data transfer follow the organization's policy.

## Observability and operational handoffs

The following are useful target telemetry fields; adding them does not by
itself mean the relevant integrations exist:

| Signal group | Examples |
|---|---|
| Run identity | Run ID, commit, test suite, app/build ID, platform, environment, device/OS |
| Execution | Scenario/step outcome, first attempt/retry, duration, driver/session lifecycle |
| Locator | Semantic key, platform, resolution outcome, timeout, catalog version |
| Evidence | Artifact ID, kind, scenario/step reference, redaction/retention classification |
| AI workflow | Capability/model/prompt/dataset version, state, tool call, validation/approval outcome |
| Reliability | Preflight failure, device/provider availability, timeout, retry, artifact/report failure |
| Cost and quality | Tokens/cost, latency, evaluation score, reviewer outcome, false-heal indicator when available |

Keep monitoring data redacted and bounded. Establish retention and access
before enabling hosted observability. The AI plan defines the metrics,
token-budget policy, compliance references, and agent/MCP-specific controls.

## Device fleet, app crawling, and scale extensions

These are optional extensions, not current delivered capabilities:

- **Device-fleet coordination:** select compatible device/app/platform
  combinations, isolate workers, account for concurrency quotas, and collect
  per-device health. Do not retry endlessly on unavailable capacity.
- **App hierarchy crawler:** inspect only authorized test builds and gather
  accessible IDs, resource IDs, labels, hierarchy snapshots, screen
  transitions, and build/version. Store fingerprints as reviewable baselines.
- **Locator drift analysis:** compare current hierarchy/selector outcomes with
  a last accepted baseline; report missing, changed, ambiguous, or
  degraded/fallback locators. A drift report opens triage; it does not update
  selectors autonomously.
- **Parallel regression:** add only after run isolation, provider quotas,
  unique run/build IDs, deterministic reporting, and failure triage have been
  tested at lower concurrency.
- **Performance/security/accessibility suites:** keep as separate test
  strategies and authorization scopes. An agent is not a substitute for
  deterministic scanners, specialist testing, or approved test environments.

## Environment, secrets, and artifact policy

- Keep `.env.example` to placeholders; local `.env` remains ignored.
- Put CI credentials in protected secret stores and non-sensitive selectors in
  validated variables/inputs.
- Resolve only credentials required by the selected lane and integration.
- Report missing variable names, never credential values.
- Never put credentials, tokens, cookies, personal data, unapproved test-user
  information, or secrets in feature text, command-line arguments, prompts,
  screenshots, traces, Jira descriptions, or reports.
- Do not share caches across identities or mutable test sessions. Cache keys
  for reusable non-sensitive artifacts should include relevant source,
  schema, tool, and corpus versions.
- Define artifact encryption, allowed recipients, expiration, and deletion
  path before retaining sensitive run evidence.

The companion plan holds the corporate security, privacy, and compliance
baseline. No standard certification or regulatory compliance is claimed by
this architecture.

## Decision records and synchronized documents

Use the companion [AI Implementation Plan](AI_IMPLEMENTATION_PLAN.md) for
implementation progress, standards references, architecture choice (including
the AutoGen archive/MAF recommendation), exact MCP server plan, token-cost
minimization, and AI acceptance gates.

Keep this architecture current when the implementation changes in a way that
affects system boundaries, runtime data flows, integration trust, or test
execution authority. Update the implementation plan when a capability starts,
passes its acceptance gate, or changes priority/status. For shared decisions:

1. Record the decision and alternatives once in an ADR or the plan's decision
   record.
2. Put component/data-flow consequences here and link to that decision.
3. Keep status/detail in the implementation plan and link back here.
4. Avoid copying the same table, policy, or milestone into both documents.

## Related documentation

- [AI Implementation Plan](AI_IMPLEMENTATION_PLAN.md) — canonical AI roadmap,
  agents, MCP, security, compliance, cost, progress, and acceptance criteria.
- [AI Architect / SDET Practical Roadmap](AI_ARCHITECT_SDET_PRACTICAL_ROADMAP.md) —
  learning and portfolio guide; the unified architecture and implementation
  plan take precedence for project-specific design and status.
- [Jira-ready General Store manual test plan](General_Store_Manual_Test_Plan.xlsx) —
  manual test cases, execution log, and test lifecycle.
- [AI Automation Interview Guide](AI_AUTOMATION_INTERVIEW_GUIDE.md) — AI
  engineering questions and evidence-grounded answers.
- [Automation Framework Interview Guide](AUTOMATION_FRAMEWORK_INTERVIEW_GUIDE.md) —
  deterministic framework, mobile, web/API, and CI questions.
