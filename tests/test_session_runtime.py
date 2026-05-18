import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SIM_DIR = ROOT / "pachinko-sim"
sys.path.insert(0, str(SIM_DIR))

from session_runtime import (  # noqa: E402
    cap_spins_before_cash_cutoff,
    cap_spins_by_seconds,
    limit_minutes_to_seconds,
    limit_reached,
    normal_seconds_per_spin,
    remaining_seconds,
)
from time_model import TimeAssumptions  # noqa: E402


class SessionRuntimeTests(unittest.TestCase):
    def test_limit_minutes_to_seconds_preserves_zero_only_when_allowed(self):
        self.assertEqual(90.0, limit_minutes_to_seconds(1.5))
        self.assertIsNone(limit_minutes_to_seconds(0))
        self.assertEqual(0.0, limit_minutes_to_seconds(0, allow_zero=True))
        self.assertIsNone(limit_minutes_to_seconds(None))
        self.assertIsNone(limit_minutes_to_seconds(-1, allow_zero=True))

    def test_remaining_seconds_and_limit_reached_handle_disabled_limits(self):
        self.assertIsNone(remaining_seconds(None, 120.0))
        self.assertEqual(30.0, remaining_seconds(90.0, 60.0))
        self.assertFalse(limit_reached(None, 999.0))
        self.assertFalse(limit_reached(90.0, 89.9))
        self.assertTrue(limit_reached(90.0, 90.0))

    def test_normal_seconds_per_spin_uses_slower_of_launch_and_display_time(self):
        assumptions = TimeAssumptions(
            launch_balls_per_minute=100.0,
            normal_base_return_rate=0.0,
            normal_seconds_per_start=6.0,
        )

        self.assertEqual(6.0, normal_seconds_per_spin(5.0, assumptions))
        self.assertEqual(12.0, normal_seconds_per_spin(20.0, assumptions))

    def test_cap_spins_by_seconds_caps_only_when_limit_applies(self):
        self.assertEqual((10, False), cap_spins_by_seconds(10, None, 6.0))
        self.assertEqual((0, True), cap_spins_by_seconds(10, 0.0, 6.0))
        self.assertEqual((10, False), cap_spins_by_seconds(10, 60.0, 0.0))
        self.assertEqual((4, True), cap_spins_by_seconds(10, 25.0, 6.0))
        self.assertEqual((10, False), cap_spins_by_seconds(10, 60.0, 6.0))

    def test_cash_cutoff_cap_preserves_existing_less_than_one_spin_behavior(self):
        self.assertEqual((10, False), cap_spins_before_cash_cutoff(10, None, 10.0, 6.0))
        self.assertEqual((10, False), cap_spins_before_cash_cutoff(10, 60.0, 60.0, 6.0))
        self.assertEqual((4, True), cap_spins_before_cash_cutoff(10, 60.0, 35.0, 6.0))
        self.assertEqual((10, False), cap_spins_before_cash_cutoff(10, 60.0, 55.0, 6.0))


if __name__ == "__main__":
    unittest.main()
