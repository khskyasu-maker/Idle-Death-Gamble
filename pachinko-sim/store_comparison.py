from typing import Any, Dict, List

from machines import Machine
from simulator import (
    SESSION_POLICIES,
    STRATEGIES,
    normalize_session_policy,
    normalize_strategy,
    simulate_multiple,
)
from start_gate import rented_balls_per_1000yen, start_probability_from_rate


STORE_COMPARISON_MODES = {
    "cash_rotation": "동일 1000엔 회전수",
    "ball_quality": "동일 헤소 입상 품질",
}


def normalize_store_comparison_mode(mode: str) -> str:
    if mode in STORE_COMPARISON_MODES:
        return mode
    return "cash_rotation"


def equivalent_spins_per_1000yen(
    reference_lend_rate: float,
    target_lend_rate: float,
    reference_spins_per_1000y: float,
) -> float:
    """Keep per-ball start probability fixed while changing the store lend rate."""
    start_probability = start_probability_from_rate(reference_lend_rate, reference_spins_per_1000y)
    target_balls = rented_balls_per_1000yen(target_lend_rate)
    return max(1.0, start_probability * target_balls)


def store_spins_per_1000yen(
    mode: str,
    reference_lend_rate: float,
    target_lend_rate: float,
    reference_spins_per_1000y: float,
) -> float:
    mode = normalize_store_comparison_mode(mode)
    if mode == "ball_quality":
        return equivalent_spins_per_1000yen(
            reference_lend_rate,
            target_lend_rate,
            reference_spins_per_1000y,
        )
    return float(reference_spins_per_1000y)


def add_store_context_to_results(results: List[Dict[str, Any]], context: Dict[str, Any]):
    for result in results:
        result["placement_summary"] = context.get("placement_summary")
        result["placement_detail"] = context.get("placement_detail")
        result["installed_full_name_ja"] = context.get("installed_full_name_ja")
        result["installed_full_name_ko"] = context.get("installed_full_name_ko")
        result["store_id"] = context.get("store_id")
        result["store_name"] = context.get("store_name")
        result["store_short_label"] = context.get("store_short_label")
        result["border_spins_per_1000yen"] = context.get("border_spins_per_1000yen")


def run_store_comparison(
    machine: Machine,
    store_contexts: List[Dict[str, Any]],
    reference_lend_rate: float,
    reference_spins_per_1000y: float,
    budget: int,
    exchange_rate: float,
    iterations: int,
    strategy: str = "no_rule",
    session_policy: str = "fixed_spin_cap",
    comparison_mode: str = "cash_rotation",
    start_variance: bool = True,
    spin_rate_quality_stddev: float = 3.0,
) -> List[Dict[str, Any]]:
    strategy = normalize_strategy(strategy)
    session_policy = normalize_session_policy(session_policy)
    comparison_mode = normalize_store_comparison_mode(comparison_mode)
    rows = []

    for context in store_contexts:
        target_lend_rate = float(context.get("rental_rate", 0.0) or 0.0)
        target_spins = store_spins_per_1000yen(
            comparison_mode,
            reference_lend_rate,
            target_lend_rate,
            reference_spins_per_1000y,
        )

        results = []
        if context.get("installed"):
            results = simulate_multiple(
                machine,
                budget,
                target_lend_rate,
                target_spins,
                exchange_rate,
                iterations,
                strategy=strategy,
                session_policy=session_policy,
                start_variance=start_variance,
                border_spins_per_1000y=context.get("border_spins_per_1000yen"),
                spin_rate_quality_stddev=spin_rate_quality_stddev,
            )
            add_store_context_to_results(results, context)

        rows.append(
            {
                **context,
                "budget": budget,
                "reference_spins_per_1000y": reference_spins_per_1000y,
                "spins_per_1000y": target_spins,
                "reference_lend_rate": reference_lend_rate,
                "comparison_mode": comparison_mode,
                "comparison_mode_label": STORE_COMPARISON_MODES[comparison_mode],
                "strategy": strategy,
                "strategy_label": STRATEGIES[strategy],
                "session_policy": session_policy,
                "session_policy_label": SESSION_POLICIES[session_policy],
                "start_probability": start_probability_from_rate(target_lend_rate, target_spins),
                "results": results,
            }
        )

    return rows
