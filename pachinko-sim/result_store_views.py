from typing import Any, Callable, Dict, List

from machines import Machine
from result_formatting import lend_rate_text, minutes_text, pct, spins_text, yen
from session_limits import SESSION_TIME_LIMIT_HOURS


MetricsFn = Callable[[List[Dict[str, Any]], int], Dict[str, Any]]
WarningFn = Callable[[str, Any, Any], str]
NoHitFn = Callable[[float, List[Dict[str, Any]]], float]
TextFn = Callable[[Any, Any], str]
RateTextFn = Callable[[Machine, Dict[str, Any]], str]
StayRateFn = Callable[[Dict[str, Any], int], str]


def store_comparison_assumption_text(mode: str) -> str:
    if mode == "ball_quality":
        return (
            "같은 구슬 1발당 헤소 입상 확률을 유지합니다. "
            "1.111엔은 1000엔당 대여 구슬이 적으므로 같은 못 상태라면 입력 회전수가 낮게 보입니다."
        )
    if mode == "border_margin":
        return (
            "각 가게의 기종별 보더 대비 같은 +/- 회전수를 적용합니다. "
            "레이트와 보더가 다른 점포를 손익분기 기준으로 맞춰 보는 비교입니다."
        )
    return (
        "각 가게에서 실제로 1000엔당 같은 회전수를 확인했다고 보는 비교입니다. "
        "1.111엔에서 같은 회전수가 나오면 구슬 1발당 헤소 입상 품질은 더 높은 조건입니다."
    )


def store_comparison_reference_rotation_text(first_row: Dict[str, Any]) -> str:
    reference_rotation = f"{spins_text(first_row.get('reference_spins_per_1000y'))}/1000엔"
    if first_row.get("reference_rotation_label"):
        return f"{first_row['reference_rotation_label']} -> {reference_rotation}"
    return reference_rotation


def store_comparison_placement_summary(comparison_results: List[Dict[str, Any]]) -> str:
    placement_summary = ""
    for row in comparison_results:
        placement_summary = row.get("placement_summary") or placement_summary
    return placement_summary


def store_comparison_name_rows(comparison_results: List[Dict[str, Any]]) -> List[List[Any]]:
    name_rows = []
    for row in comparison_results:
        if not row.get("installed"):
            name_rows.append([row.get("store_short_label", "-"), "설치 없음", "設置なし(설치 없음)"])
            continue
        name_rows.append(
            [
                row.get("store_short_label", "-"),
                row.get("installed_full_name_ko", "-"),
                row.get("installed_full_name_ja", "-"),
            ]
        )
    return name_rows


def build_store_comparison_view(
    machine: Machine,
    comparison_results: List[Dict[str, Any]],
    iterations: int,
    calculate_metrics_fn: MetricsFn,
    operating_warning_fn: WarningFn,
    theoretical_no_hit_rate_from_results_fn: NoHitFn,
    border_delta_fn: TextFn,
    rotation_condition_text_fn: TextFn,
    lt_rate_text_fn: RateTextFn,
    upper_rate_text_fn: RateTextFn,
    stay_rate_text_fn: StayRateFn,
) -> Dict[str, Any]:
    first_row = comparison_results[0]
    condition_rows = []
    money_rows = []

    for row in comparison_results:
        store_label = row.get("store_short_label", row.get("store_name", "-"))
        rate = lend_rate_text(row.get("rental_rate", 0.0))
        count_text = f"{row.get('count', 0)}대" if row.get("installed") else "설치없음"

        if not row.get("installed"):
            condition_rows.append([store_label, rate, count_text, "-", "-", "-", "-", "-", "-", "-", "-", "설치 없음"])
            money_rows.append([store_label, "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "설치 없음"])
            continue

        metrics = calculate_metrics_fn(row["results"], iterations)
        spins = row.get("spins_per_1000y")
        border_spins = row.get("border_spins_per_1000yen")
        warning = operating_warning_fn(machine.confidence, spins, border_spins)
        theory_no_hit = theoretical_no_hit_rate_from_results_fn(machine.normal_prob, row["results"])

        condition_rows.append(
            [
                store_label,
                rate,
                count_text,
                f"{spins_text(spins)}/1000엔",
                f"{row.get('start_probability', 0.0) * 100:.2f}%",
                border_delta_fn(spins, border_spins),
                rotation_condition_text_fn(spins, border_spins),
                pct(metrics["hit_rate"]),
                pct(metrics["ruin_rate"]),
                f"{theory_no_hit:.1f}%",
                pct(metrics["rush_rate"]),
                f"{lt_rate_text_fn(machine, metrics)} / {upper_rate_text_fn(machine, metrics)}",
            ]
        )
        money_rows.append(
            [
                store_label,
                pct(metrics["positive_close_rate"]),
                minutes_text(metrics["avg_play_minutes"]),
                stay_rate_text_fn(metrics, SESSION_TIME_LIMIT_HOURS),
                yen(metrics["avg_final_remaining_value"]),
                yen(metrics["avg_profit"], signed=True),
                yen(metrics["median_profit"], signed=True),
                yen(metrics["worst_10_profit"], signed=True),
                yen(metrics["top_10_profit"], signed=True),
                pct(metrics["recovery_80_rate"]),
                f"{metrics['avg_first_hit']}회",
                f"{metrics['avg_hits']:.2f}회/{metrics['avg_streak']:.2f}연",
                metrics["profit_condition_summary"],
                warning or "-",
            ]
        )

    return {
        "comparison_mode_label": first_row.get("comparison_mode_label", "-"),
        "comparison_mode": first_row.get("comparison_mode", ""),
        "assumption_text": store_comparison_assumption_text(first_row.get("comparison_mode", "")),
        "reference_rotation": store_comparison_reference_rotation_text(first_row),
        "budget": first_row.get("budget", 0),
        "strategy_label": first_row.get("strategy_label", "-"),
        "session_policy_label": first_row.get("session_policy_label", "-"),
        "placement_summary": store_comparison_placement_summary(comparison_results),
        "name_rows": store_comparison_name_rows(comparison_results),
        "condition_rows": condition_rows,
        "money_rows": money_rows,
    }
