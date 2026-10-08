"""Unit tests for SATARK normalization helpers."""
import unittest
from io import BytesIO

from satark_utils import safe_text, clean_json_text, normalize_check_value, check_class
from input_processing import MAX_IMAGE_PIXELS, image_to_data_url
from reports import make_pdf_report
from unittest.mock import patch, Mock
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

    def test_image_pixel_limit_is_enforced(self):
        upload = BytesIO(b"image")
        upload.name = "large.png"
        fake_image = Mock()
        fake_image.size = (MAX_IMAGE_PIXELS + 1, 1)
        with patch("input_processing.Image.open", return_value=fake_image):
            with self.assertRaises(ValueError):
                image_to_data_url(upload)

    def test_pdf_report_handles_malformed_confidence(self):
        result = {"risk_score": 42, "confidence": "not-a-number", "threat_analysis": {}}
        pdf = make_pdf_report(result, "Text")
        self.assertTrue(pdf.startswith(b"%PDF"))

    def test_pdf_report_handles_non_finite_confidence(self):
        result = {"risk_score": 42, "confidence": float("nan"), "threat_analysis": {}}
        pdf = make_pdf_report(result, "Text")
        self.assertTrue(pdf.startswith(b"%PDF"))


    def test_pdf_report_handles_malformed_nested_data(self):
        result = {
            "risk_score": 42,
            "confidence": 60,
            "key_indicators": "single indicator",
            "recommendations": 17,
            "threat_analysis": ["not", "a", "mapping"],
            "verification_sources": [None, "bad source", {"source": "Example", "purpose": "Verify", "website": "javascript:alert(1)"}],
        }
        pdf = make_pdf_report(result, "Text")
        self.assertTrue(pdf.startswith(b"%PDF"))

    def test_pdf_report_handles_invalid_top_level_payload(self):
        pdf = make_pdf_report(["not", "a", "mapping"], "Text")
        self.assertTrue(pdf.startswith(b"%PDF"))
        self.assertGreater(len(pdf), 500)

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


class VisibleTextParserEdgeCaseTests(unittest.TestCase):
    def test_nested_markup_inside_script_remains_hidden(self):
        parser = VisibleTextParser()
        parser.feed("<script>secret <span>still secret</span></script><p>Visible</p>")
        self.assertEqual(parser.text(), "Visible")

    def test_unclosed_script_fails_closed_for_following_text(self):
        parser = VisibleTextParser()
        parser.feed("<p>Visible</p><script>secret<p>hidden</p>")
        self.assertEqual(parser.text(), "Visible")

    def test_invalid_port_is_rejected(self):
        self.assertFalse(is_public_url("https://example.com:99999"))
        self.assertFalse(is_public_url("https://example.com:not-a-port"))
