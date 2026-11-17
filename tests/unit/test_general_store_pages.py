"""Dependency-free behavior tests for the General Store page-object port."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from mobile_test_automation.pages.cart_page import CartPage
from mobile_test_automation.pages.form_page import FormPage
from mobile_test_automation.pages.landing_page import LandingPage
from mobile_test_automation.pages.product_page import ProductPage


class FakeElement:
    def __init__(self, text: str = "", *, displayed: bool = True, element_id: str = "e1"):
        self.text = text
        self.displayed = displayed
        self.id = element_id
        self.click_count = 0
        self.cleared = False
        self.sent_text: list[str] = []

    def is_displayed(self) -> bool:
        return self.displayed

    def click(self) -> None:
        self.click_count += 1

    def clear(self) -> None:
        self.cleared = True

    def send_keys(self, text: str) -> None:
        self.sent_text.append(text)


class FakeDriver:
    def __init__(self, *, fail_hide_keyboard: bool = False, fail_long_press: bool = False):
        self.capabilities = {"platformName": "Android"}
        self.fail_hide_keyboard = fail_hide_keyboard
        self.fail_long_press = fail_long_press
        self.scripts: list[tuple[str, tuple[object, ...]]] = []
        self.find_calls: list[tuple[str, str]] = []
        self.scroll_element = FakeElement()

    def execute_script(self, command: str, *args: object) -> None:
        self.scripts.append((command, args))
        if command == "mobile: hideKeyboard" and self.fail_hide_keyboard:
            raise RuntimeError("keyboard already hidden")
        if command == "mobile: longClickGesture" and self.fail_long_press:
            raise RuntimeError("gesture unsupported")

    def find_element(self, by: str, value: str) -> FakeElement:
        self.find_calls.append((by, value))
        return self.scroll_element


class FakeLocator:
    def __init__(self, *, elements=None, plural=None):
        self.elements = elements or {}
        self.plural = {key: list(values) for key, values in (plural or {}).items()}
        self.calls: list[tuple[str, str]] = []
        self.template_values: list[tuple[str, dict[str, str] | None]] = []

    def get(self, page, key: str, *, values=None, timeout=None) -> FakeElement:
        self.calls.append((page.value, key))
        self.template_values.append((key, values))
        return self.elements[key]

    def get_all(self, page, key: str, *, timeout=None) -> list[FakeElement]:
        self.calls.append((page.value, key))
        values = self.plural.get(key, [])
        if len(values) > 1 and isinstance(values[0], list):
            return values.pop(0)
        return values[0] if values and isinstance(values[0], list) else values


class GeneralStorePageTests(unittest.TestCase):
    def setUp(self) -> None:
        screenshot_patcher = patch("mobile_test_automation.pages.base_page.capture_screenshot")
        self.capture_screenshot = screenshot_patcher.start()
        self.addCleanup(screenshot_patcher.stop)

    def test_form_country_uses_shared_xpath_locator_and_keyboard_failure_is_best_effort(self):
        driver = FakeDriver(fail_hide_keyboard=True)
        country = FakeElement()
        country_option = FakeElement()
        name = FakeElement()
        locator = FakeLocator(
            elements={
                "countrySpinner": country,
                "countryOption": country_option,
                "nameField": name,
            }
        )
        page = FormPage(driver, locator=locator)

        page.select_country("Argentina")
        page.enter_name("TestUser")

        self.assertEqual(country.click_count, 1)
        self.assertEqual(country_option.click_count, 1)
        self.assertEqual(
            locator.calls[:2], [("FormPage", "countrySpinner"), ("FormPage", "countryOption")]
        )
        self.assertEqual(locator.template_values[1], ("countryOption", {"value": "Argentina"}))
        self.assertEqual(driver.find_calls, [])
        self.assertTrue(name.cleared)
        self.assertEqual(name.sent_text, ["TestUser"])
        self.assertEqual(driver.scripts, [("mobile: hideKeyboard", ())])

    def test_product_is_added_on_first_visible_match(self):
        target = FakeElement(" Air Jordan 4 Retro ")
        target_button = FakeElement()
        button = FakeElement()
        driver = FakeDriver()
        locator = FakeLocator(
            plural={
                "productName": [FakeElement("Jordan 6 Rings"), target],
                "addCartBtn": [button, target_button],
            }
        )
        page = ProductPage(driver, locator=locator)

        page.add_product_by_name("air jordan 4 retro")

        self.assertEqual(button.click_count, 0)
        self.assertEqual(target_button.click_count, 1)
        self.assertEqual(driver.find_calls, [])
        self.assertEqual(driver.scripts, [])

    def test_product_scrolls_then_retries_and_raises_if_still_missing(self):
        target = FakeElement("Jordan 6 Rings")
        add_button = FakeElement()
        locator = FakeLocator(
            plural={
                "productName": [[], [target]],
                "addCartBtn": [[], [add_button]],
            }
        )
        driver = FakeDriver()
        ProductPage(driver, locator=locator).add_product_by_name("Jordan 6 Rings")

        self.assertEqual(driver.scripts[0][0], "mobile: scrollGesture")
        self.assertEqual(add_button.click_count, 1)

        missing_locator = FakeLocator(plural={"productName": [[], []], "addCartBtn": [[], []]})
        with self.assertRaisesRegex(RuntimeError, "Product not found: Unknown"):
            ProductPage(FakeDriver(), locator=missing_locator).add_product_by_name("Unknown")

    def test_product_list_requires_a_visible_first_item(self):
        page = ProductPage(
            FakeDriver(),
            locator=FakeLocator(
                elements={"toolbarTitle": FakeElement("Products")},
                plural={"productName": []},
            ),
        )
        with (
            patch("mobile_test_automation.pages.product_page.PRODUCT_LIST_WAIT_SECONDS", 0),
            self.assertRaisesRegex(AssertionError, "Product list was empty"),
        ):
            page.verify_product_list_displayed()

    def test_cart_totals_parse_currency_and_long_press_has_click_fallback(self):
        terms = FakeElement(element_id="terms-id")
        locator = FakeLocator(
            elements={"totalAmount": FakeElement("$2,500.50"), "termsBtn": terms},
            plural={"productPrice": [FakeElement("$1,000.25"), FakeElement("$1,500.25")]},
        )
        driver = FakeDriver(fail_long_press=True)
        page = CartPage(driver, locator=locator)

        self.assertEqual(page.sum_of_product_prices(), 2500.5)
        self.assertEqual(page.displayed_total(), 2500.5)
        page.open_terms()

        self.assertEqual(driver.scripts[-1][0], "mobile: longClickGesture")
        self.assertEqual(driver.scripts[-1][1][0], {"elementId": "terms-id", "duration": 2000})
        self.assertEqual(terms.click_count, 1)

    def test_long_press_success_uses_two_second_gesture(self):
        terms = FakeElement(element_id="terms-id")
        driver = FakeDriver()
        CartPage(driver, locator=FakeLocator(elements={"termsBtn": terms})).open_terms()

        self.assertEqual(
            driver.scripts,
            [("mobile: longClickGesture", ({"elementId": "terms-id", "duration": 2000},))],
        )
        self.assertEqual(terms.click_count, 0)

    def test_landing_gender_uses_male_only_for_exact_male_value(self):
        male = FakeElement()
        female = FakeElement()
        locator = FakeLocator(elements={"radioMale": male, "radioFemale": female})
        page = LandingPage(FakeDriver(), locator=locator)

        page.select_gender("Male")
        page.select_gender("unspecified")

        self.assertEqual(male.click_count, 1)
        self.assertEqual(female.click_count, 1)


if __name__ == "__main__":
    unittest.main()
