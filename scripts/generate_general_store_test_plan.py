"""Generate a Jira-import-oriented manual test workbook without third-party packages."""

from __future__ import annotations

from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZIP_DEFLATED, ZipFile

OUTPUT = Path(__file__).resolve().parents[1] / "docs" / "General_Store_Manual_Test_Plan.xlsx"

# ID, scenario, area, title, priority, preconditions, data, Gherkin, steps, expected
CASES = [
    (
        "001",
        "001",
        "App lifecycle",
        "Cold launch displays the shopper form",
        "High",
        "App installed on a supported Android device and not running.",
        "Fresh install or cleared app state.",
        "Given the app is installed and not running\nWhen the tester launches the app\nThen the shopper details form is displayed and usable",
        "1. Launch the app.\n2. Wait for the first screen.\n3. Observe form controls and permission prompts.",
        "App opens without a crash; country, name, gender, and shop controls are visible or reachable.",
    ),
    (
        "002",
        "001",
        "App lifecycle",
        "Relaunch app and record state behavior",
        "Medium",
        "App has been launched once and closed normally.",
        "Synthetic name: ManualTester.",
        "Given the tester entered sample details\nWhen the tester closes and relaunches the app\nThen the app is usable and reset or persistence behavior is recorded",
        "1. Enter a sample name and country.\n2. Close and relaunch the app.\n3. Record the displayed state.",
        "App launches successfully. Compare reset/persistence behavior with the requirement; do not assume persistence.",
    ),
    (
        "003",
        "002",
        "Shopper form",
        "Open and inspect the country picker",
        "High",
        "Shopper details form is displayed.",
        "None.",
        "Given the shopper details form is displayed\nWhen the tester taps the country selector\nThen a country picker is presented and can be inspected",
        "1. Tap the country selector.\n2. Inspect options and scrolling.\n3. Dismiss the picker.",
        "Country choices are readable and selectable; picker can be dismissed without a crash.",
    ),
    (
        "004",
        "002",
        "Shopper form",
        "Select a country from the picker",
        "High",
        "Shopper form and country picker are available.",
        "India or another country present in this build.",
        "Given the country picker is open\nWhen the tester selects an available country\nThen the selection is shown on the shopper form",
        "1. Open the picker.\n2. Select a country.\n3. Verify the form value.",
        "Picker closes and the selected country is displayed.",
    ),
    (
        "005",
        "002",
        "Shopper form",
        "Dismiss picker without changing selection",
        "Medium",
        "A country is selected on the form.",
        "Record selected country before opening picker.",
        "Given a country is selected\nWhen the tester opens and dismisses the picker without choosing another\nThen the form remains usable and selection behavior is recorded",
        "1. Record selected country.\n2. Open and dismiss picker with Back/close.\n3. Compare the selected country.",
        "Picker closes without a crash; selection behavior is recorded and compared with requirements.",
    ),
    (
        "006",
        "003",
        "Shopper form",
        "Submit form with an empty name",
        "High",
        "Shopper form is displayed with a valid country.",
        "Name empty; valid available country.",
        "Given a valid country and empty name\nWhen the tester taps Lets Shop\nThen the app communicates required-name validation and does not silently proceed",
        "1. Leave name blank.\n2. Tap Lets Shop.\n3. Record message and resulting screen.",
        "The app does not silently proceed as though a valid name was supplied; confirm exact UX requirement.",
    ),
    (
        "007",
        "003",
        "Shopper form",
        "Submit a whitespace-only name",
        "Medium",
        "Shopper form is displayed with a valid country.",
        "Name: three spaces.",
        "Given the shopper form is displayed\nWhen the tester enters only spaces and taps Lets Shop\nThen behavior follows the required-name validation rule",
        "1. Enter three spaces.\n2. Tap Lets Shop.\n3. Record whether the app accepts or rejects the value.",
        "Record observed behavior; confirm expected rule before filing a defect.",
    ),
    (
        "008",
        "003",
        "Shopper form",
        "Change gender selection",
        "Low",
        "Shopper form and gender controls are visible.",
        "Switch to the other available option.",
        "Given the shopper form is displayed\nWhen the tester selects the other gender option\nThen the selected control state is visibly updated",
        "1. Observe current selection.\n2. Tap the other option.\n3. Verify selected/unselected state.",
        "Selected state changes visibly and form remains usable.",
    ),
    (
        "009",
        "003",
        "Shopper form",
        "Continue with valid shopper details",
        "High",
        "Shopper details form is displayed.",
        "Name ManualTester; a country available in this build.",
        "Given the tester entered a non-empty name and selected a country\nWhen the tester taps Lets Shop\nThen the product list is displayed",
        "1. Enter ManualTester.\n2. Select country and optionally change gender.\n3. Tap Lets Shop.",
        "App navigates to a populated product list without a crash.",
    ),
    (
        "010",
        "004",
        "Product catalog",
        "Verify product list content and controls",
        "High",
        "Valid shopper details submitted; product list displayed.",
        "Products visible in the installed build.",
        "Given the product list is displayed\nWhen the tester inspects visible product cards\nThen each card presents product information and a cart action",
        "1. Inspect product cards.\n2. Record names, prices, images, and buttons.\n3. Check clipping/alignment.",
        "Visible cards have readable details and usable add-to-cart controls.",
    ),
    (
        "011",
        "004",
        "Product catalog",
        "Scroll product list to later products",
        "Medium",
        "Product list has items beyond the first screen.",
        "A later product, if available.",
        "Given the product list is displayed\nWhen the tester scrolls down and back up\nThen additional products can be inspected and the list remains responsive",
        "1. Scroll down.\n2. Inspect later cards.\n3. Scroll to the top.",
        "List scrolls without freezing or losing content; inaccessible cards are recorded.",
    ),
    (
        "012",
        "005",
        "Cart",
        "Add one product to cart",
        "High",
        "Product list is displayed.",
        "One product available in this build; record its name and price.",
        "Given the product list is displayed\nWhen the tester adds one product\nThen the product is available in the cart",
        "1. Record product name and price.\n2. Tap its Add to Cart button once.\n3. Open cart.",
        "Selected product appears in cart with matching name and price.",
    ),
    (
        "013",
        "005",
        "Cart",
        "Add two different products to cart",
        "High",
        "Product list displayed with two products.",
        "Two distinct products; use Air Jordan 4 Retro/Jordan 6 Rings only if present.",
        "Given two distinct products are available\nWhen the tester adds both and opens the cart\nThen both selected products are listed",
        "1. Record two names and prices.\n2. Add each once.\n3. Open cart and compare.",
        "Both products appear once with corresponding displayed prices.",
    ),
    (
        "014",
        "005",
        "Cart",
        "Add the same product more than once",
        "Medium",
        "Product list is displayed.",
        "One product added twice.",
        "Given the product list is displayed\nWhen the tester adds the same product twice\nThen the cart reflects the app's repeated-add behavior",
        "1. Add one product and note feedback.\n2. Add it again.\n3. Inspect line-item or quantity behavior.",
        "Record actual behavior (duplicate line, quantity, or other) and compare with approved requirement.",
    ),
    (
        "015",
        "006",
        "Cart",
        "Open cart and verify selected products",
        "High",
        "At least one product was added.",
        "One or more selected products.",
        "Given a product was added to the cart\nWhen the tester opens the cart\nThen the cart shows selected product details",
        "1. Open cart.\n2. Inspect names, prices, and quantities if shown.\n3. Compare with selections.",
        "Cart contents match selected products; no unrelated item is shown.",
    ),
    (
        "016",
        "006",
        "Cart",
        "Verify displayed total against cart lines",
        "High",
        "Cart contains at least two products with visible prices.",
        "Exact prices displayed in this build.",
        "Given cart products have visible prices\nWhen the tester sums line prices and compares with the displayed total\nThen the total and tax/fee breakdown follow the approved pricing rule",
        "1. Record each line price.\n2. Sum manually.\n3. Compare total and tax/fee lines.",
        "Displayed amount reconciles to confirmed pricing rule; account for tax/fees if shown.",
    ),
    (
        "017",
        "006",
        "Cart",
        "Verify currency and price formatting",
        "Medium",
        "Cart contains at least one product.",
        "A product with non-zero price.",
        "Given the cart contains a product\nWhen the tester reviews line prices and total\nThen currency and rounding are consistently presented",
        "1. Inspect line and total formatting.\n2. Compare decimal places and currency symbol.\n3. Record inconsistencies.",
        "Formatting is consistent with app locale/configuration; record actual currency and locale.",
    ),
    (
        "018",
        "006",
        "Cart",
        "Open cart with no selected products",
        "Low",
        "Clean session with no products; cart control reachable if supported.",
        "No cart items.",
        "Given no products have been added\nWhen the tester attempts to open the cart\nThen empty-cart behavior is recorded and the app remains stable",
        "1. Start clean session.\n2. Attempt to open cart.\n3. Record empty-state/navigation behavior.",
        "App remains stable; compare observed behavior with product requirement.",
    ),
    (
        "019",
        "007",
        "Terms",
        "Open Terms dialog from cart",
        "High",
        "Cart screen and Terms control are available.",
        "None.",
        "Given the cart is displayed\nWhen the tester long-presses Terms and Conditions\nThen the Terms dialog is displayed",
        "1. Locate Terms control.\n2. Long-press it.\n3. Observe dialog.",
        "Terms dialog opens with readable content; record if build specifies a normal tap instead.",
    ),
    (
        "020",
        "007",
        "Terms",
        "Dismiss Terms dialog",
        "Medium",
        "Terms dialog is open.",
        "None.",
        "Given the Terms dialog is open\nWhen the tester uses the available close or Back action\nThen the dialog closes and cart remains usable",
        "1. Use close control if present.\n2. Otherwise use device Back.\n3. Verify cart.",
        "Dialog closes using supported action and cart state remains intact.",
    ),
    (
        "021",
        "007",
        "Terms",
        "Read and scroll Terms content",
        "Low",
        "Terms dialog is open and content is available.",
        "None.",
        "Given the Terms dialog is open\nWhen the tester reads and scrolls the content\nThen the content remains readable",
        "1. Read initial content.\n2. Scroll within dialog.\n3. Record readability/end of content.",
        "Text remains legible and dialog responds to scrolling where applicable; this does not approve legal wording.",
    ),
    (
        "022",
        "008",
        "Checkout handoff",
        "Review checkout handoff without purchasing",
        "High",
        "Cart contains an item and proceed control is available.",
        "No payment or personal data.",
        "Given the cart contains a product\nWhen the tester taps checkout or proceed\nThen the configured handoff is observed and no purchase is completed",
        "1. Record cart contents and total.\n2. Tap proceed once.\n3. Observe destination and stop before submitting data.",
        "Handoff is recorded; no payment or real order is submitted. Confirm destination with app owner.",
    ),
    (
        "023",
        "008",
        "Checkout handoff",
        "Handle unavailable network at checkout",
        "Medium",
        "Cart has an item; network can be safely disabled/restored.",
        "Non-production device; no payment data.",
        "Given the cart contains a product and network is unavailable\nWhen the tester taps checkout or proceed\nThen an observable response occurs and app remains recoverable",
        "1. Disable network.\n2. Tap proceed.\n3. Record response; restore network.",
        "App does not become permanently unresponsive; document error/retry behavior and do not submit an order.",
    ),
    (
        "024",
        "009",
        "Interruption",
        "Resume app after backgrounding form entry",
        "Medium",
        "Shopper form is displayed.",
        "Name ManualTester; available country.",
        "Given the tester partially completed the form\nWhen the app is backgrounded and resumed\nThen the app is usable and field state is recorded",
        "1. Enter name and select country.\n2. Background for about 10 seconds.\n3. Resume from app switcher.",
        "App resumes without crash; persistence behavior is recorded against requirement.",
    ),
    (
        "025",
        "009",
        "Interruption",
        "Handle device rotation during browsing",
        "Low",
        "Product list displayed on a device with rotation enabled.",
        "Optional selected product.",
        "Given the product list is displayed\nWhen the tester rotates to landscape and back\nThen the app remains usable and state is recorded",
        "1. Rotate to landscape.\n2. Inspect content and controls.\n3. Return to portrait.",
        "No crash/unusable clipped controls on supported orientations; record unsupported behavior.",
    ),
    (
        "026",
        "010",
        "Accessibility",
        "Check form labels, focus, and keyboard",
        "Medium",
        "Shopper form displayed; screen reader available if required.",
        "Name ManualTester.",
        "Given the shopper form is displayed\nWhen the tester navigates fields with touch, keyboard, and available screen reader\nThen controls can be identified and operated",
        "1. Enter sample text.\n2. Use keyboard Next/Done.\n3. Inspect screen-reader labels if available.",
        "Controls are operable and understandable; judge against the team's accessibility standard.",
    ),
    (
        "027",
        "010",
        "End-to-end",
        "Complete shopper-to-cart journey with two items",
        "High",
        "Fresh app launch; two products available.",
        "ManualTester; available country; two products in build.",
        "Given the shopper form is displayed\nWhen valid details are entered and two products added\nThen the cart shows both products and a consistent total",
        "1. Enter sample name and country.\n2. Tap Lets Shop.\n3. Add two distinct products and open cart.\n4. Compare names, prices, total.",
        "Flow completes without crash; items are present and total follows the confirmed pricing rule.",
    ),
    (
        "028",
        "010",
        "End-to-end",
        "Complete cart review and Terms journey",
        "Medium",
        "At least one product is in cart.",
        "At least one product; no real checkout.",
        "Given a product was added and cart opened\nWhen the tester reviews total, opens and dismisses Terms\nThen cart contents remain and no purchase is made",
        "1. Review product and total.\n2. Open and dismiss Terms.\n3. Verify cart contents; stop before checkout.",
        "Cart remains usable with same contents and no order is submitted.",
    ),
]

