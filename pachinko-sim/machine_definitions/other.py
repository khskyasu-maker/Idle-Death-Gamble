from machine_types import Machine, Payout

OTHER_ADDITION_MACHINES = {
    # Other family additions.
    "lupin_77_sweet": Machine(
        id="lupin_77_sweet",
        name_ja="Pルパン三世 銭形からの招待状 77Sweet Ver.",
        name_ko="P 루팡3세 제니가타로부터의 초대장 77 Sweet Ver.",
        spec_type="甘デジ / 1種2種 LT",
        risk_grade="1/77",
        normal_prob=77.7,
        high_prob=37.3,
        normal_hit_dist=[
            Payout(balls=210, weight=0.51, next_state="ST", st_spins=34, ball_variance=0.03),
            Payout(balls=210, weight=0.49, next_state="NORMAL", counts_as_rush=False, ball_variance=0.03),
        ],
        st_hit_dist=[
            Payout(balls=1400, weight=0.15, next_state="LT", st_spins=88, is_lt=True, ball_variance=0.03),
            Payout(balls=700, weight=0.85, next_state="ST", st_spins=34, ball_variance=0.03),
        ],
        jitan_hit_dist=[],
        kakuben_hit_dist=[],
        lt_hit_dist=[
            Payout(balls=700, weight=1.00, next_state="LT", st_spins=88, is_lt=True, ball_variance=0.03),
        ],
        simplification_notes="初当り 51%でGOLDEN TIME(ST30+残保留4)へ突入. 右打ち中 15%の10R×2をLT神GOLDEN TIME(ST84+残保留4)として分離.",
        spec_source="P-WORLD news / HAZUSE DATA / DMMぱちタウン machines/4832",
        confidence="high",
        notes="700/1400/210払出をそのまま軽量LT体験モデルの予算値に使用. 残保留4はST回数に合算.",
        is_estimated=False,
    ),
    "kabaneri_2": Machine(
        id="kabaneri_2",
        name_ja="e甲鉄城のカバネリ2 咲かせや燦然",
        name_ko="e 갑철성의 카바네리2 사카세야 산젠",
        spec_type="スマパチ / 直LT ST",
        risk_grade="1/319",
        normal_prob=319.7,
        high_prob=98.3,
        normal_hit_dist=[
            Payout(balls=700, weight=0.50, next_state="LT", st_spins=134, is_lt=True, ball_variance=0.03),
            Payout(balls=700, weight=0.50, next_state="NORMAL", counts_as_rush=False, ball_variance=0.03),
        ],
        st_hit_dist=[],
        jitan_hit_dist=[],
        kakuben_hit_dist=[],
        lt_hit_dist=[
            Payout(balls=5580, weight=0.062, next_state="LT", st_spins=134, is_lt=True, ball_variance=0.03),
            Payout(balls=2790, weight=0.738, next_state="LT", st_spins=134, is_lt=True, ball_variance=0.03),
            Payout(balls=1400, weight=0.200, next_state="LT", st_spins=134, is_lt=True, ball_variance=0.03),
        ],
        simplification_notes="初当りは750払出の50%でLT直行. LTはST134回、右打ち中 6000/3000/1500払出比率を約93%の実戦予算値に変換.",
        spec_source="P-WORLD database/10400 / なな徹 / Pachiseven",
        confidence="high",
        notes="輪廻の果報の上乗せループは公開振分の6000+α枠を5580発代表値で近似.",
        is_estimated=False,
    ),
    "tokyo_ghoul": Machine(
        id="tokyo_ghoul",
        name_ja="e東京喰種",
        name_ko="e 도쿄구울",
        spec_type="スマパチ / 1種2種 LT",
        risk_grade="1/199合算",
        normal_prob=199.9,
        high_prob=95.3,
        normal_hit_dist=[
            Payout(balls=1400, weight=0.250, next_state="LT", st_spins=130, is_lt=True, ball_variance=0.03),
            Payout(balls=280, weight=0.005, next_state="LT", st_spins=130, is_lt=True, ball_variance=0.03),
            Payout(balls=1400, weight=0.245, next_state="NORMAL", counts_as_rush=False, ball_variance=0.03),
            Payout(balls=280, weight=0.500, next_state="NORMAL", counts_as_rush=False, ball_variance=0.03),
        ],
        st_hit_dist=[],
        jitan_hit_dist=[],
        kakuben_hit_dist=[],
        lt_hit_dist=[
            Payout(balls=5600, weight=0.03, next_state="LT", st_spins=130, is_lt=True, ball_variance=0.03),
            Payout(balls=2800, weight=0.97, next_state="LT", st_spins=130, is_lt=True, ball_variance=0.03),
        ],
        simplification_notes="図柄揃い1/399.9と喰種チャージ1/399.9を合算した通常1/199.9モデル. LT突入25.5%を低ベース通常条件の振分で反映.",
        spec_source="公式 pachi-e-tokyoghoul.jp / Pachiseven / pachinko-spec.info",
        confidence="high",
        notes="Pachinko-spec의実質玉数 1500払出=1400玉, 300払出=280玉 기준. 6000+α는5600発代表値로 근사.",
        is_estimated=False,
    ),
}

