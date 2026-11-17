"""Standard-library tests for shared automation configuration and utilities."""

from __future__ import annotations

import base64
import json
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest.mock import patch

from selenium.common.exceptions import NoSuchElementException, TimeoutException

from mobile_test_automation.config.runtime_config import (
    get_bool,
    get_setting,
    require_environment_value,
    resolve_environment_token,
    runtime_environment,
)
from mobile_test_automation.pages.base_page import BasePage
from mobile_test_automation.services.locator_logic import (
    LocatorConfigurationError,
    LocatorLogic,
    LocatorStrategy,
    PageName,
    read_locator_spec,
)
from mobile_test_automation.services.mobile_utility import MobileUtility
from mobile_test_automation.services.reporting import (
    capture_dom_snapshot,
    safe_name,
    start_video_recording,
    stop_video_recording,
)


class RuntimeConfigurationTests(unittest.TestCase):
    def test_runtime_environment_uses_non_empty_environment_values(self):
        config = runtime_environment(
            {"platform": "ios", "FAILURE_SCREENSHOTS": "false", "DEVICE_NAME": ""}
        )
        self.assertEqual(config["PLATFORM"], "ios")
        self.assertEqual(config["FAILURE_SCREENSHOTS"], "false")
        self.assertNotIn("DEVICE_NAME", config)

    def test_settings_boolean_and_required_values(self):
        self.assertEqual(
            get_setting("device_name", "fallback", environ={"DEVICE_NAME": "Pixel"}),
            "Pixel",
        )
        self.assertTrue(get_bool("take_all_screens", environ={"TAKE_ALL_SCREENS": "yes"}))
        self.assertFalse(get_bool("record_video", environ={"RECORD_VIDEO": "off"}))
        with self.assertRaisesRegex(ValueError, "AUTOMATION_TEST_SETTING"):
            require_environment_value("AUTOMATION_TEST_SETTING", {})
        self.assertEqual(
            require_environment_value(
                "AUTOMATION_TEST_SETTING", {"AUTOMATION_TEST_SETTING": "enabled"}
            ),
            "enabled",
        )
        self.assertEqual(
            resolve_environment_token("${DEVICE_NAME}", {"DEVICE_NAME": "Pixel"}),
            "Pixel",
        )
        self.assertIsNone(resolve_environment_token("${MISSING}", {}))


class ReportingTests(unittest.TestCase):
    class VideoDriver:
        def __init__(self):
            self.results: list[Any] = [None, base64.b64encode(b"clip").decode("ascii")]
            self.started = []

        def execute_script(self, command, *args):
            if command.endswith("startMediaProjectionRecording"):
                self.started.append((command, args))
                return None
            result = self.results.pop(0)
            return result

    def test_video_start_stop_retries_writes_safe_name_and_attaches_when_possible(self):
        driver = self.VideoDriver()
        self.assertTrue(start_video_recording(driver, True))
        with tempfile.TemporaryDirectory() as temporary:
            output = stop_video_recording(
                driver,
                "Scenario / name",
                enabled=True,
                output_dir=Path(temporary),
                settle_delay=0,
                initial_backoff=0,
                sleep=lambda _: None,
            )
            self.assertIsNotNone(output)
            assert output is not None
            self.assertEqual(output.name, "Scenario___name.mp4")
            self.assertEqual(output.read_bytes(), b"clip")
        self.assertFalse(start_video_recording(driver, False))
        self.assertEqual(safe_name("***"), "scenario")

    def test_invalid_video_data_is_best_effort(self):
        class BadVideoDriver:
            def execute_script(self, command):
                return "not base64"

        with tempfile.TemporaryDirectory() as temporary:
            output = stop_video_recording(
                BadVideoDriver(),
                "scenario",
                enabled=True,
                output_dir=Path(temporary),
                settle_delay=0,
                sleep=lambda _: None,
            )
        self.assertIsNone(output)

    def test_dom_snapshot_is_persisted_for_failure_inspection(self):
        class DomDriver:
            page_source = "<hierarchy><node text='Product list'/></hierarchy>"

        with tempfile.TemporaryDirectory() as temporary:
            output = capture_dom_snapshot(DomDriver(), "scenario failed", Path(temporary))
            self.assertIsNotNone(output)
            assert output is not None
            self.assertEqual(
                output.read_text(encoding="utf-8"),
                "<hierarchy><node text='Product list'/></hierarchy>",
            )


