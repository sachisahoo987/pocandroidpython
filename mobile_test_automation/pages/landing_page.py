"""General Store onboarding actions shared by the form and product-list flows."""

from __future__ import annotations

from typing import Any

from mobile_test_automation.pages.base_page import BasePage
from mobile_test_automation.services.locator_logic import LocatorLogic, PageName


class LandingPage(BasePage):
    """Actions on the General Store country/name/gender landing screen."""

    def __init__(self, driver: Any, *, locator: Any | None = None):
        super().__init__(driver)
        self.locator = locator or LocatorLogic(driver, platform=self.platform_name)

    def select_country(self, country: str) -> None:
        def select() -> None:
            self.locator.get(PageName.FORMPAGE, "countrySpinner").click()
            self.locator.get(PageName.FORMPAGE, "countryOption", values={"value": country}).click()

        self.perform(f"Select Country: {country}", select)

    def enter_name(self, name: str) -> None:
        def enter() -> None:
            name_field = self.locator.get(PageName.FORMPAGE, "nameField")
            name_field.clear()
            name_field.send_keys(name)

        self.perform(f"Enter Name: {name}", enter)

    def select_gender(self, gender: str) -> None:
        def select() -> None:
            key = "radioMale" if gender.casefold() == "male" else "radioFemale"
            self.locator.get(PageName.FORMPAGE, key).click()

        self.perform(f"Select Gender: {gender}", select)

    def click_shop(self) -> None:
        self.perform(
            "Tap Let's Shop Button",
            lambda: self.locator.get(PageName.FORMPAGE, "letsShopBtn").click(),
        )
