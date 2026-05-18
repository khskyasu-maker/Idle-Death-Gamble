from typing import Any, Dict, List

from machines import Machine
from result_formatting import minutes_text, pct, yen
from result_metrics import calculate_metrics
from result_output_helpers import (
    border_delta,
    cash_burn_text,
    lt_rate_text,
    operating_warning,
    rotation_condition_text,
    rotation_display_text,
    spin_capacity_text,
    stay_rate_text,
    theoretical_no_hit_rate_from_results,
    upper_rate_text,
)
from session_limits import SESSION_TIME_LIMIT_HOURS


def matrix_result_rows(machine: Machine, matrix_results: List[Dict[str, Any]], iterations: int) -> Dict[str, List[List[Any]]]:
    summary_rows = []
    risk_rows = []
    for mr in matrix_results:
        spins = mr["spins_per_1000y"]
        rotation_display = rotation_display_text(mr)
        metrics = calculate_metrics(mr["results"], iterations)
        border_spins = mr.get("border_spins_per_1000yen")
        warning = operating_warning(machine.confidence, spins, border_spins)
        theory_no_hit = theoretical_no_hit_rate_from_results(machine.normal_prob, mr["results"])
        summary_rows.append([
            rotation_display,
            spin_capacity_text(metrics),
            minutes_text(metrics["avg_play_minutes"]),
            border_delta(spins, border_spins),
            rotation_condition_text(spins, border_spins),
            pct(metrics["positive_close_rate"]),
            yen(metrics["avg_profit"], signed=True),
            yen(metrics["median_profit"], signed=True),
            yen(metrics["worst_10_profit"], signed=True),
            yen(metrics["top_10_profit"], signed=True),
            metrics["profit_condition_summary"],
            warning or "-",
        ])
        risk_rows.append([
            rotation_display,
            pct(metrics["hit_rate"]),
            pct(metrics["ruin_rate"]),
            f"{theory_no_hit:.1f}%",
            pct(metrics["rush_rate"]),
            lt_rate_text(machine, metrics),
            upper_rate_text(machine, metrics),
            f"{pct(metrics['recovery_50_rate'])}/{pct(metrics['recovery_80_rate'])}/{pct(metrics['recovery_100_rate'])}",
            f"{metrics['max_hits']}회/{metrics['max_streak_seen']}연",
            f"{metrics['p90_hits']}회/{metrics['p90_streak']}연",
        ])
    return {"summary": summary_rows, "risk": risk_rows}


def budget_result_tables(machine: Machine, matrix_results: List[Dict[str, Any]], iterations: int) -> Dict[str, List[List[Any]]]:
    tables = {
        "money": [],
        "risk": [],
        "time": [],
        "stay": [],
        "remaining": [],
        "stats": [],
    }
    for mr in matrix_results:
        budget = mr["budget"]
        spins = mr["spins_per_1000y"]
        border_spins = mr.get("border_spins_per_1000yen")
        metrics = calculate_metrics(mr["results"], iterations)
        theory_no_hit = theoretical_no_hit_rate_from_results(machine.normal_prob, mr["results"])
        tables["money"].append([
            yen(budget),
            spin_capacity_text(metrics),
            metrics["avg_spins"],
            rotation_condition_text(spins, border_spins),
            pct(metrics["positive_close_rate"]),
            yen(metrics["avg_profit"], signed=True),
            yen(metrics["median_profit"], signed=True),
            yen(metrics["worst_10_profit"], signed=True),
            yen(metrics["top_10_profit"], signed=True),
            metrics["profit_condition_summary"],
            yen(metrics["avg_cash_spent"]),
        ])
        tables["risk"].append([
            yen(budget),
            pct(metrics["hit_rate"]),
            pct(metrics["ruin_rate"]),
            f"{theory_no_hit:.1f}%",
            pct(metrics["rush_rate"]),
            lt_rate_text(machine, metrics),
            upper_rate_text(machine, metrics),
            f"{pct(metrics['recovery_50_rate'])}/{pct(metrics['recovery_80_rate'])}/{pct(metrics['recovery_100_rate'])}",
            f"{metrics['max_hits']}회/{metrics['max_streak_seen']}연",
        ])
        tables["time"].append([
            yen(budget),
            minutes_text(metrics["avg_play_minutes"]),
            f"{minutes_text(metrics['median_play_minutes'])}/{minutes_text(metrics['p90_play_minutes'])}",
            minutes_text(metrics["avg_cashless_play_minutes"]),
            f"{metrics['avg_cashless_play_share']:.1f}%",
            minutes_text(metrics["avg_post_budget_play_minutes"]),
            minutes_text(metrics["avg_normal_play_minutes"]),
            minutes_text(metrics["avg_right_play_minutes"]),
            minutes_text(metrics["avg_hit_effect_minutes"]),
            minutes_text(metrics["avg_reserve_wait_minutes"]),
            cash_burn_text(metrics),
        ])
        tables["stay"].append([
            yen(budget),
            stay_rate_text(metrics, 1),
            stay_rate_text(metrics, 2),
            stay_rate_text(metrics, 3),
            stay_rate_text(metrics, 4),
            stay_rate_text(metrics, 6),
            stay_rate_text(metrics, 8),
            stay_rate_text(metrics, SESSION_TIME_LIMIT_HOURS),
            pct(metrics["time_limit_stop_rate"]),
            pct(metrics["hard_time_limit_stop_rate"]),
            pct(metrics["cash_input_cutoff_rate"]),
        ])
        tables["remaining"].append([
            yen(budget),
            pct(metrics["budget_exhausted_rate"]),
            yen(metrics["avg_unused_cash"]),
            yen(metrics["avg_final_money"]),
            yen(metrics["avg_final_remaining_value"]),
            f"{yen(metrics['p10_final_remaining_value'])}/{yen(metrics['median_final_remaining_value'])}/{yen(metrics['p90_final_remaining_value'])}",
            yen(metrics["avg_final_remaining_balance"], signed=True),
            pct(metrics["funds_exhausted_stop_rate"]),
        ])
        tables["stats"].append([
            yen(budget),
            yen(metrics["avg_profit_standard_error"]),
            f"{yen(metrics['avg_profit_ci_low'], signed=True)}~{yen(metrics['avg_profit_ci_high'], signed=True)}",
            f"{yen(metrics['median_profit_ci_low'], signed=True)}~{yen(metrics['median_profit_ci_high'], signed=True)}",
            f"{yen(metrics['worst_10_profit_ci_low'], signed=True)}~{yen(metrics['worst_10_profit_ci_high'], signed=True)}",
            yen(metrics["cvar_10_profit"], signed=True),
            f"{yen(metrics['top_10_profit_ci_low'], signed=True)}~{yen(metrics['top_10_profit_ci_high'], signed=True)}",
        ])
    return tables


__all__ = ["budget_result_tables", "matrix_result_rows"]
