"""Create platform-specific Appium sessions from environment-backed settings."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from mobile_test_automation.config.environment_profile import load_environment_profile
from mobile_test_automation.config.runtime_config import runtime_environment

APPIUM_ENDPOINT = "http://127.0.0.1:4723"
BROWSERSTACK_ENDPOINT = "https://hub-cloud.browserstack.com/wd/hub"


def _value(environ: Mapping[str, str], name: str, default: str | None = None) -> str | None:
    value = environ.get(name, default)
    if value is None:
        return None
    value = value.strip()
    return value or None


def _required(environ: Mapping[str, str], *names: str) -> dict[str, str]:
    missing = [name for name in names if not _value(environ, name)]
    if missing:
        joined = ", ".join(missing)
        raise ValueError(f"Missing required environment variable(s): {joined}")
    return {name: _value(environ, name) or "" for name in names}


def _bool(environ: Mapping[str, str], name: str, default: bool) -> bool:
    value = _value(environ, name)
    if value is None:
        return default
    normalized = value.casefold()
    if normalized in {"true", "1", "yes", "on"}:
        return True
    if normalized in {"false", "0", "no", "off"}:
        return False
    raise ValueError(f"{name} must be a boolean value (true/false).")


def _integer(environ: Mapping[str, str], name: str, default: int) -> int:
    value = _value(environ, name)
    try:
        return default if value is None else int(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer.") from exc


def normalize_appium_url(url: str) -> str:
    """Normalize legacy Appium endpoints while retaining any configured path."""
    normalized = url.strip().rstrip("/")
    if normalized.casefold().endswith("/wd/hub"):
        normalized = normalized[:-7].rstrip("/")
    return normalized or APPIUM_ENDPOINT


def normalize_platform(platform: str | None) -> str:
    normalized = (platform or "android").strip().casefold()
    if normalized not in {"android", "ios"}:
        raise ValueError("PLATFORM must be either Android or iOS.")
    return normalized


def build_local_capabilities(
    platform: str,
    environ: Mapping[str, str],
) -> dict[str, Any]:
    """Return Appium W3C capabilities without importing the Appium client."""
    target = normalize_platform(platform)
    if target == "android":
        required = _required(environ, "APP_PACKAGE", "APP_ACTIVITY")
        caps: dict[str, Any] = {
            "platformName": "Android",
            "appium:automationName": _value(environ, "AUTOMATION_NAME", "UiAutomator2"),
            "appium:deviceName": _value(environ, "DEVICE_NAME", "emulator-5554"),
            "appium:appPackage": required["APP_PACKAGE"],
            "appium:appActivity": required["APP_ACTIVITY"],
            "appium:appWaitActivity": _value(environ, "APP_WAIT_ACTIVITY", "*"),
            "appium:autoGrantPermissions": _bool(environ, "AUTO_GRANT_PERMISSIONS", True),
            "appium:noReset": _bool(environ, "NO_RESET", True),
            "appium:nativeWebScreenshot": _bool(environ, "NATIVE_WEB_SCREENSHOT", True),
            "appium:autoWebview": _bool(environ, "AUTO_WEBVIEW", False),
            "appium:newCommandTimeout": _integer(environ, "NEW_COMMAND_TIMEOUT", 300),
            "appium:uiautomator2ServerLaunchTimeout": _integer(
                environ, "UIAUTOMATOR2_SERVER_LAUNCH_TIMEOUT", 120000
            ),
            "appium:uiautomator2ServerInstallTimeout": _integer(
                environ, "UIAUTOMATOR2_SERVER_INSTALL_TIMEOUT", 120000
            ),
            "appium:appWaitDuration": _integer(environ, "APP_WAIT_DURATION", 60000),
            "appium:adbExecTimeout": _integer(environ, "ADB_EXEC_TIMEOUT", 120000),
            # Retain the legacy Android media-projection capability; recording
            # remains separately controlled by the scenario hook.
            "appium:videoRecordingFeature": "media-projection",
        }
        udid = _value(environ, "UDID", "emulator-5554")
        chromedriver = _value(environ, "CHROMEDRIVER_EXECUTABLE")
        platform_version = _value(environ, "PLATFORM_VERSION")
        if udid:
            caps["appium:udid"] = udid
        if chromedriver:
            caps["appium:chromedriverExecutable"] = chromedriver
        if platform_version:
            caps["appium:platformVersion"] = platform_version
        return caps

    device_name = _value(environ, "IOS_DEVICE_NAME") or _value(environ, "DEVICE_NAME")
    if not device_name:
        raise ValueError("Local iOS sessions require IOS_DEVICE_NAME or DEVICE_NAME.")
    app_bundle = _value(environ, "IOS_BUNDLE_ID")
    app_path = _value(environ, "IOS_APP")
    if not app_bundle and not app_path:
        raise ValueError("Local iOS sessions require IOS_BUNDLE_ID or IOS_APP.")

    caps = {
        "platformName": "iOS",
        "appium:automationName": _value(environ, "IOS_AUTOMATION_NAME", "XCUITest"),
        "appium:deviceName": device_name,
        "appium:noReset": _bool(environ, "NO_RESET", True),
        "appium:newCommandTimeout": _integer(environ, "NEW_COMMAND_TIMEOUT", 300),
    }
    udid = _value(environ, "IOS_UDID") or _value(environ, "UDID")
    platform_version = _value(environ, "IOS_PLATFORM_VERSION") or _value(
        environ, "PLATFORM_VERSION"
    )
    if udid:
        caps["appium:udid"] = udid
    if platform_version:
        caps["appium:platformVersion"] = platform_version
    if app_bundle:
        caps["appium:bundleId"] = app_bundle
    if app_path:
        caps["appium:app"] = app_path
    return caps


def _read_capabilities(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Unable to read BrowserStack capabilities from {path}.") from exc
    if not isinstance(data, dict):
        raise ValueError(f"BrowserStack capabilities in {path} must be a JSON object.")
    return data


def build_browserstack_capabilities(
    platform: str,
    environ: Mapping[str, str],
    capability_file: Path,
) -> dict[str, Any]:
    """Build W3C BrowserStack capabilities for one selected mobile platform."""
    target = normalize_platform(platform)
    credentials = _required(environ, "BROWSERSTACK_USERNAME", "BROWSERSTACK_ACCESS_KEY")
    settings = _read_capabilities(capability_file)
    section = "androidCapabilities" if target == "android" else "iosCapabilities"
    raw = settings.get(section)
    if not isinstance(raw, dict):
        raise ValueError(f"{section} must be an object in {capability_file}.")

    caps = dict(raw)
    browserstack_options = caps.get("bstack:options", {})
    if not isinstance(browserstack_options, dict):
        raise ValueError("The bstack:options capability must be a JSON object.")

    platform_prefix = target.upper()
    device_name = (
        _value(environ, f"BROWSERSTACK_{platform_prefix}_DEVICE_NAME")
        or _value(environ, f"{platform_prefix}_DEVICE_NAME")
        or _value(environ, "BROWSERSTACK_DEVICE_NAME")
        or _value(environ, "DEVICE_NAME")
        or _value(caps, "appium:deviceName")
        or _value(caps, "deviceName")
        or _value(browserstack_options, "deviceName")
    )
    platform_version = (
        _value(environ, f"BROWSERSTACK_{platform_prefix}_OS_VERSION")
        or _value(environ, f"{platform_prefix}_PLATFORM_VERSION")
        or _value(environ, "BROWSERSTACK_OS_VERSION")
        or _value(environ, "PLATFORM_VERSION")
        or _value(caps, "appium:platformVersion")
        or _value(caps, "platformVersion")
        or _value(caps, "osVersion")
        or _value(browserstack_options, "osVersion")
    )
    app = (
        _value(environ, f"BROWSERSTACK_APP_{platform_prefix}")
        or _value(environ, "BROWSERSTACK_APP")
        or _value(caps, "app")
    )
    missing_settings = [
        setting
        for setting, value in (
            ("device name", device_name),
            ("OS version", platform_version),
            ("app reference", app),
        )
        if not value
    ]
    if missing_settings:
        raise ValueError(
            f"BrowserStack {target} session requires " + ", ".join(missing_settings) + "."
        )

    caps["platformName"] = "Android" if target == "android" else "iOS"
    caps.setdefault("appium:automationName", "UiAutomator2" if target == "android" else "XCUITest")
    caps["app"] = app
    for legacy_key in ("appium:deviceName", "appium:platformVersion", "deviceName", "osVersion"):
        caps.pop(legacy_key, None)

    options = dict(browserstack_options)
    options.update(
        {
            "deviceName": device_name,
            "osVersion": platform_version,
            "userName": credentials["BROWSERSTACK_USERNAME"],
            "accessKey": credentials["BROWSERSTACK_ACCESS_KEY"],
        }
    )
    project_name = _value(environ, "BROWSERSTACK_PROJECT_NAME")
    build_name = _value(environ, "BROWSERSTACK_BUILD_NAME")
    if project_name:
        options["projectName"] = project_name
    if build_name:
        options["buildName"] = build_name
    environment_name = _value(environ, "TEST_ENVIRONMENT", "qa") or "qa"
    options.setdefault("sessionName", f"{environment_name.upper()} {target.title()}")
    caps["bstack:options"] = options
    return caps


def _options_for(platform: str, capabilities: Mapping[str, Any]) -> Any:
    options: Any
    try:
        if platform == "android":
            from appium.options.android import UiAutomator2Options

            options = UiAutomator2Options()
        else:
            from appium.options.ios import XCUITestOptions

            options = XCUITestOptions()
    except ImportError as exc:
        raise RuntimeError(
            "Appium Python Client is required to create a device session; install the project dependencies."
        ) from exc
    options.load_capabilities(dict(capabilities))
    return options


def create_driver(
    environ: Mapping[str, str] | None = None,
    project_root: Path | None = None,
) -> Any:
    """Create one local or BrowserStack session; callers own its teardown."""
    if environ is None:
        try:
            from dotenv import load_dotenv

            load_dotenv()
        except ImportError:
            pass
    if project_root is None:
        project_root = Path(__file__).resolve().parents[2]
    environ = runtime_environment(environ)

    platform = normalize_platform(_value(environ, "PLATFORM", "android"))
    run_env = (_value(environ, "RUN_ENV", "local") or "local").casefold()
    if run_env not in {"local", "browserstack"}:
        raise ValueError("RUN_ENV must be either local or browserstack.")
    if run_env == "browserstack":
        environment = _value(environ, "TEST_ENVIRONMENT")
        if not environment:
            raise ValueError("TEST_ENVIRONMENT must be set to qa or stage for BrowserStack runs.")
        profile_directory = project_root / "mobile_test_automation" / "config" / "environments"
        environ = load_environment_profile(
            environment,
            environ=environ,
            profile_directory=profile_directory,
        )

    try:
        from appium import webdriver
    except ImportError as exc:
        raise RuntimeError(
            "Appium Python Client is required to create a device session; install the project dependencies."
        ) from exc

    if run_env == "local":
        capabilities = build_local_capabilities(platform, environ)
        options = _options_for(platform, capabilities)
        endpoint = normalize_appium_url(_value(environ, "APPIUM_URL", APPIUM_ENDPOINT) or "")
        return webdriver.Remote(command_executor=endpoint, options=options)

    capability_file = (
        project_root / "mobile_test_automation" / "resources" / "capabilities" / "browserstack.json"
    )
    capabilities = build_browserstack_capabilities(platform, environ, capability_file)
    options = _options_for(platform, capabilities)
    endpoint = _value(environ, "BROWSERSTACK_URL", BROWSERSTACK_ENDPOINT) or BROWSERSTACK_ENDPOINT
    driver = webdriver.Remote(command_executor=endpoint, options=options)
    # Match the legacy remote-session implicit wait; local sessions remain unchanged.
    driver.implicitly_wait(5)
    return driver
