"""Tests for evidence coverage review states."""
import unittest

from review_engine import build_evidence_review


class EvidenceReviewTests(unittest.TestCase):
    def test_high_risk_without_rule_evidence_needs_corroboration(self):
        review = build_evidence_review({
            "analysis_mode": "Text",
            "risk_score": 91,
            "threat_category": "Phishing",
            "key_indicators": ["Urgency"],
            "deterministic_evidence": [],
        })
        self.assertEqual(review["level"], "review")
        self.assertEqual(review["evidence_count"], 0)
        self.assertIn("uncorroborated", review["message"])

    def test_evidence_present_is_not_described_as_proof(self):
        review = build_evidence_review({
            "analysis_mode": "Text",
            "risk_score": 80,
            "threat_category": "Scam",
            "key_indicators": ["Urgency"],
            "deterministic_evidence": [{"title": "Urgency"}],
        })
        self.assertEqual(review["level"], "supported")
        self.assertIn("not proof of fraud", review["message"])

    def test_empty_evidence_objects_do_not_count_as_corroboration(self):
        review = build_evidence_review({
            "analysis_mode": "Text",
            "risk_score": 88,
            "threat_category": "Phishing",
            "deterministic_evidence": [{}],
        })
        self.assertEqual(review["evidence_count"], 0)
        self.assertEqual(review["level"], "review")
        self.assertIn("uncorroborated", review["message"])

    def test_visual_modes_do_not_claim_text_rules_failed(self):
        review = build_evidence_review({
            "analysis_mode": "Image",
            "risk_score": 75,
            "key_indicators": ["Logo mismatch"],
        })
        self.assertEqual(review["level"], "info")
        self.assertIn("visual findings", review["message"])

    def test_video_without_text_signals_is_marked_multimodal_not_uncorroborated(self):
        review = build_evidence_review({
            "analysis_mode": "Video",
            "risk_score": 86,
            "threat_category": "Scam",
            "key_indicators": ["Urgent payment request"],
        })
        self.assertEqual(review["level"], "info")
        self.assertEqual(review["status"], "Multimodal workflow")
        self.assertIn("Sampled video frames", review["message"])

    def test_video_transcript_signals_can_be_reported_as_independent_evidence(self):
        review = build_evidence_review({
            "analysis_mode": "Video",
            "risk_score": 86,
            "threat_category": "Scam",
            "deterministic_evidence": [{"title": "Urgency", "observation": "Pressure to act"}],
        })
        self.assertEqual(review["level"], "supported")
        self.assertEqual(review["evidence_count"], 1)

    def test_empty_or_malformed_result_is_safe(self):
        review = build_evidence_review(None)
        self.assertEqual(review["level"], "review")
        self.assertEqual(review["evidence_count"], 0)

    def test_no_signals_is_not_a_safety_clearance(self):
        review = build_evidence_review({
            "analysis_mode": "Text",
            "risk_score": 10,
            "threat_category": "Needs review",
        })
        self.assertIn("not a safety clearance", review["message"])


if __name__ == "__main__":
    unittest.main()
