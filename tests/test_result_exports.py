import json
import os
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SIM_DIR = ROOT / "pachinko-sim"
sys.path.insert(0, str(SIM_DIR))

from machines import MACHINES  # noqa: E402
from result_csv import CSV_HEADERS, matrix_result_csv_row, save_matrix_to_csv  # noqa: E402
from result_public_export import (  # noqa: E402
    PUBLIC_EXPORT_DIR_ENV,
    build_public_sim_result_markdown,
    build_public_sim_result_payload,
    public_docs_dir_from_env,
    save_public_sim_results,
)
from session_limits import SESSION_TIME_LIMIT_HOURS  # noqa: E402


class ResultExportTests(unittest.TestCase):
    def test_result_csv_writer_keeps_latest_only_and_non_lt_markers(self):
        def metrics_stub(results, iterations):
            self.assertEqual([{"marker": True}], results)
            self.assertEqual(3, iterations)
            return {
                "avg_true_spins_per_1000y": 70.4,
                "avg_observed_spins_per_1000y": 69.6,
                "avg_spin_capacity": 700,
                "p10_spin_capacity": 620,
                "p90_spin_capacity": 780,
                "hit_rate": 55.55,
                "rush_rate": 44.44,
                "ruin_rate": 45.45,
                "single_hit_finish_rate": 11.11,
                "under_500_finish_rate": 2.22,
                "recovery_50_rate": 66.66,
                "recovery_80_rate": 33.33,
                "recovery_100_rate": 22.22,
                "positive_close_rate": 12.34,
                "avg_profit": -100,
                "avg_profit_standard_error": 12,
                "avg_profit_se_budget_pct": 0.1234,
                "mean_ci_method": "t",
                "avg_profit_ci_low": -200,
                "avg_profit_ci_high": 50,
                "median_profit": -80,
                "median_profit_ci_low": -150,
                "median_profit_ci_high": 20,
                "worst_10_profit": -1000,
                "worst_10_profit_ci_low": -1200,
                "worst_10_profit_ci_high": -800,
                "cvar_10_profit": -1100,
                "worst_25_profit": -500,
                "top_10_profit": 1500,
                "top_10_profit_ci_low": 1200,
                "top_10_profit_ci_high": 1800,
                "upper_tail_10_profit": 1600,
                "min_profit": -2000,
                "max_profit": 3000,
                "profit_condition_summary": "통계적으로 우세한 플러스 조건 없음",
                "avg_hits": 1.4,
                "avg_first_hit": 120,
                "median_first_hit": 100,
                "p90_first_hit": 250,
                "avg_after_first_hits": 0.4,
                "avg_hits_when_hit": 2.0,
                "avg_rush_entries": 0.6,
                "avg_lt_entries": 0.0,
                "lt_success_rate": 0.0,
                "avg_upper_entries": 0.0,
                "upper_success_rate": 0.0,
                "avg_play_minutes": 80.12,
                "median_play_minutes": 70.0,
                "p90_play_minutes": 150.0,
                "time_limit_reached_rate": 1.0,
                "time_limit_stop_rate": 0.5,
                "hard_time_limit_stop_rate": 0.0,
                "cash_input_cutoff_rate": 0.0,
                "avg_final_remaining_value": 9000,
                "median_final_remaining_value": 8500,
                "p10_final_remaining_value": 3000,
                "p90_final_remaining_value": 15000,
                "budget_exhausted_rate": 40.0,
                "funds_exhausted_stop_rate": 35.0,
                "post_budget_continue_rate": 10.0,
                "avg_post_budget_play_minutes": 5.5,
                "avg_post_budget_play_minutes_when_continued": 20.0,
                "avg_cashless_play_minutes": 15.5,
                "avg_cashless_play_share": 12.0,
                "avg_reserve_wait_minutes": 1.25,
                "avg_cash_spend_per_hour": 4500,
                "avg_play_minutes_per_1000yen_cash": 9.5,
                "profit_lock_trigger_rate": 3.0,
                "stop_loss_trigger_rate": 4.0,
                "avg_streak": 1.2,
                "avg_spins": 345,
            }

        machine = MACHINES["sea_5"]
        matrix_result = {"budget": 10000, "spins_per_1000y": 70, "results": [{"marker": True}]}
        row = matrix_result_csv_row(machine, matrix_result, 3, metrics_stub)
        row_by_header = dict(zip(CSV_HEADERS, row))

        self.assertEqual(len(CSV_HEADERS), len(row))
        self.assertEqual("P 대해물어5", row_by_header["기종"])
        self.assertEqual(10000, row_by_header["예산(엔)"])
        self.assertEqual("N/A", row_by_header["평균LT진입"])
        self.assertEqual("N/A", row_by_header["상위RUSH진입성공률"])

        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "results.csv"
            csv_path.write_text("old,accumulated,row\n", encoding="utf-8")
            save_matrix_to_csv(machine, [matrix_result], 3, metrics_stub, str(csv_path))
            rows = csv_path.read_text(encoding="utf-8-sig").splitlines()

        self.assertEqual(CSV_HEADERS[0], rows[0].split(",")[0])
        self.assertEqual(2, len(rows))
        self.assertNotIn("old,accumulated,row", "\n".join(rows))
        self.assertIn("P 대해물어5", rows[1])

    def test_public_sim_result_export_is_latest_only_and_sanitized(self):
        def metrics_stub(results, iterations):
            self.assertEqual([{"marker": True}], results)
            self.assertEqual(5, iterations)
            return {
                "hit_rate": 50.0,
                "ruin_rate": 50.0,
                "rush_rate": 25.0,
                "positive_close_rate": 20.0,
                "positive_close_rate_ci_low": 10.0,
                "positive_close_rate_ci_high": 35.0,
                "avg_profit_standard_error": 321,
                "avg_profit_se_budget_pct": 3.21,
                "avg_play_minutes": 90.0,
                "median_play_minutes": 80.0,
                "p10_play_minutes": 30.0,
                "p25_play_minutes": 50.0,
                "stay_reach_rates": {1: 90.0, 2: 70.0, 3: 40.0, SESSION_TIME_LIMIT_HOURS: 10.0},
                "first_hit_miss_funds_exhausted_rate": 45.0,
                "avg_first_hit_cash_spent": 4200,
                "median_first_hit_cash_spent": 3500,
                "avg_first_hit_play_minutes": 55.5,
                "avg_final_remaining_value": 8000,
                "avg_profit": -2000,
                "median_profit": -3000,
                "worst_10_profit": -9000,
                "worst_25_profit": -7000,
                "cvar_10_profit": -9500,
                "top_10_profit": 12000,
                "funds_exhausted_stop_rate": 40.0,
                "avg_first_hit": 150,
                "lt_success_rate": 0.0,
                "lt_success_rate_ci_low": 0.0,
                "lt_success_rate_ci_high": 0.0,
                "avg_hits": 1.2,
                "avg_streak": 1.1,
                "profit_condition_summary": "테스트 조건",
            }

        rows = [
            {
                "store_name": "123難波店",
                "rotation_label": "보더+5",
                "budget": 10000,
                "spins_per_1000y": 70,
                "border_spins_per_1000yen": 65,
                "strategy": "no_rule",
                "session_policy": "fixed_spin_cap",
                "results": [{"marker": True}],
            }
        ]
        payload = build_public_sim_result_payload(
            "123難波店",
            "테스트 모드",
            MACHINES["sea_5"],
            rows,
            5,
            metrics_stub,
            generated_at="2026-05-17 12:00:00 KST",
            extra_analysis={
                "rotation_sensitivity": {
                    "budget_yen": 10000,
                    "iterations": 3,
                    "rows": [
                        {
                            "category": "대해물어",
                            "machine": "P 대해물어5",
                            "store": "123/4대",
                            "rotation_range_text": "60-75회/1000엔",
                            "median_time_range_text": "120-540분",
                            "plus_range_text": "20.0-40.0%",
                            "funds_exhausted_range_text": "30.0-60.0%",
                            "median_profit_range_text": "-10,000엔~+1,000엔",
                            "sensitivity_label": "높음",
                        }
                    ],
                },
                "tail_risk_review": {
                    "budget_yen": 10000,
                    "iterations": 5,
                    "rows": [
                        {
                            "category": "기타",
                            "machine": "테스트 LT",
                            "store": "123/1대",
                            "p10_play_text": "120분",
                            "p25_play_text": "240분",
                            "funds_exhausted_text": "60.0%",
                            "median_profit_text": "-9,000엔",
                            "cvar10_text": "-10,000엔",
                            "mean_median_gap_text": "+6,000엔",
                            "lt_entry_text": "12.0%",
                            "risk_label": "LT꼬리의존",
                        }
                    ],
                }
            },
        )
        markdown = build_public_sim_result_markdown(payload)

        self.assertFalse(payload["privacy_policy"]["raw_sample_sessions_included"])
        self.assertEqual(5, payload["schema_version"])
        self.assertFalse(payload["rows"][0]["has_lt"])
        self.assertEqual(90.0, payload["rows"][0]["1h_reach_rate_pct"])
        self.assertEqual(45.0, payload["rows"][0]["first_hit_miss_funds_exhausted_rate_pct"])
        self.assertEqual(4200, payload["rows"][0]["avg_first_hit_cash_spent_yen"])
        lt_payload = build_public_sim_result_payload(
            "123難波店",
            "테스트 모드",
            MACHINES["eva_beginning"],
            rows,
            5,
            metrics_stub,
            generated_at="2026-05-17 12:00:00 KST",
        )
        self.assertTrue(lt_payload["rows"][0]["has_lt"])
        self.assertEqual(0.0, lt_payload["rows"][0]["lt_success_rate_pct"])
        self.assertIn("simulation_method", payload)
        self.assertIn("model_structure", payload["simulation_method"])
        self.assertIn("statistics", payload["simulation_method"])
        self.assertIn("analysis", payload)
        self.assertNotIn("results", payload["rows"][0])
        self.assertIn("최신 공개 시뮬 결과", markdown)
        self.assertIn("시뮬 설계와 구성", markdown)
        self.assertIn("사전 유추와 실제 결과 비교 기준", markdown)
        self.assertIn("회전율 민감도 요약", markdown)
        self.assertIn("하방/꼬리 리스크 요약", markdown)
        self.assertIn("60-75회/1000엔", markdown)
        self.assertIn("LT꼬리의존", markdown)
        self.assertIn("기종", markdown)
        self.assertIn("평균최대연", markdown)
        self.assertIn("플러스95%CI", markdown)
        self.assertIn("손익SE", markdown)
        self.assertIn("초당첨전소진", markdown)
        self.assertIn("초당첨평균현금", markdown)
        self.assertIn("보더+5", markdown)

        with tempfile.TemporaryDirectory() as tmpdir:
            docs_dir = Path(tmpdir)
            (docs_dir / "sim-results-old.md").write_text("old", encoding="utf-8")
            paths = save_public_sim_results(
                "123難波店",
                "테스트 모드",
                MACHINES["sea_5"],
                rows,
                5,
                metrics_stub,
                docs_dir=docs_dir,
                generated_at="2026-05-17 12:00:00 KST",
            )
            saved_payload = json.loads(paths["json"].read_text(encoding="utf-8"))

        self.assertEqual("테스트 모드", saved_payload["mode"])
        self.assertFalse((docs_dir / "sim-results-old.md").exists())
        self.assertTrue(paths["html"].name.endswith(".html"))

    def test_public_sim_result_export_dir_can_be_overridden_for_cli_smoke(self):
        original_value = os.environ.get(PUBLIC_EXPORT_DIR_ENV)
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                os.environ[PUBLIC_EXPORT_DIR_ENV] = tmpdir
                self.assertEqual(Path(tmpdir), public_docs_dir_from_env())
        finally:
            if original_value is None:
                os.environ.pop(PUBLIC_EXPORT_DIR_ENV, None)
            else:
                os.environ[PUBLIC_EXPORT_DIR_ENV] = original_value


if __name__ == "__main__":
    unittest.main()
