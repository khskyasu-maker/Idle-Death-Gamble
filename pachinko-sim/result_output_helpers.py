import statistics
from typing import Any, Dict, List

from machine_traits import machine_has_lt, machine_has_upper
from machines import Machine
from model_checks import theoretical_hit_rate, theoretical_no_hit_rate
from result_formatting import build_ascii_table, format_ci, minutes_text, pct, spins_text, yen
from rotation import (
    LOW_ABSOLUTE_SPIN_WARNING,
    border_adjustment as rotation_border_adjustment,
    border_delta_text,
    border_label as rotation_border_label,
    border_margin,
    border_ratio_text,
    rotation_reality_label,
)
from sim_terms import annotate_japanese_terms


def confidence_weight(confidence: str) -> float:
    return {
        "high": 1.0,
        "medium": 0.6,
        "low": 0.15,
    }.get(confidence, 0.5)


def border_adjustment(spins_per_1000y=None, border_spins_per_1000y=None) -> float:
    return rotation_border_adjustment(spins_per_1000y, border_spins_per_1000y)


def border_label(spins_per_1000y=None, border_spins_per_1000y=None) -> str:
    return rotation_border_label(spins_per_1000y, border_spins_per_1000y)


def bilingual_ja_ko(label_ja: str, label_ko: str) -> str:
    return f"{label_ja}({label_ko})"


def probability_text(denominator: float) -> str:
    return f"1/{denominator:.1f}"


def denominator_tail_rows(machine: Machine) -> List[List[Any]]:
    rows = []
    for multiplier in [1, 2, 3, 5]:
        spins = int(round(machine.normal_prob * multiplier))
        rows.append(
            [
                f"분모 {multiplier}배",
                f"{spins}회",
                pct(theoretical_no_hit_rate(machine.normal_prob, spins)),
                pct(theoretical_hit_rate(machine.normal_prob, spins)),
                "매회 독립 시행이라 이전 실패가 다음 확률을 올리지 않음",
            ]
        )
    return rows


def value_diff(actual: float, expected: float) -> float:
    return actual - expected


def format_benchmark_value(value: float, unit: str) -> str:
    if unit == "denom":
        return probability_text(value)
    if unit == "pct":
        return pct(value)
    return f"{value:.1f}"


def benchmark_judgement(diff: float, unit: str) -> str:
    tolerance = 0.2 if unit == "denom" else 1.5
    soft_tolerance = 0.5 if unit == "denom" else 3.0
    abs_diff = abs(diff)
    if abs_diff <= tolerance:
        return "OK"
    if abs_diff <= soft_tolerance:
        return "근접"
    return "확인 필요"


def distribution_state_weight(distribution, states: List[str]) -> float:
    return sum(p.weight for p in distribution if p.next_state in states) * 100.0


def distribution_balls_weight(distribution, balls: int) -> float:
    return sum(p.weight for p in distribution if p.balls == balls) * 100.0


def distribution_jitan_spin_weight(distribution, spins: int) -> float:
    return sum(p.weight for p in distribution if p.jitan_spins == spins) * 100.0


def normal_counted_rush_weight(machine: Machine) -> float:
    return sum(p.weight for p in machine.normal_hit_dist if p.counts_as_rush) * 100.0


def normal_rush_with_jitan(machine: Machine, rush_states: List[str]) -> float:
    direct = 0.0
    jitan_return = 0.0
    for payout in machine.normal_hit_dist:
        if payout.next_state in rush_states:
            direct += payout.weight
        elif payout.next_state == "JITAN" and payout.jitan_spins > 0:
            jitan_return += payout.weight * (theoretical_hit_rate(machine.normal_prob, payout.jitan_spins) / 100.0)
    return (direct + jitan_return) * 100.0


def rush_combo_hit_chance(machine: Machine) -> float:
    if not machine.st_hit_dist:
        return 0.0
    payout = machine.st_hit_dist[0]
    high_miss = (1.0 - (1.0 / machine.high_prob)) ** max(0, payout.st_spins)
    normal_miss = (1.0 - (1.0 / machine.normal_prob)) ** max(0, payout.jitan_spins)
    return (1.0 - (high_miss * normal_miss)) * 100.0


def st_lt_event_weight(machine: Machine) -> float:
    return sum(p.weight for p in machine.st_hit_dist if p.is_lt) * 100.0


