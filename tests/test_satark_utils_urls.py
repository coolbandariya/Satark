"""Regression tests for shared SATARK safety helpers."""

import unittest

from satark_utils import safe_url


class SafeUrlTests(unittest.TestCase):
    def test_https_and_http_urls_are_allowed(self):
        self.assertEqual(safe_url("https://example.com/path"), "https://example.com/path")
        self.assertEqual(safe_url("http://example.com"), "http://example.com")

    def test_script_and_file_urls_are_rejected(self):
        self.assertEqual(safe_url("javascript:alert(1)"), "")
        self.assertEqual(safe_url("file:///etc/passwd"), "")

    def test_credentials_are_rejected(self):
        self.assertEqual(safe_url("https://user:pass@example.com"), "")

    def test_missing_host_is_rejected(self):
        self.assertEqual(safe_url("https:///broken"), "")


if __name__ == "__main__":
    unittest.main()
