"""Regression tests for the dependency-free SATARK onboarding stepper."""
import unittest

from stepper_component import _STEPS, render_stepper


class StepperComponentTests(unittest.TestCase):
    def test_workflow_has_four_clear_steps(self):
        self.assertEqual(len(_STEPS), 4)
        self.assertEqual([step[0] for step in _STEPS], ["01", "02", "03", "04"])
        for _, title, copy in _STEPS:
            self.assertTrue(title)
            self.assertTrue(copy)

    def test_public_mount_is_callable(self):
        self.assertTrue(callable(render_stepper))


if __name__ == "__main__":
    unittest.main()