def fall_state_continue_chance(machine: Machine, state: str) -> float:
    fall_denominator = machine.fall_prob.get(state)
    if not fall_denominator:
        return 0.0
    hit_probability = 1.0 / machine.high_prob
    fall_only_probability = (1.0 - hit_probability) * (1.0 / fall_denominator)
    denominator = hit_probability + fall_only_probability
    if denominator <= 0:
        return 0.0

    hit_before_fall = hit_probability / denominator
    fall_before_hit = fall_only_probability / denominator
    reserve_spins = max(0, int(machine.fall_reserve_spins.get(state, 0)))
    reserve_hit = 1.0 - ((1.0 - hit_probability) ** reserve_spins)
    return (hit_before_fall + (fall_before_hit * reserve_hit)) * 100.0


def benchmark_model_value(machine: Machine, benchmark: Dict[str, Any]) -> float:
    metric = benchmark["metric"]
    if metric == "normal_prob":
        return machine.normal_prob
    if metric == "high_prob":
        return machine.high_prob
    if metric == "normal_support_prob":
        return machine.normal_support_prob
    if metric == "normal_hit_chance":
        return theoretical_hit_rate(machine.normal_prob, benchmark["spins"])
    if metric == "high_hit_chance":
        return theoretical_hit_rate(machine.high_prob, benchmark["spins"])
    if metric == "normal_state_weight":
        return distribution_state_weight(machine.normal_hit_dist, benchmark["states"])
    if metric == "st_state_weight":
        return distribution_state_weight(machine.st_hit_dist, benchmark["states"])
    if metric == "normal_balls_weight":
        return distribution_balls_weight(machine.normal_hit_dist, benchmark["balls"])
    if metric == "st_balls_weight":
        return distribution_balls_weight(machine.st_hit_dist, benchmark["balls"])
    if metric == "normal_support_spin_weight":
        return distribution_jitan_spin_weight(machine.normal_support_dist, benchmark["spins"])
    if metric == "normal_counted_rush_weight":
        return normal_counted_rush_weight(machine)
    if metric == "normal_rush_with_jitan":
        return normal_rush_with_jitan(machine, benchmark["rush_states"])
    if metric == "rush_combo_hit_chance":
        return rush_combo_hit_chance(machine)
    if metric == "st_lt_event_weight":
        return st_lt_event_weight(machine)
    if metric == "fall_state_continue_chance":
        return fall_state_continue_chance(machine, benchmark["state"])
    return 0.0


def relative_score(metrics: Dict[str, Any], budget: int, confidence: str, spins_per_1000y=None, border_spins_per_1000y=None) -> float:
    """평균 차액 하나가 아니라 수익 가능성과 방어력을 함께 보는 비교용 점수."""
    plus = metrics["positive_close_rate"] / 100.0
    avg_component = max(0.0, min(1.0, (metrics["avg_profit"] + budget) / (budget * 2)))
    defense = max(0.0, min(1.0, (metrics["worst_10_profit"] + budget) / budget))
    hit = metrics["hit_rate"] / 100.0
    conf = confidence_weight(confidence)
    score = (plus * 35) + (avg_component * 25) + (defense * 20) + (hit * 10) + (conf * 10)
    score += border_adjustment(spins_per_1000y, border_spins_per_1000y)
    if (
        border_spins_per_1000y is None
        and spins_per_1000y is not None
        and spins_per_1000y < LOW_ABSOLUTE_SPIN_WARNING
    ):
        score = min(score, 35.0)
    if border_spins_per_1000y is not None and spins_per_1000y is not None and spins_per_1000y < border_spins_per_1000y:
        score = min(score, 45.0)
    if confidence == "low":
        score = min(score, 55.0)
    elif confidence == "medium":
        score = min(score, 82.0)
    return round(max(0.0, min(100.0, score)), 2)


def operating_warning(confidence: str, spins_per_1000y=None, border_spins_per_1000y=None) -> str:
    warnings = []
    if confidence == "low":
        warnings.append("참고용")
    elif confidence == "medium":
        warnings.append("스펙검증")
    margin = border_margin(spins_per_1000y, border_spins_per_1000y)
    if border_spins_per_1000y is None and spins_per_1000y is not None and spins_per_1000y < LOW_ABSOLUTE_SPIN_WARNING:
        warnings.append("70회미만 제외")
    if margin is not None and margin < -5:
        warnings.append("보더미만")
    elif margin is not None and margin < 0:
        warnings.append("보더부족")
    return " / ".join(warnings)


