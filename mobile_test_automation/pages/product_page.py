"""General Store product-list and cart-navigation interactions."""

from __future__ import annotations

import time
from typing import Any

from mobile_test_automation.pages.base_page import BasePage
from mobile_test_automation.services.locator_logic import LocatorLogic, PageName
from mobile_test_automation.services.mobile_utility import MobileUtility

PRODUCTS_TITLE_WAIT_SECONDS = 10
PRODUCT_LIST_WAIT_SECONDS = 20


class ProductPage(BasePage):
    def __init__(self, driver: Any, *, locator: Any | None = None):
        super().__init__(driver)
        self.locator = locator or LocatorLogic(driver, platform=self.platform_name, timeout=1)
        self.mobile = MobileUtility(driver)

    def add_product_by_name(self, name: str) -> None:
        def add() -> None:
            expected_name = name.strip().casefold()
            for attempt in range(6):
                product_names = self.locator.get_all(PageName.PRODUCTPAGE, "productName")
                add_buttons = self.locator.get_all(PageName.PRODUCTPAGE, "addCartBtn")
                for index, product in enumerate(product_names):
                    if product.text.strip().casefold() == expected_name:
                        if index >= len(add_buttons):
                            raise LookupError(f"Add-to-cart button missing for product: {name}")
                        add_buttons[index].click()
                        return
                if attempt < 5:
                    self.mobile.scroll_down()

            raise RuntimeError(f"Product not found: {name}")

        self.perform(f"Add Product: {name}", add)

    def go_to_cart(self) -> None:
        self.perform(
            "Go To Cart",
            lambda: self.locator.get(PageName.PRODUCTPAGE, "cartBtn").click(),
        )

    def verify_product_list_displayed(self) -> None:
        def verify() -> None:
            title_deadline = time.monotonic() + PRODUCTS_TITLE_WAIT_SECONDS
            while time.monotonic() < title_deadline:
                try:
                    title = self.locator.get(PageName.PRODUCTPAGE, "toolbarTitle", timeout=0)
                except LookupError:
                    title = None
                if title is not None and title.text.strip() == "Products":
                    break
                time.sleep(0.25)
            else:
                raise AssertionError(
                    f"Products page title did not appear within {PRODUCTS_TITLE_WAIT_SECONDS} seconds"
                )

            products_deadline = time.monotonic() + PRODUCT_LIST_WAIT_SECONDS
            while time.monotonic() < products_deadline:
                items = self.locator.get_all(PageName.PRODUCTPAGE, "productName", timeout=0)
                if items and items[0].is_displayed():
                    return
                time.sleep(0.25)
            raise AssertionError(
                "Product list was empty or not visible after the Products page loaded"
            )

        self.perform("Verify product list is displayed", verify)
