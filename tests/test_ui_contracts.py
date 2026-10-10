"""Static contracts for SATARK's modular UI and layout safeguards."""

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "satark.py").read_text(encoding="utf-8")
CSS = (ROOT / "styles.css").read_text(encoding="utf-8")
RADAR = (ROOT / "radar_background.py").read_text(encoding="utf-8")
STEPPER = (ROOT / "stepper_component.py").read_text(encoding="utf-8")
HISTORY = (ROOT / "ui/history.py").read_text(encoding="utf-8")
LEARNING = (ROOT / "ui/learning.py").read_text(encoding="utf-8")
HOME = (ROOT / "ui/home.py").read_text(encoding="utf-8")
NAV = (ROOT / "ui/navigation.py").read_text(encoding="utf-8")


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
        self.assertLess(len(APP), 55000)

    def test_result_renderers_receive_required_contract_arguments(self):
        self.assertIn("render_threat_analysis(result, THREAT_CHECKS)", APP)
        self.assertIn(
            "render_verification_sources(result, OFFICIAL_VERIFICATION_SOURCES)",
            APP,
        )

    def test_layout_guardrails_exist(self):
        for expected in (
            ".home-actions{",
            ".sr-only{",
            ".report-section{",
            ".workflow-grid{",
            "overflow-wrap:anywhere",
            "prefers-reduced-motion:reduce",
            "overflow-x:hidden",
        ):
            self.assertIn(expected, CSS)

    def test_learning_and_history_are_actionable(self):
        for expected in ("history_query", "history_mode_filter", "classroom_export", "academy_to_challenge"):
            self.assertIn(expected, HISTORY + LEARNING)

    def test_home_is_not_dependent_on_external_browser_runtimes(self):
        self.assertNotIn("esm.sh", RADAR)
        self.assertNotIn("esm.sh", STEPPER)

    def test_evidence_coverage_review_is_integrated(self):
        self.assertIn("render_evidence_review(result)", APP)
        self.assertIn("build_evidence_review", (ROOT / "ui/results.py").read_text(encoding="utf-8"))
        self.assertIn("evidence-review", CSS)

    def test_home_prioritizes_the_core_product_without_vanity_metrics(self):
        self.assertIn("Know what you", HOME)
        self.assertIn("guided sample report", HOME)
        self.assertIn("observable signals", HOME)
        self.assertNotIn("home-stats", HOME)

    def test_native_streamlit_theme_matches_custom_design_system(self):
        config = (ROOT / ".streamlit/config.toml").read_text(encoding="utf-8")
        self.assertIn('primaryColor = "#7dd3fc"', config)
        self.assertIn('backgroundColor = "#080d17"', config)
        self.assertIn('secondaryBackgroundColor = "#0d1523"', config)
        self.assertIn('textColor = "#edf4ff"', config)

    def test_investigation_screen_has_contextual_workflow_guidance(self):
        self.assertIn("mode_details = {", APP)
        self.assertIn("selected-workflow", APP)
        self.assertIn("Video & clips", APP)
        self.assertIn(".selected-workflow{", CSS)
        self.assertIn("@media(max-width:680px)", CSS)

    def test_provider_check_does_not_claim_success_when_discovery_fails(self):
        self.assertIn("if not available:", NAV)
        self.assertIn("Could not verify provider access", NAV)
        self.assertIn("st.session_state.text_model = None", NAV)

    def test_primary_navigation_stays_focused(self):
        self.assertIn('("Home", "Overview")', NAV)
        self.assertIn('("Analyze", "Investigate")', NAV)
        self.assertIn('("History", "Session history")', NAV)
        self.assertNotIn('("Challenge",', NAV)
        self.assertNotIn('("Classroom",', NAV)

    def test_app_does_not_reference_missing_analysis_constants(self):
        self.assertIn("THREAT_CHECKS, OFFICIAL_VERIFICATION_SOURCES", APP)


if __name__ == "__main__":
    unittest.main()
