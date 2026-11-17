"""Strict, platform-aware XPath resolution from the shared locator catalog."""

from __future__ import annotations

import json
import string
from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Literal

from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException,
)
from selenium.webdriver.support import expected_conditions as conditions
from selenium.webdriver.support.ui import WebDriverWait

_DEFAULT_RESOURCE_DIR = Path(__file__).resolve().parents[1] / "resources" / "locators"
_SUPPORTED_PLATFORMS = frozenset({"android", "ios"})


class LocatorConfigurationError(ValueError):
    """Raised when a locator is absent, malformed, or unavailable on a platform."""


class LocatorStrategy(str, Enum):
    XPATH = "xpath"


class PageName(str, Enum):
    FORMPAGE = "FormPage"
    PRODUCTPAGE = "ProductPage"
    CARTPAGE = "CartPage"
    WEBPAGE = "WebPage"

    @property
    def json_key(self) -> str:
        return self.value


@dataclass(frozen=True)
class LocatorCandidate:
    strategy: LocatorStrategy
    value: str


def normalize_platform(platform: str) -> str:
    normalized = platform.strip().casefold()
    if normalized not in _SUPPORTED_PLATFORMS:
        raise LocatorConfigurationError(
            f"Unsupported locator platform {platform!r}; expected Android or iOS."
        )
    return normalized


def _catalog_path(resource_dir: Path | None) -> Path:
    return (resource_dir or _DEFAULT_RESOURCE_DIR) / "locators.json"


def _read_catalog(path: Path) -> dict[str, Any]:
    try:
        content = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise LocatorConfigurationError(f"Unable to read locator catalog: {path}") from exc
    try:
        catalog = json.loads(content)
    except json.JSONDecodeError as exc:
        raise LocatorConfigurationError(
            f"Invalid locator catalog JSON at line {exc.lineno}, column {exc.colno}: {path}"
        ) from exc
    if not isinstance(catalog, dict):
        raise LocatorConfigurationError(f"Locator catalog must be a JSON object: {path}")
    if type(catalog.get("$schemaVersion")) is not int or catalog["$schemaVersion"] != 1:
        raise LocatorConfigurationError(
            f"Unsupported or missing locator catalog schema version in {path}."
        )
    unexpected_sections = set(catalog) - {
        "$schemaVersion",
        *(page.value for page in PageName),
    }
    if unexpected_sections:
        raise LocatorConfigurationError(
            f"Unknown locator catalog section(s): {', '.join(sorted(unexpected_sections))}."
        )
    return catalog


def _xpath_literal(value: str) -> str:
    if "'" not in value:
        return f"'{value}'"
    if '"' not in value:
        return f'"{value}"'
    parts = value.split("'")
    arguments: list[str] = []
    for index, part in enumerate(parts):
        if part:
            arguments.append(f"'{part}'")
        if index < len(parts) - 1:
            arguments.append('"\'"')
    return f"concat({', '.join(arguments)})"


def _format_xpath(xpath: str, values: Mapping[str, str] | None) -> str:
    try:
        parts = list(string.Formatter().parse(xpath))
    except ValueError as exc:
        raise LocatorConfigurationError("Malformed XPath template.") from exc
    fields: set[str] = set()
    for _, field_name, format_spec, conversion in parts:
        if field_name is None:
            continue
        if not field_name.isidentifier() or format_spec or conversion:
            raise LocatorConfigurationError("XPath templates support only simple named values.")
        fields.add(field_name)
    supplied = set(values or {})
    if fields != supplied:
        missing = sorted(fields - supplied)
        unexpected = sorted(supplied - fields)
        details = []
        if missing:
            details.append(f"missing template values: {', '.join(missing)}")
        if unexpected:
            details.append(f"unexpected template values: {', '.join(unexpected)}")
        raise LocatorConfigurationError("; ".join(details))
    if any(not isinstance(value, str) for value in (values or {}).values()):
        raise LocatorConfigurationError("XPath template values must be strings.")
    escaped = {name: _xpath_literal(value) for name, value in (values or {}).items()}
    try:
        return xpath.format_map(escaped)
    except (KeyError, ValueError) as exc:
        raise LocatorConfigurationError("Malformed XPath template.") from exc


