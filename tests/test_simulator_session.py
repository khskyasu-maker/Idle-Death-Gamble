import random
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SIM_DIR = ROOT / "pachinko-sim"
sys.path.insert(0, str(SIM_DIR))

from machines import MACHINES, Machine, Payout  # noqa: E402
from model_checks import theoretical_no_hit_rate  # noqa: E402
from result_metrics import calculate_metrics  # noqa: E402
from result_output_helpers import denominator_tail_rows  # noqa: E402
from rotation import rotation_reality_label  # noqa: E402
from session_limits import SESSION_TIME_LIMIT_HOURS  # noqa: E402
from simulator import (  # noqa: E402
    run_budget_matrix,
    sample_payout_balls,
    simulate_multiple,
    simulate_single,
    spins_until_hit,
)
from start_gate import estimate_rate_from_observed_spins, sample_session_spin_rate  # noqa: E402
from time_model import (  # noqa: E402
    DEFAULT_TIME_ASSUMPTIONS,
    gross_launch_balls,
    hit_effect_seconds,
    normal_time_components,
    right_seconds,
    time_assumptions_for_machine,
)


class SimulatorSessionTests(unittest.TestCase):
    def test_shinsea_support_time_is_not_counted_as_a_jackpot(self):
        shinsea = MACHINES["shinsea_99"]
        self.assertAlmostEqual(199.8, shinsea.normal_support_prob)
        self.assertEqual([678, 678, 45, 20], [p.jitan_spins for p in shinsea.normal_hit_dist])
        self.assertEqual([379, 100, 40, 20], [p.jitan_spins for p in shinsea.normal_support_dist])
        self.assertTrue(all(p.balls == 0 for p in shinsea.normal_support_dist))
        self.assertFalse(any(p.counts_as_rush for p in shinsea.normal_support_dist))

        result = simulate_single(
            shinsea,
            budget=1000,
            lend_rate=1.0,
            spins_per_1000y=100,
            exchange_rate=0.89,
            start_variance=False,
        )
        self.assertIn("total_hits", result)

    def test_hit_wait_uses_geometric_independent_trials(self):
        random.seed(20260513)
        denominator = 99.9
        spins = int(round(denominator))
        samples = [spins_until_hit(denominator) for _ in range(20000)]
        empirical_no_hit_after_denominator = (
            sum(1 for sample in samples if sample > spins) / len(samples)
        ) * 100.0

        self.assertAlmostEqual(
            theoretical_no_hit_rate(denominator, spins),
            empirical_no_hit_after_denominator,
            delta=1.5,
        )

        tail_rows = denominator_tail_rows(MACHINES["sea_5_agnes"])
        self.assertEqual("분모 1배", tail_rows[0][0])
        self.assertEqual("100회", tail_rows[0][1])
        self.assertIn("36.", tail_rows[0][2])

    def test_simulate_multiple_seed_is_reproducible_and_restores_global_random_state(self):
        kwargs = {
            "budget": 1000,
            "lend_rate": 1.0,
            "spins_per_1000y": 70,
            "exchange_rate": 0.89,
            "iterations": 5,
            "session_policy": "fixed_spin_cap",
            "seed": 12345,
        }

        first = simulate_multiple(MACHINES["sea_5"], **kwargs)
        second = simulate_multiple(MACHINES["sea_5"], **kwargs)
        self.assertEqual(
            [result["net_profit"] for result in first],
            [result["net_profit"] for result in second],
        )

        random.seed(999)
        expected_next = random.random()
        random.seed(999)
        simulate_multiple(MACHINES["sea_5"], **kwargs)
        self.assertEqual(expected_next, random.random())

    def test_monte_carlo_fixed_spin_cap_converges_for_simple_normal_model(self):
        simple_machine = Machine(
            id="test_simple_normal",
            name_ja="テスト単純機",
            name_ko="테스트 단순기",
            spec_type="test",
            risk_grade="1/100",
            normal_prob=100.0,
            high_prob=100.0,
            normal_hit_dist=[
                Payout(balls=1000, weight=1.0, next_state="NORMAL", ball_variance=0.0),
            ],
            st_hit_dist=[],
            jitan_hit_dist=[],
            kakuben_hit_dist=[],
            lt_hit_dist=[],
        )
        iterations = 3000
        normal_spins = 500

        results = simulate_multiple(
            simple_machine,
            budget=5000,
            lend_rate=1.0,
            spins_per_1000y=100,
            exchange_rate=1.0,
            iterations=iterations,
            session_policy="fixed_spin_cap",
            start_variance=False,
            seed=20260518,
        )
        metrics = calculate_metrics(results, iterations)

        expected_avg_hits = normal_spins / simple_machine.normal_prob
        expected_hit_rate = 100.0 - theoretical_no_hit_rate(simple_machine.normal_prob, normal_spins)
        self.assertAlmostEqual(expected_avg_hits, metrics["avg_hits"], delta=0.20)
        self.assertAlmostEqual(expected_hit_rate, metrics["hit_rate"], delta=1.0)
        self.assertAlmostEqual(metrics["avg_hits"] * 1000, metrics["avg_total_out_balls"], delta=250)

    def test_basic_stop_uses_probe_rotation_and_charges_failed_probe(self):
        slow_machine = Machine(
            id="test_slow_machine",
            name_ja="テスト機",
            name_ko="테스트기",
            spec_type="test",
            risk_grade="1/99",
            normal_prob=1_000_000_000.0,
            high_prob=1_000_000_000.0,
            normal_hit_dist=[Payout(balls=0, weight=1.0, next_state="NORMAL")],
            st_hit_dist=[],
            jitan_hit_dist=[],
            kakuben_hit_dist=[],
            lt_hit_dist=[],
        )

        result = simulate_single(
            slow_machine,
            budget=10000,
            lend_rate=1.0,
            spins_per_1000y=60,
            exchange_rate=0.89,
            strategy="basic_stop",
            start_variance=False,
        )

        self.assertTrue(result["stop_loss_triggered"])
        self.assertEqual(60, result["stop_loss_probe_spins"])
        self.assertEqual(60.0, result["stop_loss_probe_rate"])
        self.assertLessEqual(result["spins_used"], 60)
        self.assertEqual(1000, result["cash_spent"])

    def test_table_quality_distribution_is_separate_from_start_sampling(self):
        for _ in range(100):
            sampled_rate = sample_session_spin_rate(
                70,
                border_spins_per_1000y=63,
                quality_stddev=5,
                min_spins_per_1000y=60,
                max_spins_per_1000y=80,
            )
            self.assertGreaterEqual(sampled_rate, 60)
            self.assertLessEqual(sampled_rate, 80)

        self.assertAlmostEqual(70.0, estimate_rate_from_observed_spins(14, 200))

        result = simulate_single(
            MACHINES["sea_5_agnes"],
            budget=1000,
            lend_rate=1.0,
            spins_per_1000y=70,
            exchange_rate=0.89,
            start_variance=True,
            border_spins_per_1000y=63,
            spin_rate_quality_stddev=4,
            spin_rate_min=70,
            spin_rate_max=70,
        )
        self.assertEqual(70.0, result["true_spins_per_1000y"])
        self.assertEqual(63, result["border_spins_per_1000yen"])
        self.assertEqual(4, result["spin_rate_quality_stddev"])

    def test_time_model_counts_launch_display_and_cashless_play(self):
        parts = normal_time_components(
            start_spins=120,
            net_consumed_balls=1000,
            assumptions=DEFAULT_TIME_ASSUMPTIONS,
        )
        self.assertAlmostEqual(1250.0, parts["gross_launched_balls"])
        self.assertAlmostEqual(750.0, parts["active_launch_seconds"])
        self.assertAlmostEqual(720.0, parts["display_seconds"])
        self.assertAlmostEqual(0.0, parts["reserve_wait_seconds"])
        self.assertAlmostEqual(
            1333.333,
            gross_launch_balls(1000, time_assumptions_for_machine(MACHINES["sea_5_agnes"])),
            delta=0.01,
        )
        self.assertAlmostEqual(67.5, right_seconds("ST", 50))
        self.assertAlmostEqual(118.0, hit_effect_seconds(1500, "NORMAL"))
        self.assertEqual("sea_classic", time_assumptions_for_machine(MACHINES["sea_5_agnes"]).profile_name)
        self.assertEqual("eva_vst", time_assumptions_for_machine(MACHINES["eva_15_roar"]).profile_name)
        self.assertEqual("rezero_fast", time_assumptions_for_machine(MACHINES["re_zero_99"]).profile_name)

        result = simulate_single(
            MACHINES["sea_5_agnes"],
            budget=1000,
            lend_rate=1.0,
            spins_per_1000y=70,
            exchange_rate=0.89,
            start_variance=False,
        )
        self.assertGreater(result["play_minutes"], 0)
        self.assertIn("cashless_play_minutes", result)
        self.assertIn("unused_cash", result)
        self.assertIn("final_remaining_value", result)
        self.assertIn("time_assumptions", result)
        self.assertEqual("sea_classic", result["time_assumptions"]["profile_name"])
        self.assertGreater(result["normal_balls_fired"], result["normal_net_balls_consumed"])
        self.assertAlmostEqual(0.0525, result["start_probability"], delta=0.0001)
        metrics = calculate_metrics([result], 1)
        self.assertIn(SESSION_TIME_LIMIT_HOURS, metrics["stay_reach_rates"])
        self.assertNotIn(SESSION_TIME_LIMIT_HOURS + 1, metrics["stay_reach_rates"])
        self.assertIn("avg_final_remaining_value", metrics)
        self.assertIn("avg_post_budget_play_minutes", metrics)
        self.assertEqual("타협", rotation_reality_label(65, None))

        no_hit_machine = Machine(
            id="test_no_hit",
            name_ja="テスト",
            name_ko="테스트",
            spec_type="test",
            risk_grade="test",
            normal_prob=1_000_000_000.0,
            high_prob=1.0,
            normal_hit_dist=[Payout(balls=0, weight=1.0, next_state="NORMAL")],
            st_hit_dist=[],
            jitan_hit_dist=[],
            kakuben_hit_dist=[],
            lt_hit_dist=[],
        )
        limited = simulate_single(
            no_hit_machine,
            budget=100000,
            lend_rate=1.0,
            spins_per_1000y=100,
            exchange_rate=0.89,
            session_policy="play_until_budget_and_balls_gone",
            session_time_limit_minutes=0.2,
            cash_input_cutoff_minutes=None,
            start_variance=False,
        )
        self.assertTrue(limited["time_limit_triggered"])
        self.assertLessEqual(limited["play_minutes"], 0.21)

        soft_limited = simulate_single(
            no_hit_machine,
            budget=100000,
            lend_rate=1.0,
            spins_per_1000y=100,
            exchange_rate=0.89,
            session_policy="play_until_budget_and_balls_gone",
            session_time_limit_minutes=10,
            soft_stop_minutes=0.2,
            cash_input_cutoff_minutes=None,
            start_variance=False,
        )
        self.assertTrue(soft_limited["soft_stop_triggered"])
        self.assertFalse(soft_limited["time_limit_triggered"])
        self.assertLessEqual(soft_limited["play_minutes"], 0.21)

        cash_blocked = simulate_single(
            no_hit_machine,
            budget=1000,
            lend_rate=1.0,
            spins_per_1000y=100,
            exchange_rate=0.89,
            session_policy="play_until_budget_and_balls_gone",
            session_time_limit_minutes=10,
            cash_input_cutoff_minutes=0,
            start_variance=False,
        )
        self.assertTrue(cash_blocked["cash_input_cutoff_triggered"])
        self.assertEqual(0, cash_blocked["cash_spent"])
        self.assertEqual(1000, cash_blocked["final_remaining_value"])

        post_budget = simulate_single(
            no_hit_machine,
            budget=1000,
            lend_rate=1.0,
            spins_per_1000y=100,
            exchange_rate=0.89,
            session_policy="play_until_budget_and_balls_gone",
            session_time_limit_minutes=30,
            soft_stop_minutes=None,
            cash_input_cutoff_minutes=None,
            start_variance=False,
        )
        self.assertTrue(post_budget["cash_budget_exhausted"])
        self.assertTrue(post_budget["funds_exhausted_triggered"])
        self.assertEqual(0, post_budget["post_budget_play_minutes"])

        budget_matrix = run_budget_matrix(
            no_hit_machine,
            lend_rate=1.0,
            exchange_rate=0.89,
            iterations=1,
            budgets=[1000],
            spins_per_1000y=100,
            session_policy="play_until_budget_and_balls_gone",
            start_variance=False,
        )
        self.assertIsNone(budget_matrix[0]["results"][0]["normal_spin_cap"])

    def test_payout_variance_uses_bounded_centered_distribution(self):
        fixed = Payout(balls=1000, weight=1.0, next_state="NORMAL", ball_variance=0.0)
        self.assertEqual(1000, sample_payout_balls(fixed))

        variable = Payout(balls=1000, weight=1.0, next_state="NORMAL", ball_variance=0.10)
        samples = [sample_payout_balls(variable) for _ in range(500)]
        self.assertTrue(all(900 <= value <= 1100 for value in samples))
        self.assertLess(abs(sum(samples) / len(samples) - 1000), 20)


if __name__ == "__main__":
    unittest.main()
