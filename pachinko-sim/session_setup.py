from dataclasses import dataclass

from start_gate import (
    observed_rate_per_1000yen,
    rented_balls_per_1000yen,
    sample_start_spins,
    sample_session_spin_rate,
)
from time_model import TimeAssumptions, gross_launch_balls


@dataclass(frozen=True)
class SessionStart:
    true_spins_per_1000y: float
    effective_quality_stddev: float
    rented_balls_1000: float
    gross_rented_balls_1000: float
    start_probability: float
    expected_total_spins_possible: int
    observed_spins_per_1000y: float
    total_spins_possible: int
    stop_loss_probe_budget: int
    stop_loss_probe_spins: int
    stop_loss_probe_rate: float
    normal_spin_cap: int | None
    stop_loss_normal_spin_cap: int | None


def build_session_start(
    budget: int,
    lend_rate: float,
    spins_per_1000y: float,
    strategy: str,
    session_policy: str,
    max_normal_spins: int | None,
    start_variance: bool,
    border_spins_per_1000y: float | None,
    spin_rate_quality_stddev: float,
    spin_rate_min: float | None,
    spin_rate_max: float | None,
    stop_loss_probe_yen: int,
    stop_loss_spin_threshold: int,
    time_assumptions: TimeAssumptions,
) -> SessionStart:
    true_spins_per_1000y = float(spins_per_1000y)
    effective_quality_stddev = spin_rate_quality_stddev if start_variance else 0.0
    if start_variance:
        true_spins_per_1000y = sample_session_spin_rate(
            spins_per_1000y,
            border_spins_per_1000y=border_spins_per_1000y,
            quality_stddev=effective_quality_stddev,
            min_spins_per_1000y=spin_rate_min,
            max_spins_per_1000y=spin_rate_max,
        )

    rented_balls_1000 = rented_balls_per_1000yen(lend_rate)
    gross_rented_balls_1000 = gross_launch_balls(rented_balls_1000, time_assumptions)
    start_probability = (
        max(0.0, min(1.0, true_spins_per_1000y / gross_rented_balls_1000))
        if gross_rented_balls_1000 > 0
        else 0.0
    )
    expected_total_spins_possible = int((budget / 1000) * true_spins_per_1000y)

    if start_variance and session_policy == "fixed_spin_cap":
        total_budget_balls = budget / lend_rate
        total_spins_possible = sample_start_spins(
            gross_launch_balls(total_budget_balls, time_assumptions),
            start_probability,
        )
        observed_spins_per_1000y = observed_rate_per_1000yen(total_spins_possible, budget)
    elif start_variance:
        sampled_1000y_spins = sample_start_spins(gross_rented_balls_1000, start_probability)
        observed_spins_per_1000y = float(sampled_1000y_spins)
        total_spins_possible = int((budget / 1000) * observed_spins_per_1000y)
    else:
        observed_spins_per_1000y = float(spins_per_1000y)
        total_spins_possible = expected_total_spins_possible

    stop_loss_probe_budget = max(0, min(int(stop_loss_probe_yen), int(budget)))
    if stop_loss_probe_budget > 0:
        if start_variance:
            stop_loss_probe_spins = sample_start_spins(
                gross_launch_balls(stop_loss_probe_budget / lend_rate, time_assumptions),
                start_probability,
            )
        else:
            stop_loss_probe_spins = int(round((stop_loss_probe_budget / 1000.0) * spins_per_1000y))
        stop_loss_probe_rate = observed_rate_per_1000yen(stop_loss_probe_spins, stop_loss_probe_budget)
    else:
        stop_loss_probe_spins = 0
        stop_loss_probe_rate = 0.0

    normal_spin_cap = total_spins_possible if session_policy == "fixed_spin_cap" else max_normal_spins
    stop_loss_normal_spin_cap = None
    if strategy == "basic_stop" and stop_loss_probe_budget > 0 and stop_loss_probe_rate < stop_loss_spin_threshold:
        stop_loss_normal_spin_cap = min(total_spins_possible, stop_loss_probe_spins)

    return SessionStart(
        true_spins_per_1000y=true_spins_per_1000y,
        effective_quality_stddev=effective_quality_stddev,
        rented_balls_1000=rented_balls_1000,
        gross_rented_balls_1000=gross_rented_balls_1000,
        start_probability=start_probability,
        expected_total_spins_possible=expected_total_spins_possible,
        observed_spins_per_1000y=observed_spins_per_1000y,
        total_spins_possible=total_spins_possible,
        stop_loss_probe_budget=stop_loss_probe_budget,
        stop_loss_probe_spins=stop_loss_probe_spins,
        stop_loss_probe_rate=stop_loss_probe_rate,
        normal_spin_cap=normal_spin_cap,
        stop_loss_normal_spin_cap=stop_loss_normal_spin_cap,
    )


__all__ = ["SessionStart", "build_session_start"]
