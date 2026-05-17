import csv
from typing import Any, Callable, Dict, List

from machine_traits import machine_has_lt, machine_has_upper
from machines import Machine
from session_limits import HARD_SESSION_TIME_LIMIT_HOURS, SESSION_TIME_LIMIT_HOURS


CSV_HEADERS = [
    "기종", "예산(엔)", "입력1000엔당회전율", "평균다이품질회전율", "평균관측1000엔당회전율", "가능회전평균", "가능회전P10", "가능회전P90",
    "당첨체험률(%)", "RUSH체험률(%)", "당첨0회확률(%)", "단발종료율(%)", "500발이하종료율(%)", "투자금50%회수율(%)", "투자금80%회수율(%)", "투자금100%회수율(%)", "플러스마감비율(%)",
    "평균차액", "평균차액표준오차", "평균차액표준오차예산비(%)", "평균차액CI방식", "평균차액95CI하한", "평균차액95CI상한",
    "중앙값차액", "중앙값95CI하한", "중앙값95CI상한",
    "하위10%차액", "하위10%95CI하한", "하위10%95CI상한", "CVaR10차액",
    "하위25%차액", "상위10%차액", "상위10%95CI하한", "상위10%95CI상한", "상위10%평균차액",
    "최대손실", "최대이익", "실익조건", "평균당첨횟수", "초당첨평균회전", "초당첨중앙회전", "초당첨P90회전", "초당첨후평균당첨", "당첨세션평균대당첨", "평균RUSH진입", "평균LT진입", "LT진입성공률", "평균상위RUSH진입", "상위RUSH진입성공률", "평균체류분", "중앙체류분", "P90체류분", f"{SESSION_TIME_LIMIT_HOURS}시간도달률", f"{SESSION_TIME_LIMIT_HOURS}시간정리율", f"{HARD_SESSION_TIME_LIMIT_HOURS}시간하드종료율", "현금마감작동률", "평균최종잔류액", "중앙최종잔류액", "최종잔류P10", "최종잔류P90", "예산소진률", "완전소진정지율", "예산소진후지속률", "평균예산소진후체류분", "소진후지속시평균분", "평균현금없는분", "평균무현금비율", "평균보류대기분", "평균현금소모엔시간", "1000엔당평균분", "익절발동률", "손절발동률", "평균최대연속", "평균플레이회전"
]


def matrix_result_csv_row(
    machine: Machine,
    matrix_result: Dict[str, Any],
    iterations: int,
    calculate_metrics_fn: Callable[[List[Dict[str, Any]], int], Dict[str, Any]],
) -> List[Any]:
    budget = matrix_result["budget"]
    spins = matrix_result["spins_per_1000y"]
    metrics = calculate_metrics_fn(matrix_result["results"], iterations)

    return [
        machine.name_ko, budget, spins,
        round(metrics["avg_true_spins_per_1000y"], 1),
        round(metrics["avg_observed_spins_per_1000y"], 1),
        metrics["avg_spin_capacity"],
        metrics["p10_spin_capacity"],
        metrics["p90_spin_capacity"],
        round(metrics["hit_rate"], 1),
        round(metrics["rush_rate"], 1),
        round(metrics["ruin_rate"], 1),
        round(metrics["single_hit_finish_rate"], 1),
        round(metrics["under_500_finish_rate"], 1),
        round(metrics["recovery_50_rate"], 1),
        round(metrics["recovery_80_rate"], 1),
        round(metrics["recovery_100_rate"], 1),
        round(metrics["positive_close_rate"], 1),
        metrics["avg_profit"],
        metrics["avg_profit_standard_error"],
        round(metrics["avg_profit_se_budget_pct"], 3),
        metrics["mean_ci_method"],
        metrics["avg_profit_ci_low"],
        metrics["avg_profit_ci_high"],
        metrics["median_profit"],
        metrics["median_profit_ci_low"],
        metrics["median_profit_ci_high"],
        metrics["worst_10_profit"],
        metrics["worst_10_profit_ci_low"],
        metrics["worst_10_profit_ci_high"],
        metrics["cvar_10_profit"],
        metrics["worst_25_profit"],
        metrics["top_10_profit"],
        metrics["top_10_profit_ci_low"],
        metrics["top_10_profit_ci_high"],
        metrics["upper_tail_10_profit"],
        metrics["min_profit"],
        metrics["max_profit"],
        metrics["profit_condition_summary"],
        round(metrics["avg_hits"], 1),
        metrics["avg_first_hit"],
        metrics["median_first_hit"],
        metrics["p90_first_hit"],
        round(metrics["avg_after_first_hits"], 2),
        round(metrics["avg_hits_when_hit"], 2),
        round(metrics["avg_rush_entries"], 2),
        round(metrics["avg_lt_entries"], 2) if machine_has_lt(machine) else "N/A",
        round(metrics["lt_success_rate"], 1) if machine_has_lt(machine) else "N/A",
        round(metrics["avg_upper_entries"], 2) if machine_has_upper(machine) else "N/A",
        round(metrics["upper_success_rate"], 1) if machine_has_upper(machine) else "N/A",
        round(metrics["avg_play_minutes"], 2),
        round(metrics["median_play_minutes"], 2),
        round(metrics["p90_play_minutes"], 2),
        round(metrics["time_limit_reached_rate"], 1),
        round(metrics["time_limit_stop_rate"], 1),
        round(metrics["hard_time_limit_stop_rate"], 1),
        round(metrics["cash_input_cutoff_rate"], 1),
        metrics["avg_final_remaining_value"],
        metrics["median_final_remaining_value"],
        metrics["p10_final_remaining_value"],
        metrics["p90_final_remaining_value"],
        round(metrics["budget_exhausted_rate"], 1),
        round(metrics["funds_exhausted_stop_rate"], 1),
        round(metrics["post_budget_continue_rate"], 1),
        round(metrics["avg_post_budget_play_minutes"], 2),
        round(metrics["avg_post_budget_play_minutes_when_continued"], 2),
        round(metrics["avg_cashless_play_minutes"], 2),
        round(metrics["avg_cashless_play_share"], 1),
        round(metrics["avg_reserve_wait_minutes"], 2),
        metrics["avg_cash_spend_per_hour"],
        round(metrics["avg_play_minutes_per_1000yen_cash"], 2),
        round(metrics["profit_lock_trigger_rate"], 1),
        round(metrics["stop_loss_trigger_rate"], 1),
        round(metrics["avg_streak"], 1),
        metrics["avg_spins"],
    ]


def save_matrix_to_csv(
    machine: Machine,
    matrix_results: List[Dict[str, Any]],
    iterations: int,
    calculate_metrics_fn: Callable[[List[Dict[str, Any]], int], Dict[str, Any]],
    filepath: str = "results.csv",
) -> None:
    """Write the latest explicitly requested matrix result only.

    The simulator must not accumulate a local play-result history in GitHub.
    `results.csv` is gitignored and overwritten on each explicit save.
    """
    with open(filepath, "w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.writer(handle)
        writer.writerow(CSV_HEADERS)

        for matrix_result in matrix_results:
            writer.writerow(matrix_result_csv_row(machine, matrix_result, iterations, calculate_metrics_fn))
