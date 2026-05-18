from typing import Any, Dict, List

from machines import Machine
from model_checks import theoretical_hit_rate
from result_formatting import minutes_text, pct, yen
from result_metrics import calculate_metrics
from result_model_helpers import benchmark_judgement, benchmark_model_value, format_benchmark_value, value_diff
from result_output_helpers import (
    bilingual_ja_ko,
    border_label,
    cash_burn_text,
    lt_rate_text,
    observed_spin_rate_text,
    probability_text,
    remaining_value_text,
    spin_capacity_text,
    stay_rate_text,
    theoretical_no_hit_rate_from_results,
    true_spin_rate_text,
    upper_rate_text,
)
from session_limits import SESSION_TIME_LIMIT_HOURS
from spec_benchmarks import PUBLIC_BENCHMARKS


def model_profile_intro_rows(
    machine: Machine,
    first_row: Dict[str, Any],
    first_metrics: Dict[str, Any],
) -> List[List[Any]]:
    first_result = first_row["results"][0] if first_row.get("results") else {}
    time_assumptions = first_result.get("time_assumptions", {})
    lend_rate = first_result.get("lend_rate", 1.0)
    rented_balls = int(1000 / lend_rate) if lend_rate else 0
    base_return_rate = max(
        0.0,
        min(0.90, float(time_assumptions.get("normal_base_return_rate", 0.0) or 0.0)),
    )
    gross_balls_per_1000y = rented_balls / max(0.10, 1.0 - base_return_rate) if lend_rate else 0.0
    spins_per_1000y = first_row["spins_per_1000y"]
    border_spins = first_row.get("border_spins_per_1000yen")
    one_k_hit = theoretical_hit_rate(machine.normal_prob, spins_per_1000y)
    one_k_no_hit = theoretical_no_hit_rate_from_results(machine.normal_prob, first_row["results"])
    one_k_hit_with_variance = 100.0 - one_k_no_hit
    return [
        ["대여 구슬", f"{rented_balls:,}발", f"{lend_rate:.3f}엔/발 기준"],
        ["ベース(반환)", f"{base_return_rate * 100:.0f}%", "통상시 반환구슬을 감안한 체류시간 보정값"],
        ["총 발사 추정", f"{gross_balls_per_1000y:.0f}발", "표시 회전수의 순소모 구슬을 실제 발사구슬로 환산"],
        ["입력 회전수", f"{spins_per_1000y}회/1000엔", "현장 1000엔 테스트 입력값"],
        ["헤소 입상", f"{first_metrics['start_probability'] * 100:.2f}%/발", "구슬 1발이 헤소에 들어가 회전이 생기는 확률"],
        ["다이 품질", true_spin_rate_text(first_metrics), "釘(못)/風車(풍차)/ステージ(스테이지) 등을 회전율 분포로 근사"],
        ["입상 표본", observed_spin_rate_text(first_metrics), "같은 다이라도 1000엔마다 고정 회전이 아니라 표본 변동"],
        ["입력회전 당첨", pct(one_k_hit), f"{probability_text(machine.normal_prob)}에서 입력 {spins_per_1000y}회 고정 기준"],
        ["표본회전 당첨", pct(one_k_hit_with_variance), "다이 품질/헤소 입상 표본 변동 반영"],
        ["표본회전 무당첨", pct(one_k_no_hit), "회전 변동까지 반영한 1000엔 무당첨 확률"],
        ["보더 대비", border_label(spins_per_1000y, border_spins), "1엔/1.111엔 혼동 방지"],
    ]


def model_profile_result_tables(machine: Machine, matrix_results: List[Dict[str, Any]], iterations: int) -> Dict[str, List[List[Any]]]:
    tables = {"feel": [], "time": [], "stay": []}
    for mr in matrix_results:
        budget = mr["budget"]
        metrics = calculate_metrics(mr["results"], iterations)
        theory_hit = 100.0 - theoretical_no_hit_rate_from_results(machine.normal_prob, mr["results"])
        tables["feel"].append(
            [
                yen(budget),
                spin_capacity_text(metrics),
                f"{theory_hit:.1f}%",
                pct(metrics["hit_rate"]),
                f"{metrics['avg_first_hit']}회",
                f"{metrics['median_first_hit']}/{metrics['p90_first_hit']}회",
                f"{metrics['median_first_hit_total_spins']}/{metrics['p90_first_hit_total_spins']}회",
                f"{metrics['avg_hits']:.2f}회",
                f"{metrics['avg_after_first_hits']:.2f}회",
                f"{metrics['avg_streak']:.2f}연",
                f"{metrics['avg_right_spins']}회",
                pct(metrics["rush_rate"]),
                lt_rate_text(machine, metrics),
                upper_rate_text(machine, metrics),
                metrics["profit_condition_summary"],
                yen(metrics["median_profit"], signed=True),
                yen(metrics["worst_10_profit"], signed=True),
            ]
        )
        tables["time"].append(
            [
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
            ]
        )
        tables["stay"].append(
            [
                yen(budget),
                stay_rate_text(metrics, 1),
                stay_rate_text(metrics, 2),
                stay_rate_text(metrics, 3),
                stay_rate_text(metrics, 4),
                stay_rate_text(metrics, 6),
                stay_rate_text(metrics, 8),
                stay_rate_text(metrics, SESSION_TIME_LIMIT_HOURS),
                remaining_value_text(metrics),
            ]
        )
    return tables


def benchmark_rows(machine: Machine) -> List[List[Any]]:
    rows = []
    for benchmark in PUBLIC_BENCHMARKS.get(machine.id, []):
        model_value = benchmark_model_value(machine, benchmark)
        public_value = float(benchmark["public"])
        diff = value_diff(model_value, public_value)
        unit = benchmark["unit"]
        diff_text = f"{diff:+.1f}" if unit == "denom" else f"{diff:+.1f}pt"
        rows.append(
            [
                bilingual_ja_ko(benchmark["label_ja"], benchmark["label_ko"]),
                format_benchmark_value(public_value, unit),
                format_benchmark_value(model_value, unit),
                diff_text,
                benchmark_judgement(diff, unit),
                benchmark.get("source", "-"),
            ]
        )
    return rows


__all__ = ["benchmark_rows", "model_profile_intro_rows", "model_profile_result_tables"]