class BasePageTests(unittest.TestCase):
    class Driver:
        capabilities = {"platformName": "Android"}

        def __init__(self):
            self.screenshots = 0

        def get_screenshot_as_png(self):
            self.screenshots += 1
            return b"png"

    def test_actions_attach_screenshots_and_platform_helpers(self):
        driver = self.Driver()
        page = BasePage(driver)
        with patch.dict("os.environ", {"ACTION_SCREENSHOTS": "true"}):
            self.assertEqual(page.perform("Read", lambda: "value"), "value")
        self.assertEqual(driver.screenshots, 1)
        self.assertTrue(page.is_android)
        self.assertFalse(page.is_ios)

    def test_action_screenshots_can_be_disabled_for_faster_runs(self):
        driver = self.Driver()
        page = BasePage(driver)
        with patch.dict("os.environ", {"ACTION_SCREENSHOTS": "false"}):
            self.assertEqual(page.perform("Read", lambda: "value"), "value")
        self.assertEqual(driver.screenshots, 0)

    def test_page_rejects_missing_driver_and_waits_for_visibility(self):
        with self.assertRaisesRegex(RuntimeError, "Driver is required"):
            BasePage(None)

        class Element:
            def is_displayed(self):
                return True

        page = BasePage(self.Driver())
        element = Element()
        self.assertIs(page.wait_for_visible(element, seconds=0), element)