OTHER_TRAILING_MACHINES = {
    "hokuto_jibo": Machine(
        id="hokuto_jibo",
        name_ja="デジハネP北斗の拳 慈母",
        name_ko="디지하네 P 북두의 권 자모",
        spec_type="甘デジ / ST+時短 LT",
        risk_grade="1/79",
        normal_prob=79.9,
        high_prob=7.99,
        normal_hit_dist=[
            Payout(balls=900, weight=0.012, next_state="ST", st_spins=5, jitan_spins=50, ball_variance=0.03),
            Payout(balls=450, weight=0.788, next_state="ST", st_spins=5, jitan_spins=25, ball_variance=0.03),
            Payout(balls=120, weight=0.200, next_state="ST", st_spins=5, ball_variance=0.03),
        ],
        st_hit_dist=[
            Payout(balls=900, weight=0.010, next_state="LT", st_spins=5, jitan_spins=166, is_lt=True, ball_variance=0.03),
            Payout(balls=900, weight=0.002, next_state="ST", st_spins=5, jitan_spins=50, ball_variance=0.03),
            Payout(balls=450, weight=0.788, next_state="ST", st_spins=5, jitan_spins=25, ball_variance=0.03),
            Payout(balls=120, weight=0.200, next_state="ST", st_spins=5, jitan_spins=25, ball_variance=0.03),
        ],
        jitan_hit_dist=[
            Payout(balls=900, weight=0.010, next_state="LT", st_spins=5, jitan_spins=166, is_lt=True, ball_variance=0.03),
            Payout(balls=900, weight=0.002, next_state="ST", st_spins=5, jitan_spins=50, ball_variance=0.03),
            Payout(balls=450, weight=0.788, next_state="ST", st_spins=5, jitan_spins=25, ball_variance=0.03),
            Payout(balls=120, weight=0.200, next_state="ST", st_spins=5, jitan_spins=25, ball_variance=0.03),
        ],
        kakuben_hit_dist=[],
        lt_hit_dist=[
            Payout(balls=900, weight=0.012, next_state="LT", st_spins=5, jitan_spins=166, is_lt=True, ball_variance=0.03),
            Payout(balls=450, weight=0.788, next_state="LT", st_spins=5, jitan_spins=166, is_lt=True, ball_variance=0.03),
            Payout(balls=120, weight=0.200, next_state="LT", st_spins=5, jitan_spins=166, is_lt=True, ball_variance=0.03),
        ],
        simplification_notes="通常時は全大当り後CHANCE TIMEへ. LTはST5回+時短166回をLT→LT_JITANの2段階で処理し、LT中当りは全てLT継続.",
        spec_source="P-WORLD database/10235 / Pachiseven / DMMぱちタウン machines/4772",
        confidence="high",
        notes="1000/500/140払出は実戦予算値 900/450/120玉に変換. 特図2 10Rの1%だけLT、LT中は171回サポ継続.",
        is_estimated=False,
    ),

    "hokuto_10": Machine(
        id="hokuto_10",
        name_ja="e北斗の拳10",
        name_ko="e 북두의 권 10",
        spec_type="스마트 파친코 / 전락형 LT",
        risk_grade="1/349",
        normal_prob=348.6,
        high_prob=40.0,
        normal_hit_dist=[
            Payout(balls=1500, weight=0.05, next_state="ST", st_spins=10000),
            Payout(balls=300, weight=0.70, next_state="ST", st_spins=10000),
            Payout(balls=300, weight=0.01, next_state="LT", st_spins=10000, is_lt=True),
            Payout(balls=300, weight=0.04, next_state="ST", st_spins=10000),
            Payout(balls=300, weight=0.20, next_state="NORMAL", counts_as_rush=False),
        ],
        st_hit_dist=[
            Payout(balls=1500, weight=0.126, next_state="LT", st_spins=10000, is_lt=True),
            Payout(balls=1500, weight=0.574, next_state="ST", st_spins=10000),
            Payout(balls=450, weight=0.300, next_state="ST", st_spins=10000),
        ],
        jitan_hit_dist=[],
        kakuben_hit_dist=[],
        lt_hit_dist=[
            Payout(balls=1500, weight=0.70, next_state="LT", st_spins=10000, is_lt=True),
            Payout(balls=450, weight=0.30, next_state="LT", st_spins=10000, is_lt=True),
        ],
        simplification_notes=(
            "BATTLE MODE/HYPER BATTLE MODE는 大当りor転落小当り까지인 전락형으로 모델링. "
            "전락 시 残保留4개引き戻し를 포함해 공개 継続率 약80%/약89%에 맞춥니다."
        ),
        spec_source="P-WORLD database/10054 / なな徹 / Pachiseven",
        confidence="high",
        notes=(
            "ヘソ 5% 10R+BATTLE, 70% 2R+BATTLE, 1% 2R+HYPER, 4% 2R+BATTLE, 20% 通常. "
            "BATTLE 중 10R의 약36%에서 無想転生チャンス, 그중 약50% 성공을 LT 전이 12.6%로 반영. "
            "世紀末チャージ(特図1小当り 約1/478)의 1% HYPER 루트는 보수적으로 별도 초당첨 확률에 합산하지 않음."
        ),
        is_estimated=False,
        fall_prob={"ST": 136.9, "LT": 275.9},
        fall_reserve_spins={"ST": 4, "LT": 4},
    ),
}
