"""Regression tests for PDF report generation."""
import math
import unittest

from reports import make_pdf_report


class ReportGenerationTests(unittest.TestCase):
    def test_empty_result_still_generates_a_valid_pdf(self):
        data = make_pdf_report({}, "History")
        self.assertTrue(data.startswith(b"%PDF"))
        self.assertGreater(len(data), 500)

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
