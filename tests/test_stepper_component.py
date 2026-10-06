"""Contract tests for the React Bits Stepper integration."""
import unittest

from stepper_component import _STEPPER_HTML, render_stepper


class StepperComponentTests(unittest.TestCase):
    def test_loads_react_and_motion(self):
        self.assertIn("react@18.3.1", _STEPPER_HTML)
        self.assertIn("react-dom@18.3.1/client", _STEPPER_HTML)
        self.assertIn("motion@13.4.6/react", _STEPPER_HTML)

    def test_contains_stepper_interactions(self):
        for token in ("setCurrent", "AnimatePresence", "Previous", "Next", "Complete"):
            self.assertIn(token, _STEPPER_HTML)

    def test_has_accessible_step_controls(self):
        self.assertIn('aria-label', _STEPPER_HTML)
        self.assertIn('type:"button"', _STEPPER_HTML)

    def test_public_mount_is_callable(self):
        self.assertTrue(callable(render_stepper))


if __name__ == "__main__":
    unittest.main()