SCENARIOS = [
    (
        "001",
        "App lifecycle and launch",
        "Installation, cold launch, and relaunch stability.",
        "001; 002",
        "High",
    ),
    (
        "002",
        "Country selection",
        "Inspect, select, and dismiss the country picker.",
        "003; 004; 005",
        "High",
    ),
    (
        "003",
        "Shopper details form",
        "Validate name, gender, and transition to product catalog.",
        "006; 007; 008; 009",
        "High",
    ),
    (
        "004",
        "Product catalog browsing",
        "Inspect product cards and product-list scrolling.",
        "010; 011",
        "High",
    ),
    (
        "005",
        "Add products to cart",
        "Add one, multiple, and repeated products.",
        "012; 013; 014",
        "High",
    ),
    (
        "006",
        "Cart review and pricing",
        "Verify items, amounts, formatting, and empty cart.",
        "015; 016; 017; 018",
        "High",
    ),
    (
        "007",
        "Terms and conditions",
        "Open, read, and dismiss Terms dialog.",
        "019; 020; 021",
        "Medium",
    ),
    (
        "008",
        "Checkout handoff",
        "Observe handoff and offline response without purchase.",
        "022; 023",
        "High",
    ),
    (
        "009",
        "Mobile interruption and recovery",
        "Check background/resume and supported rotation.",
        "024; 025",
        "Medium",
    ),
    (
        "010",
        "Accessibility and end-to-end regression",
        "Review form usability and complete representative journeys.",
        "026; 027; 028",
        "High",
    ),
]

