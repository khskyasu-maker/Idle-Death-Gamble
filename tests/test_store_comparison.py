import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SIM_DIR = ROOT / "pachinko-sim"
sys.path.insert(0, str(SIM_DIR))

from machines import MACHINES  # noqa: E402
from result_output_helpers import simulation_scope_note, store_auxiliary_note  # noqa: E402
from result_store_views import (  # noqa: E402
    build_store_comparison_view,
    store_comparison_assumption_text,
    store_comparison_name_rows,
    store_comparison_reference_rotation_text,
)
from session_limits import SESSION_TIME_LIMIT_HOURS  # noqa: E402
from store_comparison import store_spins_per_1000yen  # noqa: E402


class StoreComparisonTests(unittest.TestCase):
    def test_store_comparison_view_builds_installed_and_missing_rows(self):
        def metrics_stub(results, iterations):
            self.assertEqual([{"marker": True}], results)
            self.assertEqual(7, iterations)
            return {
                "hit_rate": 55.5,
                "ruin_rate": 44.5,
                "rush_rate": 33.3,
                "positive_close_rate": 22.2,
                "avg_play_minutes": 80.0,
                "avg_final_remaining_value": 11000,
                "avg_profit": 500,
                "median_profit": -100,
                "worst_10_profit": -4000,
                "top_10_profit": 9000,
                "recovery_80_rate": 66.6,
                "avg_first_hit": 123,
                "avg_hits": 1.5,
                "avg_streak": 1.2,
                "profit_condition_summary": "테스트 조건",
                "lt_success_rate": 0.0,
                "upper_success_rate": 0.0,
                "stay_reach_rates": {SESSION_TIME_LIMIT_HOURS: 12.3},
            }

        rows = [
            {
                "store_short_label": "123",
                "store_name": "123難波店",
                "installed": True,
                "rental_rate": 1.0,
                "count": 2,
                "results": [{"marker": True}],
                "spins_per_1000y": 70,
                "border_spins_per_1000yen": 65,
                "start_probability": 0.07,
                "comparison_mode_label": "동일 보더 마진",
                "comparison_mode": "border_margin",
                "reference_spins_per_1000y": 70,
                "reference_rotation_label": "보더+5",
                "budget": 10000,
                "strategy_label": "노룰",
                "session_policy_label": "9시간",
                "placement_summary": "123 2대/1yen",
                "installed_full_name_ko": "테스트 한국어",
                "installed_full_name_ja": "テスト",
            },
            {
                "store_short_label": "라쿠엔",
                "store_name": "楽園なんば店",
                "installed": False,
                "rental_rate": 1.111,
                "count": 0,
            },
        ]
        view = build_store_comparison_view(
            MACHINES["sea_5"],
            rows,
            7,
            metrics_stub,
            lambda confidence, spins, border: "주의문구",
            lambda normal_prob, results: 40.4,
            lambda spins, border: "+5.0",
            lambda spins, border: "좋음/1.08x",
            lambda machine, metrics: "LT 없음",
            lambda machine, metrics: "상위 없음",
            lambda metrics, hour: f"{metrics['stay_reach_rates'][hour]:.1f}%",
        )

        self.assertIn("보더 대비", store_comparison_assumption_text("border_margin"))
        self.assertIn("헤소 입상", store_comparison_assumption_text("ball_quality"))
        self.assertIn("1000엔당 같은 회전수", store_comparison_assumption_text("cash_rotation"))
        self.assertEqual("보더+5 -> 70회/1000엔", store_comparison_reference_rotation_text(rows[0]))
        self.assertEqual(
            "70회/1000엔",
            store_comparison_reference_rotation_text({"reference_spins_per_1000y": 70}),
        )
        self.assertEqual(
            [["123", "테스트 한국어", "テスト"], ["라쿠엔", "설치 없음", "設置なし(설치 없음)"]],
            store_comparison_name_rows(rows),
        )
        self.assertEqual("동일 보더 마진", view["comparison_mode_label"])
        self.assertEqual("보더+5 -> 70회/1000엔", view["reference_rotation"])
        self.assertEqual("123 2대/1yen", view["placement_summary"])
        self.assertEqual("70회/1000엔", view["condition_rows"][0][3])
        self.assertEqual("7.00%", view["condition_rows"][0][4])
        self.assertEqual("LT 없음 / 상위 없음", view["condition_rows"][0][11])
        self.assertEqual("설치 없음", view["condition_rows"][1][11])
        self.assertEqual("+500yen", view["money_rows"][0][5])
        self.assertEqual("주의문구", view["money_rows"][0][13])
        self.assertEqual("설치 없음", view["money_rows"][1][13])

    def test_store_comparison_is_documented_as_auxiliary_context(self):
        self.assertIn("기종 스펙", simulation_scope_note())
        self.assertIn("보조 조건", simulation_scope_note())
        self.assertIn("추천 순위가 아니라", store_auxiliary_note())
        self.assertIn("보조 분석", store_auxiliary_note())
        self.assertIn("점포 자체 평가가 아니라", store_comparison_assumption_text("border_margin"))

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


if __name__ == "__main__":
    unittest.main()
