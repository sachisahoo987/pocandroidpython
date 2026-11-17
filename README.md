# Mobile Test Automation

An installable Python/Appium framework for the General Store mobile application.
Android and iOS driver sessions use the same test and page-object modules, with
platform-specific XPath values selected from one JSON catalog.

## Project layout

```text
mobile_test_automation/
  config/       Runtime settings and QA/stage properties profiles
  drivers/      Local and BrowserStack Appium session creation
  pages/        General Store page objects and shared page behavior
  resources/    App locators and BrowserStack device capabilities
  services/     Locator resolution, gestures, reporting, and dialog assertions
  tools/        Locator-key generation
tests/
  bdd/          Gherkin features and pytest-bdd entry points
    steps/      Gherkin step bindings
  fixtures/     Synthetic inputs for the AI-QA implementation plan
  unit/         Device-independent tests
```

Keep application behavior in `mobile_test_automation`, scenario wiring in
`tests/bdd` and its `steps` package, and regression checks in `tests/unit`.
The shared locator catalog includes the native, hybrid WebView, and mobile
browser selectors represented in the
[upstream General Store examples](https://github.com/kmieshkov/appium-General-Store/tree/main/src/test/java);
failure DOM snapshots are saved locally for inspection and are never used to
rewrite selectors automatically.

## AI implementation status

The current framework is deterministic mobile automation; it does not yet
include an LLM, RAG pipeline, agent, MCP integration, or self-healing logic.
See the [unified mobile automation architecture](docs/UNIFIED_MOBILE_AUTOMATION_ARCHITECTURE.md)
for current system boundaries and target mobile/CI flows, and the
[AI implementation plan](docs/AI_IMPLEMENTATION_PLAN.md) for the repository
audit, AutoGen/MAF multi-agent direction, MCP server plan, enterprise security
and compliance controls, token-cost optimization, staged development
checklist, and out-of-scope roadmap. The architecture and plan are complementary
sources of truth with no duplicated phase tracker. Synthetic starter inputs
are in `tests/fixtures/ai_qa/starter_cases.json`.

## Interview preparation

- [AI automation interview guide](docs/AI_AUTOMATION_INTERVIEW_GUIDE.md) —
  LLMs, RAG, agents, MCP, evaluation, governance, and production AI.
- [Automation framework interview guide](docs/AUTOMATION_FRAMEWORK_INTERVIEW_GUIDE.md) —
  framework design, Appium, Playwright, API testing, CI, and quality strategy.
- [AI Architect / SDET practical roadmap](docs/AI_ARCHITECT_SDET_PRACTICAL_ROADMAP.md) —
  learning plan and portfolio milestones.

## AI engineer concept labs

The [AI Engineer Concept-to-Practice Roadmap](docs/AI_ENGINEER_CONCEPT_TO_PRACTICE_ROADMAP.md)
maps all concepts shown in the eight supplied AI-engineer infographic images
to this framework, with current status and a practical implementation or
learning exercise for each. It complements—but does not replace—the canonical
[AI implementation plan](docs/AI_IMPLEMENTATION_PLAN.md).

## Documentation map

- **Current system boundaries:** [Unified architecture](docs/UNIFIED_MOBILE_AUTOMATION_ARCHITECTURE.md).
- **AI status, decisions, and acceptance gates:** [AI implementation plan](docs/AI_IMPLEMENTATION_PLAN.md).
- **Hands-on learning sequence:** [Practical roadmap](docs/AI_ARCHITECT_SDET_PRACTICAL_ROADMAP.md),
  sequenced to follow the implementation plan.
- **Image concepts mapped to framework labs:** [AI Engineer concept roadmap](docs/AI_ENGINEER_CONCEPT_TO_PRACTICE_ROADMAP.md).
- **Interview reference:** the two focused guides above; use them as speaking
  aids, not implementation status records.

## Jira-ready manual test plan

The [General Store manual test workbook](docs/General_Store_Manual_Test_Plan.xlsx)
contains the test plan, scenario groups, 28 Gherkin-format manual test cases,
execution and defect logs, and the full manual QA lifecycle. Confirm the exact
public app build and build-dependent expected behavior before execution; all
cases are initially marked `Not Run`. Regenerate it with
`python scripts/generate_general_store_test_plan.py`.

## Setup

The project targets CPython 3.14. Create a virtual environment and install the
project dependencies:

```powershell
py -3.14 -m venv .venv
& .\.venv\Scripts\Activate.ps1
python -m pip install .
```

```sh
python3.14 -m venv .venv
. .venv/bin/activate
python -m pip install .
```

Copy `.env.example` to `.env` and set device/app values for your environment.
`.env` is ignored by Git. Never commit credentials.

BrowserStack profiles are selected with `TEST_ENVIRONMENT=qa` or
`TEST_ENVIRONMENT=stage`. The matching
`mobile_test_automation/config/environments/{qa,stage}.properties` file supplies
device defaults and BrowserStack project/build labels. Credentials are
referenced by variable name and are not stored in the properties files. For
local runs, set `QA_BROWSERSTACK_USERNAME` / `QA_BROWSERSTACK_ACCESS_KEY` or
`STAGE_BROWSERSTACK_USERNAME` / `STAGE_BROWSERSTACK_ACCESS_KEY`, plus the
platform app reference variables. For GitHub Actions, create GitHub Environments
named `qa` and `stage`. In `qa`, configure `QA_BROWSERSTACK_USERNAME` and
`QA_BROWSERSTACK_ACCESS_KEY`; in `stage`, configure
`STAGE_BROWSERSTACK_USERNAME` and `STAGE_BROWSERSTACK_ACCESS_KEY`. Configure
each environment with its own `BROWSERSTACK_APP_ANDROID` and
`BROWSERSTACK_APP_IOS` secrets. The selected properties file resolves its
environment-specific credentials to the standard BrowserStack variables before
pytest starts.

## Run tests

Run device-independent checks:

```sh
python -m pytest tests/unit
```

The `Python CI` GitHub Actions workflow runs on pushes and pull requests, and
can also be started manually from the Actions tab. It audits dependencies,
checks Ruff lint and formatting (including naming and redundant-pattern rules),
checks application types with mypy, detects duplicated application code, runs
unit tests with coverage, and verifies BDD scenario discovery without requiring
a device. CI enforces a 70% minimum coverage threshold and uploads an XML
report as a workflow artifact. Dependabot checks for Python and GitHub Actions
updates weekly. CodeQL analyzes the Python code on pushes, pull requests, and
weekly. CodeQL availability for private repositories depends on the
repository's GitHub Advanced Security eligibility and settings.

Run the same code-quality checks locally after installing the optional tools:

```sh
python -m pip install ".[quality]"
python -m pip_audit .
python -m ruff check mobile_test_automation tests
python -m ruff format --check mobile_test_automation tests
python -m mypy
python -m pylint --disable=all --enable=duplicate-code --min-similarity-lines=10 mobile_test_automation
python -m pytest tests/unit --cov --cov-report=term-missing --cov-report=xml:coverage.xml
```

Run General Store BDD scenarios with a local Android device. The managed runner
checks the connected device and installed app, grants requested Android runtime
permissions, starts Appium when it is not already available, runs pytest, and
terminates the app and any Appium server it started:

```powershell
python scripts/run_local_android.py tests/bdd/test_general_store.py -k test_launch_fill_form_and_navigate_to_products
```

Run all local BDD scenarios by omitting the test selector:

```powershell
python scripts/run_local_android.py
```

The runner leaves an already-running Appium server untouched. Set `UDID` when
multiple devices are connected; the General Store package defaults to
`com.androidsample.generalstore`, and the launch activity is discovered from
the installed app unless `APP_ACTIVITY` is set. `AUTO_GRANT_PERMISSIONS=true`
grants only dangerous runtime permissions requested by that app.
`RESET_APP_DATA=true` clears only the configured test app before execution for
repeatability; set it to `false` to retain app data. Video and
per-action screenshots are disabled by default for faster local runs; set
`RECORD_VIDEO=true` or `ACTION_SCREENSHOTS=true` when those artifacts are
needed. Failure screenshots and native DOM dumps are enabled by default; DOM
snapshots are written to `%TEMP%\\pocandroid-dom-dumps` (or `DOM_DUMP_DIR`) and
attached to Allure when available.

Local BDD runs use one session and remain sequential by default. Direct
`python -m pytest tests/bdd` execution still requires an Appium server to be
started separately. Parallel workers are only used by the BrowserStack workflow.

In the manual BrowserStack workflow, set `parallel` to `false` for sequential
Android/iOS platform lanes and one worker per lane. Set it to `true` to run the
two platform lanes concurrently; choose `workers` as `1`, `2`, or `3` for
additional scenario workers within each lane.

Available BrowserStack sessions are approximately `workers` when `parallel` is
false and `2 × workers` when true. Keep that total within the concurrency
capacity of your BrowserStack plan. With `parallel=false`, the workflow forces
one worker per lane regardless of the selected worker count. These controls
belong to the BrowserStack workflow; local real-device commands remain
sequential and do not read them.

Start an Appium server and connect an Android device or emulator first. Set
`APP_PACKAGE` and `APP_ACTIVITY`; `DEVICE_NAME`, `UDID`, and `PLATFORM_VERSION`
can be supplied when needed.

Local Android and iOS execution both use `RUN_ENV=local`; Android uses
`APP_PACKAGE` and `APP_ACTIVITY`, while iOS uses `IOS_DEVICE_NAME` and either
`IOS_BUNDLE_ID` or `IOS_APP`. The existing local Appium endpoint and device
capabilities remain independently configured from BrowserStack.

BrowserStack execution requires `BROWSERSTACK_USERNAME`,
`BROWSERSTACK_ACCESS_KEY`, and a platform-specific app reference:
`BROWSERSTACK_APP_ANDROID` or `BROWSERSTACK_APP_IOS`. Choose device names and OS
versions available to your BrowserStack account with the corresponding
`BROWSERSTACK_ANDROID_DEVICE_NAME` / `BROWSERSTACK_ANDROID_OS_VERSION` and
`BROWSERSTACK_IOS_DEVICE_NAME` / `BROWSERSTACK_IOS_OS_VERSION` settings. The
manual GitHub Actions workflow accepts device selections at dispatch and lets
you select QA or stage, control platform-lane concurrency, and set the worker
count. BrowserStack account concurrency limits apply.

Run one Android landing scenario directly against BrowserStack after setting
the required variables above:

```powershell
$env:RUN_ENV = "browserstack"
$env:TEST_ENVIRONMENT = "qa"
$env:PLATFORM = "android"
python -m pytest tests/bdd/test_general_store.py -k test_launch_fill_form_and_navigate_to_products
```

BDD steps report `[STEP START]`, `[STEP PASS]`, and `[STEP FAIL]` with the
scenario and step names in pytest's live console log. Failed steps include the
exception message; failed scenario setup (for example, missing BrowserStack
configuration) is reported by pytest before a step can start.

The unit tests do not contact Appium, devices, or BrowserStack. The BDD scenarios
require an installed app, device, and configured session.
To run the device-dependent BDD scenarios in GitHub Actions, start the
`Mobile Test Automation (BrowserStack)` workflow manually and configure the
required secrets in the selected GitHub Environment.

Failed scenarios are retried up to two times. Allure results are written to
`allure-results/`; if the Allure CLI is installed, view them with
`allure serve allure-results`. Each pytest-BDD step is recorded as a nested
Allure step with its pass or fail status, in addition to the live console log.

Application selectors are kept in one versioned JSON catalog. Each locator
contains an XPath per platform (`android` and `ios`); the resolver selects the
XPath for the active Appium session and fails explicitly when a selector is
unconfigured. The checked-in General Store XPath values are verified for
Android. The iOS XPath entries remain `null` until verified from the iOS app's
accessibility hierarchy; an iOS app build and verified selectors are required
before the General Store BDD flows can complete on iOS.

## Locator-key generator

Generate enum modules for the supported General Store locator pages:

```sh
python -m mobile_test_automation.tools.generate_locator_keys
```

The default input is
`mobile_test_automation/resources/locators/locators.json`. Use `--input PATH`
and `--output-dir PATH` to override the paths.
