from machine_types import Machine, Payout


PRACTICAL_PAYOUT_RATIO = 0.93


def practical_paid_out_balls(paid_out_balls: int, ratio: float = PRACTICAL_PAYOUT_RATIO) -> int:
    return int(round((paid_out_balls * ratio) / 10.0) * 10)


def sea_kakuhen_loop(
    machine_id: str,
    name_ja: str,
    name_ko: str,
    source: str,
    normal_prob: float,
    high_prob: float,
    kakuhen_weight: float,
    normal_weight: float,
    balls: int,
    risk_grade: str = "1/319",
    normal_jitan_spins: int = 100,
    jitan_normal_jitan_spins: int = None,
    kakuben_normal_jitan_spins: int = None,
    confidence: str = "medium",
    simplification_notes: str = "",
    notes: str = "",
    ball_variance: float = 0.03,
    paid_out_to_practical_ratio: float = PRACTICAL_PAYOUT_RATIO,
) -> Machine:
    practical_balls = practical_paid_out_balls(balls, paid_out_to_practical_ratio)
    jitan_normal_jitan_spins = (
        normal_jitan_spins if jitan_normal_jitan_spins is None else jitan_normal_jitan_spins
    )
    kakuben_normal_jitan_spins = (
        normal_jitan_spins if kakuben_normal_jitan_spins is None else kakuben_normal_jitan_spins
    )
    return Machine(
        id=machine_id,
        name_ja=name_ja,
        name_ko=name_ko,
        spec_type="미들 / 확변 루프",
        risk_grade=risk_grade,
        normal_prob=normal_prob,
        high_prob=high_prob,
        normal_hit_dist=[
            Payout(
                balls=practical_balls,
                weight=kakuhen_weight,
                next_state="KAKUBEN",
                ball_variance=ball_variance,
            ),
            Payout(
                balls=practical_balls,
                weight=normal_weight,
                next_state="JITAN",
                jitan_spins=normal_jitan_spins,
                counts_as_rush=False,
                ball_variance=ball_variance,
            ),
        ],
        st_hit_dist=[],
        jitan_hit_dist=[
            Payout(
                balls=practical_balls,
                weight=kakuhen_weight,
                next_state="KAKUBEN",
                ball_variance=ball_variance,
            ),
            Payout(
                balls=practical_balls,
                weight=normal_weight,
                next_state="JITAN",
                jitan_spins=jitan_normal_jitan_spins,
                ball_variance=ball_variance,
            ),
        ],
        kakuben_hit_dist=[
            Payout(
                balls=practical_balls,
                weight=kakuhen_weight,
                next_state="KAKUBEN",
                ball_variance=ball_variance,
            ),
            Payout(
                balls=practical_balls,
                weight=normal_weight,
                next_state="JITAN",
                jitan_spins=kakuben_normal_jitan_spins,
                ball_variance=ball_variance,
            ),
        ],
        lt_hit_dist=[],
        simplification_notes=simplification_notes,
        spec_source=source,
        confidence=confidence,
        notes=notes,
        is_estimated=confidence != "high",
    )


def sea_kakuhen_10r(
    machine_id: str,
    name_ja: str,
    name_ko: str,
    source: str,
    normal_prob: float = 319.6,
    high_prob: float = 31.9,
    confidence: str = "medium",
) -> Machine:
    return sea_kakuhen_loop(
        machine_id=machine_id,
        name_ja=name_ja,
        name_ko=name_ko,
        source=source,
        normal_prob=normal_prob,
        high_prob=high_prob,
        kakuhen_weight=0.60,
        normal_weight=0.40,
        balls=1500,
        confidence=confidence,
        simplification_notes="확변 60% / 통상 40% / 통상 후 시단 100회인 바다 미들 기본형. 전 당첨 10R 1500払出 모델.",
        notes="DMM 스펙의 주요 확률/전サポ 구조를 반영. 1500払出은 예산 계산용 실전 근사 1400발로 사용. 보류연, 3000 보너스 일부 연출은 1500払出 연속 당첨으로 근사.",
    )


