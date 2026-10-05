"""Static contracts for SATARK's public UI copy and navigation."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "satark.py").read_text(encoding="utf-8")
CSS = (ROOT / "styles.css").read_text(encoding="utf-8")


class UIContractTests(unittest.TestCase):
    def test_home_copy_has_clear_user_facing_value_proposition(self):
        self.assertIn("Not sure if it’s safe?", APP)
        self.assertIn("SATARK</span> investigate.", APP)
        self.assertIn("highlights evidence, explains uncertainty", APP)

    def test_navigation_uses_plain_language(self):
        self.assertIn('"Analyze","🔎 Analyze"', APP)
        self.assertIn('"Academy","🎓 Academy"', APP)
        self.assertIn('"Classroom","👨‍🏫 Classroom"', APP)
        self.assertNotIn("Who are you?", APP)

    def test_scanner_copy_matches_current_seven_modes(self):
        self.assertIn("Seven scanners cover text, links, images, documents, QR codes and video.", APP)
        self.assertNotIn("original six SATARK modes", APP)
        self.assertIn('f"Select {name}"', APP)
        for label in ("Text", "URL", "Image", "PDF", "QR", "Video"):
            self.assertIn(f'("{label}"', APP)

    def test_privacy_boundary_is_explicit(self):
        self.assertIn("Privacy boundary", APP)
        self.assertIn("Never submit passwords, OTPs, private keys", APP)

    def test_editorial_responsive_contracts_exist(self):
        self.assertIn(".hero-note", CSS)
        self.assertIn(".home-grid{", CSS)
        self.assertIn("grid-template-columns:1fr;", CSS)
        self.assertIn("justify-content:flex-start", CSS)


if __name__ == "__main__":
    unittest.main()
