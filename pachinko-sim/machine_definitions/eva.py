from machine_templates import eva_breakthrough_st_jitan, eva_vst_split_entry
from machine_types import Machine, Payout

EVA_INITIAL_MACHINES = {
    # B-4. 新世紀エヴァンゲリオン〜未来への咆哮〜 (에바15 미들)
    "eva_15_roar": eva_vst_split_entry(
        machine_id="eva_15_roar",
        name_ja="新世紀エヴァンゲリオン〜未来への咆哮〜",
        name_ko="신세기 에반게리온 미래로의 포효 (에바15)",
        source="SANKYO collection/925 / DMMぱちタウン machines/4021 / GA 2021-10-07 T1Y sheet",
        normal_prob=319.7,
        high_prob=99.4,
        st_spins=163,
        jitan_spins=100,
        first_10r_weight=0.03,
        first_3r_st_weight=0.56,
        first_3r_jitan_weight=0.41,
        first_10r_balls=1400,
        first_3r_balls=420,
        right_balls=1400,
        risk_grade="1/319",
        spec_type="미들 / V-ST",
        confidence="high",
        simplification_notes=(
            "特図1 10R確変 3% / 3R確変 56% / 3R通常 41%. "
            "通常後 時短100 중 당첨 시 ST163으로 승격."
        ),
        notes=(
            "DMM/SANKYO는 우측 ALL1500個払出로 표기하지만 예산/체류시간 계산은 "
            "T1Y 근사 10R 1400발, 3R 420발을 사용. ST継続率 약81%는 ST163회 기준으로 검증. "
            "右打ち中의 잔존ヘソ特図1通常後 時短500 예외와 残保留4는 별도 상태로 모델링하지 않음."
        ),
    ),

    # B-5. P新世紀エヴァンゲリオン〜未来への咆哮〜PREMIUM MODEL (에바15 프리미엄 1/129)
    "eva_15_premium": eva_breakthrough_st_jitan(
        machine_id="eva_15_premium",
        name_ja="P新世紀エヴァンゲリオン〜未来への咆哮〜PREMIUM MODEL",
        name_ko="P 신세기 에반게리온 미래로의 포효 프리미엄 모델",
        source="DMMぱちタウン machines/4498 / P-WORLD database/9993 / なな徹",
        normal_prob=129.8,
        high_prob=35.7,
        direct_rush_weight=0.10,
        challenge_st_weight=0.54,
        challenge_jitan_weight=0.36,
        challenge_st_spins=30,
        challenge_jitan_spins=30,
        rush_st_spins=30,
        rush_jitan_spins=100,
        first_10r_balls=930,
        first_3r_balls=280,
        right_10r_balls=930,
        right_3r_balls=280,
        right_10r_weight=0.60,
        right_3r_weight=0.40,
        risk_grade="1/129",
        spec_type="라이트 / 돌파형 V-ST",
        confidence="high",
        simplification_notes=(
            "ヘソ 10%는 RUSH 직행, 54%는 ST30 챌린지, 36%는 時短30 챌린지. "
            "챌린지 중 당첨 시 RUSH(ST30+時短100)로 승격."
        ),
        notes=(
            "DMM/P-WORLD의 約1000/300個払出을 예산 계산용 실전 근사 930/280발로 사용. "
            "残保留4 引き戻し는 별도 보류 상태 없이 회전수/벤치마크에 흡수."
        ),
    ),

    # B-6. ぱちんこ シン・エヴァンゲリオン 129 LT ver. (신 에바 129 LT)
    "shin_eva_129_lt": Machine(
        id="shin_eva_129_lt",
        name_ja="ぱちんこ シン・エヴァンゲリオン 129 LT ver.",
        name_ko="P 신 에반게리온 129 LT 버전",
        spec_type="라이트 / 1種2種 LT",
        risk_grade="1/129",
        normal_prob=129.8,
        high_prob=54.4,
        normal_hit_dist=[
            Payout(balls=930, weight=0.005, next_state="LT", st_spins=127, is_lt=True, ball_variance=0.03),
            Payout(balls=280, weight=0.500, next_state="ST", st_spins=64, ball_variance=0.03),
            Payout(balls=280, weight=0.495, next_state="NORMAL", counts_as_rush=False, ball_variance=0.03),
        ],
        st_hit_dist=[
            Payout(balls=930, weight=0.10, next_state="LT", st_spins=127, is_lt=True, ball_variance=0.03),
            Payout(balls=930, weight=0.90, next_state="ST", st_spins=64, ball_variance=0.03),
        ],
        jitan_hit_dist=[
        ],
        kakuben_hit_dist=[],
        lt_hit_dist=[
            Payout(balls=930, weight=1.00, next_state="LT", st_spins=127, is_lt=True, ball_variance=0.03)
        ],
        simplification_notes="ヘソ 0.5% LT 직행, 50.0% RUSH, 49.5% 통상. RUSH는 60회+残保留4개, LT는 123회+残保留4개로 합산.",
        spec_source="P-WORLD database/10206 / DMM machines/4736 / なな徹",
        confidence="high",
        notes="DMM의 約1000/300個払出을 예산 계산용 실전 근사 930/280발로 사용. RUSH 중 10% LT, LT 중 100% LT継続 분포 반영.",
        is_estimated=False,
    ),

    # B-7. e 新世紀エヴァンゲリオン ～はじまりの記憶～ (1/399)
    "eva_beginning": Machine(
        id="eva_beginning",
        name_ja="e新世紀エヴァンゲリオン ～はじまりの記憶～",
        name_ko="e 신세기 에반게리온 시작의 기억",
        spec_type="스마트 파친코 / 399 LT-ST",
        risk_grade="1/399",
        normal_prob=349.9,
        high_prob=99.6,
        jitan_prob=399.9,
        normal_hit_dist=[
            Payout(balls=1400, weight=0.005, next_state="LT", st_spins=157, is_lt=True, ball_variance=0.03),
            Payout(balls=280, weight=0.500, next_state="LT", st_spins=157, is_lt=True, ball_variance=0.03),
            Payout(balls=280, weight=0.495, next_state="JITAN", jitan_spins=100, counts_as_rush=False, ball_variance=0.03),
        ],
        st_hit_dist=[],
        jitan_hit_dist=[
            Payout(balls=280, weight=1.00, next_state="LT", st_spins=157, is_lt=True, ball_variance=0.03),
        ],
        kakuben_hit_dist=[],
        lt_hit_dist=[
            Payout(balls=4480, weight=0.005, next_state="LT", st_spins=157, is_lt=True, ball_variance=0.03),
            Payout(balls=2240, weight=0.995, next_state="LT", st_spins=157, is_lt=True, ball_variance=0.03),
        ],
        simplification_notes="ST突入=LT로 분류. 通常 당첨 대기는 チャージ込み大当り確率 약1/349.9, 時短100 되돌림은 図柄揃い約1/399.9로 분리. ヘソ는 0.5% 10R LT, 50.0% 2R LT, 49.5% 2R+時短100. 오른쪽은 8R×2=2400払出 중심, 0.5%만 8R×4로 근사.",
        spec_source="DMMぱちタウン machines/4894 / P-WORLD database/10353 / 777パチガブ / SANKYO",
        confidence="high",
        notes="DMM 123難波店 1円に1台あり. チャージ経由の突入大当り는 별도 이벤트가 아니라 통상 대기 확률 1/349.9에 흡수. チャージ 후 非突入으로 통상 복귀하는 세부 소当り는 공개突入率 계산 대상이 아니므로 미반영. 1500/300/2400/4800払出은 예산 계산용 실전 근사 1400/280/2240/4480발로 사용.",
        is_estimated=False,
    ),
}

