"""Regression tests for the SATARK Scam Challenge engine."""

import unittest

from scam_challenge import (
    SC_MAX_POINTS,
    sc_build_bank,
    sc_compute_points,
    sc_rank_for_level,
)


class ScamChallengeTests(unittest.TestCase):
    def test_bank_has_100_levels_and_ten_questions_each(self):
        bank = sc_build_bank()
        self.assertEqual(set(bank), set(range(1, 101)))
        self.assertTrue(all(len(questions) == 10 for questions in bank.values()))

    def test_question_bank_is_deterministic(self):
        first = sc_build_bank()
        second = sc_build_bank()
        self.assertEqual(first, second)

    def test_question_ids_are_unique(self):
        bank = sc_build_bank()
        ids = [question["id"] for questions in bank.values() for question in questions]
        self.assertEqual(len(ids), len(set(ids)))

    def test_points_never_exceed_maximum(self):
        self.assertEqual(sc_compute_points(False, 0), 0)
        self.assertEqual(sc_compute_points(True, 0), SC_MAX_POINTS)
        self.assertGreater(sc_compute_points(True, 10_000), 0)
        self.assertLessEqual(sc_compute_points(True, 10_000), SC_MAX_POINTS)

    def test_rank_boundaries_are_stable(self):
        self.assertEqual(sc_rank_for_level(1)["roman"], "I")
        self.assertEqual(sc_rank_for_level(10)["roman"], "I")
        self.assertEqual(sc_rank_for_level(11)["roman"], "II")
        self.assertEqual(sc_rank_for_level(100)["roman"], "X")


if __name__ == "__main__":
    unittest.main()
