import random
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SIM_DIR = ROOT / "pachinko-sim"
sys.path.insert(0, str(SIM_DIR))

from machine_traits import machine_has_lt, machine_has_upper  # noqa: E402
from machines import MACHINES  # noqa: E402
from machines import Machine, Payout  # noqa: E402
from model_checks import theoretical_no_hit_rate, validate_all_machine_models  # noqa: E402
from result import (  # noqa: E402
    SESSION_TIME_LIMIT_HOURS,
    benchmark_model_value,
    calculate_metrics,
    denominator_tail_rows,
    fall_state_continue_chance,
    mean_interval,
)
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
from simulator import sample_payout_balls, simulate_single, spins_until_hit  # noqa: E402
from spec_benchmarks import PUBLIC_BENCHMARKS  # noqa: E402
from start_gate import estimate_rate_from_observed_spins, sample_session_spin_rate  # noqa: E402
from store_comparison import store_spins_per_1000yen  # noqa: E402
from time_model import (  # noqa: E402
    DEFAULT_TIME_ASSUMPTIONS,
    hit_effect_seconds,
    normal_time_components,
    right_seconds,
    time_assumptions_for_machine,
)


class SimulatorSpecTests(unittest.TestCase):
    def test_all_machine_models_validate(self):
        self.assertEqual([], validate_all_machine_models(MACHINES))

    def test_public_benchmarks_stay_close_to_model_values(self):
        issues = []
        for machine_id, benchmarks in PUBLIC_BENCHMARKS.items():
            machine = MACHINES[machine_id]
            for benchmark in benchmarks:
                model_value = benchmark_model_value(machine, benchmark)
                public_value = float(benchmark["public"])
                tolerance = 0.5 if benchmark["unit"] == "denom" else 3.0
                if abs(model_value - public_value) > tolerance:
                    issues.append(
                        f"{machine_id} {benchmark['label_ja']}: "
                        f"public={public_value}, model={model_value:.2f}"
                    )
        self.assertEqual([], issues)

    def test_non_lt_upper_rush_is_not_counted_as_lt(self):
        machine = MACHINES["sea_5_black_199"]
        self.assertFalse(machine_has_lt(machine))
        self.assertTrue(machine_has_upper(machine))
        self.assertAlmostEqual(
            0.0,
            sum(p.weight for p in machine.st_hit_dist if p.next_state == "LT"),
        )
        self.assertAlmostEqual(
            0.04,
            sum(p.weight for p in machine.st_hit_dist if p.next_state == "UPPER"),
        )

    def test_core_lt_machine_step_specs(self):
        sea_black_lt = MACHINES["sea_5_black_lt"]
        self.assertTrue(machine_has_lt(sea_black_lt))
        self.assertEqual([330, 330], [p.balls for p in sea_black_lt.normal_hit_dist])
        self.assertAlmostEqual(
            0.70,
            sum(p.weight for p in sea_black_lt.normal_hit_dist if p.next_state == "ST"),
        )
        self.assertAlmostEqual(
            0.10,
            sum(p.weight for p in sea_black_lt.st_hit_dist if p.next_state == "LT"),
        )
        self.assertAlmostEqual(
            0.40,
            sum(p.weight for p in sea_black_lt.st_hit_dist if p.balls == 880),
        )
        self.assertAlmostEqual(
            0.60,
            sum(p.weight for p in sea_black_lt.st_hit_dist if p.balls == 330),
        )

        shin_eva_lt = MACHINES["shin_eva_129_lt"]
        self.assertAlmostEqual(
            0.005,
            sum(p.weight for p in shin_eva_lt.normal_hit_dist if p.next_state == "LT"),
        )
        self.assertAlmostEqual(
            0.10,
            sum(p.weight for p in shin_eva_lt.st_hit_dist if p.next_state == "LT"),
        )

        mediterranean = MACHINES["mediterranean_2_89"]
        self.assertEqual({24}, {p.st_spins for p in mediterranean.normal_hit_dist})
        self.assertEqual(
            {48, 100},
            {p.st_spins for p in mediterranean.st_hit_dist},
        )
        self.assertEqual({100}, {p.st_spins for p in mediterranean.lt_hit_dist})

        re_zero_s2_129 = MACHINES["re_zero_s2_129"]
        self.assertTrue(machine_has_lt(re_zero_s2_129))
        self.assertFalse(any(p.next_state == "LT" for p in re_zero_s2_129.st_hit_dist))
        self.assertAlmostEqual(
            0.125,
            sum(p.weight for p in re_zero_s2_129.st_hit_dist if p.is_lt),
        )

    def test_additional_sea_models_match_public_step_specs(self):
        black4 = MACHINES["sea_4_special_black"]
        self.assertEqual([1500, 750, 450], [p.balls for p in black4.normal_hit_dist])
        self.assertAlmostEqual(0.30, black4.normal_hit_dist[0].weight)
        self.assertAlmostEqual(0.30, black4.normal_hit_dist[1].weight)
        self.assertAlmostEqual(0.40, black4.normal_hit_dist[2].weight)
        self.assertEqual({51}, {p.st_spins for p in black4.st_hit_dist})

        sea3r3 = MACHINES["sea_3r3"]
        self.assertAlmostEqual(
            0.51,
            sum(p.weight for p in sea3r3.normal_hit_dist if p.next_state == "KAKUBEN"),
        )
        self.assertAlmostEqual(
            0.49,
            sum(p.weight for p in sea3r3.normal_hit_dist if p.next_state == "JITAN"),
        )
        self.assertEqual({40}, {p.jitan_spins for p in sea3r3.normal_hit_dist if p.next_state == "JITAN"})

        extreme = MACHINES["sea_extreme_japan"]
        self.assertEqual([True, False], [p.counts_as_rush for p in extreme.normal_hit_dist])
        self.assertEqual({24, 104}, {p.st_spins for p in extreme.normal_hit_dist})
        self.assertAlmostEqual(0.20, sum(p.weight for p in extreme.st_hit_dist if p.balls == 3000))
        self.assertAlmostEqual(0.55, sum(p.weight for p in extreme.st_hit_dist if p.balls == 1500))
        self.assertAlmostEqual(0.25, sum(p.weight for p in extreme.st_hit_dist if p.balls == 300))

        naginami = MACHINES["sea_extreme_japan_naginami"]
        self.assertEqual({20, 74}, {p.st_spins for p in naginami.normal_hit_dist})
        self.assertAlmostEqual(0.05, sum(p.weight for p in naginami.st_hit_dist if p.balls == 800))
        self.assertAlmostEqual(0.95, sum(p.weight for p in naginami.st_hit_dist if p.balls == 240))

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

    def test_rotation_unit_conversions_handle_1yen_and_1111yen(self):
        self.assertAlmostEqual(70.0, spins_from_yen_observation(14, 200))
        self.assertAlmostEqual(70.0, spins_from_ball_unit(17.5, 250, 1.0))
        self.assertAlmostEqual(70.0, spins_from_ball_unit(14, 200, 1.0))
        self.assertAlmostEqual(70.0, spins_from_ball_unit(14, 180, 1.111), delta=0.1)
        self.assertAlmostEqual(63.0, spins_from_ball_unit(17.5, 250, 1.111), delta=0.1)
        self.assertEqual(72.5, spins_from_border_margin(67.5, 5))

    def test_border_case_rates_and_labels_are_border_relative(self):
        cases = border_case_rates(67.5)
        self.assertEqual(["보더-10.0", "보더-5.0", "보더±0", "보더+5.0", "보더+10.0"], [row["rotation_label"] for row in cases])
        self.assertEqual([57.5, 62.5, 67.5, 72.5, 77.5], [row["spins_per_1000y"] for row in cases])
        self.assertEqual("+5.0", border_delta_text(72.5, 67.5))
        self.assertEqual("1.07x", border_ratio_text(72.5, 67.5))
        self.assertEqual("좋음", rotation_reality_label(72.5, 67.5))

    def test_time_model_counts_launch_display_and_cashless_play(self):
        parts = normal_time_components(
            start_spins=120,
            fired_balls=1000,
            assumptions=DEFAULT_TIME_ASSUMPTIONS,
        )
        self.assertAlmostEqual(600.0, parts["active_launch_seconds"])
        self.assertAlmostEqual(720.0, parts["display_seconds"])
        self.assertAlmostEqual(120.0, parts["reserve_wait_seconds"])
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

    def test_store_comparison_can_keep_same_border_margin(self):
        self.assertAlmostEqual(
            66.0,
            store_spins_per_1000yen(
                "border_margin",
                reference_lend_rate=1.111,
                target_lend_rate=1.0,
                reference_spins_per_1000y=60.0,
                reference_border_spins_per_1000y=55.0,
                target_border_spins_per_1000y=61.0,
            ),
        )
        self.assertAlmostEqual(
            60.0,
            store_spins_per_1000yen(
                "border_margin",
                reference_lend_rate=1.111,
                target_lend_rate=1.0,
                reference_spins_per_1000y=60.0,
                reference_border_spins_per_1000y=None,
                target_border_spins_per_1000y=61.0,
            ),
        )

    def test_payout_variance_uses_bounded_centered_distribution(self):
        fixed = Payout(balls=1000, weight=1.0, next_state="NORMAL", ball_variance=0.0)
        self.assertEqual(1000, sample_payout_balls(fixed))

        variable = Payout(balls=1000, weight=1.0, next_state="NORMAL", ball_variance=0.10)
        samples = [sample_payout_balls(variable) for _ in range(500)]
        self.assertTrue(all(900 <= value <= 1100 for value in samples))
        self.assertLess(abs(sum(samples) / len(samples) - 1000), 20)

    def test_hokuto_fall_type_continuation_rates(self):
        hokuto = MACHINES["hokuto_10"]
        self.assertEqual({"ST": 136.9, "LT": 275.9}, hokuto.fall_prob)
        self.assertEqual({"ST": 4, "LT": 4}, hokuto.fall_reserve_spins)
        self.assertAlmostEqual(80.0, fall_state_continue_chance(hokuto, "ST"), delta=0.2)
        self.assertAlmostEqual(89.0, fall_state_continue_chance(hokuto, "LT"), delta=0.3)

    def test_profit_distribution_metrics_include_uncertainty_and_tail_risk(self):
        def result_row(net_profit):
            return {
                "budget": 10000,
                "net_profit": net_profit,
                "total_hits": 1,
                "max_streak": 1,
                "spins_used": 80,
                "total_spins_possible": 800,
                "observed_spins_per_1000y": 80.0,
                "right_spins": 0,
                "normal_balls_fired": 1000,
                "total_out_balls": 1000,
                "cash_spent": 10000,
                "final_money": 10000 + net_profit,
                "rush_entries": 0,
                "lt_entries": 0,
                "upper_entries": 0,
                "first_hit_spin": 80,
                "first_hit_total_spins": 95,
                "experienced_rush": False,
                "start_variance": False,
                "start_probability": 0.08,
            }

        results = [result_row(value * 100) for value in range(-50, 50)]
        metrics = calculate_metrics(results, len(results))

        self.assertGreater(metrics["avg_profit_standard_error"], 0)
        self.assertEqual("t", metrics["mean_ci_method"])
        self.assertGreater(metrics["avg_profit_se_budget_pct"], 0)
        self.assertEqual(95, metrics["median_first_hit_total_spins"])
        self.assertLessEqual(metrics["median_profit_ci_low"], metrics["median_profit"])
        self.assertGreaterEqual(metrics["median_profit_ci_high"], metrics["median_profit"])
        self.assertLessEqual(metrics["cvar_10_profit"], metrics["worst_10_profit"])
        self.assertLessEqual(metrics["worst_10_profit_ci_low"], metrics["worst_10_profit"])
        self.assertGreaterEqual(metrics["top_10_profit_ci_high"], metrics["top_10_profit"])

    def test_profit_condition_metrics_are_conditioned_on_useful_outcomes(self):
        def result_row(net_profit, total_hits, max_streak):
            return {
                "budget": 10000,
                "net_profit": net_profit,
                "total_hits": total_hits,
                "max_streak": max_streak,
                "spins_used": 80,
                "total_spins_possible": 800,
                "observed_spins_per_1000y": 80.0,
                "right_spins": 0,
                "normal_balls_fired": 1000,
                "total_out_balls": 1000,
                "cash_spent": 10000,
                "final_money": 10000 + net_profit,
                "rush_entries": 0,
                "lt_entries": 0,
                "upper_entries": 0,
                "first_hit_spin": 80 if total_hits else None,
                "first_hit_total_spins": 95 if total_hits else None,
                "experienced_rush": total_hits >= 2,
                "start_variance": False,
                "start_probability": 0.08,
            }

        results = (
            [result_row(-10000, 0, 0) for _ in range(40)]
            + [result_row(-3000, 1, 1) for _ in range(30)]
            + [result_row(5000, 2, 2) for _ in range(30)]
        )
        metrics = calculate_metrics(results, len(results))

        hit_two = next(
            row for row in metrics["profit_condition_rows"]
            if row["kind"] == "hits" and row["threshold"] == 2
        )
        self.assertEqual(30, hit_two["sample_count"])
        self.assertEqual(30.0, hit_two["occurrence_rate"])
        self.assertEqual(100.0, hit_two["positive_rate"])
        self.assertEqual("플러스우세", hit_two["judgement"])
        self.assertIn("2당+", metrics["profit_condition_summary"])

    def test_mean_interval_uses_small_sample_t_critical_value(self):
        low, high = mean_interval([0, 10])
        self.assertLessEqual(low, -30)
        self.assertGreaterEqual(high, 40)


if __name__ == "__main__":
    unittest.main()
