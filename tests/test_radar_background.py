"""Regression tests for the CSS-only SATARK background hook."""
import unittest

from radar_background import render_radar_background


class RadarBackgroundTests(unittest.TestCase):
    def test_public_mount_is_callable(self):
        self.assertTrue(callable(render_radar_background))

    def test_background_hook_is_dependency_free(self):
        self.assertIsNone(render_radar_background())


if __name__ == "__main__":
    unittest.main()
