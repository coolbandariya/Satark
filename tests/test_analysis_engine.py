"""Contract tests for SATARK's pure analysis layer."""
import unittest
from analysis_engine import normalize_result, calibrate_confidence, risk_label

class AnalysisEngineTests(unittest.TestCase):
    def test_normalize_result_has_stable_findings(self):
        result=normalize_result({
            "risk_score":82,
            "confidence":62,
            "threat_category":"Phishing",
            "verdict":"Do not trust this message.",
            "summary":"Credential pressure is present.",
            "key_indicators":["Urgency","Credential request"],
            "threat_analysis":{"Phishing Signs":"Detected","Malware Indicators":"Not detected"},
        })
        self.assertEqual(result["risk_band"],"CRITICAL THREAT")
        self.assertEqual(result["findings"][0]["severity"],"high")
        self.assertEqual(result["findings"][0]["title"],"Phishing Signs")
        clear=[item for item in result["findings"] if item["title"]=="Malware Indicators"][0]
        self.assertEqual(clear["severity"],"clear")

    def test_ambiguous_evidence_reduces_confidence(self):
        result=calibrate_confidence(
            {"confidence":80},
            {"confidence":80,"key_indicators":[],"threat_analysis":{"a":"Needs review","b":"Needs review"}},
        )
        self.assertLess(result["confidence"],80)

    def test_risk_label_boundaries_are_stable(self):
        self.assertEqual(risk_label(0)[0],"SAFE")
        self.assertEqual(risk_label(34)[0],"SAFE")
        self.assertEqual(risk_label(35)[0],"CAUTION")
        self.assertEqual(risk_label(69)[0],"CAUTION")
        self.assertEqual(risk_label(70)[0],"CRITICAL THREAT")

if __name__=="__main__":
    unittest.main()
