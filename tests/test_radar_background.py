"""Contract tests for the SATARK OGL radar background integration."""
import unittest

from radar_background import _RADAR_HTML, render_radar_background


class RadarBackgroundTests(unittest.TestCase):
    def test_uses_ogl_runtime(self):
        self.assertIn("esm.sh/ogl@1.0.11", _RADAR_HTML)
        self.assertIn("Renderer", _RADAR_HTML)
        self.assertIn("Program", _RADAR_HTML)
        self.assertIn("Triangle", _RADAR_HTML)

    def test_is_full_screen_and_non_interactive(self):
        self.assertIn('frame.style.position="fixed"', _RADAR_HTML)
        self.assertIn('frame.style.width="100vw"', _RADAR_HTML)
        self.assertIn('frame.style.height="100vh"', _RADAR_HTML)
        self.assertIn('frame.style.pointerEvents="none"', _RADAR_HTML)

    def test_radar_shader_contract(self):
        for uniform in (
            "uTime", "uResolution", "uRingCount", "uSpokeCount",
            "uRingThickness", "uSpokeThickness", "uSweepSpeed",
            "uSweepWidth", "uSweepLobes", "uFalloff", "uBrightness",
        ):
            self.assertIn(uniform, _RADAR_HTML)

    def test_public_mount_is_callable(self):
        self.assertTrue(callable(render_radar_background))


if __name__ == "__main__":
    unittest.main()
