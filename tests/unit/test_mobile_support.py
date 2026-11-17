"""Dependency-free checks for Appium configuration and modal verification."""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import tomllib
import types
import unittest
from pathlib import Path
from typing import Any
from unittest.mock import patch

from mobile_test_automation.config.environment_profile import (
    configure_github_environment,
    load_environment_profile,
)
from mobile_test_automation.drivers.driver_factory import (
    build_browserstack_capabilities,
    build_local_capabilities,
    create_driver,
    normalize_appium_url,
    normalize_platform,
)
from mobile_test_automation.services.terms_modal import (
    _terms_title_locator,
    assert_terms_modal_displayed,
    is_terms_modal_displayed,
)


class DriverConfigurationTests(unittest.TestCase):
    class FakeOptions:
        def __init__(self):
            self.capabilities = {}

        def load_capabilities(self, capabilities):
            self.capabilities = capabilities

    class FakeAndroidOptions(FakeOptions):
        pass

    class FakeIOSOptions(FakeOptions):
        pass

    class FakeDriver:
        def __init__(self):
            self.implicit_wait_seconds = None
            self.quit_called = False

        def implicitly_wait(self, seconds: int):
            self.implicit_wait_seconds = seconds

        def quit(self):
            self.quit_called = True

    def appium_modules(self):
        appium = types.ModuleType("appium")
        appium.webdriver = types.SimpleNamespace(Remote=lambda **kwargs: self.fake_remote(**kwargs))
        options = types.ModuleType("appium.options")
        android_options = types.ModuleType("appium.options.android")
        android_options.UiAutomator2Options = self.FakeAndroidOptions
        ios_options = types.ModuleType("appium.options.ios")
        ios_options.XCUITestOptions = self.FakeIOSOptions
        return {
            "appium": appium,
            "appium.options": options,
            "appium.options.android": android_options,
            "appium.options.ios": ios_options,
        }

    def fake_remote(self, **kwargs):
        self.remote_kwargs = kwargs
        self.remote_driver = self.FakeDriver()
        return self.remote_driver

    def test_environment_profiles_resolve_credentials_and_environment_defaults(self):
        project_root = Path(__file__).resolve().parents[2]
        profile_directory = project_root / "mobile_test_automation" / "config" / "environments"
        secrets = {
            "QA_BROWSERSTACK_USERNAME": "qa-user",
            "QA_BROWSERSTACK_ACCESS_KEY": "qa-key",
            "STAGE_BROWSERSTACK_USERNAME": "stage-user",
            "STAGE_BROWSERSTACK_ACCESS_KEY": "stage-key",
        }

        qa = load_environment_profile("QA", environ=secrets, profile_directory=profile_directory)
        stage = load_environment_profile(
            "stage", environ=secrets, profile_directory=profile_directory
        )

        self.assertEqual(qa["BROWSERSTACK_USERNAME"], "qa-user")
        self.assertEqual(qa["BROWSERSTACK_ACCESS_KEY"], "qa-key")
        self.assertEqual(stage["BROWSERSTACK_USERNAME"], "stage-user")
        self.assertEqual(stage["BROWSERSTACK_ACCESS_KEY"], "stage-key")
        self.assertIn("QA", qa["BROWSERSTACK_PROJECT_NAME"])
        self.assertIn("Stage", stage["BROWSERSTACK_PROJECT_NAME"])
        self.assertNotEqual(qa["BROWSERSTACK_BUILD_NAME"], stage["BROWSERSTACK_BUILD_NAME"])

    def test_environment_profile_requires_credentials_and_known_environment(self):
        project_root = Path(__file__).resolve().parents[2]
        profile_directory = project_root / "mobile_test_automation" / "config" / "environments"
        with self.assertRaisesRegex(ValueError, "BROWSERSTACK_USERNAME"):
            load_environment_profile("qa", environ={}, profile_directory=profile_directory)
        with self.assertRaisesRegex(ValueError, "qa or stage"):
            load_environment_profile(
                "production",
                environ={
                    "BROWSERSTACK_USERNAME": "user",
                    "BROWSERSTACK_ACCESS_KEY": "key",
                },
                profile_directory=profile_directory,
            )

    def test_github_environment_writer_uses_delimited_values(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "github-env"
            secret = "sensitive-key-placeholder"

            configure_github_environment(
                output, {"BROWSERSTACK_ACCESS_KEY": secret, "PROFILE_NAME": "qa"}
            )

            content = output.read_text(encoding="utf-8")
        self.assertIn("BROWSERSTACK_ACCESS_KEY<<", content)
        self.assertIn(secret, content)

    def test_android_local_capabilities_preserve_driver_defaults(self):
        caps = build_local_capabilities(
            "android",
            {
                "APP_PACKAGE": "sample.app",
                "APP_ACTIVITY": ".MainActivity",
                "DEVICE_NAME": "pixel",
                "UDID": "emulator-5556",
            },
        )

        self.assertEqual(caps["platformName"], "Android")
        self.assertEqual(caps["appium:automationName"], "UiAutomator2")
        self.assertEqual(caps["appium:deviceName"], "pixel")
        self.assertEqual(caps["appium:udid"], "emulator-5556")
        self.assertEqual(caps["appium:appPackage"], "sample.app")
        self.assertTrue(caps["appium:autoGrantPermissions"])
        self.assertEqual(caps["appium:appWaitDuration"], 60000)

    def test_android_local_requires_app_identity(self):
        with self.assertRaisesRegex(ValueError, "APP_PACKAGE, APP_ACTIVITY"):
            build_local_capabilities("android", {})

    def test_ios_local_requires_device_and_installed_app_or_path(self):
        with self.assertRaisesRegex(ValueError, "IOS_DEVICE_NAME"):
            build_local_capabilities("ios", {})
        with self.assertRaisesRegex(ValueError, "IOS_BUNDLE_ID or IOS_APP"):
            build_local_capabilities("ios", {"IOS_DEVICE_NAME": "iPhone"})

        caps = build_local_capabilities(
            "ios",
            {
                "IOS_DEVICE_NAME": "iPhone 16",
                "IOS_PLATFORM_VERSION": "18.0",
                "IOS_BUNDLE_ID": "com.example.mobile",
            },
        )
        self.assertEqual(caps["platformName"], "iOS")
        self.assertEqual(caps["appium:automationName"], "XCUITest")
        self.assertEqual(caps["appium:bundleId"], "com.example.mobile")
        self.assertEqual(caps["appium:platformVersion"], "18.0")

    def test_browserstack_android_preserves_resource_caps_and_uses_env_app(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            capability_file = Path(temp_dir) / "browserstack.json"
            capability_file.write_text(
                json.dumps(
                    {
                        "androidCapabilities": {
                            "platformName": "Android",
                            "app": "bs://configured-app",
                            "deviceName": "Pixel",
                            "osVersion": "14",
                            "browserstack.debug": True,
                        }
                    }
                ),
                encoding="utf-8",
            )
            caps = build_browserstack_capabilities(
                "android",
                {
                    "BROWSERSTACK_USERNAME": "username-placeholder",
                    "BROWSERSTACK_ACCESS_KEY": "key-placeholder",
                    "BROWSERSTACK_APP": "bs://env-app",
                },
                capability_file,
            )

        self.assertEqual(caps["app"], "bs://env-app")
        self.assertTrue(caps["browserstack.debug"])
        self.assertEqual(caps["bstack:options"]["userName"], "username-placeholder")
        self.assertEqual(caps["bstack:options"]["accessKey"], "key-placeholder")

    def test_browserstack_platform_settings_override_catalog_for_parallel_lanes(self):
        project_root = Path(__file__).resolve().parents[2]
        capability_file = (
            project_root
            / "mobile_test_automation"
            / "resources"
            / "capabilities"
            / "browserstack.json"
        )
        credentials = {
            "BROWSERSTACK_USERNAME": "username-placeholder",
            "BROWSERSTACK_ACCESS_KEY": "key-placeholder",
        }
        android = build_browserstack_capabilities(
            "android",
            {
                **credentials,
                "BROWSERSTACK_ANDROID_DEVICE_NAME": "Android device from account",
                "BROWSERSTACK_ANDROID_OS_VERSION": "15",
                "BROWSERSTACK_APP_ANDROID": "bs://android-app",
            },
            capability_file,
        )
        ios = build_browserstack_capabilities(
            "ios",
            {
                **credentials,
                "BROWSERSTACK_IOS_DEVICE_NAME": "iOS device from account",
                "BROWSERSTACK_IOS_OS_VERSION": "18",
                "BROWSERSTACK_APP_IOS": "bs://ios-app",
            },
            capability_file,
        )

        self.assertEqual(android["platformName"], "Android")
        self.assertEqual(android["appium:automationName"], "UiAutomator2")
        self.assertEqual(android["app"], "bs://android-app")
        self.assertEqual(android["bstack:options"]["deviceName"], "Android device from account")
        self.assertEqual(android["bstack:options"]["osVersion"], "15")
        self.assertEqual(ios["platformName"], "iOS")
        self.assertEqual(ios["appium:automationName"], "XCUITest")
        self.assertEqual(ios["app"], "bs://ios-app")
        self.assertEqual(ios["bstack:options"]["deviceName"], "iOS device from account")
        self.assertEqual(ios["bstack:options"]["osVersion"], "18")
        self.assertNotIn("appium:deviceName", android)
        self.assertNotIn("appium:deviceName", ios)

    def test_browserstack_rejects_missing_platform_app(self):
        project_root = Path(__file__).resolve().parents[2]
        capability_file = (
            project_root
            / "mobile_test_automation"
            / "resources"
            / "capabilities"
            / "browserstack.json"
        )
        with self.assertRaisesRegex(ValueError, "BrowserStack ios session requires"):
            build_browserstack_capabilities(
                "ios",
                {
                    "BROWSERSTACK_USERNAME": "username-placeholder",
                    "BROWSERSTACK_ACCESS_KEY": "key-placeholder",
                },
                capability_file,
            )

    def test_browserstack_ios_builds_explicit_caps_from_environment(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            capability_file = Path(temp_dir) / "browserstack.json"
            capability_file.write_text(
                '{"androidCapabilities": {}, "iosCapabilities": {}}',
                encoding="utf-8",
            )
            caps = build_browserstack_capabilities(
                "ios",
                {
                    "BROWSERSTACK_USERNAME": "username-placeholder",
                    "BROWSERSTACK_ACCESS_KEY": "key-placeholder",
                    "IOS_DEVICE_NAME": "iPhone 16",
                    "IOS_PLATFORM_VERSION": "18.0",
                    "BROWSERSTACK_APP": "bs://ios-app",
                },
                capability_file,
            )

        self.assertEqual(caps["platformName"], "iOS")
        self.assertEqual(caps["appium:automationName"], "XCUITest")
        self.assertEqual(caps["bstack:options"]["deviceName"], "iPhone 16")
        self.assertEqual(caps["bstack:options"]["osVersion"], "18.0")
        self.assertEqual(caps["app"], "bs://ios-app")

    def test_browserstack_credentials_are_required_without_echoing_values(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            capability_file = Path(temp_dir) / "browserstack.json"
            capability_file.write_text('{"androidCapabilities": {}}', encoding="utf-8")
            with self.assertRaisesRegex(
                ValueError, "BROWSERSTACK_USERNAME, BROWSERSTACK_ACCESS_KEY"
            ):
                build_browserstack_capabilities("android", {}, capability_file)

    def test_create_local_driver_uses_platform_options_and_normalized_endpoint(self):
        env = {
            "RUN_ENV": "local",
            "PLATFORM": "Android",
            "APPIUM_URL": "http://localhost:4723/wd/hub",
            "APP_PACKAGE": "sample.app",
            "APP_ACTIVITY": ".MainActivity",
        }
        with patch.dict(sys.modules, self.appium_modules()):
            driver = create_driver(environ=env)

        self.assertIs(driver, self.remote_driver)
        self.assertEqual(self.remote_kwargs["command_executor"], "http://localhost:4723")
        self.assertIsInstance(self.remote_kwargs["options"], self.FakeAndroidOptions)
        self.assertIsNone(driver.implicit_wait_seconds)

    def test_create_local_driver_selects_xcuitest_for_ios(self):
        env = {
            "RUN_ENV": "local",
            "PLATFORM": "iOS",
            "IOS_DEVICE_NAME": "iPhone 16",
            "IOS_BUNDLE_ID": "com.example.mobile",
        }
        with patch.dict(sys.modules, self.appium_modules()):
            create_driver(environ=env)

        options = self.remote_kwargs["options"]
        self.assertIsInstance(options, self.FakeIOSOptions)
        self.assertEqual(options.capabilities["platformName"], "iOS")
        self.assertEqual(options.capabilities["appium:automationName"], "XCUITest")

    def test_create_browserstack_driver_keeps_remote_implicit_wait(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            resources = root / "mobile_test_automation" / "resources" / "capabilities"
            resources.mkdir(parents=True)
            (resources / "browserstack.json").write_text(
                '{"androidCapabilities": {"platformName": "Android"}}',
                encoding="utf-8",
            )
            profiles = root / "mobile_test_automation" / "config" / "environments"
            profiles.mkdir(parents=True)
            source_profile = (
                Path(__file__).resolve().parents[2]
                / "mobile_test_automation"
                / "config"
                / "environments"
                / "qa.properties"
            )
            (profiles / "qa.properties").write_text(
                source_profile.read_text(encoding="utf-8"), encoding="utf-8"
            )
            env = {
                "RUN_ENV": "browserstack",
                "TEST_ENVIRONMENT": "qa",
                "PLATFORM": "Android",
                "QA_BROWSERSTACK_USERNAME": "qa-username-placeholder",
                "QA_BROWSERSTACK_ACCESS_KEY": "qa-key-placeholder",
                "BROWSERSTACK_APP_ANDROID": "bs://android-app",
                "BROWSERSTACK_ANDROID_DEVICE_NAME": "Pixel",
                "BROWSERSTACK_ANDROID_OS_VERSION": "14",
            }
            with patch.dict(sys.modules, self.appium_modules()):
                driver = create_driver(environ=env, project_root=root)

        self.assertEqual(
            self.remote_kwargs["command_executor"],
            "https://hub-cloud.browserstack.com/wd/hub",
        )
        self.assertEqual(driver.implicit_wait_seconds, 5)

    def test_browserstack_driver_requires_explicit_environment(self):
        with self.assertRaisesRegex(ValueError, "TEST_ENVIRONMENT"):
            create_driver(
                environ={
                    "RUN_ENV": "browserstack",
                    "PLATFORM": "android",
                }
            )

    def test_platform_and_legacy_endpoint_normalization(self):
        self.assertEqual(normalize_platform(" iOS "), "ios")
        self.assertEqual(
            normalize_appium_url(" http://localhost:4723/wd/hub/ "),
            "http://localhost:4723",
        )
        with self.assertRaisesRegex(ValueError, "PLATFORM"):
            normalize_platform("Windows")


class TermsModalTests(unittest.TestCase):
    class Element:
        def __init__(self, displayed: bool):
            self.displayed = displayed

        def is_displayed(self) -> bool:
            return self.displayed

    class Driver:
        def __init__(self, platform: str, elements: list[Any]):
            self.capabilities = {"platformName": platform}
            self.elements = elements
            self.last_locator = None

        def find_elements(self, by: str, value: str):
            self.last_locator = (by, value)
            return self.elements

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.resource_dir = Path(self.temp_dir.name)
        (self.resource_dir / "locators.json").write_text(
            json.dumps(
                {
                    "$schemaVersion": 1,
                    "CartPage": {
                        "termsTitle": {
                            "xpath": {
                                "android": "//*[contains(@text, 'Terms Of Use')]",
                                "ios": "//*[contains(@label, 'Terms Of Use')]",
                            }
                        }
                    },
                }
            ),
            encoding="utf-8",
        )

    def test_terms_title_locator_uses_xpath_selected_from_shared_catalog(self):
        self.assertEqual(
            _terms_title_locator("android", self.resource_dir),
            ("xpath", "//*[contains(@text, 'Terms Of Use')]"),
        )
        self.assertEqual(
            _terms_title_locator("ios", self.resource_dir),
            ("xpath", "//*[contains(@label, 'Terms Of Use')]"),
        )

    def test_visible_terms_title_passes_and_missing_title_fails(self):
        android_driver = self.Driver("Android", [self.Element(True)])
        self.assertTrue(is_terms_modal_displayed(android_driver, resource_dir=self.resource_dir))
        self.assertEqual(android_driver.last_locator[0], "xpath")
        assert_terms_modal_displayed(
            android_driver, timeout_seconds=0, resource_dir=self.resource_dir
        )

        missing_driver = self.Driver("iOS", [])
        self.assertFalse(is_terms_modal_displayed(missing_driver, resource_dir=self.resource_dir))
        with self.assertRaisesRegex(AssertionError, "Terms Of Use modal title"):
            assert_terms_modal_displayed(
                missing_driver, timeout_seconds=0, resource_dir=self.resource_dir
            )

    def test_hidden_title_is_not_accepted_and_unknown_platform_fails(self):
        hidden_driver = self.Driver("Android", [self.Element(False)])
        self.assertFalse(is_terms_modal_displayed(hidden_driver, resource_dir=self.resource_dir))
        with self.assertRaisesRegex(ValueError, "Android or iOS"):
            is_terms_modal_displayed(self.Driver("macOS", []), resource_dir=self.resource_dir)


class RunnerConfigurationTests(unittest.TestCase):
    def test_pytest_retries_match_two_retry_legacy_intent(self):
        project = tomllib.loads(
            (Path(__file__).resolve().parents[2] / "pyproject.toml").read_text(encoding="utf-8")
        )
        dependencies = project["project"]["dependencies"]
        addopts = project["tool"]["pytest"]["ini_options"]["addopts"]

        self.assertIn("pytest-rerunfailures==16.0", dependencies)
        self.assertIn("pytest-xdist==3.8.0", dependencies)
        self.assertIn("--reruns=2", addopts)

    def test_browserstack_workflow_runs_platform_matrix_concurrently(self):
        project_root = Path(__file__).resolve().parents[2]
        workflow = (project_root / ".github" / "workflows" / "browserstack-python.yml").read_text(
            encoding="utf-8"
        )
        for expected in (
            "environment:",
            "options:",
            "- qa",
            "- stage",
            "TEST_ENVIRONMENT: ${{ inputs.environment }}",
            "QA_BROWSERSTACK_USERNAME",
            "QA_BROWSERSTACK_ACCESS_KEY",
            "STAGE_BROWSERSTACK_USERNAME",
            "STAGE_BROWSERSTACK_ACCESS_KEY",
            "BROWSERSTACK_ANDROID_DEVICE_NAME",
            "BROWSERSTACK_IOS_DEVICE_NAME",
            "Load selected environment properties",
            "fail-fast: false",
            "parallel:",
            "default: false",
            "type: boolean",
            "workers:",
            "type: choice",
            '"1"',
            '"2"',
            '"3"',
            "platform: android",
            "platform: ios",
            "BROWSERSTACK_APP_ANDROID",
            "BROWSERSTACK_APP_IOS",
            "BROWSERSTACK_PARALLEL",
            "BROWSERSTACK_WORKERS",
            "max-parallel: ${{ inputs.parallel && 2 || 1 }}",
            'if [[ "${BROWSERSTACK_PARALLEL}" == "true" ]]',
            "-n",
        ):
            self.assertIn(expected, workflow)


class BddRegistrationTests(unittest.TestCase):
    def test_general_store_feature_is_registered(self):
        project_root = Path(__file__).resolve().parents[2]
        registrations: list[str] = []

        pytest_bdd = types.ModuleType("pytest_bdd")
        pytest_bdd.scenarios = lambda feature: registrations.append(feature)

        modules = (project_root / "tests" / "bdd" / "test_general_store.py",)
        with patch.dict(sys.modules, {"pytest_bdd": pytest_bdd}):
            for index, module_path in enumerate(modules):
                spec = importlib.util.spec_from_file_location(
                    f"_bdd_registration_check_{index}", module_path
                )
                self.assertIsNotNone(spec)
                self.assertIsNotNone(spec.loader)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

        self.assertEqual(
            registrations,
            ["general_store.feature"],
        )
        feature_directory = project_root / "tests" / "bdd" / "features"
        self.assertTrue(all((feature_directory / feature).is_file() for feature in registrations))


if __name__ == "__main__":
    unittest.main()
