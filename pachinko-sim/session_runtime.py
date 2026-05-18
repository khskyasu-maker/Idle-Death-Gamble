from time_model import TimeAssumptions, gross_launch_balls


def limit_minutes_to_seconds(limit_minutes: float | None, *, allow_zero: bool = False) -> float | None:
    if limit_minutes is None:
        return None
    if limit_minutes > 0 or (allow_zero and limit_minutes >= 0):
        return max(0.0, float(limit_minutes)) * 60.0
    return None


def remaining_seconds(limit_seconds: float | None, elapsed_seconds: float) -> float | None:
    if limit_seconds is None:
        return None
    return limit_seconds - elapsed_seconds


def limit_reached(limit_seconds: float | None, elapsed_seconds: float) -> bool:
    return limit_seconds is not None and elapsed_seconds >= limit_seconds


def normal_seconds_per_spin(spin_cost_balls: float, time_assumptions: TimeAssumptions) -> float:
    gross_spin_balls = gross_launch_balls(spin_cost_balls, time_assumptions)
    active_per_spin = (
        (gross_spin_balls / time_assumptions.launch_balls_per_minute) * 60.0
        if time_assumptions.launch_balls_per_minute > 0
        else 0.0
    )
    return max(active_per_spin, time_assumptions.normal_seconds_per_start)


def cap_spins_by_seconds(
    spin_count: int,
    seconds_remaining: float | None,
    seconds_per_spin: float,
) -> tuple[int, bool]:
    if seconds_remaining is None:
        return spin_count, False
    if seconds_remaining <= 0:
        return 0, True
    if seconds_per_spin <= 0:
        return spin_count, False

    capped = int(seconds_remaining // seconds_per_spin)
    if capped < spin_count:
        return max(0, capped), True
    return spin_count, False


def cap_spins_before_cash_cutoff(
    spin_count: int,
    cutoff_seconds: float | None,
    elapsed_seconds: float,
    seconds_per_spin: float,
) -> tuple[int, bool]:
    if cutoff_seconds is None or elapsed_seconds >= cutoff_seconds:
        return spin_count, False
    if seconds_per_spin <= 0:
        return spin_count, False

    seconds_to_cutoff = cutoff_seconds - elapsed_seconds
    capped = int(seconds_to_cutoff // seconds_per_spin)
    if 0 < capped < spin_count:
        return capped, True
    return spin_count, False


__all__ = [
    "cap_spins_before_cash_cutoff",
    "cap_spins_by_seconds",
    "limit_minutes_to_seconds",
    "limit_reached",
    "normal_seconds_per_spin",
    "remaining_seconds",
]
