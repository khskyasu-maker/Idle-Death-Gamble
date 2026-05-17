from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class TimeAssumptions:
    profile_name: str = "generic"
    launch_balls_per_minute: float = 100.0
    normal_base_return_rate: float = 0.20
    normal_seconds_per_start: float = 6.0
    st_seconds_per_spin: float = 1.35
    lt_seconds_per_spin: float = 1.10
    upper_seconds_per_spin: float = 1.20
    jitan_seconds_per_spin: float = 1.80
    kakuben_seconds_per_spin: float = 2.80
    jinbee_seconds_per_spin: float = 1.60
    hit_base_seconds: float = 18.0
    rush_hit_base_seconds: float = 10.0
    payout_balls_per_minute: float = 900.0
    min_hit_seconds: float = 10.0
    normal_support_event_seconds: float = 5.0
    source_note: str = "범용 시간 예산 프로파일"


DEFAULT_TIME_ASSUMPTIONS = TimeAssumptions()
SEA_TIME_ASSUMPTIONS = TimeAssumptions(
    profile_name="sea_classic",
    normal_base_return_rate=0.25,
    st_seconds_per_spin=1.85,
    lt_seconds_per_spin=1.35,
    upper_seconds_per_spin=1.45,
    jitan_seconds_per_spin=2.40,
    kakuben_seconds_per_spin=3.20,
    jinbee_seconds_per_spin=1.70,
    hit_base_seconds=18.0,
    rush_hit_base_seconds=12.0,
    payout_balls_per_minute=850.0,
    source_note="바다 계열: 전통 확변/시단 소화와 당첨 출옥을 보수적으로 느리게 반영",
)
EVA_TIME_ASSUMPTIONS = TimeAssumptions(
    profile_name="eva_vst",
    normal_base_return_rate=0.20,
    st_seconds_per_spin=1.30,
    lt_seconds_per_spin=1.15,
    upper_seconds_per_spin=1.20,
    jitan_seconds_per_spin=1.75,
    kakuben_seconds_per_spin=2.60,
    jinbee_seconds_per_spin=1.60,
    hit_base_seconds=16.0,
    rush_hit_base_seconds=10.0,
    payout_balls_per_minute=1000.0,
    source_note="에바 V-ST 계열: 우타치 약 2.5만발/시급 보도·후기 기준 중간 속도",
)
REZERO_TIME_ASSUMPTIONS = TimeAssumptions(
    profile_name="rezero_fast",
    normal_base_return_rate=0.20,
    st_seconds_per_spin=0.85,
    lt_seconds_per_spin=0.85,
    upper_seconds_per_spin=0.85,
    jitan_seconds_per_spin=0.95,
    kakuben_seconds_per_spin=1.40,
    jinbee_seconds_per_spin=1.00,
    hit_base_seconds=10.0,
    rush_hit_base_seconds=4.0,
    payout_balls_per_minute=1600.0,
    min_hit_seconds=5.0,
    source_note="리제로 계열: 최단 0.76초 변동과 약 2분 RUSH 종료 후기 기준 고속",
)
BATTLE_TIME_ASSUMPTIONS = TimeAssumptions(
    profile_name="battle_fast",
    normal_base_return_rate=0.20,
    st_seconds_per_spin=1.00,
    lt_seconds_per_spin=0.90,
    upper_seconds_per_spin=0.95,
    jitan_seconds_per_spin=1.20,
    kakuben_seconds_per_spin=1.80,
    jinbee_seconds_per_spin=1.00,
    hit_base_seconds=12.0,
    rush_hit_base_seconds=6.0,
    payout_balls_per_minute=1300.0,
    min_hit_seconds=6.0,
    source_note="현대 배틀/LT 계열: 전통기보다 빠른 우타치와 출옥 속도",
)


def time_assumptions_for_machine(machine) -> TimeAssumptions:
    machine_id = getattr(machine, "id", "")
    name_ja = getattr(machine, "name_ja", "")
    spec_type = getattr(machine, "spec_type", "")
    haystack = f"{machine_id} {name_ja} {spec_type}"

    if "re_zero" in machine_id or "Re:ゼロ" in haystack or "リゼロ" in haystack:
        return REZERO_TIME_ASSUMPTIONS
    if "eva" in machine_id or "エヴァ" in haystack:
        return EVA_TIME_ASSUMPTIONS
    if (
        "hokuto" in machine_id
        or "北斗" in haystack
        or ("LT" in spec_type and "海" not in haystack)
    ):
        return BATTLE_TIME_ASSUMPTIONS
    if (
        "sea" in machine_id
        or "海物語" in haystack
        or "大海" in haystack
        or "沖縄" in haystack
        or "地中海" in haystack
        or "ギンギラ" in haystack
    ):
        return SEA_TIME_ASSUMPTIONS
    return DEFAULT_TIME_ASSUMPTIONS


def assumption_dict(assumptions: TimeAssumptions = DEFAULT_TIME_ASSUMPTIONS) -> dict:
    return asdict(assumptions)


def launch_seconds(ball_count: float, assumptions: TimeAssumptions = DEFAULT_TIME_ASSUMPTIONS) -> float:
    if ball_count <= 0 or assumptions.launch_balls_per_minute <= 0:
        return 0.0
    return (ball_count / assumptions.launch_balls_per_minute) * 60.0


def gross_launch_balls(
    net_consumed_balls: float,
    assumptions: TimeAssumptions = DEFAULT_TIME_ASSUMPTIONS,
) -> float:
    """Return fired balls needed to create the observed net ball consumption.

    Field rotation such as 70回/1000円 already reflects the net loss after
    ヘソ(헤소) and general-pocket returns. Time spent launching balls should use
    gross fired balls, so a 25% base means 1000 net balls took about 1333 fired
    balls.
    """
    if net_consumed_balls <= 0:
        return 0.0
    base = max(0.0, min(0.90, assumptions.normal_base_return_rate))
    return net_consumed_balls / max(0.10, 1.0 - base)


def normal_time_components(
    start_spins: int,
    net_consumed_balls: float,
    assumptions: TimeAssumptions = DEFAULT_TIME_ASSUMPTIONS,
) -> dict:
    """Return elapsed normal-play time and the part caused by reserve waiting.

    Net consumed balls are the cash/card balance reduction implied by field
    rotation. Gross launched balls add back ベース(반환 구슬) before converting to
    active launch time. Display time is the time for sampled starts to resolve
    on screen. If display time is longer, the extra part approximates pauses
    when 保留(보류) is full or the machine is busy with effects.
    """
    gross_balls = gross_launch_balls(net_consumed_balls, assumptions)
    active_launch = launch_seconds(gross_balls, assumptions)
    display = max(0, start_spins) * assumptions.normal_seconds_per_start
    elapsed = max(active_launch, display)
    return {
        "elapsed_seconds": elapsed,
        "active_launch_seconds": active_launch,
        "display_seconds": display,
        "reserve_wait_seconds": max(0.0, display - active_launch),
        "net_consumed_balls": net_consumed_balls,
        "gross_launched_balls": gross_balls,
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
        "LT_JITAN": assumptions.jitan_seconds_per_spin,
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
