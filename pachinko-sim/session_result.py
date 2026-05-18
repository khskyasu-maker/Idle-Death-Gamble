from typing import Any, Dict, List

from session_accounting import SESSION_POLICIES, STRATEGIES
from session_setup import SessionStart
from time_model import TimeAssumptions, assumption_dict, minutes


def build_session_result(
    *,
    budget: int,
    session_start: SessionStart,
    stop_loss_spin_threshold: int,
    first_hit_spin: int | None,
    first_hit_total_spins: int | None,
    first_hit_cash_spent: int | None,
    first_hit_play_seconds: float | None,
    total_hits: int,
    max_streak: int,
    total_out_balls: float,
    bank_balls: float,
    locked_balls: float,
    exchange_rate: float,
    lend_rate: float,
    cash_spent: float,
    cash_budget_exhausted_seconds: float | None,
    normal_play_seconds: float,
    active_launch_seconds: float,
    normal_display_seconds: float,
    reserve_wait_seconds: float,
    right_play_seconds: float,
    hit_effect_seconds_total: float,
    support_event_seconds: float,
    cashless_play_seconds: float,
    session_time_limit_minutes: float,
    cash_input_cutoff_minutes: float,
    soft_stop_minutes: float,
    rush_entries: int,
    lt_entries: int,
    upper_entries: int,
    hit_events: List[Dict[str, Any]],
    spins_used: int,
    right_spins: int,
    normal_balls_fired: float,
    normal_net_balls_consumed: float,
    time_assumptions: TimeAssumptions,
    strategy: str,
    spins_per_1000y: int,
    border_spins_per_1000y: float | None,
    spin_rate_min: float | None,
    spin_rate_max: float | None,
    start_variance: bool,
    card_reuse: bool,
    session_policy: str,
    flags: Dict[str, Any],
) -> Dict[str, Any]:
    final_balls = max(0.0, bank_balls + locked_balls)
    final_money = int(final_balls * exchange_rate)
    unused_cash = max(0.0, float(budget) - cash_spent)
    final_remaining_value = int(unused_cash + final_money)
    net_profit = int(final_money - cash_spent)
    exchange_loss = int(final_balls * lend_rate - final_money)
    play_seconds = (
        normal_play_seconds
        + right_play_seconds
        + hit_effect_seconds_total
        + support_event_seconds
    )
    post_budget_play_seconds = (
        max(0.0, play_seconds - cash_budget_exhausted_seconds)
        if cash_budget_exhausted_seconds is not None
        else 0.0
    )
    cashless_share = (
        (cashless_play_seconds / play_seconds) * 100.0
        if play_seconds > 0
        else 0.0
    )

    return {
        "budget": budget,
        "total_spins_possible": session_start.total_spins_possible,
        "expected_total_spins_possible": session_start.expected_total_spins_possible,
        "normal_spin_cap": session_start.normal_spin_cap,
        "stop_loss_probe_yen": session_start.stop_loss_probe_budget,
        "stop_loss_probe_spins": session_start.stop_loss_probe_spins,
        "stop_loss_probe_rate": session_start.stop_loss_probe_rate,
        "stop_loss_spin_threshold": stop_loss_spin_threshold,
        "stop_loss_normal_spin_cap": session_start.stop_loss_normal_spin_cap,
        "first_hit_spin": first_hit_spin,
        "first_hit_total_spins": first_hit_total_spins,
        "first_hit_cash_spent": first_hit_cash_spent,
        "first_hit_play_minutes": minutes(first_hit_play_seconds or 0.0),
        "total_hits": total_hits,
        "max_streak": max_streak,
        "total_out_balls": int(total_out_balls),
        "final_balls": int(final_balls),
        "locked_balls": int(locked_balls),
        "final_money": final_money,
        "unused_cash": int(unused_cash),
        "final_remaining_value": final_remaining_value,
        "final_remaining_balance": int(final_remaining_value - budget),
        "net_profit": net_profit,
        "cash_spent": int(cash_spent),
        "exchange_loss": exchange_loss,
        "session_time_limit_minutes": session_time_limit_minutes,
        "cash_input_cutoff_minutes": cash_input_cutoff_minutes,
        "soft_stop_minutes": soft_stop_minutes,
        "cash_budget_exhausted": cash_budget_exhausted_seconds is not None,
        "cash_budget_exhausted_minutes": minutes(cash_budget_exhausted_seconds or 0.0),
        "post_budget_play_minutes": minutes(post_budget_play_seconds),
        "experienced_rush": rush_entries > 0 or lt_entries > 0,
        "rush_entries": rush_entries,
        "lt_entries": lt_entries,
        "upper_entries": upper_entries,
        "hit_events": hit_events,
        "spins_used": spins_used,
        "right_spins": right_spins,
        "normal_balls_fired": int(normal_balls_fired),
        "normal_net_balls_consumed": int(normal_net_balls_consumed),
        "play_seconds": play_seconds,
        "play_minutes": minutes(play_seconds),
        "normal_play_seconds": normal_play_seconds,
        "normal_play_minutes": minutes(normal_play_seconds),
        "active_launch_seconds": active_launch_seconds,
        "normal_display_seconds": normal_display_seconds,
        "reserve_wait_seconds": reserve_wait_seconds,
        "reserve_wait_minutes": minutes(reserve_wait_seconds),
        "right_play_seconds": right_play_seconds,
        "right_play_minutes": minutes(right_play_seconds),
        "hit_effect_seconds": hit_effect_seconds_total,
        "hit_effect_minutes": minutes(hit_effect_seconds_total),
        "support_event_seconds": support_event_seconds,
        "cashless_play_seconds": cashless_play_seconds,
        "cashless_play_minutes": minutes(cashless_play_seconds),
        "cashless_play_share": cashless_share,
        "time_assumptions": assumption_dict(time_assumptions),
        "strategy": strategy,
        "strategy_label": STRATEGIES[strategy],
        "spins_per_1000y": spins_per_1000y,
        "observed_spins_per_1000y": session_start.observed_spins_per_1000y,
        "true_spins_per_1000y": session_start.true_spins_per_1000y,
        "border_spins_per_1000y": border_spins_per_1000y,
        "border_spins_per_1000yen": border_spins_per_1000y,
        "spin_rate_quality_stddev": session_start.effective_quality_stddev,
        "spin_rate_min": spin_rate_min,
        "spin_rate_max": spin_rate_max,
        "start_probability": session_start.start_probability,
        "start_variance": start_variance,
        "lend_rate": lend_rate,
        "exchange_rate": exchange_rate,
        "card_reuse": card_reuse,
        "session_policy": session_policy,
        "session_policy_label": SESSION_POLICIES[session_policy],
        **flags,
    }


__all__ = ["build_session_result"]
