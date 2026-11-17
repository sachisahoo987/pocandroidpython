"""Platform-aware verification for the General Store Terms dialog."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from mobile_test_automation.services.locator_logic import (
    LocatorStrategy,
    PageName,
    normalize_platform,
    read_locator_spec,
)


def _platform_name(driver: Any) -> str:
    capabilities = getattr(driver, "capabilities", {}) or {}
    name = capabilities.get("platformName", capabilities.get("platform", ""))
    return normalize_platform(str(name))


def _terms_title_locator(platform: str, resource_dir: Path | None = None) -> tuple[str, str]:
    xpath = read_locator_spec(
        PageName.CARTPAGE,
        "termsTitle",
        platform=platform,
        resource_dir=resource_dir,
    )[LocatorStrategy.XPATH]
    return "xpath", xpath


def is_terms_modal_displayed(driver: Any, *, resource_dir: Path | None = None) -> bool:
    """Return true only when the Terms Of Use title is visible in the dialog."""
    locator = _terms_title_locator(_platform_name(driver), resource_dir)
    return any(element.is_displayed() for element in driver.find_elements(*locator))


def assert_terms_modal_displayed(
    driver: Any,
    timeout_seconds: float = 5.0,
    poll_interval_seconds: float = 0.2,
    *,
    resource_dir: Path | None = None,
) -> None:
    """Wait briefly for a visible Terms Of Use title, then fail with context."""
    if timeout_seconds < 0:
        raise ValueError("timeout_seconds cannot be negative.")
    if poll_interval_seconds <= 0:
        raise ValueError("poll_interval_seconds must be greater than zero.")

    platform = _platform_name(driver)
    deadline = time.monotonic() + timeout_seconds
    while True:
        if is_terms_modal_displayed(driver, resource_dir=resource_dir):
            return
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break
        time.sleep(min(poll_interval_seconds, remaining))

    raise AssertionError(
        f"Terms Of Use modal title was not visible on {platform} within "
        f"{timeout_seconds:g} seconds."
    )
