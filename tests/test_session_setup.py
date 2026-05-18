import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SIM_DIR = ROOT / "pachinko-sim"
sys.path.insert(0, str(SIM_DIR))

from session_setup import build_session_start  # noqa: E402
from time_model import DEFAULT_TIME_ASSUMPTIONS  # noqa: E402


class SessionSetupTests(unittest.TestCase):
    def test_fixed_spin_cap_setup_without_start_variance_is_deterministic(self):
        setup = build_session_start(
            budget=5000,
            lend_rate=1.0,
            spins_per_1000y=80,
            strategy="no_rule",
            session_policy="fixed_spin_cap",
            max_normal_spins=None,
            start_variance=False,
            border_spins_per_1000y=70,
            spin_rate_quality_stddev=3.0,
            spin_rate_min=None,
            spin_rate_max=None,
            stop_loss_probe_yen=1000,
            stop_loss_spin_threshold=70,
            time_assumptions=DEFAULT_TIME_ASSUMPTIONS,
        )

        self.assertEqual(80.0, setup.true_spins_per_1000y)
        self.assertEqual(0.0, setup.effective_quality_stddev)
        self.assertEqual(400, setup.expected_total_spins_possible)
        self.assertEqual(400, setup.total_spins_possible)
        self.assertEqual(400, setup.normal_spin_cap)
        self.assertEqual(1000, setup.stop_loss_probe_budget)
        self.assertEqual(80, setup.stop_loss_probe_spins)
        self.assertEqual(80.0, setup.stop_loss_probe_rate)
        self.assertIsNone(setup.stop_loss_normal_spin_cap)

    def test_basic_stop_setup_caps_normal_spins_after_slow_probe(self):
        setup = build_session_start(
            budget=5000,
            lend_rate=1.0,
            spins_per_1000y=60,
            strategy="basic_stop",
            session_policy="fixed_spin_cap",
            max_normal_spins=None,
            start_variance=False,
            border_spins_per_1000y=None,
            spin_rate_quality_stddev=3.0,
            spin_rate_min=None,
            spin_rate_max=None,
            stop_loss_probe_yen=1000,
            stop_loss_spin_threshold=70,
            time_assumptions=DEFAULT_TIME_ASSUMPTIONS,
        )

        self.assertEqual(300, setup.total_spins_possible)
        self.assertEqual(60, setup.stop_loss_probe_spins)
        self.assertEqual(60.0, setup.stop_loss_probe_rate)
        self.assertEqual(60, setup.stop_loss_normal_spin_cap)


if __name__ == "__main__":
    unittest.main()
