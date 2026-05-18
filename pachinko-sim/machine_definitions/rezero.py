from machine_types import Machine, Payout

REZERO_INITIAL_MACHINES = {
    # C-8. P Re:ゼロから始める異世界生活 鬼がかり 99ver. (리제로 99)
    "re_zero_99": Machine(
        id="re_zero_99",
        name_ja="P Re:ゼロから始める異世界生活 鬼がかり 99ver.",
        name_ko="P 리제로 귀신들린 99버전",
        spec_type="감데지 / ST",
        risk_grade="1/99",
        normal_prob=99.9,
        high_prob=79.9,
        normal_hit_dist=[
            Payout(balls=300, weight=0.50, next_state='ST', st_spins=104),
            Payout(balls=300, weight=0.50, next_state='NORMAL')
        ],
        st_hit_dist=[
            Payout(balls=1800, weight=0.25, next_state='ST', st_spins=104),
            Payout(balls=900, weight=0.50, next_state='ST', st_spins=104),
            Payout(balls=300, weight=0.05, next_state='ST', st_spins=104),
            Payout(balls=0, weight=0.20, next_state='ST', st_spins=104),
        ],
        jitan_hit_dist=[],
        kakuben_hit_dist=[],
        lt_hit_dist=[],
        simplification_notes="50%로 RUSH(ST104회) 진입. 電チュー는 1800/900/300/Re:Start를 실제 비율로 분리.",
        spec_source="P-WORLD database/10364 / Pachiseven",
        confidence="high",
        notes="Re:Start는 0발 ST 리셋으로 모델링.",
        is_estimated=False,
    ),

    # C-9. P Re:ゼロから始める異世界生活 鬼がかり 199ver. (리제로 199)
    "re_zero_199": Machine(
        id="re_zero_199",
        name_ja="P Re:ゼロから始める異世界生活 鬼がかり 199ver.",
        name_ko="P 리제로 귀신들린 199버전",
        spec_type="라이트미들 / ST",
        risk_grade="1/199",
        normal_prob=199.8,
        high_prob=105.9,
        normal_hit_dist=[
            Payout(balls=300, weight=0.55, next_state='ST', st_spins=144),
            Payout(balls=300, weight=0.45, next_state='NORMAL')
        ],
        st_hit_dist=[
            Payout(balls=3000, weight=0.40, next_state='ST', st_spins=144),
            Payout(balls=1500, weight=0.40, next_state='ST', st_spins=144),
            Payout(balls=0, weight=0.20, next_state='ST', st_spins=144),
        ],
        jitan_hit_dist=[],
        kakuben_hit_dist=[],
        lt_hit_dist=[],
        simplification_notes="55%로 RUSH(ST144회) 진입. 電チュー는 3000/1500/Re:Start를 실제 비율로 분리.",
        spec_source="P-WORLD database/10363 / なな徹",
        confidence="high",
        notes="Re:Start는 0발 ST 리셋으로 모델링.",
        is_estimated=False,
    )
}