PLAN = [
    ("Test Plan ID", "GS-TP-001", "Recommended Jira issue type: Test Plan if supported."),
    (
        "Title",
        "General Store Android - Manual Functional Test Plan",
        "Confirm exact public app source and build before execution.",
    ),
    (
        "Objective",
        "Validate the shopper journey from launch and shopper details through product browsing, cart, Terms, and checkout handoff.",
        "Manual execution only; no real purchase or payment.",
    ),
    (
        "Functional scope",
        "Install/launch, country picker, name and gender fields, product list, add-to-cart, cart contents/totals, Terms, checkout handoff.",
        "See traceable cases on Test Cases tab.",
    ),
    (
        "Quality scope",
        "Basic mobile interruption/recovery and form accessibility/usability observations.",
        "Not formal accessibility certification.",
    ),
    (
        "Out of scope",
        "Real payment/order submission; backend/API; security penetration; load/performance; verified iOS coverage; production data.",
        "Requires separate approval and environment.",
    ),
    (
        "Target platform",
        "Android manual testing is primary.",
        "Repository iOS locator values are null and iOS app behavior is unverified.",
    ),
    (
        "Application/build",
        "Public General Store sample app; record exact distribution, package, version, and build.",
        "Public copies can differ in inventory, prices, labels, and checkout destination.",
    ),
    (
        "Environment",
        "Supported Android phone/emulator, reusable app state, network available for baseline; optional offline case.",
        "Record model, OS, screen size, app version, and network in Execution Log.",
    ),
    (
        "Test data",
        "Synthetic name ManualTester; select countries and products actually present in installed build.",
        "No personal, payment, or customer data.",
    ),
    (
        "Entry criteria",
        "App installed and launchable; exact build identified; device available; expected business rules confirmed.",
        "Block execution if prerequisite unavailable.",
    ),
    (
        "Exit criteria",
        "All cases executed or explicitly blocked/deferred; failures evidenced and linked to defects/disposition; retests and regression completed; risks reviewed.",
        "QA lead records final counts and sign-off in Jira.",
    ),
    (
        "Pass/fail",
        "Pass only against approved expected behavior. Fail for reproducible deviation, crash, data mismatch, or unusable control.",
        "TBC behavior requires product-owner decision before verdict.",
    ),
    (
        "Status values",
        "Pass, Fail, Blocked, Not Run.",
        "Never mark an unexecuted or blocked case Pass.",
    ),
    (
        "Severity guidance",
        "Critical: app unusable/data loss; Major: core shopper journey broken; Minor: non-blocking feature/format; Trivial: cosmetic.",
        "Map to project Jira field names.",
    ),
    (
        "Assumptions to confirm",
        "Blank-name validation; repeat add; country/gender rules; price/tax; empty cart; Terms gesture; checkout destination; orientation support.",
        "Record decisions before execution.",
    ),
    (
        "Repository traceability",
        "tests/bdd/features/general_store.feature; mobile_test_automation/pages/; resources/locators/locators.json.",
        "Reference only; this workbook is for manual testing.",
    ),
    (
        "Jira import note",
        "Test Cases rows use common fields: Issue Type, Summary, Description, Priority, Labels, plus test fields.",
        "Xray/Zephyr issue types and step-field mapping differ; validate a small import first.",
    ),
]

