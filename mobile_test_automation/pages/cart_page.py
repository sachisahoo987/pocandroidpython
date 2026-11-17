"""General Store cart totals and Terms interaction."""

from __future__ import annotations

import re
from typing import Any

from mobile_test_automation.pages.base_page import BasePage
from mobile_test_automation.services.locator_logic import LocatorLogic, PageName


def _price_value(text: str) -> float:
    """Parse the source app's currency display by removing nonnumeric symbols."""
    return float(re.sub(r"[^0-9.]", "", text))


class CartPage(BasePage):
    def __init__(self, driver: Any, *, locator: Any | None = None):
        super().__init__(driver)
        self.locator = locator or LocatorLogic(driver, platform=self.platform_name)

    def sum_of_product_prices(self) -> float:
        return self.perform(
            "Calculate Sum of Product Prices",
            lambda: sum(
                _price_value(element.text)
                for element in self.locator.get_all(PageName.CARTPAGE, "productPrice")
            ),
        )

    def displayed_total(self) -> float:
        return self.perform(
            "Get Displayed Cart Total",
            lambda: _price_value(self.locator.get(PageName.CARTPAGE, "totalAmount").text),
        )

    def open_terms(self) -> None:
        def open_dialog() -> None:
            terms_button = self.locator.get(PageName.CARTPAGE, "termsBtn")
            try:
                self.driver.execute_script(
                    "mobile: longClickGesture",
                    {"elementId": terms_button.id, "duration": 2000},
                )
            except Exception:
                # Remote drivers that reject this Appium gesture use a regular click.
                terms_button.click()

        self.perform("Open Terms & Conditions", open_dialog)
