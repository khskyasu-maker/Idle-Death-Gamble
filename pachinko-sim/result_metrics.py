import statistics
from typing import Any, Dict, List

from result_stats import (
    calculate_profit_condition_rows,
    mean_interval,
    percentile_float,
    percentile_value,
    profit_condition_summary_from_rows,
    quantile_interval,
    standard_error,
    tail_mean,
    wilson_interval,
)
from session_limits import (
    HARD_SESSION_TIME_LIMIT_HOURS,
    SESSION_TIME_LIMIT_HOURS,
    SESSION_TIME_LIMIT_MINUTES,
    STAY_HOUR_THRESHOLDS,
)


def calculate_metrics(results: List[Dict[str, Any]], iterations: int) -> Dict[str, Any]:
    profits = [r["net_profit"] for r in results]
    hits = [r["total_hits"] for r in results]
    streaks = [r["max_streak"] for r in results]
    spins_used = [r["spins_used"] for r in results]
    spin_capacities = [int(r.get("total_spins_possible", 0) or 0) for r in results]
    true_spin_rates = [float(r.get("true_spins_per_1000y", r.get("spins_per_1000y", 0)) or 0) for r in results]
    observed_spin_rates = [float(r.get("observed_spins_per_1000y", r.get("spins_per_1000y", 0)) or 0) for r in results]
    start_probabilities = [float(r.get("start_probability", 0.0) or 0.0) for r in results]
    right_spins = [r.get("right_spins", 0) for r in results]
    normal_balls_fired = [r.get("normal_balls_fired", 0) for r in results]
    normal_net_balls_consumed = [
        r.get("normal_net_balls_consumed", r.get("normal_balls_fired", 0))
        for r in results
    ]
    total_out_balls = [r.get("total_out_balls", 0) for r in results]
    cash_spent = [r.get("cash_spent", r["budget"]) for r in results]
    budgets = [r.get("budget", 0) for r in results]
    final_money = [r["final_money"] for r in results]
    unused_cash = [
        int(r.get("unused_cash", max(0, r.get("budget", 0) - r.get("cash_spent", r.get("budget", 0)))))
        for r in results
    ]
    final_remaining_value = [
        int(r.get("final_remaining_value", r.get("final_money", 0) + max(0, r.get("budget", 0) - r.get("cash_spent", r.get("budget", 0)))))
        for r in results
    ]
    final_remaining_balance = [
        int(r.get("final_remaining_balance", r.get("net_profit", 0)))
        for r in results
    ]
    play_minutes = [float(r.get("play_minutes", 0.0) or 0.0) for r in results]
    normal_play_minutes = [float(r.get("normal_play_minutes", 0.0) or 0.0) for r in results]
    right_play_minutes = [float(r.get("right_play_minutes", 0.0) or 0.0) for r in results]
    hit_effect_minutes = [float(r.get("hit_effect_minutes", 0.0) or 0.0) for r in results]
    reserve_wait_minutes = [float(r.get("reserve_wait_minutes", 0.0) or 0.0) for r in results]
    cashless_play_minutes = [float(r.get("cashless_play_minutes", 0.0) or 0.0) for r in results]
    cashless_play_shares = [float(r.get("cashless_play_share", 0.0) or 0.0) for r in results]
    post_budget_play_minutes = [float(r.get("post_budget_play_minutes", 0.0) or 0.0) for r in results]
    time_assumption = results[0].get("time_assumptions", {}) if results else {}
    time_limit_stop_count = sum(1 for r in results if r.get("time_limit_triggered"))
    soft_stop_count = sum(1 for r in results if r.get("soft_stop_triggered"))
    cash_input_cutoff_count = sum(1 for r in results if r.get("cash_input_cutoff_triggered"))
    cash_budget_exhausted_count = sum(1 for r in results if r.get("cash_budget_exhausted"))
    post_budget_continue_count = sum(1 for value in post_budget_play_minutes if value > 0)
    funds_exhausted_count = sum(1 for r in results if r.get("funds_exhausted_triggered"))
    rush_entries = [r.get("rush_entries", 0) for r in results]
    lt_entries = [r.get("lt_entries", 0) for r in results]
    upper_entries = [r.get("upper_entries", 0) for r in results]
    first_hits = [r["first_hit_spin"] for r in results if r["first_hit_spin"] is not None]
    first_hit_total_spins = [
        r.get("first_hit_total_spins", r.get("first_hit_spin"))
        for r in results
        if r.get("first_hit_total_spins", r.get("first_hit_spin")) is not None
    ]
    first_hit_cash_spent = [
        int(r.get("first_hit_cash_spent", 0) or 0)
        for r in results
        if r.get("first_hit_spin") is not None
    ]
    first_hit_play_minutes = [
        float(r.get("first_hit_play_minutes", 0.0) or 0.0)
        for r in results
        if r.get("first_hit_spin") is not None
    ]

    avg_profit = int(statistics.mean(profits))
    median_profit = int(statistics.median(profits))
    max_profit = max(profits)
    min_profit = min(profits)

    sorted_profits = sorted(profits)
    worst_10_profit = sorted_profits[max(0, int(iterations * 0.1) - 1)]
    worst_25_profit = sorted_profits[max(0, int(iterations * 0.25) - 1)]
    top_10_profit = sorted_profits[min(iterations - 1, int(iterations * 0.9))]

    positive_count = sum(1 for p in profits if p > 0)
    ruin_count = sum(1 for r in results if r["total_hits"] == 0)
    first_hit_miss_funds_exhausted_count = sum(
        1
        for r in results
        if r["total_hits"] == 0 and r.get("funds_exhausted_triggered")
    )
    rush_count = sum(1 for r in results if r["experienced_rush"])
    lt_count = sum(1 for r in results if r.get("lt_entries", 0) > 0)
    upper_count = sum(1 for r in results if r.get("upper_entries", 0) > 0)
    profit_lock_count = sum(1 for r in results if r.get("profit_lock_triggered"))
    profit_exit_count = sum(1 for r in results if r.get("profit_exit_triggered"))
    stop_loss_count = sum(1 for r in results if r.get("stop_loss_triggered"))
    aggressive_redeploy_count = sum(1 for r in results if r.get("aggressive_redeploy_triggered"))

    positive_close_rate = (positive_count / iterations) * 100
    ruin_rate = (ruin_count / iterations) * 100
    hit_rate = 100.0 - ruin_rate

    rush_rate = (rush_count / iterations) * 100
    single_hit_finish_rate = (sum(1 for r in results if r["total_hits"] == 1) / iterations) * 100
    under_500_finish_rate = (sum(1 for r in results if 0 < r["total_out_balls"] <= 500) / iterations) * 100

    def recovery_rate(ratio: float) -> float:
        recovered = 0
        for r in results:
            spent = max(1, r.get("cash_spent", r["budget"]))
            if r["final_money"] >= spent * ratio:
                recovered += 1
        return (recovered / iterations) * 100

    recovery_50_rate = recovery_rate(0.5)
    recovery_80_rate = recovery_rate(0.8)
    recovery_100_rate = recovery_rate(1.0)

    avg_hits = statistics.mean(hits)
    avg_streak = statistics.mean(streaks)
    avg_spins = statistics.mean(spins_used)
    avg_spin_capacity = statistics.mean(spin_capacities) if spin_capacities else 0
    avg_true_spin_rate = statistics.mean(true_spin_rates) if true_spin_rates else 0
    avg_observed_spin_rate = statistics.mean(observed_spin_rates) if observed_spin_rates else 0
    avg_first_hit = statistics.mean(first_hits) if first_hits else 0
    median_first_hit = percentile_value(first_hits, 0.5) if first_hits else 0
    p90_first_hit = percentile_value(first_hits, 0.9) if first_hits else 0
    avg_first_hit_total_spins = statistics.mean(first_hit_total_spins) if first_hit_total_spins else 0
    median_first_hit_total_spins = percentile_value(first_hit_total_spins, 0.5) if first_hit_total_spins else 0
    p90_first_hit_total_spins = percentile_value(first_hit_total_spins, 0.9) if first_hit_total_spins else 0
    avg_first_hit_cash_spent = statistics.mean(first_hit_cash_spent) if first_hit_cash_spent else 0
    median_first_hit_cash_spent = percentile_value(first_hit_cash_spent, 0.5) if first_hit_cash_spent else 0
    p90_first_hit_cash_spent = percentile_value(first_hit_cash_spent, 0.9) if first_hit_cash_spent else 0
    avg_first_hit_play_minutes = statistics.mean(first_hit_play_minutes) if first_hit_play_minutes else 0.0
    median_first_hit_play_minutes = percentile_float(first_hit_play_minutes, 0.5) if first_hit_play_minutes else 0.0
    hit_session_hits = [r["total_hits"] for r in results if r["total_hits"] > 0]
    avg_hits_when_hit = statistics.mean(hit_session_hits) if hit_session_hits else 0
    avg_after_first_hits = statistics.mean(max(0, hits - 1) for hits in hit_session_hits) if hit_session_hits else 0
    avg_profit_ci_low, avg_profit_ci_high = mean_interval(profits)
    avg_profit_standard_error = standard_error(profits)
    profit_stddev = statistics.stdev(profits) if len(profits) > 1 else 0.0
    avg_budget = statistics.mean(budgets) if budgets else 0.0
    avg_play_minutes = statistics.mean(play_minutes) if play_minutes else 0.0
    capped_play_minutes = [min(value, SESSION_TIME_LIMIT_MINUTES) for value in play_minutes]
    stay_reach_rates = {
        hour: (sum(1 for value in play_minutes if value >= hour * 60) / iterations) * 100.0
        for hour in STAY_HOUR_THRESHOLDS
    }
    limit_hour_over_count = sum(1 for value in play_minutes if value > SESSION_TIME_LIMIT_MINUTES)
    avg_cash_spent_value = statistics.mean(cash_spent) if cash_spent else 0.0
    avg_cash_spend_per_hour = (
        int((avg_cash_spent_value / avg_play_minutes) * 60.0)
        if avg_play_minutes > 0
        else 0
    )
    avg_play_minutes_per_1000yen_cash = (
        avg_play_minutes / (avg_cash_spent_value / 1000.0)
        if avg_cash_spent_value > 0
        else 0.0
    )
    avg_profit_se_budget_pct = (avg_profit_standard_error / avg_budget * 100.0) if avg_budget > 0 else 0.0
    play_time_uncertainty_pct = max(
        0.0,
        float(time_assumption.get("play_time_error_pct", 0.0) or 0.0) * 100.0,
    )
    play_time_uncertainty_ratio = play_time_uncertainty_pct / 100.0
    median_ci_low, median_ci_high = quantile_interval(profits, 0.5)
    worst_10_ci_low, worst_10_ci_high = quantile_interval(profits, 0.1)
    top_10_ci_low, top_10_ci_high = quantile_interval(profits, 0.9)
    cvar_10_profit = tail_mean(profits, 0.1, lower=True)
    upper_tail_10_profit = tail_mean(profits, 0.1, lower=False)
    positive_ci_low, positive_ci_high = wilson_interval(positive_count, iterations)
    ruin_ci_low, ruin_ci_high = wilson_interval(ruin_count, iterations)
    rush_ci_low, rush_ci_high = wilson_interval(rush_count, iterations)
    lt_ci_low, lt_ci_high = wilson_interval(lt_count, iterations)
    upper_ci_low, upper_ci_high = wilson_interval(upper_count, iterations)
    profit_condition_rows = calculate_profit_condition_rows(results, iterations)

    return {
        "avg_profit": avg_profit,
        "avg_profit_ci_low": avg_profit_ci_low,
        "avg_profit_ci_high": avg_profit_ci_high,
        "avg_profit_standard_error": int(avg_profit_standard_error),
        "avg_profit_se_budget_pct": avg_profit_se_budget_pct,
        "mean_ci_method": "t" if len(profits) <= 121 else "normal",
        "profit_stddev": int(profit_stddev),
        "median_profit": median_profit,
        "median_profit_ci_low": median_ci_low,
        "median_profit_ci_high": median_ci_high,
        "max_profit": max_profit,
        "min_profit": min_profit,
        "max_hits": max(hits),
        "max_streak_seen": max(streaks),
        "p90_hits": percentile_value(hits, 0.9),
        "p90_streak": percentile_value(streaks, 0.9),
        "max_rush_entries": max(rush_entries),
        "max_lt_entries": max(lt_entries),
        "max_upper_entries": max(upper_entries),
        "max_right_spins": max(r.get("right_spins", 0) for r in results),
        "worst_10_profit": worst_10_profit,
        "worst_10_profit_ci_low": worst_10_ci_low,
        "worst_10_profit_ci_high": worst_10_ci_high,
        "cvar_10_profit": cvar_10_profit,
        "worst_25_profit": worst_25_profit,
        "top_10_profit": top_10_profit,
        "top_10_profit_ci_low": top_10_ci_low,
        "top_10_profit_ci_high": top_10_ci_high,
        "upper_tail_10_profit": upper_tail_10_profit,
        "positive_close_rate": positive_close_rate,
        "positive_close_rate_ci_low": positive_ci_low,
        "positive_close_rate_ci_high": positive_ci_high,
        "profit_condition_rows": profit_condition_rows,
        "profit_condition_summary": profit_condition_summary_from_rows(profit_condition_rows),
        "ruin_rate": ruin_rate,
        "ruin_rate_ci_low": ruin_ci_low,
        "ruin_rate_ci_high": ruin_ci_high,
        "first_hit_miss_funds_exhausted_rate": (
            first_hit_miss_funds_exhausted_count / iterations
        ) * 100.0,
        "hit_rate": hit_rate,
        "rush_rate": rush_rate,
        "rush_rate_ci_low": rush_ci_low,
        "rush_rate_ci_high": rush_ci_high,
        "single_hit_finish_rate": single_hit_finish_rate,
        "under_500_finish_rate": under_500_finish_rate,
        "recovery_50_rate": recovery_50_rate,
        "recovery_80_rate": recovery_80_rate,
        "recovery_100_rate": recovery_100_rate,
        "avg_hits": avg_hits,
        "avg_streak": avg_streak,
        "avg_spins": int(avg_spins),
        "avg_spin_capacity": int(avg_spin_capacity),
        "p10_spin_capacity": percentile_value(spin_capacities, 0.1),
        "p90_spin_capacity": percentile_value(spin_capacities, 0.9),
        "avg_true_spins_per_1000y": avg_true_spin_rate,
        "p10_true_spins_per_1000y": percentile_float(true_spin_rates, 0.1),
        "p90_true_spins_per_1000y": percentile_float(true_spin_rates, 0.9),
        "avg_observed_spins_per_1000y": avg_observed_spin_rate,
        "p10_observed_spins_per_1000y": percentile_float(observed_spin_rates, 0.1),
        "p90_observed_spins_per_1000y": percentile_float(observed_spin_rates, 0.9),
        "start_variance": any(r.get("start_variance") for r in results),
        "start_probability": statistics.mean(start_probabilities) if start_probabilities else 0.0,
        "spin_rate_quality_stddev": float(results[0].get("spin_rate_quality_stddev", 0.0) or 0.0) if results else 0.0,
        "avg_normal_balls_fired": int(statistics.mean(normal_balls_fired)) if normal_balls_fired else 0,
        "avg_normal_net_balls_consumed": (
            int(statistics.mean(normal_net_balls_consumed)) if normal_net_balls_consumed else 0
        ),
        "avg_right_spins": int(statistics.mean(right_spins)),
        "avg_total_out_balls": int(statistics.mean(total_out_balls)),
        "avg_first_hit": int(avg_first_hit),
        "median_first_hit": median_first_hit,
        "p90_first_hit": p90_first_hit,
        "avg_first_hit_total_spins": int(avg_first_hit_total_spins),
        "median_first_hit_total_spins": median_first_hit_total_spins,
        "p90_first_hit_total_spins": p90_first_hit_total_spins,
        "avg_first_hit_cash_spent": int(avg_first_hit_cash_spent),
        "median_first_hit_cash_spent": median_first_hit_cash_spent,
        "p90_first_hit_cash_spent": p90_first_hit_cash_spent,
        "avg_first_hit_play_minutes": avg_first_hit_play_minutes,
        "median_first_hit_play_minutes": median_first_hit_play_minutes,
        "avg_hits_when_hit": avg_hits_when_hit,
        "avg_after_first_hits": avg_after_first_hits,
        "avg_cash_spent": int(statistics.mean(cash_spent)),
        "avg_final_money": int(statistics.mean(final_money)),
        "avg_unused_cash": int(statistics.mean(unused_cash)) if unused_cash else 0,
        "avg_final_remaining_value": int(statistics.mean(final_remaining_value)) if final_remaining_value else 0,
        "median_final_remaining_value": percentile_value(final_remaining_value, 0.5),
        "p10_final_remaining_value": percentile_value(final_remaining_value, 0.1),
        "p90_final_remaining_value": percentile_value(final_remaining_value, 0.9),
        "avg_final_remaining_balance": int(statistics.mean(final_remaining_balance)) if final_remaining_balance else 0,
        "median_final_remaining_balance": percentile_value(final_remaining_balance, 0.5),
        "budget_exhausted_rate": (sum(1 for spent, budget in zip(cash_spent, budgets) if spent >= budget) / iterations) * 100.0,
        "cash_budget_exhausted_rate": (cash_budget_exhausted_count / iterations) * 100.0,
        "funds_exhausted_stop_rate": (funds_exhausted_count / iterations) * 100.0,
        "post_budget_continue_rate": (post_budget_continue_count / iterations) * 100.0,
        "avg_post_budget_play_minutes": statistics.mean(post_budget_play_minutes) if post_budget_play_minutes else 0.0,
        "avg_post_budget_play_minutes_when_continued": (
            statistics.mean(value for value in post_budget_play_minutes if value > 0)
            if post_budget_continue_count
            else 0.0
        ),
        "avg_play_minutes": avg_play_minutes,
        "play_time_uncertainty_pct": play_time_uncertainty_pct,
        "avg_play_minutes_low_estimate": avg_play_minutes * max(0.0, 1.0 - play_time_uncertainty_ratio),
        "avg_play_minutes_high_estimate": avg_play_minutes * (1.0 + play_time_uncertainty_ratio),
        "median_play_minutes": percentile_float(play_minutes, 0.5),
        "median_play_minutes_low_estimate": (
            percentile_float(play_minutes, 0.5) * max(0.0, 1.0 - play_time_uncertainty_ratio)
        ),
        "median_play_minutes_high_estimate": (
            percentile_float(play_minutes, 0.5) * (1.0 + play_time_uncertainty_ratio)
        ),
        "p10_play_minutes": percentile_float(play_minutes, 0.1),
        "p25_play_minutes": percentile_float(play_minutes, 0.25),
        "p90_play_minutes": percentile_float(play_minutes, 0.9),
        "max_play_minutes": max(play_minutes) if play_minutes else 0.0,
        "avg_capped_play_minutes": statistics.mean(capped_play_minutes) if capped_play_minutes else 0.0,
        "stay_reach_rates": stay_reach_rates,
        "time_limit_hours": SESSION_TIME_LIMIT_HOURS,
        "hard_time_limit_hours": HARD_SESSION_TIME_LIMIT_HOURS,
        "time_limit_reached_rate": stay_reach_rates.get(SESSION_TIME_LIMIT_HOURS, 0.0),
        "time_limit_over_rate": (limit_hour_over_count / iterations) * 100.0,
        "time_limit_stop_rate": (soft_stop_count / iterations) * 100.0,
        "soft_stop_rate": (soft_stop_count / iterations) * 100.0,
        "hard_time_limit_stop_rate": (time_limit_stop_count / iterations) * 100.0,
        "cash_input_cutoff_rate": (cash_input_cutoff_count / iterations) * 100.0,
        "avg_normal_play_minutes": statistics.mean(normal_play_minutes) if normal_play_minutes else 0.0,
        "avg_right_play_minutes": statistics.mean(right_play_minutes) if right_play_minutes else 0.0,
        "avg_hit_effect_minutes": statistics.mean(hit_effect_minutes) if hit_effect_minutes else 0.0,
        "avg_reserve_wait_minutes": statistics.mean(reserve_wait_minutes) if reserve_wait_minutes else 0.0,
        "avg_cashless_play_minutes": statistics.mean(cashless_play_minutes) if cashless_play_minutes else 0.0,
        "avg_cashless_play_share": statistics.mean(cashless_play_shares) if cashless_play_shares else 0.0,
        "avg_cash_spend_per_hour": avg_cash_spend_per_hour,
        "avg_play_minutes_per_1000yen_cash": avg_play_minutes_per_1000yen_cash,
        "time_profile": time_assumption.get("profile_name", "generic"),
        "time_profile_note": time_assumption.get("source_note", ""),
        "avg_rush_entries": statistics.mean(rush_entries),
        "avg_lt_entries": statistics.mean(lt_entries),
        "avg_upper_entries": statistics.mean(upper_entries),
        "lt_success_rate": (lt_count / iterations) * 100,
        "lt_success_rate_ci_low": lt_ci_low,
        "lt_success_rate_ci_high": lt_ci_high,
        "upper_success_rate": (upper_count / iterations) * 100,
        "upper_success_rate_ci_low": upper_ci_low,
        "upper_success_rate_ci_high": upper_ci_high,
        "profit_lock_trigger_rate": (profit_lock_count / iterations) * 100,
        "profit_exit_trigger_rate": (profit_exit_count / iterations) * 100,
        "stop_loss_trigger_rate": (stop_loss_count / iterations) * 100,
        "aggressive_redeploy_trigger_rate": (aggressive_redeploy_count / iterations) * 100,
    }
