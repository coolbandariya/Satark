"""Static contracts for SATARK's public UI copy, modularity and accessibility."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "satark.py").read_text(encoding="utf-8")
HOME = (ROOT / "ui" / "home.py").read_text(encoding="utf-8")
NAV = (ROOT / "ui" / "navigation.py").read_text(encoding="utf-8")
RESULTS = (ROOT / "ui" / "results.py").read_text(encoding="utf-8")
LEARNING = (ROOT / "ui" / "learning.py").read_text(encoding="utf-8")
HISTORY = (ROOT / "ui" / "history.py").read_text(encoding="utf-8")
DEMO = (ROOT / "ui" / "demo.py").read_text(encoding="utf-8")
CSS = (ROOT / "styles.css").read_text(encoding="utf-8")


class UIContractTests(unittest.TestCase):
    def test_entry_point_is_modular(self):
        self.assertIn("from ui.home import render_home", APP)
        self.assertIn("from ui.navigation import render_sidebar", APP)
        self.assertIn("from ui.results import render_threat_analysis", APP)
        self.assertIn("from ui.learning import render_academy, render_classroom", APP)
        self.assertIn("from ui.history import render_history", APP)
        self.assertLess(len(APP), 65000)

    def test_home_copy_has_clear_user_facing_value_proposition(self):
        self.assertIn("Pause. Investigate. Then act.", HOME)
        self.assertIn("Start an investigation", HOME)
        self.assertIn("Explore a sample result", HOME)

    def test_navigation_uses_plain_language_and_privacy_boundary(self):
        self.assertIn('"Analyze","🔎 Analyze"', NAV)
        self.assertIn('"Academy","🎓 Academy"', NAV)
        self.assertIn('"Classroom","👨‍🏫 Classroom"', NAV)
        self.assertIn("Privacy boundary", NAV)
        self.assertIn("Never submit passwords, OTPs, private keys", NAV)
        self.assertNotIn("Who are you?", NAV)

    def test_result_hierarchy_prioritizes_action_and_uncertainty(self):
        self.assertIn("Current assessment", APP)
        self.assertIn("Recommended next steps", APP)
        self.assertIn("Moderate confidence", APP)
        self.assertIn("Verify through an independent official channel", APP)

    def test_scanner_copy_matches_current_modes(self):
        self.assertIn("Seven scanners cover text, links, images, documents, QR codes and video.", APP)
        self.assertNotIn("original six SATARK modes", APP)
        self.assertIn('f"Select {name}"', APP)
        for label in ("Text", "URL", "Image", "PDF", "QR", "Video"):
            self.assertIn(f'("{label}"', APP)

    def test_offline_demo_exists(self):
        self.assertIn("DEMO_RESULT", DEMO)
        self.assertIn("get_demo_result", DEMO)
        self.assertIn("offline example", APP)

    def test_accessibility_and_responsive_contracts_exist(self):
        self.assertIn('scope="col"', RESULTS)
        self.assertIn('rel="noopener noreferrer"', RESULTS)
        self.assertIn(".hero-note", CSS)
        self.assertIn(".home-actions", CSS)
        self.assertIn("prefers-reduced-motion:reduce", CSS)
        self.assertIn("--accent:#ff6a00", CSS)
        self.assertNotIn("--violet", CSS)
        self.assertNotIn("#a99cff", CSS)

    def test_learning_and_history_are_modular(self):
        self.assertIn("render_academy", LEARNING)
        self.assertIn("render_classroom", LEARNING)
        self.assertIn("render_history", HISTORY)


if __name__ == "__main__":
    unittest.main()