def sea_st_jitan(
    machine_id: str,
    name_ja: str,
    name_ko: str,
    source: str,
    normal_prob: float,
    high_prob: float,
    payout_rows: list[tuple[int, float, int, int]],
    risk_grade: str,
    spec_type: str = "감데지 / ST+時短",
    confidence: str = "medium",
    simplification_notes: str = "",
    notes: str = "",
    ball_variance: float = 0.03,
    paid_out_to_practical_ratio: float = PRACTICAL_PAYOUT_RATIO,
) -> Machine:
    def distribution():
        return [
            Payout(
                balls=practical_paid_out_balls(balls, paid_out_to_practical_ratio),
                weight=weight,
                next_state="ST",
                st_spins=st_spins,
                jitan_spins=jitan_spins,
                ball_variance=ball_variance,
            )
            for balls, weight, st_spins, jitan_spins in payout_rows
        ]

    return Machine(
        id=machine_id,
        name_ja=name_ja,
        name_ko=name_ko,
        spec_type=spec_type,
        risk_grade=risk_grade,
        normal_prob=normal_prob,
        high_prob=high_prob,
        normal_hit_dist=distribution(),
        st_hit_dist=distribution(),
        jitan_hit_dist=distribution(),
        kakuben_hit_dist=[],
        lt_hit_dist=[],
        simplification_notes=simplification_notes,
        spec_source=source,
        confidence=confidence,
        notes=notes,
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


def eva_vst_split_entry(
    machine_id: str,
    name_ja: str,
    name_ko: str,
    source: str,
    normal_prob: float,
    high_prob: float,
    st_spins: int,
    jitan_spins: int,
    first_10r_weight: float,
    first_3r_st_weight: float,
    first_3r_jitan_weight: float,
    first_10r_balls: int,
    first_3r_balls: int,
    right_balls: int,
    risk_grade: str,
    spec_type: str = "에바 / V-ST",
    confidence: str = "medium",
    simplification_notes: str = "",
    notes: str = "",
    ball_variance: float = 0.03,
) -> Machine:
    return Machine(
        id=machine_id,
        name_ja=name_ja,
        name_ko=name_ko,
        spec_type=spec_type,
        risk_grade=risk_grade,
        normal_prob=normal_prob,
        high_prob=high_prob,
        normal_hit_dist=[
            Payout(
                balls=first_10r_balls,
                weight=first_10r_weight,
                next_state="ST",
                st_spins=st_spins,
                ball_variance=ball_variance,
            ),
            Payout(
                balls=first_3r_balls,
                weight=first_3r_st_weight,
                next_state="ST",
                st_spins=st_spins,
                ball_variance=ball_variance,
            ),
            Payout(
                balls=first_3r_balls,
                weight=first_3r_jitan_weight,
                next_state="JITAN",
                jitan_spins=jitan_spins,
                counts_as_rush=False,
                ball_variance=ball_variance,
            ),
        ],
        st_hit_dist=[
            Payout(
                balls=right_balls,
                weight=1.0,
                next_state="ST",
                st_spins=st_spins,
                ball_variance=ball_variance,
            )
        ],
        jitan_hit_dist=[
            Payout(
                balls=right_balls,
                weight=1.0,
                next_state="ST",
                st_spins=st_spins,
                ball_variance=ball_variance,
            )
        ],
        kakuben_hit_dist=[],
        lt_hit_dist=[],
        simplification_notes=simplification_notes,
        spec_source=source,
        confidence=confidence,
        notes=notes,
        is_estimated=confidence != "high",
    )


def eva_breakthrough_st_jitan(
    machine_id: str,
    name_ja: str,
    name_ko: str,
    source: str,
    normal_prob: float,
    high_prob: float,
    direct_rush_weight: float,
    challenge_st_weight: float,
    challenge_jitan_weight: float,
    challenge_st_spins: int,
    challenge_jitan_spins: int,
    rush_st_spins: int,
    rush_jitan_spins: int,
    first_10r_balls: int,
    first_3r_balls: int,
    right_10r_balls: int,
    right_3r_balls: int,
    right_10r_weight: float,
    right_3r_weight: float,
    risk_grade: str,
    spec_type: str,
    confidence: str = "medium",
    simplification_notes: str = "",
    notes: str = "",
    ball_variance: float = 0.03,
) -> Machine:
    def right_distribution():
        return [
            Payout(
                balls=right_10r_balls,
                weight=right_10r_weight,
                next_state="ST",
                st_spins=rush_st_spins,
                jitan_spins=rush_jitan_spins,
                ball_variance=ball_variance,
            ),
            Payout(
                balls=right_3r_balls,
                weight=right_3r_weight,
                next_state="ST",
                st_spins=rush_st_spins,
                jitan_spins=rush_jitan_spins,
                ball_variance=ball_variance,
            ),
        ]

    return Machine(
        id=machine_id,
        name_ja=name_ja,
        name_ko=name_ko,
        spec_type=spec_type,
        risk_grade=risk_grade,
        normal_prob=normal_prob,
        high_prob=high_prob,
        normal_hit_dist=[
            Payout(
                balls=first_10r_balls,
                weight=direct_rush_weight,
                next_state="ST",
                st_spins=rush_st_spins,
                jitan_spins=rush_jitan_spins,
                ball_variance=ball_variance,
            ),
            Payout(
                balls=first_3r_balls,
                weight=challenge_st_weight,
                next_state="ST",
                st_spins=challenge_st_spins,
                counts_as_rush=False,
                ball_variance=ball_variance,
            ),
            Payout(
                balls=first_3r_balls,
                weight=challenge_jitan_weight,
                next_state="JITAN",
                jitan_spins=challenge_jitan_spins,
                counts_as_rush=False,
                ball_variance=ball_variance,
            ),
        ],
        st_hit_dist=right_distribution(),
        jitan_hit_dist=right_distribution(),
        kakuben_hit_dist=[],
        lt_hit_dist=[],
        simplification_notes=simplification_notes,
        spec_source=source,
        confidence=confidence,
        notes=notes,
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