LIFECYCLE = [
    (
        "1. Planning",
        "Confirm app owner/source/build, supported Android matrix, scope, risks, Jira project and test-management plugin.",
        "Test lead / Product owner",
        "Approved plan and assumptions.",
    ),
    (
        "2. Analysis",
        "Review shopper flows and rules; identify positive, negative, boundary, interruption, and usability coverage.",
        "QA",
        "Prioritized scenarios.",
    ),
    (
        "3. Design",
        "Author Gherkin cases with preconditions, synthetic data, steps, expected outcome, and traceability IDs.",
        "QA author",
        "Reviewed Test Cases; TBC behavior flagged.",
    ),
    (
        "4. Review/import",
        "Peer-review; map Jira fields; import plan/set/tests using configured Jira app.",
        "QA reviewer / Jira admin",
        "Imported keys and field/link verification.",
    ),
    (
        "5. Readiness",
        "Install/identify build; prepare device, clean state, network, and safe test data.",
        "Tester / Device owner",
        "Entry criteria and environment recorded.",
    ),
    (
        "6. Execution",
        "Execute; record outcome, actual result, tester/date, versions, and evidence.",
        "Tester",
        "Execution Log completed for run cases.",
    ),
    (
        "7. Defect triage",
        "Reproduce; capture permitted evidence; compare approved expected behavior; create/link Jira Bug.",
        "Tester / Developer / Product owner",
        "Defect has steps, expected/actual, environment, evidence, and test link.",
    ),
    (
        "8. Retest",
        "Run failed case on fixed build and link fix/build.",
        "Tester",
        "Retest result recorded and defect synchronized.",
    ),
    (
        "9. Regression",
        "Re-run impacted tests and critical shopper-to-cart flow.",
        "QA",
        "Regression outcomes and reopened defects linked.",
    ),
    (
        "10. Closure",
        "Summarize pass/fail/blocked, open defects, residual risks, and recommendation; obtain sign-off.",
        "QA lead / Product owner",
        "Jira report and approval recorded.",
    ),
]