class LocatorLogicTests(unittest.TestCase):
    class Element:
        def __init__(self, displayed=True):
            self.displayed = displayed

        def is_displayed(self):
            return self.displayed

    def test_shared_locator_catalog_selects_platform_specific_xpath(self):
        with tempfile.TemporaryDirectory() as temporary:
            resource_dir = Path(temporary)
            (resource_dir / "locators.json").write_text(
                json.dumps(
                    {
                        "$schemaVersion": 1,
                        "FormPage": {
                            "continueButton": {
                                "xpath": {
                                    "android": "//*[@resource-id='continue']",
                                    "ios": "//*[@name='continue']",
                                }
                            }
                        },
                    }
                ),
                encoding="utf-8",
            )
            android_spec = read_locator_spec(
                PageName.FORMPAGE,
                "continueButton",
                platform="android",
                resource_dir=resource_dir,
            )
            ios_spec = read_locator_spec(
                PageName.FORMPAGE,
                "continueButton",
                platform="ios",
                resource_dir=resource_dir,
            )

            class Driver:
                def __init__(self):
                    self.calls = []
                    self.element = LocatorLogicTests.Element()

                def find_element(self, by, value):
                    self.calls.append((by, value))
                    return self.element

            android_driver = Driver()
            ios_driver = Driver()
            LocatorLogic(
                android_driver, platform="android", timeout=0, resource_dir=resource_dir
            ).get(PageName.FORMPAGE, "continueButton")
            LocatorLogic(ios_driver, platform="ios", timeout=0, resource_dir=resource_dir).get(
                PageName.FORMPAGE, "continueButton"
            )
        self.assertEqual(android_spec[LocatorStrategy.XPATH], "//*[@resource-id='continue']")
        self.assertEqual(ios_spec[LocatorStrategy.XPATH], "//*[@name='continue']")
        self.assertEqual(android_driver.calls, [("xpath", "//*[@resource-id='continue']")])
        self.assertEqual(ios_driver.calls, [("xpath", "//*[@name='continue']")])

    def test_locator_uses_xpath_and_escapes_dynamic_values(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "locators.json").write_text(
                json.dumps(
                    {
                        "$schemaVersion": 1,
                        "FormPage": {
                            "countryOption": {
                                "xpath": {
                                    "android": "//*[@text={value}]",
                                    "ios": "//*[@label={value}]",
                                }
                            }
                        },
                    }
                ),
                encoding="utf-8",
            )

            class Driver:
                def __init__(self):
                    self.calls: list[tuple[str, str]] = []
                    self.fallback = LocatorLogicTests.Element()

                def find_element(self, by, value):
                    self.calls.append((by, value))
                    return self.fallback

            driver = Driver()
            logic = LocatorLogic(
                driver,
                platform="android",
                timeout=0,
                resource_dir=root,
            )
            element = logic.get(
                PageName.FORMPAGE,
                "countryOption",
                values={"value": """Sam's "Market"""},  # Both XPath quote styles.
            )
            self.assertIs(element, driver.fallback)
            self.assertEqual(driver.calls[0][0], "xpath")
            self.assertIn("concat(", driver.calls[0][1])

    def test_missing_platform_xpath_fails_with_configuration_error(self):
        with self.assertRaisesRegex(LocatorConfigurationError, "not configured for ios"):
            read_locator_spec(
                PageName.FORMPAGE,
                "nameField",
                platform="ios",
            )

    def test_missing_platform_mapping_is_explicit_in_application_catalog(self):
        project_root = Path(__file__).resolve().parents[2]
        catalog = json.loads(
            (
                project_root / "mobile_test_automation" / "resources" / "locators" / "locators.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(catalog["$schemaVersion"], 1)
        for page_name, locators in catalog.items():
            if page_name == "$schemaVersion":
                continue
            for locator_name, locator in locators.items():
                self.assertEqual(set(locator), {"xpath"}, (page_name, locator_name))
                self.assertEqual(
                    set(locator["xpath"]), {"android", "ios"}, (page_name, locator_name)
                )
                self.assertIsInstance(locator["xpath"]["android"], str)
                self.assertIsNone(locator["xpath"]["ios"])

    def test_unknown_locator_is_a_configuration_error(self):
        class Driver:
            pass

        logic = LocatorLogic(Driver(), platform="android", timeout=0)
        with self.assertRaisesRegex(LocatorConfigurationError, "Unknown locator"):
            logic.get(PageName.FORMPAGE, "doesNotExist")
        with self.assertRaisesRegex(LocatorConfigurationError, "Unknown locator"):
            logic.get_all(PageName.FORMPAGE, "doesNotExist")

    def test_wait_timeout_is_reported_as_lookup_error_and_plural_timeout_is_empty(self):
        class Driver:
            def find_element(self, by, value):
                raise NoSuchElementException(value)

            def find_elements(self, by, value):
                return []

        logic = LocatorLogic(Driver(), platform="android", timeout=0)
        with self.assertRaisesRegex(LookupError, "No visible element") as result:
            logic.get(PageName.FORMPAGE, "nameField")
        self.assertIsInstance(result.exception.__cause__, TimeoutException)
        self.assertEqual(logic.get_all(PageName.PRODUCTPAGE, "productName"), [])

    def test_plural_lookup_uses_shared_xpath_catalog(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "locators.json").write_text(
                json.dumps(
                    {
                        "$schemaVersion": 1,
                        "FormPage": {
                            "rows": {"xpath": {"android": "//*[@resource-id='row']", "ios": None}}
                        },
                    }
                ),
                encoding="utf-8",
            )

            class Driver:
                def __init__(self, displayed):
                    self.displayed = displayed

                def find_elements(self, by, value):
                    return [LocatorLogicTests.Element(item) for item in self.displayed]

            visible_logic = LocatorLogic(
                Driver([True, True]), platform="android", timeout=0, resource_dir=root
            )
            hidden_logic = LocatorLogic(
                Driver([True, False]), platform="android", timeout=0, resource_dir=root
            )
            self.assertEqual(len(visible_logic.get_all(PageName.FORMPAGE, "rows")), 2)
            self.assertEqual(hidden_logic.get_all(PageName.FORMPAGE, "rows"), [])

    def test_upstream_general_store_locator_ids_are_kept_in_the_catalog(self):
        self.assertEqual(
            read_locator_spec("ProductPage", "cartBtn", platform="android")[LocatorStrategy.XPATH],
            "//*[@resource-id='com.androidsample.generalstore:id/appbar_btn_cart']",
        )
        self.assertEqual(
            read_locator_spec("CartPage", "termsTitle", platform="android")[LocatorStrategy.XPATH],
            "//*[@resource-id='com.androidsample.generalstore:id/alertTitle']",
        )
        self.assertEqual(
            read_locator_spec("WebPage", "searchInput", platform="android")[LocatorStrategy.XPATH],
            "//*[@name='q']",
        )


class MobileUtilityTests(unittest.TestCase):
    class Driver:
        contexts = ["NATIVE_APP", "WEBVIEW_com.example"]
        current_context = "NATIVE_APP"

        class Switch:
            def __init__(self):
                self.context_name = None

            def context(self, name):
                self.context_name = name

        def __init__(self):
            self.capabilities = {"platformName": "Android"}
            self.switch_to = self.Switch()
            self.scripts = []

        def execute_script(self, script, parameters):
            self.scripts.append((script, parameters))

    def test_context_switch_and_android_gesture_mapping(self):
        driver = self.Driver()
        utility = MobileUtility(driver)
        self.assertEqual(utility.wait_for_webview(0.1), "WEBVIEW_com.example")
        self.assertEqual(driver.switch_to.context_name, "WEBVIEW_com.example")
        utility.switch_to_native()
        self.assertEqual(driver.switch_to.context_name, "NATIVE_APP")
        self.assertEqual(utility.current_context, "NATIVE_APP")
        self.assertTrue(utility.scroll_down())
        self.assertEqual(driver.scripts[0][0], "mobile: scrollGesture")
        utility.perform_back()
        self.assertEqual(driver.scripts[-1][1], {"action": "back"})

    def test_ios_product_list_swipe_uses_mobile_swipe(self):
        driver = self.Driver()
        driver.capabilities = {"platformName": "iOS"}

        self.assertTrue(MobileUtility(driver).scroll_down())

        self.assertEqual(driver.scripts, [("mobile: swipe", {"direction": "up"})])

    def test_missing_driver_is_rejected(self):
        with self.assertRaisesRegex(RuntimeError, "active Appium driver"):
            MobileUtility(None)


if __name__ == "__main__":
    unittest.main()
