import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SIM_DIR = ROOT / "pachinko-sim"
sys.path.insert(0, str(SIM_DIR))

from result_metrics import calculate_metrics  # noqa: E402
from result_stats import mean_interval, profit_condition_thresholds, wilson_interval  # noqa: E402


class ResultMetricsTests(unittest.TestCase):
    def test_result_stats_helpers_are_importable_without_result_output_layer(self):
        low, high = wilson_interval(5, 10)

        self.assertLess(low, 50.0)
        self.assertGreater(high, 50.0)
        self.assertEqual((0.0, 0.0), wilson_interval(0, 0))
        self.assertEqual([1, 2, 3, 5, 7], profit_condition_thresholds(7, include_one=True))
        self.assertEqual([2, 3, 5, 7], profit_condition_thresholds(7, include_one=False))

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
                "first_hit_cash_spent": 1200,
                "first_hit_play_minutes": 8.5,
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
        self.assertEqual(1200, metrics["median_first_hit_cash_spent"])
        self.assertEqual(8.5, metrics["median_first_hit_play_minutes"])
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
                "first_hit_cash_spent": 1200 if total_hits else None,
                "first_hit_play_minutes": 8.5 if total_hits else None,
                "funds_exhausted_triggered": not total_hits,
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
        self.assertEqual(40.0, metrics["first_hit_miss_funds_exhausted_rate"])

    def test_mean_interval_uses_small_sample_t_critical_value(self):
        low, high = mean_interval([0, 10])
        self.assertLessEqual(low, -30)
        self.assertGreaterEqual(high, 40)


if __name__ == "__main__":
    unittest.main()
