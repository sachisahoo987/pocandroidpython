"""Tests for the General Store locator-key generation tool."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from mobile_test_automation.tools.generate_locator_keys import generate_key_sources


class LocatorKeyGeneratorTests(unittest.TestCase):
    def test_generates_modules_for_general_store_pages(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "locators.json"
            source.write_text(
                json.dumps(
                    {
                        "$schemaVersion": 1,
                        "FormPage": {
                            "letsShopBtn": {"xpath": {"android": "//button", "ios": None}}
                        },
                        "ProductPage": {
                            "addCartBtn": {"xpath": {"android": "//button", "ios": None}}
                        },
                        "CartPage": {"totalAmount": {"xpath": {"android": "//label", "ios": None}}},
                    }
                ),
                encoding="utf-8",
            )
            output = root / "generated"

            paths = generate_key_sources(source, output)

            self.assertEqual(
                [path.name for path in paths],
                ["FormPageKey.py", "ProductPageKey.py", "CartPageKey.py"],
            )
            generated = (output / "FormPageKey.py").read_text(encoding="utf-8")
            self.assertIn("class FormPageKey(str, Enum):", generated)
            self.assertIn('LETS_SHOP_BTN = "letsShopBtn"', generated)
            self.assertTrue((output / "__init__.py").is_file())
            compile(generated, str(output / "FormPageKey.py"), "exec")

    def test_rejects_non_general_store_page_before_creating_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "locators.json"
            source.write_text(
                '{"$schemaVersion": 1, "OtherApp": {"login": {}}}',
                encoding="utf-8",
            )
            output = root / "generated"

            with self.assertRaisesRegex(ValueError, "Unknown page"):
                generate_key_sources(source, output)

            self.assertFalse(output.exists())

    def test_invalid_json_shape_is_reported_as_input_failure(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "locators.json"
            source.write_text("[]", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "JSON object"):
                generate_key_sources(source, root / "generated")

    def test_rejects_locators_missing_platform_xpath_values(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "locators.json"
            source.write_text(
                '{"$schemaVersion": 1, "FormPage": {"name": {"xpath": {"android": "//input"}}}}',
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "Android and iOS XPath"):
                generate_key_sources(source, root / "generated")

            self.assertFalse((root / "generated").exists())


if __name__ == "__main__":
    unittest.main()
