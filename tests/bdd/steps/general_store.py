"""pytest-bdd bindings for the active General Store Gherkin scenarios."""

from __future__ import annotations

from dataclasses import dataclass

import pytest
from pytest_bdd import given, parsers, then, when

from mobile_test_automation.pages import CartPage, FormPage, LandingPage, ProductPage


@dataclass(frozen=True)
class GeneralStorePages:
    form: FormPage
    landing: LandingPage
    products: ProductPage
    cart: CartPage


@pytest.fixture
def general_store_pages(driver):
    """Mirror the Cucumber before-scenario page-object initialization."""
    return GeneralStorePages(
        form=FormPage(driver),
        landing=LandingPage(driver),
        products=ProductPage(driver),
        cart=CartPage(driver),
    )


@given("the app is launched")
def app_is_launched(general_store_pages: GeneralStorePages) -> None:
    form = general_store_pages.form
    # Keep both source perform wrappers (and their screenshot side effects).
    form.perform("App Launched / Form Ready", form.wait_for_form_ready)


@given("user is on product list page")
def user_is_on_product_list_page(general_store_pages: GeneralStorePages) -> None:
    landing = general_store_pages.landing
    landing.select_country("India")
    landing.enter_name("Sachi")
    landing.select_gender("Male")
    landing.click_shop()


@given("user is on cart page")
def user_is_on_cart_page(general_store_pages: GeneralStorePages) -> None:
    # This scenario assumes the user is already on the cart page.
    pass


@when(parsers.parse('the user selects country "{country}"'))
def user_selects_country(country: str, general_store_pages: GeneralStorePages) -> None:
    general_store_pages.form.select_country(country)


@when(parsers.parse('the user enters name "{name}"'))
def user_enters_name(name: str, general_store_pages: GeneralStorePages) -> None:
    general_store_pages.form.enter_name(name)


@when("the user taps Let's Shop")
def user_taps_lets_shop(general_store_pages: GeneralStorePages) -> None:
    general_store_pages.form.tap_lets_shop()


@then("the product list should be displayed")
def product_list_should_be_displayed(general_store_pages: GeneralStorePages) -> None:
    general_store_pages.products.verify_product_list_displayed()


@when(parsers.parse('the user adds product "{first}" and "{second}"'))
def user_adds_products(first: str, second: str, general_store_pages: GeneralStorePages) -> None:
    general_store_pages.products.add_product_by_name(first)
    general_store_pages.products.add_product_by_name(second)


@when("the user navigates to cart")
def user_navigates_to_cart(general_store_pages: GeneralStorePages) -> None:
    general_store_pages.products.go_to_cart()


@then("the cart total should equal sum of item prices")
def cart_total_matches_item_prices(general_store_pages: GeneralStorePages) -> None:
    expected = general_store_pages.cart.sum_of_product_prices()
    actual = general_store_pages.cart.displayed_total()
    assert abs(actual - expected) <= 0.01, (
        f"Displayed cart total {actual} differs from item sum {expected} by more than 0.01."
    )


@when("the user long presses on Terms and Conditions")
def user_long_presses_terms(general_store_pages: GeneralStorePages) -> None:
    general_store_pages.cart.open_terms()
