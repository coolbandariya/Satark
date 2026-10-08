"""Static contracts for SATARK's modular UI and layout safeguards."""
from pathlib import Path
import inspect
import unittest

from ui.results import render_threat_analysis, render_verification_sources
ROOT=Path(__file__).resolve().parents[1]
APP=(ROOT/"satark.py").read_text(encoding="utf-8")
CSS=(ROOT/"styles.css").read_text(encoding="utf-8")

class UIContractTests(unittest.TestCase):
    def test_entry_point_uses_modular_surfaces(self):
        for expected in ("from ui.home import render_home","from ui.navigation import render_sidebar","from ui.results import render_threat_analysis, render_verification_sources","from ui.history import render_history","from ui.learning import render_academy, render_classroom"):
            self.assertIn(expected,APP)
        self.assertLess(len(APP),50000)

    def test_layout_guardrails_exist(self):
        for expected in (".st-key-home-actions{",".sr-only{",".report-section{","overflow-wrap:anywhere","prefers-reduced-motion:reduce","overflow-x:hidden"):
            self.assertIn(expected,CSS)

    def test_app_does_not_reference_missing_analysis_constants(self):
        self.assertIn("THREAT_CHECKS, OFFICIAL_VERIFICATION_SOURCES",APP)

    def test_result_renderers_have_safe_defaults(self):
        threat_default = inspect.signature(render_threat_analysis).parameters["threat_checks"].default
        sources_default = inspect.signature(render_verification_sources).parameters["default_sources"].default
        self.assertIsNone(threat_default)
        self.assertIsNone(sources_default)

if __name__=="__main__":
    unittest.main()
