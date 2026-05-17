import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SIM_DIR = ROOT / "pachinko-sim"
sys.path.insert(0, str(SIM_DIR))

from machines import MACHINES  # noqa: E402
from result_table_builders import ball_graph_rows, hit_event_rows, single_summary_rows  # noqa: E402


class ResultTableBuilderTests(unittest.TestCase):
    def test_single_summary_rows_include_balance_and_non_lt_markers(self):
        machine = MACHINES["sea_5"]
        result = {
            "budget": 1000,
            "first_hit_spin": None,
            "first_hit_total_spins": None,
            "observed_spins_per_1000y": 68.4,
            "start_probability": 0.0684,
            "session_policy": "fixed_spin_cap",
            "strategy_label": "노룰",
            "cash_spent": 1000,
            "final_remaining_value": 0,
            "unused_cash": 0,
            "final_money": 0,
            "cash_budget_exhausted": True,
            "post_budget_play_minutes": 0.0,
            "funds_exhausted_triggered": True,
            "soft_stop_minutes": 540,
            "session_time_limit_minutes": 660,
            "cash_input_cutoff_minutes": 540,
            "soft_stop_triggered": False,
            "time_limit_triggered": False,
            "cash_input_cutoff_triggered": False,
            "time_assumptions": {"profile_name": "sea_classic"},
            "play_minutes": 14.0,
            "cashless_play_minutes": 0.0,
            "cashless_play_share": 0.0,
            "normal_play_minutes": 14.0,
            "right_play_minutes": 0.0,
            "hit_effect_minutes": 0.0,
            "reserve_wait_minutes": 0.0,
            "total_hits": 0,
            "max_streak": 0,
            "experienced_rush": False,
            "rush_entries": 0,
            "lt_entries": 0,
            "upper_entries": 0,
            "total_out_balls": 0,
            "final_balls": 0,
            "locked_balls": 0,
            "net_profit": -1000,
            "installed_full_name_ko": "P 대해물어5",
            "installed_full_name_ja": "P大海物語5",
            "placement_summary": "테스트 배치",
        }

        rows = single_summary_rows("테스트점", machine, result, 70)
        row_map = {row[0]: row[1:] for row in rows}

        self.assertEqual(["테스트점"], row_map["매장"])
        self.assertEqual(["P 대해물어5"], row_map["실설치명(한국어)"])
        self.assertIn("미사용 0yen", row_map["최종 잔류액"][0])
        self.assertIn("해당없음", row_map["RUSH / LT 진입"][0])
        self.assertEqual(["해당없음"], row_map["상위RUSH 진입"])

    def test_hit_event_and_graph_rows_format_runtime_events(self):
        events = [
            {
                "hit_no": 1,
                "label": "初当り",
                "normal_spins": 42,
                "right_spins": 0,
                "state_before": "NORMAL",
                "state_after": "ST",
                "probability_denominator": 99.9,
                "payout_balls": 400,
                "streak": 1,
                "rush_entry": True,
                "lt_entry": False,
                "upper_entry": False,
                "bank_balls_after": 400,
            },
            {
                "hit_no": 2,
                "label": "右打ち",
                "normal_spins": 0,
                "right_spins": 12,
                "state_before": "ST",
                "state_after": "LT",
                "probability_denominator": 19.9,
                "payout_balls": 1000,
                "streak": 2,
                "rush_entry": False,
                "lt_entry": True,
                "upper_entry": True,
                "bank_balls_after": 1400,
            },
        ]

        event_rows = hit_event_rows(events)
        graph_rows = ball_graph_rows(events)

        self.assertIn("RUSH/ST 진입", event_rows[0][-1])
        self.assertIn("LT 진입", event_rows[1][-1])
        self.assertIn("상위RUSH 진입", event_rows[1][-1])
        self.assertEqual("1,400발", graph_rows[1][1])
        self.assertTrue(graph_rows[1][2])


if __name__ == "__main__":
    unittest.main()
