import unittest

from firstlight_engine import (
    append_audit,
    apply_simulated_response,
    create_demo_case,
    investigate_case,
    seal_evidence,
    verify_audit_chain,
    verify_evidence,
)


class FirstlightEngineTests(unittest.TestCase):
    def setUp(self):
        self.case = create_demo_case()
        self.evidence = [seal_evidence(event) for event in self.case["events"]]

    def test_evidence_verifies_and_tampering_is_detected(self):
        item = self.evidence[0]
        self.assertTrue(verify_evidence(item)["valid"])
        item["record"]["summary"] += " tampered"
        self.assertFalse(verify_evidence(item)["valid"])

    def test_findings_reference_evidence(self):
        result = investigate_case(self.case, self.evidence)
        self.assertGreaterEqual(len(result["findings"]), 3)
        known = {item["evidence_id"] for item in self.evidence}
        for finding in result["findings"]:
            self.assertTrue(set(finding["evidence_ids"]).issubset(known))
            self.assertIn("explanation", finding)

    def test_audit_chain_detects_modification(self):
        chain = append_audit([], "created", "tester", {"case": "demo"})
        chain = append_audit(chain, "collected", "tester", {"evidence": "EV-001"})
        self.assertTrue(verify_audit_chain(chain))
        chain[0]["payload"]["case"] = "altered"
        self.assertFalse(verify_audit_chain(chain))

    def test_response_is_simulated_and_requires_explicit_approval(self):
        result = investigate_case(self.case, self.evidence)
        proposals, rejected = apply_simulated_response(result["response_proposals"], "ACT-001", False, "reviewer")
        self.assertEqual(rejected["status"], "rejected")
        proposals, approved = apply_simulated_response(proposals, "ACT-002", True, "reviewer")
        self.assertEqual(approved["status"], "simulated_success")
        self.assertTrue(approved["simulated"])
        self.assertIn("No real", approved["message"])

    def test_unknown_action_fails_closed(self):
        with self.assertRaises(ValueError):
            apply_simulated_response([], "ACT-404", True, "reviewer")


if __name__ == "__main__":
    unittest.main()