EVA_ADDITION_MACHINES = {
    # Eva family additions.
    "shin_eva_type_rei": eva_vst_split_entry(
        machine_id="shin_eva_type_rei",
        name_ja="ぱちんこ シン・エヴァンゲリオン Type レイ",
        name_ko="P 신 에반게리온 Type 레이",
        source="DMMぱちタウン machines/4452 / P-WORLD / Pachiseven",
        normal_prob=319.7,
        high_prob=99.5,
        st_spins=163,
        jitan_spins=100,
        first_10r_weight=0.01,
        first_3r_st_weight=0.62,
        first_3r_jitan_weight=0.37,
        first_10r_balls=1400,
        first_3r_balls=280,
        right_balls=1400,
        risk_grade="1/319",
        spec_type="에바 / V-ST",
        confidence="high",
        simplification_notes=(
            "特図1 10R確変 1% / 3R確変 62% / 3R通常 37%. "
            "通常後 時短100 중 당첨 시 ST163으로 승격."
        ),
        notes=(
            "1500/300個払出 표기는 예산 계산용 실전 근사 1400/280발로 사용. "
            "高ベース中의 特図1通常当り 時短500 예외와 残保留4는 별도 상태로 모델링하지 않음."
        ),
    ),
    "shin_eva_premium_99": eva_breakthrough_st_jitan(
        machine_id="shin_eva_premium_99",
        name_ja="ぱちんこ シン・エヴァンゲリオン PREMIUM MODEL",
        name_ko="P 신 에반게리온 프리미엄 모델",
        source="DMMぱちタウン machines/4865 / P-WORLD database/10331",
        normal_prob=99.9,
        high_prob=37.5,
        direct_rush_weight=0.01,
        challenge_st_weight=0.58,
        challenge_jitan_weight=0.41,
        challenge_st_spins=30,
        challenge_jitan_spins=30,
        rush_st_spins=30,
        rush_jitan_spins=70,
        first_10r_balls=930,
        first_3r_balls=280,
        right_10r_balls=930,
        right_3r_balls=280,
        right_10r_weight=0.50,
        right_3r_weight=0.50,
        risk_grade="1/99",
        spec_type="감데지 / 돌파형 ST",
        confidence="high",
        simplification_notes=(
            "ヘソ 1%는 RUSH 직행, 58%는 ST30 챌린지, 41%는 時短30 챌린지. "
            "챌린지 중 당첨 시 RUSH(ST30+時短70)로 승격."
        ),
        notes=(
            "DMM/P-WORLD의 約1000/300個払出을 예산 계산용 실전 근사 930/280발로 사용. "
            "残保留4 引き戻し는 별도 보류 상태 없이 회전수/벤치마크에 흡수."
        ),
    ),
    "eva_15_special_199": eva_vst_split_entry(
        machine_id="eva_15_special_199",
        name_ja="P新世紀エヴァンゲリオン〜未来への咆哮〜SPECIAL EDITION",
        name_ko="P 에바15 스페셜 에디션 199",
        source="DMMぱちタウン / P-WORLD database/9892",
        normal_prob=199.2,
        high_prob=82.6,
        st_spins=135,
        jitan_spins=100,
        first_10r_weight=0.01,
        first_3r_st_weight=0.24,
        first_3r_jitan_weight=0.75,
        first_10r_balls=1020,
        first_3r_balls=300,
        right_balls=1020,
        risk_grade="1/199",
        spec_type="라이트미들 / 돌파형 V-ST",
        confidence="high",
        simplification_notes=(
            "特図1 10R確変 1% / 3R確変 24% / 3R通常 75%. "
            "通常後 時短100 중 당첨 시 ST135으로 승격."
        ),
        notes=(
            "1100/330個払出 표기는 예산 계산용 실전 근사 1020/300발로 사용. "
            "高ベース中의 特図1通常当り 時短200 예외와 残保留4는 별도 상태로 모델링하지 않음."
        ),
    ),
}
