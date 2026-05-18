from typing import Any, Dict, List

from machines import Machine
from model_checks import theoretical_hit_rate, theoretical_no_hit_rate
from result_formatting import pct


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
    jitan_prob = machine.jitan_prob if machine.jitan_prob > 1 else machine.normal_prob
    for payout in machine.normal_hit_dist:
        if payout.next_state in rush_states:
            direct += payout.weight
        elif payout.next_state == "JITAN" and payout.jitan_spins > 0:
            jitan_return += payout.weight * (theoretical_hit_rate(jitan_prob, payout.jitan_spins) / 100.0)
    return (direct + jitan_return) * 100.0


def rush_combo_hit_chance(machine: Machine) -> float:
    if not machine.st_hit_dist:
        return 0.0
    payout = machine.st_hit_dist[0]
    high_miss = (1.0 - (1.0 / machine.high_prob)) ** max(0, payout.st_spins)
    normal_miss = (1.0 - (1.0 / machine.normal_prob)) ** max(0, payout.jitan_spins)
    return (1.0 - (high_miss * normal_miss)) * 100.0


def upper_combo_hit_chance(machine: Machine) -> float:
    if not machine.upper_hit_dist:
        return 0.0
    payout = machine.upper_hit_dist[0]
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
    if metric == "jitan_prob":
        return machine.jitan_prob if machine.jitan_prob > 1 else machine.normal_prob
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
    if metric == "upper_combo_hit_chance":
        return upper_combo_hit_chance(machine)
    if metric == "st_lt_event_weight":
        return st_lt_event_weight(machine)
    if metric == "fall_state_continue_chance":
        return fall_state_continue_chance(machine, benchmark["state"])
    return 0.0


__all__ = [
    "benchmark_judgement",
    "benchmark_model_value",
    "denominator_tail_rows",
    "distribution_balls_weight",
    "distribution_jitan_spin_weight",
    "distribution_state_weight",
    "fall_state_continue_chance",
    "format_benchmark_value",
    "normal_counted_rush_weight",
    "normal_rush_with_jitan",
    "probability_text",
    "rush_combo_hit_chance",
    "st_lt_event_weight",
    "upper_combo_hit_chance",
    "value_diff",
]
