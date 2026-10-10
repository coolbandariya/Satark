import unittest

from findings import build_findings, finding_severity


class FindingSeverityTests(unittest.TestCase):
    def test_empty_and_unrecognized_values_remain_unknown(self):
        self.assertEqual(finding_severity(""), "unknown")
        self.assertEqual(finding_severity(None), "unknown")
        self.assertEqual(finding_severity("Needs review"), "unknown")

    def test_explicit_negative_states_take_precedence(self):
        for value in ("Not detected", "No sign found", "Clear", "False", "Absent"):
            with self.subTest(value=value):
                self.assertEqual(finding_severity(value), "clear")

    def test_explicit_severity_is_preserved(self):
        cases = {
            "Critical risk": "critical",
            "High risk": "high",
            "Medium": "medium",
            "Moderate concern": "medium",
            "Low risk": "low",
        }
        for value, expected in cases.items():
            with self.subTest(value=value):
                self.assertEqual(finding_severity(value), expected)

    def test_generic_detection_is_high_only_without_explicit_severity(self):
        self.assertEqual(finding_severity("Detected"), "high")
        self.assertEqual(finding_severity("Low risk — detected"), "low")
        self.assertEqual(finding_severity("Medium concern, indicator present"), "medium")
        self.assertEqual(finding_severity("Not detected"), "clear")

    def test_build_findings_handles_malformed_payload_and_orders_severity(self):
        self.assertEqual(build_findings(None), [])
        self.assertEqual(build_findings({"threat_analysis": []}), [])
        findings = build_findings({
            "threat_analysis": {
                "low check": "Low risk — detected",
                "high check": "High risk",
                "unknown check": "Needs review",
                "clear check": "Not detected",
            }
        })
        self.assertEqual(
            [item["severity"] for item in findings],
            ["high", "low", "unknown", "clear"],
        )
        self.assertTrue(all("action" in item and "id" in item for item in findings))


if __name__ == "__main__":
    unittest.main()
