"""Security boundary tests for URL fetching; no real network is used."""
import unittest
from unittest.mock import Mock, patch

from url_security import SafeRedirectHandler, fetch_url_text, is_public_url


def fake_response(body=b"<html><body>Hello</body></html>", headers=None, final_url="https://example.com/"):
    response = Mock()
    response.headers = headers or {"Content-Type": "text/html; charset=utf-8", "Content-Length": str(len(body))}
    response.read.return_value = body
    response.geturl.return_value = final_url
    response.__enter__ = Mock(return_value=response)
    response.__exit__ = Mock(return_value=False)
    return response


class URLSecurityTests(unittest.TestCase):
    def test_redirect_budget_is_enforced(self):
        handler = SafeRedirectHandler(max_redirects=1)
        req = Mock()
        with patch("url_security.is_public_url", return_value=True), patch(
            "url_security.HTTPRedirectHandler.redirect_request", return_value=req
        ):
            handler.redirect_request(req, Mock(), 302, "Found", {}, "https://example.com/one")
            with self.assertRaisesRegex(ValueError, "redirect safety limit"):
                handler.redirect_request(req, Mock(), 302, "Found", {}, "https://example.com/two")

    def test_redirect_to_private_address_is_rejected(self):
        handler = SafeRedirectHandler()
        with patch("url_security.is_public_url", return_value=False):
            with self.assertRaisesRegex(ValueError, "private or unsafe"):
                handler.redirect_request(
                    Mock(), Mock(), 302, "Found", {}, "http://127.0.0.1/admin"
                )

    def test_non_http_schemes_and_credentials_fail_closed(self):
        self.assertFalse(is_public_url("file:///etc/passwd"))
        self.assertFalse(is_public_url("ftp://example.com/file"))
        self.assertFalse(is_public_url("https://user:password@example.com/"))
        self.assertFalse(is_public_url("http://localhost/"))
        self.assertFalse(is_public_url("http://127.0.0.1/"))

    def test_mixed_public_and_private_dns_answers_fail_closed(self):
        answers = [
            (None, None, None, None, ("93.184.216.34", 443)),
            (None, None, None, None, ("10.0.0.5", 443)),
        ]
        with patch("url_security.socket.getaddrinfo", return_value=answers):
            self.assertFalse(is_public_url("https://example.com/"))

    def test_dns_resolution_failure_fails_closed(self):
        with patch("url_security.socket.getaddrinfo", side_effect=OSError("dns unavailable")):
            self.assertFalse(is_public_url("https://example.com/"))

    def test_unsupported_binary_content_is_rejected(self):
        response = fake_response(b"\x00\x01\x02", {"Content-Type": "application/octet-stream", "Content-Length": "3"})
        with patch("url_security.is_public_url", return_value=True), patch(
            "url_security.build_opener"
        ) as opener_factory:
            opener_factory.return_value.open.return_value = response
            with self.assertRaisesRegex(ValueError, "unsupported content type"):
                fetch_url_text("https://example.com/file.bin")

    def test_oversized_declared_response_is_rejected_before_read(self):
        response = fake_response(b"tiny", {"Content-Type": "text/plain", "Content-Length": "999999999"})
        with patch("url_security.is_public_url", return_value=True), patch(
            "url_security.build_opener"
        ) as opener_factory:
            opener_factory.return_value.open.return_value = response
            with self.assertRaisesRegex(ValueError, "larger than"):
                fetch_url_text("https://example.com/large.txt")
        response.read.assert_not_called()

    def test_malformed_content_length_is_rejected(self):
        response = fake_response(b"tiny", {"Content-Type": "text/plain", "Content-Length": "unknown"})
        with patch("url_security.is_public_url", return_value=True), patch(
            "url_security.build_opener"
        ) as opener_factory:
            opener_factory.return_value.open.return_value = response
            with self.assertRaisesRegex(ValueError, "invalid content length"):
                fetch_url_text("https://example.com/page.txt")

    def test_response_read_limit_is_enforced(self):
        from config import URL_MAX_BYTES
        response = fake_response(b"x" * (URL_MAX_BYTES + 1), {"Content-Type": "text/plain"})
        with patch("url_security.is_public_url", return_value=True), patch(
            "url_security.build_opener"
        ) as opener_factory:
            opener_factory.return_value.open.return_value = response
            with self.assertRaisesRegex(ValueError, "larger than"):
                fetch_url_text("https://example.com/large.txt")

    def test_html_parser_excludes_script_and_style_text(self):
        response = fake_response(
            b"<html><body>Visible<script>secret()</script><style>.hidden{}</style><p>Text</p></body></html>",
            {"Content-Type": "text/html", "Content-Length": "100"},
        )
        with patch("url_security.is_public_url", return_value=True), patch(
            "url_security.build_opener"
        ) as opener_factory:
            opener_factory.return_value.open.return_value = response
            result = fetch_url_text("https://example.com/")
        self.assertIn("Visible", result)
        self.assertIn("Text", result)
        self.assertNotIn("secret", result)
        self.assertNotIn(".hidden", result)


if __name__ == "__main__":
    unittest.main()