def profit_condition_table_rows(metrics: Dict[str, Any]) -> List[List[Any]]:
    rows = []
    for row in metrics.get("profit_condition_rows", []):
        rows.append(
            [
                row["label"],
                f"{row['sample_count']}회 / {pct(row['occurrence_rate'])}",
                pct(row["positive_rate"]),
                format_ci(row["positive_rate_ci_low"], row["positive_rate_ci_high"]),
                yen(row["median_profit"], signed=True),
                yen(row["avg_profit"], signed=True),
                row["judgement"],
            ]
        )
    return rows


def theoretical_no_hit_rate_from_results(probability_denominator: float, results: List[Dict[str, Any]]) -> float:
    if probability_denominator <= 1 or not results:
        return 0.0
    miss_probability = 1.0 - (1.0 / probability_denominator)
    capacities = [
        max(0, int(r.get("total_spins_possible", 0) or 0))
        for r in results
    ]
    if not capacities:
        return 0.0
    return statistics.mean((miss_probability ** capacity) * 100.0 for capacity in capacities)


def session_policy_label_from_results(results: List[Dict[str, Any]]) -> str:
    if not results:
        return ""
    return results[0].get("session_policy_label") or results[0].get("session_policy", "")


def placement_summary_from_results(results: List[Dict[str, Any]]) -> str:
    if not results:
        return ""
    return results[0].get("placement_summary") or ""


def installed_name_ko_from_results(results: List[Dict[str, Any]]) -> str:
    if not results:
        return ""
    return results[0].get("installed_full_name_ko") or results[0].get("installed_full_name_ja") or ""


def installed_name_ja_from_results(results: List[Dict[str, Any]]) -> str:
    if not results:
        return ""
    return results[0].get("installed_full_name_ja") or ""


def print_ascii_table(title: str, headers: List[str], rows: List[List[Any]]):
    print(f"\n[{title}]")
    if not rows:
        print("(표시할 데이터 없음)")
        return
    print(build_ascii_table(headers, rows))


def cash_burn_text(metrics: Dict[str, Any]) -> str:
    per_hour = metrics.get("avg_cash_spend_per_hour", 0)
    per_1000 = metrics.get("avg_play_minutes_per_1000yen_cash", 0)
    return f"{yen(per_hour)}/h / 1000엔당 {per_1000:.1f}분"


def stay_rate_text(metrics: Dict[str, Any], hour: int) -> str:
    return pct(metrics.get("stay_reach_rates", {}).get(hour, 0.0))


def remaining_value_text(metrics: Dict[str, Any]) -> str:
    return (
        f"평균 {yen(metrics.get('avg_final_remaining_value', 0))} / "
        f"중앙 {yen(metrics.get('median_final_remaining_value', 0))}"
    )


def time_profile_text(results: List[Dict[str, Any]]) -> str:
    if not results:
        return "-"
    assumptions = results[0].get("time_assumptions", {})
    profile = assumptions.get("profile_name", "generic")
    note = assumptions.get("source_note", "")
    return f"{profile} ({note})" if note else profile


def ci_pct(metrics: Dict[str, Any], prefix: str) -> str:
    return format_ci(metrics[f"{prefix}_ci_low"], metrics[f"{prefix}_ci_high"])


def border_delta(spins_per_1000y=None, border_spins_per_1000y=None) -> str:
    return border_delta_text(spins_per_1000y, border_spins_per_1000y)


def rotation_condition_text(spins_per_1000y=None, border_spins_per_1000y=None) -> str:
    return (
        f"{rotation_reality_label(spins_per_1000y, border_spins_per_1000y)} / "
        f"{border_ratio_text(spins_per_1000y, border_spins_per_1000y)}"
    )


def rotation_display_text(row: Dict[str, Any]) -> str:
    spins = row.get("spins_per_1000y")
    label = row.get("rotation_label")
    if label:
        return f"{label}({spins_text(spins)})"
    return spins_text(spins)


