"""Regression tests for defensive learning/history helpers."""
import unittest

from ui.history import _safe_entry, _safe_score
from ui.learning import _safe_score as classroom_score


class UISafetyTests(unittest.TestCase):
    def test_history_score_is_bounded_and_tolerant(self):
        self.assertEqual(_safe_score("88.9"), 88)
        self.assertEqual(_safe_score("bad"), 0)
        self.assertEqual(_safe_score(999), 100)
        self.assertEqual(_safe_score(-5), 0)

    def test_history_entry_normalizes_malformed_values(self):
        entry = _safe_entry({"score": "not-a-number", "result": "broken"})
        self.assertEqual(entry["score"], 0)
        self.assertEqual(entry["result"], {})

    def test_classroom_score_is_bounded_and_tolerant(self):
        self.assertEqual(classroom_score("72"), 72)
        self.assertEqual(classroom_score("oops"), 0)
        self.assertEqual(classroom_score(150), 100)


if __name__ == "__main__":
    unittest.main()
