"""Static contracts for SATARK's modular UI and layout safeguards."""

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "satark.py").read_text(encoding="utf-8")
CSS = (ROOT / "styles.css").read_text(encoding="utf-8")
RADAR = (ROOT / "radar_background.py").read_text(encoding="utf-8")
STEPPER = (ROOT / "stepper_component.py").read_text(encoding="utf-8")


class UIContractTests(unittest.TestCase):
    def test_entry_point_uses_modular_surfaces(self):
        for expected in (
            "from ui.home import render_home",
            "from ui.navigation import render_sidebar",
            "from ui.results import render_threat_analysis, render_verification_sources",
            "from ui.history import render_history",
            "from ui.learning import render_academy, render_classroom",
        ):
            self.assertIn(expected, APP)
        self.assertLess(len(APP), 50000)

    def test_result_renderers_receive_required_contract_arguments(self):
        self.assertIn("render_threat_analysis(result, THREAT_CHECKS)", APP)
        self.assertIn(
            "render_verification_sources(result, OFFICIAL_VERIFICATION_SOURCES)",
            APP,
        )

    def test_layout_guardrails_exist(self):
        for expected in (
            ".home-actions,",
            ".sr-only{",
            ".report-section{",
            ".workflow-grid{",
            "overflow-wrap:anywhere",
            "prefers-reduced-motion:reduce",
            "overflow-x:hidden",
        ):
            self.assertIn(expected, CSS)

    def test_home_is_not_dependent_on_external_browser_runtimes(self):
        self.assertNotIn("esm.sh", RADAR)
        self.assertNotIn("esm.sh", STEPPER)

    def test_app_does_not_reference_missing_analysis_constants(self):
        self.assertIn("THREAT_CHECKS, OFFICIAL_VERIFICATION_SOURCES", APP)


if __name__ == "__main__":
    unittest.main()
