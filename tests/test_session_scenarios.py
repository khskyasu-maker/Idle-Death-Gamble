import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SIM_DIR = ROOT / "pachinko-sim"
sys.path.insert(0, str(SIM_DIR))

import session_scenarios  # noqa: E402
import simulator  # noqa: E402
from machines import MACHINES  # noqa: E402


class SessionScenarioTests(unittest.TestCase):
    def test_simulator_reexports_scenario_constants_for_legacy_imports(self):
        self.assertIs(simulator.SPIN_RATE_CASES, session_scenarios.SPIN_RATE_CASES)
        self.assertIs(simulator.BUDGET_CASES, session_scenarios.BUDGET_CASES)
        self.assertIs(simulator.PROFILE_BUDGET_CASES, session_scenarios.PROFILE_BUDGET_CASES)

    def test_rotation_cases_use_absolute_or_border_relative_inputs(self):
        absolute = session_scenarios.rotation_cases([55, 65], border_spins_per_1000y=70)
        self.assertEqual(["55회", "65회"], [case["rotation_label"] for case in absolute])
        self.assertEqual([55.0, 65.0], [case["spins_per_1000y"] for case in absolute])

        border_relative = session_scenarios.rotation_cases(None, border_spins_per_1000y=70)
        self.assertEqual("보더-10.0", border_relative[0]["rotation_label"])
        self.assertEqual(60.0, border_relative[0]["spins_per_1000y"])
        self.assertEqual(0, border_relative[2]["border_margin"])

    def test_budget_matrix_normalizes_policy_and_applies_normal_spin_multiplier(self):
        captured_calls = []
        original = simulator.simulate_multiple

        def fake_simulate_multiple(*args, **kwargs):
            captured_calls.append((args, kwargs))
            return [{"stub": True}]

        simulator.simulate_multiple = fake_simulate_multiple
        try:
            rows = session_scenarios.run_budget_matrix(
                MACHINES["sea_5"],
                lend_rate=1.0,
                exchange_rate=0.89,
                iterations=2,
                budgets=[1000],
                spins_per_1000y=70,
                session_policy="play_until_budget_and_balls_gone",
                max_normal_spin_multiplier=3,
                start_variance=False,
            )
        finally:
            simulator.simulate_multiple = original

        self.assertEqual(1, len(rows))
        self.assertEqual([{"stub": True}], rows[0]["results"])
        self.assertEqual("play_until_budget_and_balls_gone", rows[0]["session_policy"])
        self.assertEqual(210, captured_calls[0][1]["max_normal_spins"])
        self.assertFalse(captured_calls[0][1]["start_variance"])

    def test_simulator_matrix_wrapper_keeps_legacy_function_path(self):
        captured_calls = []
        original = simulator.simulate_multiple

        def fake_simulate_multiple(*args, **kwargs):
            captured_calls.append((args, kwargs))
            return []

        simulator.simulate_multiple = fake_simulate_multiple
        try:
            rows = simulator.run_matrix_simulation(
                MACHINES["sea_5"],
                lend_rate=1.0,
                exchange_rate=0.89,
                iterations=1,
                budget=1000,
                spin_rates=[60],
                start_variance=False,
            )
        finally:
            simulator.simulate_multiple = original

        self.assertEqual(1, len(rows))
        self.assertEqual("60회", rows[0]["rotation_label"])
        self.assertEqual(60.0, rows[0]["spins_per_1000y"])
        self.assertEqual(60.0, captured_calls[0][0][3])

    def test_strategy_matrix_adds_strategy_labels(self):
        original = simulator.simulate_multiple
        simulator.simulate_multiple = lambda *args, **kwargs: []
        try:
            rows = session_scenarios.run_strategy_matrix(
                MACHINES["sea_5"],
                lend_rate=1.0,
                exchange_rate=0.89,
                budget=1000,
                iterations=1,
                spin_rates=[70],
                strategies=["profit_lock"],
            )
        finally:
            simulator.simulate_multiple = original

        self.assertEqual(1, len(rows))
        self.assertEqual("profit_lock", rows[0]["strategy"])
        self.assertEqual("이익 잠금", rows[0]["strategy_label"])


if __name__ == "__main__":
    unittest.main()
