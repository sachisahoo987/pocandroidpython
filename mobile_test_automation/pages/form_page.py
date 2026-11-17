"""General Store form-page actions used by the primary active scenario."""

from __future__ import annotations

from contextlib import suppress

from mobile_test_automation.pages.landing_page import LandingPage
from mobile_test_automation.services.locator_logic import PageName


class FormPage(LandingPage):
    """Form actions shared across supported Appium platforms."""

    def wait_for_form_ready(self) -> None:
        self.perform(
            "Wait for Form Page Ready",
            lambda: self.locator.get(PageName.FORMPAGE, "nameField"),
        )

    def enter_name(self, name: str) -> None:
        def enter() -> None:
            name_field = self.locator.get(PageName.FORMPAGE, "nameField")
            name_field.clear()
            name_field.send_keys(name)
            with suppress(Exception):
                # The original Android flow treats keyboard dismissal as best-effort.
                self.driver.execute_script("mobile: hideKeyboard")

        self.perform(f"Enter Name: {name}", enter)

    def select_country(self, country: str) -> None:
        def select() -> None:
            self.locator.get(PageName.FORMPAGE, "countrySpinner").click()
            self.locator.get(PageName.FORMPAGE, "countryOption", values={"value": country}).click()

        self.perform(f"Select Country: {country}", select)

    def tap_lets_shop(self) -> None:
        self.perform(
            "Tap Let's Shop",
            lambda: self.locator.get(PageName.FORMPAGE, "letsShopBtn").click(),
        )