REZERO_ADDITION_MACHINES = {
    # Re:Zero additions. User scope keeps non-Eva/Umi additions to Re:Zero only.
    "re_zero_319": Machine(
        id="re_zero_319",
        name_ja="P Re:ゼロから始める異世界生活 鬼がかりver.",
        name_ko="P 리제로 귀신들린 버전",
        spec_type="리제로 / 1種2種 RUSH",
        risk_grade="1/319",
        normal_prob=319.6,
        high_prob=99.9,
        normal_hit_dist=[
            Payout(balls=3000, weight=0.55, next_state="ST", st_spins=144),
            Payout(balls=1500, weight=0.45, next_state="NORMAL"),
        ],
        st_hit_dist=[
            Payout(balls=3000, weight=0.25, next_state="ST", st_spins=144),
            Payout(balls=1500, weight=0.55, next_state="ST", st_spins=144),
            Payout(balls=300, weight=0.06, next_state="ST", st_spins=144),
            Payout(balls=0, weight=0.14, next_state="ST", st_spins=144),
        ],
        jitan_hit_dist=[],
        kakuben_hit_dist=[],
        lt_hit_dist=[],
        simplification_notes="通常時 3000発+RUSH 55% / 1500発通常 45%. RUSH中은 3000/1500/300/Re:Start 실제比率.",
        spec_source="P-WORLD database/9537 / Pachiseven / Dechau",
        confidence="high",
        notes="Re:Start는 0발 ST 리셋으로 모델링.",
        is_estimated=False,
    ),
    "re_zero_s2_349": Machine(
        id="re_zero_s2_349",
        name_ja="e Re:ゼロから始める異世界生活 season2",
        name_ko="e 리제로 시즌2",
        spec_type="스마트 파친코 / 1種2種 RUSH",
        risk_grade="1/349",
        normal_prob=349.9,
        high_prob=99.9,
        normal_hit_dist=[
            Payout(balls=3000, weight=0.55, next_state="ST", st_spins=145),
            Payout(balls=1500, weight=0.45, next_state="NORMAL"),
        ],
        st_hit_dist=[
            Payout(balls=3000, weight=0.25, next_state="ST", st_spins=145),
            Payout(balls=1500, weight=0.55, next_state="ST", st_spins=145),
            Payout(balls=300, weight=0.20, next_state="ST", st_spins=145),
        ],
        jitan_hit_dist=[],
        kakuben_hit_dist=[],
        lt_hit_dist=[],
        simplification_notes="通常時 RUSH突入時は約3000発+α로 ST145, 非突入은約1500発通常. RUSH中은 3000/1500/300 실제比率.",
        spec_source="P-WORLD database/9931 / なな徹",
        confidence="high",
        notes="3000発+α의 추가上乗せ는 3000발 대표값으로 보수화.",
        is_estimated=False,
    ),
    "re_zero_s2_129": Machine(
        id="re_zero_s2_129",
        name_ja="P Re:ゼロから始める異世界生活 season2 129ver.",
        name_ko="P 리제로 시즌2 129버전",
        spec_type="라이트 / RUSH+LT 보너스",
        risk_grade="1/129",
        normal_prob=129.9,
        high_prob=99.9,
        normal_hit_dist=[
            Payout(balls=300, weight=0.50, next_state="ST", st_spins=120),
            Payout(balls=300, weight=0.50, next_state="NORMAL"),
        ],
        st_hit_dist=[
            Payout(balls=9000, weight=0.03225, next_state="ST", st_spins=120, is_lt=True),
            Payout(balls=6000, weight=0.02450, next_state="ST", st_spins=120, is_lt=True),
            Payout(balls=4500, weight=0.01850, next_state="ST", st_spins=120, is_lt=True),
            Payout(balls=3000, weight=0.02450, next_state="ST", st_spins=120, is_lt=True),
            Payout(balls=1800, weight=0.02525, next_state="ST", st_spins=120, is_lt=True),
            Payout(balls=1500, weight=0.12500, next_state="ST", st_spins=120),
            Payout(balls=750, weight=0.55000, next_state="ST", st_spins=120),
            Payout(balls=300, weight=0.20000, next_state="ST", st_spins=120),
        ],
        jitan_hit_dist=[],
        kakuben_hit_dist=[],
        lt_hit_dist=[],
        simplification_notes="RUSH 중 1500個 25% 중 절반을 LT 보너스로 분리. LT는 별도 전サポ 상태가 아니라 대량出玉 후 ST120으로 복귀하는 보너스로 모델링.",
        spec_source="P-WORLD database/10435 / P-WORLD news / Pachiseven",
        confidence="high",
        notes="超強欲PREMIUM BONUS의 300個 약 95% 루프는 공개 출玉帯 분포(9000/6000/4500/3000/1800+)로 근사.",
        is_estimated=False,
    ),
}
