"""Shared Appium page actions, waits, platform helpers, and screenshots."""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any, TypeVar

from mobile_test_automation.config.runtime_config import get_bool
from mobile_test_automation.services.reporting import capture_screenshot

T = TypeVar("T")


class BasePage:
    def __init__(self, driver: Any):
        if driver is None:
            raise RuntimeError("Driver is required before creating a page object.")
        self.driver = driver

    def perform(self, action: str, operation: Callable[[], T]) -> T:
        """Run an action and optionally capture its post-action screenshot."""
        result = operation()
        if get_bool("ACTION_SCREENSHOTS", default=True):
            capture_screenshot(self.driver, f"{action} Screenshot")
        return result

    def wait_for_visible(self, element: Any, seconds: float = 20) -> Any:
        deadline = time.monotonic() + seconds
        last_error: Exception | None = None
        while True:
            try:
                if element.is_displayed():
                    return element
            except Exception as exc:
                last_error = exc
            if time.monotonic() >= deadline:
                message = f"Element was not visible within {seconds} seconds."
                if last_error is not None:
                    raise TimeoutError(message) from last_error
                raise TimeoutError(message)
            time.sleep(min(0.1, max(0, deadline - time.monotonic())))

    def click(self, element: Any, message: str = "Click") -> None:
        self.perform(message, element.click)

    def type_text(self, element: Any, text: str, message: str = "Type") -> None:
        self.perform(message, lambda: element.send_keys(text))

    def get_text(self, element: Any, message: str = "Read text") -> str:
        return self.perform(message, lambda: element.text)

    @property
    def platform_name(self) -> str:
        capabilities = getattr(self.driver, "capabilities", {}) or {}
        return str(capabilities.get("platformName", "")).casefold()

    @property
    def is_android(self) -> bool:
        return "android" in self.platform_name

    @property
    def is_ios(self) -> bool:
        return "ios" in self.platform_name
