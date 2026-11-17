"""Pytest fixtures shared by Appium BDD scenarios."""

from __future__ import annotations

import logging
import tempfile
import time
from contextlib import AbstractContextManager
from pathlib import Path

import pytest

from mobile_test_automation.config.runtime_config import get_bool, get_setting
from mobile_test_automation.drivers.driver_factory import create_driver
from mobile_test_automation.services.reporting import (
    capture_dom_snapshot,
    capture_screenshot,
    safe_name,
    start_video_recording,
    stop_video_recording,
)

pytest_plugins = (
    "tests.bdd.steps.general_store",
    "tests.bdd.steps.general_store_terms",
)

LOGGER = logging.getLogger(__name__)
REP_CALL_KEY: pytest.StashKey[pytest.TestReport] = pytest.StashKey()
ALLURE_STEPS_KEY: pytest.StashKey[dict[int, AbstractContextManager[None]]] = pytest.StashKey()


@pytest.fixture
def driver(request):
    """Create and always best-effort close a scenario-scoped Appium session."""
    session = create_driver()
    record_video = get_bool("RECORD_VIDEO", default=False)
    platform = str(getattr(session, "capabilities", {}).get("platformName", "")).casefold()
    record_video = record_video and "android" in platform
    start_video_recording(session, record_video)
    try:
        yield session
    finally:
        report = request.node.stash.get(REP_CALL_KEY, None)
        if report is not None and report.failed:
            scenario_name = f"{safe_name(request.node.name)}_{time.time_ns()}"
            if get_bool("FAILURE_SCREENSHOTS", default=True):
                capture_screenshot(session, "Failure Screenshot")
            if get_bool("DUMP_DOM_ON_FAILURE", default=True):
                output_dir = Path(
                    get_setting(
                        "DOM_DUMP_DIR",
                        str(Path(tempfile.gettempdir()) / "pocandroid-dom-dumps"),
                    )
                )
                capture_dom_snapshot(session, scenario_name, output_dir)
        try:
            stop_video_recording(
                session,
                safe_name(request.node.name),
                enabled=record_video,
            )
        except Exception:
            LOGGER.exception("Unable to finalize scenario video recording.")
        capabilities = getattr(session, "capabilities", {}) or {}
        app_package = get_setting("APP_PACKAGE") or capabilities.get(
            "appium:appPackage", capabilities.get("appPackage")
        )
        if "android" in platform and app_package:
            try:
                terminated = session.terminate_app(app_package)
                if terminated is False:
                    LOGGER.warning("App %s was not running at scenario teardown.", app_package)
            except Exception:
                LOGGER.exception(
                    "Unable to terminate app %s during scenario teardown.", app_package
                )
        try:
            session.quit()
        except Exception:
            LOGGER.exception("Unable to close the Appium session during scenario teardown.")


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Keep the call result available to the driver fixture before teardown."""
    outcome = yield
    report = outcome.get_result()
    if report.when == "call":
        item.stash[REP_CALL_KEY] = report


def pytest_bdd_before_scenario(request, feature, scenario):
    """Create the shared driver before each BDD scenario, even if steps use helpers."""
    request.getfixturevalue("driver")


def pytest_bdd_before_step(request, feature, scenario, step, step_func):
    """Log and record each BDD step for console progress and Allure reports."""
    LOGGER.info("[STEP START] %s :: %s", scenario.name, step.name)
    import allure

    allure_step = allure.step(step.name)
    allure_step.__enter__()
    active_steps = request.node.stash.setdefault(ALLURE_STEPS_KEY, {})
    active_steps[id(step)] = allure_step


def pytest_bdd_after_step(request, feature, scenario, step, step_func, step_func_args):
    """Log successful BDD steps and optionally attach a screenshot."""
    LOGGER.info("[STEP PASS] %s :: %s", scenario.name, step.name)
    active_steps = request.node.stash.get(ALLURE_STEPS_KEY, {})
    allure_step = active_steps.pop(id(step), None)
    if allure_step is not None:
        allure_step.__exit__(None, None, None)
    if get_bool("TAKE_ALL_SCREENS", default=False):
        driver_session = request.getfixturevalue("driver")
        capture_screenshot(driver_session, f"{scenario.name}_{step.name}")


def pytest_bdd_step_error(request, feature, scenario, step, step_func, step_func_args, exception):
    """Log failed BDD steps with their exception for live console diagnostics."""
    LOGGER.error(
        "[STEP FAIL] %s :: %s - %s",
        scenario.name,
        step.name,
        exception,
    )
    active_steps = request.node.stash.get(ALLURE_STEPS_KEY, {})
    allure_step = active_steps.pop(id(step), None)
    if allure_step is not None:
        allure_step.__exit__(type(exception), exception, exception.__traceback__)


def pytest_bdd_step_func_lookup_error(request, feature, scenario, step, exception):
    """Log undefined or unresolved steps as failures."""
    LOGGER.error(
        "[STEP FAIL] %s :: %s - %s",
        scenario.name,
        step.name,
        exception,
    )
