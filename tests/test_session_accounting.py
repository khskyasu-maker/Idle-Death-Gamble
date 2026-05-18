import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SIM_DIR = ROOT / "pachinko-sim"
sys.path.insert(0, str(SIM_DIR))

import simulator  # noqa: E402
from session_accounting import (  # noqa: E402
    SESSION_POLICIES,
    STRATEGIES,
    apply_strategy_rules,
    current_profit_balls,
    normalize_session_policy,
    normalize_strategy,
)


class SessionAccountingTests(unittest.TestCase):
    def test_normalizers_fallback_to_default_runtime_modes(self):
        self.assertEqual("profit_lock", normalize_strategy("profit_lock"))
        self.assertEqual("no_rule", normalize_strategy("missing"))
        self.assertEqual(
            "play_until_budget_and_balls_gone",
            normalize_session_policy("play_until_budget_and_balls_gone"),
        )
        self.assertEqual("fixed_spin_cap", normalize_session_policy("missing"))

    def test_current_profit_balls_converts_cash_spent_by_lend_rate(self):
        self.assertEqual(2500, current_profit_balls(3000, 500, cash_spent=1000, lend_rate=1.0))
        self.assertAlmostEqual(
            2600,
            current_profit_balls(3000, 500, cash_spent=1000, lend_rate=1.1111111111),
        )

    def test_profit_lock_locks_balls_and_requests_exit_at_threshold(self):
        flags = {}
        bank_balls, locked_balls, stop_requested = apply_strategy_rules(
            "profit_lock",
            bank_balls=3000,
            locked_balls=0,
            cash_spent=500,
            lend_rate=1.0,
            flags=flags,
        )
        self.assertEqual(1500, bank_balls)
        self.assertEqual(1500, locked_balls)
        self.assertFalse(stop_requested)
        self.assertTrue(flags["lock_2000"])
        self.assertTrue(flags["profit_lock_triggered"])

        flags = {}
        bank_balls, locked_balls, stop_requested = apply_strategy_rules(
            "profit_lock",
            bank_balls=10000,
            locked_balls=0,
            cash_spent=1000,
            lend_rate=1.0,
            flags=flags,
        )
        self.assertEqual(5000, bank_balls)
        self.assertEqual(5000, locked_balls)
        self.assertTrue(stop_requested)
        self.assertTrue(flags["profit_exit_triggered"])

    def test_aggressive_strategy_keeps_redeploy_bank_and_locks_excess(self):
        flags = {}
        bank_balls, locked_balls, stop_requested = apply_strategy_rules(
            "aggressive",
            bank_balls=6000,
            locked_balls=0,
            cash_spent=500,
            lend_rate=1.0,
            flags=flags,
        )

        self.assertEqual(3000, bank_balls)
        self.assertEqual(3000, locked_balls)
        self.assertFalse(stop_requested)
        self.assertTrue(flags["profit_lock_triggered"])
        self.assertTrue(flags["aggressive_redeploy_triggered"])

    def test_simulator_keeps_legacy_policy_and_strategy_exports(self):
        self.assertIs(simulator.SESSION_POLICIES, SESSION_POLICIES)
        self.assertIs(simulator.STRATEGIES, STRATEGIES)
        self.assertIs(simulator.apply_strategy_rules, apply_strategy_rules)
        self.assertIs(simulator.current_profit_balls, current_profit_balls)


if __name__ == "__main__":
    unittest.main()
