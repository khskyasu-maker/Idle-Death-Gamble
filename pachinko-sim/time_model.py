from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class TimeAssumptions:
    launch_balls_per_minute: float = 100.0
    normal_seconds_per_start: float = 6.0
    st_seconds_per_spin: float = 1.25
    lt_seconds_per_spin: float = 1.10
    upper_seconds_per_spin: float = 1.15
    jitan_seconds_per_spin: float = 1.60
    kakuben_seconds_per_spin: float = 2.20
    jinbee_seconds_per_spin: float = 1.30
    hit_base_seconds: float = 18.0
    rush_hit_base_seconds: float = 10.0
    payout_balls_per_minute: float = 900.0
    min_hit_seconds: float = 10.0
    normal_support_event_seconds: float = 5.0


DEFAULT_TIME_ASSUMPTIONS = TimeAssumptions()


def assumption_dict(assumptions: TimeAssumptions = DEFAULT_TIME_ASSUMPTIONS) -> dict:
    return asdict(assumptions)


def launch_seconds(ball_count: float, assumptions: TimeAssumptions = DEFAULT_TIME_ASSUMPTIONS) -> float:
    if ball_count <= 0 or assumptions.launch_balls_per_minute <= 0:
        return 0.0
    return (ball_count / assumptions.launch_balls_per_minute) * 60.0


def normal_time_components(
    start_spins: int,
    fired_balls: float,
    assumptions: TimeAssumptions = DEFAULT_TIME_ASSUMPTIONS,
) -> dict:
    """Return elapsed normal-play time and the part caused by reserve waiting.

    Active launch time is the time to fire the required balls. Display time is
    the time for the sampled starts to resolve on screen. If display time is
    longer, the extra part approximates pauses when 保留(보류) is full or the
    machine is busy with effects.
    """
    active_launch = launch_seconds(fired_balls, assumptions)
    display = max(0, start_spins) * assumptions.normal_seconds_per_start
    elapsed = max(active_launch, display)
    return {
        "elapsed_seconds": elapsed,
        "active_launch_seconds": active_launch,
        "display_seconds": display,
        "reserve_wait_seconds": max(0.0, display - active_launch),
    }


def right_seconds(
    state: str,
    spins: int,
    assumptions: TimeAssumptions = DEFAULT_TIME_ASSUMPTIONS,
) -> float:
    if spins <= 0:
        return 0.0
    seconds_per_spin = {
        "ST": assumptions.st_seconds_per_spin,
        "LT": assumptions.lt_seconds_per_spin,
        "UPPER": assumptions.upper_seconds_per_spin,
        "JITAN": assumptions.jitan_seconds_per_spin,
        "JINBEE_JITAN": assumptions.jitan_seconds_per_spin,
        "KAKUBEN": assumptions.kakuben_seconds_per_spin,
        "JINBEE": assumptions.jinbee_seconds_per_spin,
    }.get(state, assumptions.st_seconds_per_spin)
    return max(0, spins) * seconds_per_spin


def hit_effect_seconds(
    payout_balls: int,
    previous_state: str,
    assumptions: TimeAssumptions = DEFAULT_TIME_ASSUMPTIONS,
) -> float:
    if payout_balls <= 0:
        return assumptions.normal_support_event_seconds
    base = (
        assumptions.hit_base_seconds
        if previous_state == "NORMAL"
        else assumptions.rush_hit_base_seconds
    )
    payout_seconds = (
        (payout_balls / assumptions.payout_balls_per_minute) * 60.0
        if assumptions.payout_balls_per_minute > 0
        else 0.0
    )
    return max(assumptions.min_hit_seconds, base + payout_seconds)


def minutes(seconds: float) -> float:
    return max(0.0, seconds) / 60.0
