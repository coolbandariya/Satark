"""Regression tests for explainable, offline evidence extraction."""

import unittest

from evidence_engine import extract_deterministic_evidence


class DeterministicEvidenceTests(unittest.TestCase):
    def test_empty_input_returns_no_findings(self):
        self.assertEqual(extract_deterministic_evidence("   "), [])

    def test_extracts_url_and_known_shortener_without_network(self):
        findings = extract_deterministic_evidence(
            "Please check https://bit.ly/abc123 before continuing."
        )
        ids = [item["id"] for item in findings]
        self.assertIn("url-present", ids)
        self.assertIn("url-shortener", ids)
        self.assertTrue(all(item["method"] == "Deterministic pattern" for item in findings))

    def test_detects_literal_ip_host(self):
        findings = extract_deterministic_evidence("Visit http://192.0.2.10/login")
        self.assertIn("url-ip-host", [item["id"] for item in findings])

    def test_detects_upi_style_identifier(self):
        findings = extract_deterministic_evidence("Pay to demo.user@okaxis")
        self.assertIn("upi-present", [item["id"] for item in findings])

    def test_detects_indian_phone_like_number_without_claiming_fraud(self):
        findings = extract_deterministic_evidence("Call 9876543210 for more information")
        item = next(item for item in findings if item["id"] == "phone-present")
        self.assertIn("does not indicate fraud", item["observation"])

    def test_detects_urgency_and_credential_request(self):
        findings = extract_deterministic_evidence(
            "Urgent! Send your OTP immediately or your account will be blocked."
        )
        ids = [item["id"] for item in findings]
        self.assertIn("urgency-language", ids)
        self.assertIn("credential-request", ids)

    def test_detects_payment_language_as_review_signal(self):
        findings = extract_deterministic_evidence(
            "Please pay ₹500 registration fee to complete the application."
        )
        self.assertIn("payment-request", [item["id"] for item in findings])

    def test_finding_count_is_bounded_and_no_position_leaks(self):
        findings = extract_deterministic_evidence(
            ("urgent send your OTP https://bit.ly/demo " * 20),
            max_findings=4,
        )
        self.assertLessEqual(len(findings), 4)
        self.assertTrue(all("position" not in item for item in findings))

    def test_no_network_or_verdict_claim(self):
        findings = extract_deterministic_evidence(
            "Your account will be blocked. Visit https://example.com"
        )
        self.assertTrue(all(item["interpretation"] == "Review signal — not a verdict" for item in findings))


if __name__ == "__main__":
    unittest.main()
