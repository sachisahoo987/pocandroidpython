"""Unit tests for local Android runner preflight helpers."""

from __future__ import annotations

import unittest

from scripts.run_local_android import _appium_endpoint, _requested_runtime_permissions


class LocalAndroidRunnerTests(unittest.TestCase):
    def test_appium_endpoint_normalizes_legacy_path(self):
        self.assertEqual(
            _appium_endpoint("http://127.0.0.1:4723/wd/hub/"),
            ("127.0.0.1", 4723, "", "http://127.0.0.1:4723/status"),
        )

    def test_only_requested_android_runtime_permissions_are_selected(self):
        package_dump = """\
requested permissions:
    android.permission.POST_NOTIFICATIONS
    android.permission.INTERNET
install permissions:
    android.permission.INTERNET: granted=true
"""
        dangerous_permissions = """\
Dangerous Permissions:
group:android.permission-group.NOTIFICATIONS
  permission:android.permission.POST_NOTIFICATIONS
  permission:android.permission.READ_CONTACTS
"""
        self.assertEqual(
            _requested_runtime_permissions(package_dump, dangerous_permissions),
            ["android.permission.POST_NOTIFICATIONS"],
        )


if __name__ == "__main__":
    unittest.main()