def read_locator_spec(
    page: PageName | str,
    key: str,
    *,
    platform: str,
    resource_dir: Path | None = None,
    values: Mapping[str, str] | None = None,
) -> dict[LocatorStrategy, str]:
    """Resolve one XPath for a platform from the shared JSON catalog."""
    target = normalize_platform(platform)
    path = _catalog_path(resource_dir)
    catalog = _read_catalog(path)
    page_name = page.json_key if isinstance(page, PageName) else str(page)
    page_data = catalog.get(page_name)
    if not isinstance(page_data, dict):
        raise LocatorConfigurationError(f"Unknown page {page_name!r} in locator catalog {path}.")

    locator_data = page_data.get(key)
    if not isinstance(locator_data, dict):
        raise LocatorConfigurationError(
            f"Unknown locator {page_name}.{key} in locator catalog {path}."
        )
    if set(locator_data) != {"xpath"}:
        raise LocatorConfigurationError(
            f"Locator {page_name}.{key} must contain only an XPath definition."
        )

    xpath_by_platform = locator_data.get("xpath")
    if not isinstance(xpath_by_platform, dict):
        raise LocatorConfigurationError(
            f"Locator {page_name}.{key} must define platform-specific XPath values."
        )
    if set(xpath_by_platform) != _SUPPORTED_PLATFORMS:
        raise LocatorConfigurationError(
            f"Locator {page_name}.{key} must define exactly Android and iOS XPath values."
        )
    if any(
        expression is not None and (not isinstance(expression, str) or not expression.strip())
        for expression in xpath_by_platform.values()
    ):
        raise LocatorConfigurationError(
            f"Locator {page_name}.{key} contains a malformed platform XPath value."
        )
    xpath = xpath_by_platform.get(target)
    if not isinstance(xpath, str) or not xpath.strip():
        raise LocatorConfigurationError(
            f"XPath for {page_name}.{key} is not configured for {target} in locator catalog {path}."
        )
    return {LocatorStrategy.XPATH: _format_xpath(xpath.strip(), values)}


def to_by(locator: LocatorCandidate) -> tuple[str, str]:
    if locator.strategy is not LocatorStrategy.XPATH:
        raise LocatorConfigurationError(f"Unsupported locator strategy: {locator.strategy.value}.")
    return "xpath", locator.value


class LocatorLogic:
    """Resolve only catalogued XPath selectors and report configuration errors."""

    def __init__(
        self,
        driver: Any,
        *,
        platform: str,
        timeout: float = 15,
        resource_dir: Path | None = None,
        poll_interval: float = 0.25,
    ) -> None:
        if driver is None:
            raise ValueError("An active Appium driver is required for locator resolution.")
        if timeout < 0:
            raise ValueError("Locator timeout cannot be negative.")
        if poll_interval <= 0:
            raise ValueError("Locator poll interval must be greater than zero.")
        self.driver = driver
        self.platform = normalize_platform(platform)
        self.timeout = timeout
        self.resource_dir = resource_dir
        self.poll_interval = poll_interval

    def one_ele(self, key: Any) -> Any:
        page = key.page() if callable(key.page) else key.page
        locator_key = key.key() if callable(key.key) else key.key
        return self.get(page, locator_key)

    def mul_ele(self, key: Any) -> list[Any]:
        page = key.page() if callable(key.page) else key.page
        locator_key = key.key() if callable(key.key) else key.key
        return self.get_all(page, locator_key)

    def get(
        self,
        page: PageName | str,
        locator_key: str,
        *,
        values: Mapping[str, str] | None = None,
        timeout: float | None = None,
    ) -> Any:
        xpath = read_locator_spec(
            page,
            locator_key,
            platform=self.platform,
            resource_dir=self.resource_dir,
            values=values,
        )[LocatorStrategy.XPATH]
        wait_timeout = self.timeout if timeout is None else timeout
        if wait_timeout < 0:
            raise ValueError("Locator timeout cannot be negative.")
        try:
            return WebDriverWait(
                self.driver,
                wait_timeout,
                poll_frequency=self.poll_interval,
                ignored_exceptions=(
                    NoSuchElementException,
                    StaleElementReferenceException,
                ),
            ).until(conditions.visibility_of_element_located(("xpath", xpath)))
        except TimeoutException as exc:
            raise LookupError(
                f"No visible element found for page={_page_key(page)}, "
                f"key={locator_key}, platform={self.platform}"
            ) from exc

    def get_all(
        self,
        page: PageName | str,
        locator_key: str,
        *,
        values: Mapping[str, str] | None = None,
        timeout: float | None = None,
    ) -> list[Any]:
        xpath = read_locator_spec(
            page,
            locator_key,
            platform=self.platform,
            resource_dir=self.resource_dir,
            values=values,
        )[LocatorStrategy.XPATH]
        wait_timeout = self.timeout if timeout is None else timeout
        if wait_timeout < 0:
            raise ValueError("Locator timeout cannot be negative.")

        def find_visible(driver: Any) -> list[Any] | Literal[False]:
            elements = driver.find_elements("xpath", xpath)
            if elements and all(element.is_displayed() for element in elements):
                return elements
            return False

        try:
            return WebDriverWait(
                self.driver,
                wait_timeout,
                poll_frequency=self.poll_interval,
                ignored_exceptions=(
                    NoSuchElementException,
                    StaleElementReferenceException,
                ),
            ).until(find_visible)
        except TimeoutException:
            return []


def _page_key(page: PageName | str) -> str:
    return page.json_key if isinstance(page, PageName) else str(page)
