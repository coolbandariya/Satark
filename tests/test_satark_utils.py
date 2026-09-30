"""Unit tests for SATARK normalization helpers."""
import unittest

from satark_utils import safe_text, clean_json_text, normalize_check_value, check_class
from reports import make_pdf_report
from unittest.mock import patch
from url_security import is_public_url, VisibleTextParser

class TextNormalizationTests(unittest.TestCase):
    def test_url_scheme_and_credentials_are_rejected(self):
        self.assertFalse(is_public_url('file:///etc/passwd'))
        self.assertFalse(is_public_url('https://user:pass@example.com'))
        self.assertFalse(is_public_url('http://localhost'))

    @patch('url_security.socket.getaddrinfo', side_effect=OSError('DNS unavailable'))
    def test_url_dns_failure_fails_closed(self, _mock_dns):
        self.assertFalse(is_public_url('https://example.com'))

    @patch('url_security.socket.getaddrinfo')
    def test_url_private_address_is_rejected(self, mock_dns):
        mock_dns.return_value = [(None, None, None, None, ('127.0.0.1', 443))]
        self.assertFalse(is_public_url('https://example.com'))

    def test_visible_text_parser_skips_script_and_style(self):
        parser = VisibleTextParser()
        parser.feed('<p>Visible</p><script>secret()</script><style>.x{}</style>')
        self.assertEqual(parser.text(), 'Visible')

    def test_safe_text(self):
        self.assertEqual(safe_text(None, "fallback"), "fallback")
        self.assertEqual(safe_text("  hello  "), "hello")

    def test_clean_json_text(self):
        self.assertEqual(clean_json_text('```json\n{"ok": true}\n```'), '{"ok": true}')
        self.assertEqual(clean_json_text("no object here"), "no object here")

    def test_normalize_check_value(self):
        self.assertEqual(normalize_check_value(True), "Detected")
        self.assertEqual(normalize_check_value(False), "Not detected")
        self.assertEqual(normalize_check_value(85), "High")
        self.assertEqual(normalize_check_value(50), "Medium")
        self.assertEqual(normalize_check_value(10), "Low")
        self.assertEqual(normalize_check_value(""), "Needs review")

    def test_pdf_report_handles_malformed_confidence(self):
        result = {"risk_score": 42, "confidence": "not-a-number", "threat_analysis": {}}
        pdf = make_pdf_report(result, "Text")
        self.assertTrue(pdf.startswith(b"%PDF"))

    def test_pdf_report_handles_non_finite_confidence(self):
        result = {"risk_score": 42, "confidence": float("nan"), "threat_analysis": {}}
        pdf = make_pdf_report(result, "Text")
        self.assertTrue(pdf.startswith(b"%PDF"))

    def test_pdf_report_generation(self):
        result = {
            "risk_score": 42,
            "confidence": 60,
            "threat_category": "Other",
            "verdict": "Review independently.",
            "summary": "Test report summary.",
            "key_indicators": ["Test indicator"],
            "recommendations": ["Verify the source."],
            "threat_analysis": {},
        }
        pdf = make_pdf_report(result, "Text")
        self.assertTrue(pdf.startswith(b"%PDF"))
        self.assertGreater(len(pdf), 500)

    def test_check_class(self):
        self.assertEqual(check_class("Not detected"), "check-clear")
        self.assertEqual(check_class("Low"), "check-low")
        self.assertEqual(check_class("High risk detected"), "check-detected")
        self.assertEqual(check_class("Needs review"), "check-review")

if __name__ == "__main__":
    unittest.main()
