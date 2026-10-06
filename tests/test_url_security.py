"""Security boundary tests for URL fetching."""
import unittest
from unittest.mock import patch, Mock
from url_security import SafeRedirectHandler, is_public_url

class URLSecurityTests(unittest.TestCase):
    def test_redirect_budget_is_enforced(self):
        handler=SafeRedirectHandler(max_redirects=1)
        req=Mock()
        with patch("url_security.is_public_url", return_value=True):
            handler.redirect_request(req, Mock(), 302, "Found", {}, "https://example.com/one")
            with self.assertRaises(ValueError):
                handler.redirect_request(req, Mock(), 302, "Found", {}, "https://example.com/two")

    def test_non_http_schemes_fail_closed(self):
        self.assertFalse(is_public_url("file:///etc/passwd"))
        self.assertFalse(is_public_url("ftp://example.com/file"))

if __name__=="__main__":
    unittest.main()
