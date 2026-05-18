import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SIM_DIR = ROOT / "pachinko-sim"
sys.path.insert(0, str(SIM_DIR))

from rotation import (  # noqa: E402
    border_case_rates,
    border_delta_text,
    border_ratio_text,
    estimate_from_absolute_spins,
    estimate_from_ball_unit,
    estimate_from_border_margin,
    estimate_from_yen_observation,
    estimate_summary,
    rotation_reality_label,
    spins_from_ball_unit,
    spins_from_border_margin,
    spins_from_yen_observation,
)


class RotationTests(unittest.TestCase):
    def test_rotation_unit_conversions_handle_1yen_and_1111yen(self):
        self.assertAlmostEqual(70.0, spins_from_yen_observation(14, 200))
        self.assertAlmostEqual(70.0, spins_from_ball_unit(17.5, 250, 1.0))
        self.assertAlmostEqual(70.0, spins_from_ball_unit(14, 200, 1.0))
        self.assertAlmostEqual(70.0, spins_from_ball_unit(14, 180, 1.111), delta=0.1)
        self.assertAlmostEqual(63.0, spins_from_ball_unit(17.5, 250, 1.111), delta=0.1)
        self.assertEqual(72.5, spins_from_border_margin(67.5, 5))

    def test_border_case_rates_and_labels_are_border_relative(self):
        cases = border_case_rates(67.5)
        self.assertEqual(
            ["보더-10.0", "보더-5.0", "보더±0", "보더+5.0", "보더+10.0"],
            [row["rotation_label"] for row in cases],
        )
        self.assertEqual([57.5, 62.5, 67.5, 72.5, 77.5], [row["spins_per_1000y"] for row in cases])
        self.assertEqual("+5.0", border_delta_text(72.5, 67.5))
        self.assertEqual("1.07x", border_ratio_text(72.5, 67.5))
        self.assertEqual("좋음", rotation_reality_label(72.5, 67.5))
        self.assertEqual("타협", rotation_reality_label(65, None))

    def test_rotation_estimates_keep_input_basis_and_summary(self):
        cash = estimate_from_yen_observation(14, 200)
        self.assertEqual("cash_observation", cash.input_basis)
        self.assertAlmostEqual(70.0, cash.spins_per_1000y)
        self.assertIn("200엔당 14.0회", cash.source_label)
        self.assertIn("보더비 1.04x", estimate_summary(cash, 67.5))

        balls = estimate_from_ball_unit(17.5, 250, 1.111)
        self.assertEqual("ball_unit", balls.input_basis)
        self.assertAlmostEqual(63.0, balls.spins_per_1000y, delta=0.1)

        margin = estimate_from_border_margin(67.5, 5)
        self.assertEqual("border_margin", margin.input_basis)
        self.assertEqual("보더+5.0", margin.source_label)
        self.assertAlmostEqual(72.5, margin.spins_per_1000y)

        absolute = estimate_from_absolute_spins(70)
        self.assertIn("보더 미확정", estimate_summary(absolute, None))


if __name__ == "__main__":
    unittest.main()