def col(n: int) -> str:
    result = ""
    while n:
        n, rem = divmod(n - 1, 26)
        result = chr(65 + rem) + result
    return result


def cell(ref: str, value: object, style: int) -> ET.Element:
    item = ET.Element(f"{{{MAIN}}}c", {"r": ref, "s": str(style), "t": "inlineStr"})
    inline = ET.SubElement(item, f"{{{MAIN}}}is")
    text = ET.SubElement(inline, f"{{{MAIN}}}t")
    text.text = str(value)
    if "\n" in str(value) or str(value).startswith(" ") or str(value).endswith(" "):
        text.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    return item


MAIN = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
ET.register_namespace("", MAIN)


def worksheet(rows: list[list[object]], widths: list[int]) -> bytes:
    root = ET.Element(f"{{{MAIN}}}worksheet")
    views = ET.SubElement(root, f"{{{MAIN}}}sheetViews")
    view = ET.SubElement(views, f"{{{MAIN}}}sheetView", {"workbookViewId": "0"})
    ET.SubElement(
        view,
        f"{{{MAIN}}}pane",
        {"ySplit": "1", "topLeftCell": "A2", "activePane": "bottomLeft", "state": "frozen"},
    )
    ET.SubElement(
        view, f"{{{MAIN}}}selection", {"pane": "bottomLeft", "activeCell": "A2", "sqref": "A2"}
    )
    ET.SubElement(root, f"{{{MAIN}}}sheetFormatPr", {"defaultRowHeight": "30"})
    cols = ET.SubElement(root, f"{{{MAIN}}}cols")
    for index, width in enumerate(widths, 1):
        ET.SubElement(
            cols,
            f"{{{MAIN}}}col",
            {"min": str(index), "max": str(index), "width": str(width), "customWidth": "1"},
        )
    data = ET.SubElement(root, f"{{{MAIN}}}sheetData")
    for row_index, row in enumerate(rows, 1):
        row_element = ET.SubElement(
            data,
            f"{{{MAIN}}}row",
            {"r": str(row_index), "customHeight": "1", "ht": "32" if row_index == 1 else "48"},
        )
        for col_index, value in enumerate(row, 1):
            if value is not None and str(value) != "":
                row_element.append(
                    cell(f"{col(col_index)}{row_index}", value, 1 if row_index == 1 else 2)
                )
    if len(rows) > 1:
        ET.SubElement(
            root,
            f"{{{MAIN}}}autoFilter",
            {"ref": f"A1:{col(max(len(row) for row in rows))}{len(rows)}"},
        )
    ET.SubElement(
        root,
        f"{{{MAIN}}}pageMargins",
        {
            "left": "0.25",
            "right": "0.25",
            "top": "0.5",
            "bottom": "0.5",
            "header": "0.2",
            "footer": "0.2",
        },
    )
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def make_workbook() -> None:
    case_headers = [
        "Issue Type",
        "Test Case ID",
        "Summary",
        "Description",
        "Priority",
        "Labels",
        "Test Type",
        "Scenario ID",
        "Feature Area",
        "Preconditions",
        "Test Data",
        "Gherkin Scenario",
        "Manual Test Steps",
        "Expected Result",
        "Execution Status",
        "Actual Result",
        "Evidence / Attachment",
        "Defect Key",
        "Tester",
        "Execution Date",
        "App Version",
        "Device / OS",
    ]
    case_rows = []
    for suffix, scenario, area, title, priority, pre, data, gherkin, steps, expected in CASES:
        case_rows.append(
            [
                "Test",
                f"GS-TC-{suffix}",
                title,
                f"Manual General Store test. Scenario GS-SCN-{scenario}; area: {area}.",
                priority,
                "general-store;manual;android",
                "Manual",
                f"GS-SCN-{scenario}",
                area,
                pre,
                data,
                f"Feature: General Store\n  Scenario: {title}\n  {gherkin}",
                steps,
                expected,
                "Not Run",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
            ]
        )
    scenarios = [
        [
            f"GS-SCN-{sid}",
            "Test Set",
            name,
            objective,
            priority,
            "; ".join(f"GS-TC-{n}" for n in ids.split("; ")),
            "Not Run",
            "Public sample app; validate against installed build.",
        ]
        for sid, name, objective, ids, priority in SCENARIOS
    ]
    executions = [
        [row[1], "", row[2], "", "", "", "", "", "", "Not Run", "", "", "", "", "", ""]
        for row in case_rows
    ]
    sheets = [
        (
            "Read Me",
            [
                ["Item", "Guidance"],
                [
                    "Purpose",
                    "Jira-oriented manual test workbook for the public General Store sample app.",
                ],
                ["Execution status", "No test has been run; all cases start Not Run."],
                [
                    "Build caveat",
                    "Confirm exact app source/package/version. Public variants differ in content and behavior.",
                ],
                [
                    "Gherkin",
                    "Test Cases has Feature/Scenario/Given/When/Then plus manual steps and expected result.",
                ],
                [
                    "Jira import",
                    "Common fields are provided. Test Plan/Test Set/Test types and step fields depend on Xray/Zephyr/Jira configuration.",
                ],
                [
                    "Import tip",
                    "Validate a small sample import; map stable IDs to a Jira custom field or label.",
                ],
                [
                    "Test data",
                    "ManualTester is synthetic. Use only countries/products present in installed build; no personal/payment data.",
                ],
                ["Platform", "Android is primary. iOS coverage is not claimed."],
                ["Tabs", "Test Plan; Scenarios; Test Cases; Execution Log; Defect Log; Lifecycle."],
                [
                    "Traceability",
                    "Stable workbook IDs: GS-TP-001, GS-SCN-xxx, GS-TC-xxx. Record Jira keys after import.",
                ],
            ],
        ),
        ("Test Plan", [["Field", "Value", "Notes / Owner"]] + [list(row) for row in PLAN]),
        (
            "Scenarios",
            [
                [
                    "Scenario ID",
                    "Recommended Jira Issue Type",
                    "Summary",
                    "Objective",
                    "Priority",
                    "Related Test Case IDs",
                    "Status",
                    "Notes",
                ]
            ]
            + scenarios,
        ),
        ("Test Cases", [case_headers] + case_rows),
        (
            "Execution Log",
            [
                [
                    "Test Case ID",
                    "Jira Test Key",
                    "Summary",
                    "Tester",
                    "Execution Date",
                    "Environment",
                    "Device Model",
                    "Android Version",
                    "App Version / Build",
                    "Run Result",
                    "Actual Result / Notes",
                    "Evidence Link / Attachment",
                    "Linked Defect Key",
                    "Retest Result",
                    "Retest Date",
                    "Comments",
                ]
            ]
            + executions,
        ),
        (
            "Defect Log",
            [
                [
                    "Defect Key",
                    "Summary",
                    "Linked Test Case ID",
                    "Severity",
                    "Priority",
                    "Environment / Build",
                    "Steps to Reproduce",
                    "Expected Result",
                    "Actual Result",
                    "Evidence Link",
                    "Reporter",
                    "Assignee",
                    "Status",
                    "Fix Version",
                    "Retest Result",
                    "Resolution Notes",
                ]
            ]
            + [
                ["", "", "", "", "", "", "", "", "", "", "", "", "Open", "", "Not Run", ""]
                for _ in range(10)
            ],
        ),
        (
            "Lifecycle",
            [["Lifecycle Stage", "Manual QA Activity", "Suggested Owner", "Completion Evidence"]]
            + [list(row) for row in LIFECYCLE],
        ),
    ]
    widths = {
        "Read Me": [25, 115],
        "Test Plan": [30, 95, 78],
        "Scenarios": [18, 25, 42, 64, 13, 65, 16, 65],
        "Test Cases": [
            14,
            17,
            44,
            58,
            13,
            28,
            12,
            17,
            22,
            58,
            42,
            76,
            72,
            66,
            18,
            55,
            38,
            18,
            18,
            18,
            20,
            24,
        ],
        "Execution Log": [17, 20, 44, 20, 18, 25, 22, 18, 22, 17, 55, 40, 20, 18, 18, 45],
        "Defect Log": [18, 45, 20, 15, 15, 28, 65, 55, 55, 40, 20, 20, 18, 20, 18, 55],
        "Lifecycle": [25, 90, 30, 78],
    }
    content_ns = "http://schemas.openxmlformats.org/package/2006/content-types"
    rel_ns = "http://schemas.openxmlformats.org/package/2006/relationships"
    content = ET.Element(f"{{{content_ns}}}Types")
    ET.SubElement(
        content,
        f"{{{content_ns}}}Default",
        {
            "Extension": "rels",
            "ContentType": "application/vnd.openxmlformats-package.relationships+xml",
        },
    )
    ET.SubElement(
        content, f"{{{content_ns}}}Default", {"Extension": "xml", "ContentType": "application/xml"}
    )
    for part, kind in [
        (
            "/xl/workbook.xml",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml",
        ),
        (
            "/xl/styles.xml",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml",
        ),
    ]:
        ET.SubElement(content, f"{{{content_ns}}}Override", {"PartName": part, "ContentType": kind})
    for index in range(1, len(sheets) + 1):
        ET.SubElement(
            content,
            f"{{{content_ns}}}Override",
            {
                "PartName": f"/xl/worksheets/sheet{index}.xml",
                "ContentType": "application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml",
            },
        )
    package_rels = ET.Element(f"{{{rel_ns}}}Relationships")
    ET.SubElement(
        package_rels,
        f"{{{rel_ns}}}Relationship",
        {
            "Id": "rId1",
            "Type": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument",
            "Target": "xl/workbook.xml",
        },
    )
    workbook = ET.Element(f"{{{MAIN}}}workbook")
    book_views = ET.SubElement(workbook, f"{{{MAIN}}}bookViews")
    ET.SubElement(
        book_views,
        f"{{{MAIN}}}workbookView",
        {
            "activeTab": "0",
            "visibility": "visible",
            "windowWidth": "24000",
            "windowHeight": "12000",
        },
    )
    sheet_list = ET.SubElement(workbook, f"{{{MAIN}}}sheets")
    workbook_rels = ET.Element(f"{{{rel_ns}}}Relationships")
    doc_rel = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/"
    for index, (name, _) in enumerate(sheets, 1):
        ET.SubElement(
            sheet_list,
            f"{{{MAIN}}}sheet",
            {
                "name": name,
                "sheetId": str(index),
                "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id": f"rId{index}",
            },
        )
        ET.SubElement(
            workbook_rels,
            f"{{{rel_ns}}}Relationship",
            {
                "Id": f"rId{index}",
                "Type": doc_rel + "worksheet",
                "Target": f"worksheets/sheet{index}.xml",
            },
        )
    ET.SubElement(
        workbook_rels,
        f"{{{rel_ns}}}Relationship",
        {"Id": f"rId{len(sheets) + 1}", "Type": doc_rel + "styles", "Target": "styles.xml"},
    )
    styles = b"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