def spin_capacity_text(metrics: Dict[str, Any]) -> str:
    if metrics.get("start_variance"):
        return (
            f"평균 {metrics['avg_spin_capacity']}회 "
            f"(10~90% {metrics['p10_spin_capacity']}~{metrics['p90_spin_capacity']}회)"
        )
    return f"{metrics['avg_spin_capacity']}회"


def observed_spin_rate_text(metrics: Dict[str, Any]) -> str:
    if metrics.get("start_variance"):
        return (
            f"{metrics['avg_observed_spins_per_1000y']:.1f}회/1000엔 "
            f"(10~90% {metrics['p10_observed_spins_per_1000y']:.1f}~{metrics['p90_observed_spins_per_1000y']:.1f})"
        )
    return f"{metrics['avg_observed_spins_per_1000y']:.1f}회/1000엔"


def true_spin_rate_text(metrics: Dict[str, Any]) -> str:
    if metrics.get("start_variance") and metrics.get("spin_rate_quality_stddev", 0) > 0:
        return (
            f"{metrics['avg_true_spins_per_1000y']:.1f}회/1000엔 "
            f"(10~90% {metrics['p10_true_spins_per_1000y']:.1f}~{metrics['p90_true_spins_per_1000y']:.1f})"
        )
    return f"{metrics['avg_true_spins_per_1000y']:.1f}회/1000엔"


def lt_rate_text(machine: Machine, metrics: Dict[str, Any]) -> str:
    if not machine_has_lt(machine):
        return "해당없음"
    return pct(metrics["lt_success_rate"])


def lt_ci_text(machine: Machine, metrics: Dict[str, Any]) -> str:
    if not machine_has_lt(machine):
        return "비LT 기종"
    return f"95% CI {ci_pct(metrics, 'lt_success_rate')}"


def lt_count_text(machine: Machine, count: float, suffix: str = "회") -> str:
    if not machine_has_lt(machine):
        return "해당없음"
    if isinstance(count, float):
        return f"{count:.2f}{suffix}"
    return f"{count}{suffix}"


def upper_rate_text(machine: Machine, metrics: Dict[str, Any]) -> str:
    if not machine_has_upper(machine):
        return "해당없음"
    return pct(metrics["upper_success_rate"])


def upper_count_text(machine: Machine, count: float, suffix: str = "회") -> str:
    if not machine_has_upper(machine):
        return "해당없음"
    if isinstance(count, float):
        return f"{count:.2f}{suffix}"
    return f"{count}{suffix}"


def print_travel_satisfaction_grade(machine: Machine):
    print("\n[여행 만족도 및 목적 분류]")
    if machine.risk_grade == "1/99":
        print("▶ 1/99 감데지 계열: 연출 감상 / 멘탈 치유 / 오래 놀기용.")
        print("회수 기대가 아니라 흐름을 익히고 적은 예산으로 당첨 체감을 확인하는 용도입니다.")
    elif machine.risk_grade in ["1/129", "1/199"]:
        print("▶ 1/129 ~ 1/199 라이트/미들 계열: 가벼운 승부용.")
        print("여행 중 1만 엔 내외의 적당한 리스크로 '운이 좋으면 1~2만 발'을 노려보는 타협점입니다.")
    elif machine.risk_grade == "1/319":
        print("▶ 1/319 미들 계열: 승부/대박 체험용.")
        print("1만 엔 전액 투입 시 무당첨 증발 리스크가 매우 큽니다. 여행 기분을 망치지 않으려면 예산을 쪼개거나 멘탈 관리가 필수입니다.")
    elif machine.risk_grade == "1/399":
        print("▶ 1/399 e기 계열: 고위험 짧은 체험용.")
        print("1엔 파친코라도 돈이 녹는 속도가 빠릅니다. 3000엔~5000엔 정도로 '한 번 앉아봤다'에 의의를 두는 것을 권장합니다.")

    print(f"\n모델 신뢰도: {machine.confidence} | 출처: {annotate_japanese_terms(machine.spec_source)}")
    if machine.confidence == "low":
        print("주의: 이 기종은 추정 의존도가 높아 순위/손익 해석을 낮은 신뢰도로 봐야 합니다.")
    print("※ 스펙 단순화 노트:", annotate_japanese_terms(machine.simplification_notes))
    if machine.notes:
        print("※ 모델링 주의:", annotate_japanese_terms(machine.notes))
