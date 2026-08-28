import sys
import unittest
from pathlib import Path


FIRMWARE_DIR = Path(__file__).resolve().parents[1] / "firmware"
sys.path.insert(0, str(FIRMWARE_DIR))

import source_characterizer as source


class SourceCharacterizerTests(unittest.TestCase):
    def test_valid_synthetic_source(self):
        points = [
            {"current_a": 0.10, "voltage_v": 4.80},
            {"current_a": 0.20, "voltage_v": 4.60},
            {"current_a": 0.30, "voltage_v": 4.40},
        ]

        result = source.fit_source(points)

        self.assertEqual(result["status"], "completed")
        self.assertAlmostEqual(result["voc_v"], 5.0, places=9)
        self.assertAlmostEqual(result["source_resistance_ohm"], 2.0, places=9)
        self.assertAlmostEqual(result["r_squared"], 1.0, places=9)

    def test_negative_resistance_example_is_invalid(self):
        points = [
            {"current_a": 0.001, "voltage_v": 0.003395},
            {"current_a": 0.002, "voltage_v": 0.009790},
            {"current_a": 0.003, "voltage_v": 0.016185},
        ]

        result = source.fit_source(points)

        self.assertEqual(result["status"], "invalid")
        self.assertAlmostEqual(result["voc_v"], -0.003, places=6)
        self.assertAlmostEqual(result["source_resistance_ohm"], -6.395, places=6)
        self.assertAlmostEqual(result["r_squared"], 1.0, places=9)
        self.assertIn("slope must be negative", result["reason"])

    def test_nearly_identical_current_is_rejected_on_capture(self):
        session = source.GuidedSourceTest()
        self.assertEqual(session.add_point(5.0, 0.1000), (True, "captured"))
        self.assertEqual(
            session.add_point(4.9, 0.1002),
            (False, "current too similar"),
        )

    def test_negative_current_polarity_is_rejected(self):
        session = source.GuidedSourceTest()
        self.assertEqual(
            session.add_point(5.0, -0.010),
            (False, "check current polarity"),
        )

    def test_too_small_current_span_is_invalid(self):
        result = source.fit_source(
            [
                {"current_a": 0.1000, "voltage_v": 4.80},
                {"current_a": 0.1006, "voltage_v": 4.79},
            ]
        )

        self.assertEqual(result["status"], "invalid")
        self.assertIn("current span is too small", result["reason"])


if __name__ == "__main__":
    unittest.main()
