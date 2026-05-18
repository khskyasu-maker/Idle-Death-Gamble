from typing import Any, Dict, List

from machines import Machine
from result_formatting import minutes_text, pct, yen
from result_metrics import calculate_metrics
from result_output_helpers import (
    border_delta,
    lt_rate_text,
    operating_warning,
    relative_score,
    rotation_condition_text,
    rotation_display_text,
    upper_rate_text,
)


def strategy_result_tables(machine: Machine, matrix_results: List[Dict[str, Any]], iterations: int) -> Dict[str, List[List[Any]]]:
    ranked = []
    core_rows = []
    condition_rows = []
    for mr in matrix_results:
        metrics = calculate_metrics(mr["results"], iterations)
        border_spins = mr.get("border_spins_per_1000yen")
        score = relative_score(metrics, mr["budget"], machine.confidence, mr["spins_per_1000y"], border_spins)
        ranked.append((score, mr, metrics))
        strategy_label = mr.get("strategy_label", mr["strategy"])
        rotation_display = rotation_display_text(mr)
        warning = operating_warning(machine.confidence, mr["spins_per_1000y"], border_spins)
        core_rows.append([
            strategy_label,
            rotation_display,
            f"{score:.2f}",
            pct(metrics["positive_close_rate"]),
            minutes_text(metrics["avg_play_minutes"]),
            yen(metrics["avg_profit"], signed=True),
            yen(metrics["median_profit"], signed=True),
            yen(metrics["worst_10_profit"], signed=True),
            pct(metrics["ruin_rate"]),
            pct(metrics["rush_rate"]),
            lt_rate_text(machine, metrics),
            upper_rate_text(machine, metrics),
        ])
        condition_rows.append([
            strategy_label,
            rotation_display,
            border_delta(mr["spins_per_1000y"], border_spins),
            rotation_condition_text(mr["spins_per_1000y"], border_spins),
            warning or "-",
            f"{metrics['max_hits']}회/{metrics['max_streak_seen']}연",
            pct(metrics["recovery_50_rate"]),
            pct(metrics["recovery_80_rate"]),
            pct(metrics["recovery_100_rate"]),
            metrics["profit_condition_summary"],
            pct(metrics["profit_lock_trigger_rate"]),
            pct(metrics["stop_loss_trigger_rate"]),
        ])

    top_rows = []
    for rank, (score, mr, metrics) in enumerate(sorted(ranked, key=lambda row: row[0], reverse=True)[:5], 1):
        warning = operating_warning(machine.confidence, mr["spins_per_1000y"], mr.get("border_spins_per_1000yen"))
        strategy_label = mr.get("strategy_label", mr["strategy"])
        top_rows.append([
            rank,
            strategy_label,
            rotation_display_text(mr),
            f"{score:.2f}",
            pct(metrics["positive_close_rate"]),
            yen(metrics["avg_profit"], signed=True),
            yen(metrics["worst_10_profit"], signed=True),
            border_delta(mr["spins_per_1000y"], mr.get("border_spins_per_1000yen")),
            warning or "-",
        ])
    return {"core": core_rows, "condition": condition_rows, "top": top_rows}


__all__ = ["strategy_result_tables"]
