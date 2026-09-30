"""Unit tests for SATARK normalization helpers."""
import unittest

from satark_utils import safe_text, clean_json_text, normalize_check_value, check_class

class TextNormalizationTests(unittest.TestCase):
    def test_safe_text(self):
        self.assertEqual(safe_text(None, "fallback"), "fallback")
        self.assertEqual(safe_text("  hello  "), "hello")

    def test_clean_json_text(self):
        self.assertEqual(clean_json_text('```json\n{"ok": true}\n```'), '{"ok": true}')
        self.assertEqual(clean_json_text("no object here"), "no object here")

    def test_normalize_check_value(self):
        self.assertEqual(normalize_check_value(True), "Detected")
        self.assertEqual(normalize_check_value(False), "Not detected")
        self.assertEqual(normalize_check_value(85), "High")
        self.assertEqual(normalize_check_value(50), "Medium")
        self.assertEqual(normalize_check_value(10), "Low")
        self.assertEqual(normalize_check_value(""), "Needs review")

    def test_check_class(self):
        self.assertEqual(check_class("Not detected"), "check-clear")
        self.assertEqual(check_class("Low"), "check-low")
        self.assertEqual(check_class("High risk detected"), "check-detected")
        self.assertEqual(check_class("Needs review"), "check-review")

if __name__ == "__main__":
    unittest.main()
