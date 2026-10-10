"""Regression tests for PDF report generation."""
import math
import unittest
from io import BytesIO

from pypdf import PdfReader

from reports import make_pdf_report, risk_label


class ReportGenerationTests(unittest.TestCase):
    def test_empty_result_still_generates_a_valid_pdf(self):
        data = make_pdf_report({}, "History")
        self.assertTrue(data.startswith(b"%PDF"))
        self.assertGreater(len(data), 500)
        self.assertTrue(PdfReader(BytesIO(data)).pages)

    def test_pdf_includes_rule_based_evidence_ledger(self):
        data = make_pdf_report(
            {
                "risk_score": 62,
                "confidence": 54,
                "threat_category": "Needs review",
                "deterministic_evidence": [
                    {
                        "title": "Urgency language",
                        "observation": "Pressure to act quickly can reduce careful verification.",
                        "evidence": "account will be blocked today",
                    }
                ],
            },
            "Text",
        )
        self.assertTrue(data.startswith(b"%PDF"))
        self.assertGreater(len(data), 500)
        extracted = "\n".join(page.extract_text() or "" for page in PdfReader(BytesIO(data)).pages)
        self.assertIn("Urgency language", extracted)
        self.assertIn("account will be blocked today", extracted)
        self.assertIn("Rule-Based Evidence Ledger", extracted)
        self.assertIn("Evidence Coverage Review", extracted)
        self.assertIn("Investigation Workflow", extracted)
        self.assertIn("Local evidence rules", extracted)
        self.assertIn("Independent text signals found", extracted)


    def test_pdf_omits_empty_malformed_evidence_rows(self):
        data = make_pdf_report(
            {
                "risk_score": 86,
                "threat_category": "Phishing",
                "deterministic_evidence": [{}, {"title": "", "observation": "", "evidence": ""}],
            },
            "Text",
        )
        extracted = "\\n".join(page.extract_text() or "" for page in PdfReader(BytesIO(data)).pages)
        self.assertIn("Evidence Coverage Review", extracted)
        self.assertIn("uncorroborated", extracted.lower())
        self.assertNotIn("Observed text:", extracted)

    def test_low_score_is_not_exported_as_a_safety_guarantee(self):
        label, _ = risk_label(10, "Needs review")
        self.assertEqual(label, "LOWER SIGNAL")
        self.assertNotEqual(label, "SAFE")

    def test_malformed_numeric_fields_are_safe(self):
        data = make_pdf_report(
            {
                "risk_score": "not-a-number",
                "confidence": math.nan,
                "threat_category": "Scam",
                "verdict": None,
                "summary": None,
                "key_indicators": "unexpected scalar",
                "recommendations": None,
                "threat_analysis": "unexpected scalar",
            },
            "Text",
        )
        self.assertTrue(data.startswith(b"%PDF"))


if __name__ == "__main__":
    unittest.main()
