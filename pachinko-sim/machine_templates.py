from machine_types import Machine, Payout


def sea_kakuhen_10r(
    machine_id: str,
    name_ja: str,
    name_ko: str,
    source: str,
    normal_prob: float = 319.6,
    high_prob: float = 31.9,
    confidence: str = "medium",
) -> Machine:
    return Machine(
        id=machine_id,
        name_ja=name_ja,
        name_ko=name_ko,
        spec_type="미들 / 확변 루프",
        risk_grade="1/319",
        normal_prob=normal_prob,
        high_prob=high_prob,
        normal_hit_dist=[
            Payout(balls=1500, weight=0.60, next_state="KAKUBEN"),
            Payout(balls=1500, weight=0.40, next_state="JITAN", jitan_spins=100),
        ],
        st_hit_dist=[],
        jitan_hit_dist=[
            Payout(balls=1500, weight=0.60, next_state="KAKUBEN"),
            Payout(balls=1500, weight=0.40, next_state="JITAN", jitan_spins=100),
        ],
        kakuben_hit_dist=[
            Payout(balls=1500, weight=0.60, next_state="KAKUBEN"),
            Payout(balls=1500, weight=0.40, next_state="JITAN", jitan_spins=100),
        ],
        lt_hit_dist=[],
        simplification_notes="확변 60% / 통상 40% / 통상 후 시단 100회인 바다 미들 기본형. 전 당첨 10R 1500발 지급 모델.",
        spec_source=source,
        confidence=confidence,
        notes="DMM 스펙의 주요 확률/전サポ 구조를 반영. 보류연, 3000 보너스 일부 연출은 1500발 연속 당첨으로 근사.",
        is_estimated=confidence != "high",
    )


def sea_light_st(
    machine_id: str,
    name_ja: str,
    name_ko: str,
    source: str,
    normal_prob: float = 199.8,
    high_prob: float = 40.6,
    st_spins: int = 50,
    confidence: str = "medium",
) -> Machine:
    return Machine(
        id=machine_id,
        name_ja=name_ja,
        name_ko=name_ko,
        spec_type="라이트미들 / ST",
        risk_grade="1/199",
        normal_prob=normal_prob,
        high_prob=high_prob,
        normal_hit_dist=[
            Payout(balls=1500, weight=0.25, next_state="ST", st_spins=st_spins),
            Payout(balls=450, weight=0.75, next_state="ST", st_spins=st_spins),
        ],
        st_hit_dist=[
            Payout(balls=1500, weight=0.25, next_state="ST", st_spins=st_spins),
            Payout(balls=450, weight=0.75, next_state="ST", st_spins=st_spins),
        ],
        jitan_hit_dist=[],
        kakuben_hit_dist=[],
        lt_hit_dist=[],
        simplification_notes="大海BLACK/BLACK系 라이트미들 ST 모델. 10R 비중과 3R/4R 비중을 분포로 처리.",
        spec_source=source,
        confidence=confidence,
        notes="세부 라운드 비율은 기종별 차이가 있어 수동 스펙 보강 전까지 medium 이하로 해석.",
        is_estimated=confidence != "high",
    )


def eva_vst(
    machine_id: str,
    name_ja: str,
    name_ko: str,
    source: str,
    normal_prob: float,
    high_prob: float,
    rush_entry: float,
    st_spins: int,
    jitan_spins: int,
    first_balls: int,
    right_balls: int,
    risk_grade: str,
    confidence: str = "medium",
) -> Machine:
    return Machine(
        id=machine_id,
        name_ja=name_ja,
        name_ko=name_ko,
        spec_type="에바 / V-ST",
        risk_grade=risk_grade,
        normal_prob=normal_prob,
        high_prob=high_prob,
        normal_hit_dist=[
            Payout(balls=first_balls, weight=rush_entry, next_state="ST", st_spins=st_spins),
            Payout(balls=first_balls, weight=1.0 - rush_entry, next_state="JITAN", jitan_spins=jitan_spins),
        ],
        st_hit_dist=[Payout(balls=right_balls, weight=1.0, next_state="ST", st_spins=st_spins)],
        jitan_hit_dist=[Payout(balls=right_balls, weight=1.0, next_state="ST", st_spins=st_spins)],
        kakuben_hit_dist=[],
        lt_hit_dist=[],
        simplification_notes="에바 V-ST 계열. 초기 ST/時短 분기와 우측 10R 중심 구조를 분리.",
        spec_source=source,
        confidence=confidence,
        notes="전サポ 중 잔보류와 세부 라운드 예외는 단순화.",
        is_estimated=confidence != "high",
    )


def re_zero_rush(
    machine_id: str,
    name_ja: str,
    name_ko: str,
    source: str,
    normal_prob: float,
    high_prob: float,
    rush_entry: float,
    st_spins: int,
    risk_grade: str,
    confidence: str = "medium",
) -> Machine:
    return Machine(
        id=machine_id,
        name_ja=name_ja,
        name_ko=name_ko,
        spec_type="리제로 / RUSH",
        risk_grade=risk_grade,
        normal_prob=normal_prob,
        high_prob=high_prob,
        normal_hit_dist=[
            Payout(balls=300, weight=rush_entry, next_state="ST", st_spins=st_spins),
            Payout(balls=300, weight=1.0 - rush_entry, next_state="NORMAL"),
        ],
        st_hit_dist=[
            Payout(balls=3000, weight=0.25, next_state="ST", st_spins=st_spins),
            Payout(balls=1500, weight=0.25, next_state="ST", st_spins=st_spins),
            Payout(balls=300, weight=0.50, next_state="ST", st_spins=st_spins),
        ],
        jitan_hit_dist=[],
        kakuben_hit_dist=[],
        lt_hit_dist=[],
        simplification_notes="リゼロ 계열 RUSH 모델. 3000/1500/300발 분포로 오른쪽 출옥 편차를 반영.",
        spec_source=source,
        confidence=confidence,
        notes="鬼がかり/season2 계열별 세부振分은 수동 스펙 보강 전까지 medium 이하로 해석.",
        is_estimated=confidence != "high",
    )