<fonts count="2"><font><sz val="11"/><name val="Calibri"/></font><font><b/><color rgb="FFFFFFFF"/><sz val="11"/><name val="Calibri"/></font></fonts>
<fills count="3"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill><fill><patternFill patternType="solid"><fgColor rgb="FF17365D"/><bgColor indexed="64"/></patternFill></fill></fills>
<borders count="2"><border><left/><right/><top/><bottom/><diagonal/></border><border><left style="thin"><color rgb="FFD9E1F2"/></left><right style="thin"><color rgb="FFD9E1F2"/></right><top style="thin"><color rgb="FFD9E1F2"/></top><bottom style="thin"><color rgb="FFD9E1F2"/></bottom><diagonal/></border></borders>
<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>
<cellXfs count="3"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/><xf numFmtId="0" fontId="1" fillId="2" borderId="1" xfId="0" applyAlignment="1"><alignment vertical="center" wrapText="1"/></xf><xf numFmtId="0" fontId="0" fillId="0" borderId="1" xfId="0" applyAlignment="1"><alignment vertical="top" wrapText="1"/></xf></cellXfs>
<cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles><dxfs count="0"/><tableStyles count="0" defaultTableStyle="TableStyleMedium2" defaultPivotStyle="PivotStyleLight16"/>
</styleSheet>"""
    with ZipFile(OUTPUT, "w", ZIP_DEFLATED) as archive:
        archive.writestr(
            "[Content_Types].xml", ET.tostring(content, encoding="utf-8", xml_declaration=True)
        )
        archive.writestr(
            "_rels/.rels", ET.tostring(package_rels, encoding="utf-8", xml_declaration=True)
        )
        archive.writestr(
            "xl/workbook.xml", ET.tostring(workbook, encoding="utf-8", xml_declaration=True)
        )
        archive.writestr(
            "xl/_rels/workbook.xml.rels",
            ET.tostring(workbook_rels, encoding="utf-8", xml_declaration=True),
        )
        archive.writestr("xl/styles.xml", styles)
        for index, (name, rows) in enumerate(sheets, 1):
            archive.writestr(f"xl/worksheets/sheet{index}.xml", worksheet(rows, widths[name]))
    print(f"Created {OUTPUT} with {len(CASES)} cases and {len(sheets)} worksheets.")


if __name__ == "__main__":
    make_workbook()
