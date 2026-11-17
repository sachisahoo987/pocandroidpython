"""Step binding for verifying the General Store Terms dialog."""

from pytest_bdd import then

from mobile_test_automation.services.terms_modal import assert_terms_modal_displayed


@then("the Terms modal should be displayed")
def terms_modal_should_be_displayed(driver):
    assert_terms_modal_displayed(driver)
