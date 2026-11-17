"""Instance-scoped Appium gestures, context switching, and permission helpers."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any


class MobileUtility:
    def __init__(self, driver: Any):
        if driver is None:
            raise RuntimeError("An active Appium driver is required.")
        self.driver = driver

    def safe_click(self, element: Any, timeout_seconds: float) -> None:
        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            try:
                if element.is_displayed() and element.is_enabled():
                    element.click()
                    return
            except Exception:
                pass
            time.sleep(0.3)
        raise RuntimeError("safeClick failed: element never became interactable.")

    def wait_and_click(self, element: Any, timeout_seconds: float) -> None:
        self.safe_click(element, timeout_seconds)

    def tap(self, element: Any) -> Any:
        return self.driver.execute_script(
            "mobile: tapGesture", {"elementId": getattr(element, "id", None)}
        )

    def wait_for_webview(self, timeout_seconds: float) -> str:
        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            try:
                contexts = self.driver.contexts
                for context in contexts:
                    if "webview" in context.casefold():
                        self.driver.switch_to.context(context)
                        return context
            except Exception:
                pass
            time.sleep(0.5)
        raise TimeoutError(f"No WEBVIEW context available after {timeout_seconds} seconds.")

    def switch_to_webview(self) -> str:
        return self.wait_for_webview(30)

    def switch_to_native(self) -> None:
        self.driver.switch_to.context("NATIVE_APP")

    def print_contexts(self) -> list[str]:
        return list(self.driver.contexts)

    @property
    def current_context(self) -> str:
        return str(self.driver.current_context)

    def screenshot_bytes(self) -> bytes:
        try:
            content = self.driver.get_screenshot_as_png()
            return content if isinstance(content, bytes) else bytes(content)
        except Exception:
            return b""

    def save_screenshot(
        self, name: str, output_dir: Path = Path("test-output/screenshots")
    ) -> bytes:
        content = self.screenshot_bytes()
        if not content:
            return b""
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
            destination = output_dir / f"{name}_{int(time.time() * 1000)}.png"
            destination.write_bytes(content)
            return content
        except OSError:
            return b""

    def scroll_down(self) -> bool:
        capabilities = getattr(self.driver, "capabilities", {}) or {}
        platform = str(capabilities.get("platformName", "")).strip().casefold()
        if platform == "android":
            self.driver.execute_script(
                "mobile: scrollGesture", {"direction": "down", "percent": 0.8}
            )
            return True
        if platform == "ios":
            self.driver.execute_script("mobile: swipe", {"direction": "up"})
            return True
        raise ValueError(f"Scrolling is not configured for platform {platform!r}.")

    def perform_back(self) -> Any:
        return self.driver.execute_script("mobile: pressButton", {"action": "back"})

    def handle_permission_popup(self) -> bool:
        resource_ids = (
            "com.android.permissioncontroller:id/permission_allow_button",
            "com.android.permissioncontroller:id/permission_allow_one_time_button",
            "com.android.permissioncontroller:id/permission_allow_foreground_only_button",
            "com.android.permissioncontroller:id/permission_allow_always_button",
        )
        for resource_id in resource_ids:
            try:
                self.driver.find_element("id", resource_id).click()
                time.sleep(0.5)
                return True
            except Exception:
                pass

        for text in (
            "Allow",
            "ALLOW",
            "Allow all the time",
            "Allow this time",
            "Allow only while using the app",
            "OK",
            "Yes",
        ):
            try:
                selector = f'new UiSelector().textContains("{text}")'
                self.driver.find_element("-android uiautomator", selector).click()
                time.sleep(0.5)
                return True
            except Exception:
                pass
        try:
            selector = 'new UiSelector().className("android.widget.Button").clickable(true)'
            self.driver.find_element("-android uiautomator", selector).click()
            return True
        except Exception:
            return False
