from dataclasses import dataclass, field
from typing import List, Dict

@dataclass
class Payout:
    balls: int
    weight: float
    next_state: str  # 'NORMAL', 'ST', 'JITAN', 'KAKUBEN', 'LT', 'UPPER', 'JINBEE', 'JINBEE_JITAN'
    st_spins: int = 0
    jitan_spins: int = 0
    is_lt: bool = False
    ball_variance: float = 0.08
    counts_as_rush: bool = True

@dataclass
class Machine:
    id: str
    name_ja: str
    name_ko: str
    spec_type: str
    risk_grade: str
    
    normal_prob: float
    high_prob: float
    
    # 상태별 당첨 시 출옥 및 상태 전이 분포
    normal_hit_dist: List[Payout]
    st_hit_dist: List[Payout]
    jitan_hit_dist: List[Payout]
    kakuben_hit_dist: List[Payout]
    lt_hit_dist: List[Payout]
    upper_hit_dist: List[Payout] = field(default_factory=list)
    jinbee_hit_dist: List[Payout] = field(default_factory=list)
    
    simplification_notes: str = ""
    spec_source: str = "manual_estimate"
    confidence: str = "medium"  # high / medium / low
    notes: str = ""
    is_estimated: bool = True
    right_spend_per_spin: Dict[str, float] = field(
        default_factory=lambda: {
            "ST": 0.20,
            "JITAN": 0.35,
            "RUSH": 0.20,
            "LT": 0.25,
            "UPPER": 0.25,
            "KAKUBEN": 0.15,
            "JINBEE": 0.15,
            "JINBEE_JITAN": 0.35,
        }
    )
    fall_prob: Dict[str, float] = field(default_factory=dict)
    fall_reserve_spins: Dict[str, int] = field(default_factory=dict)
    normal_support_prob: float = 0.0
    normal_support_dist: List[Payout] = field(default_factory=list)


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

MACHINES = {
    # A-1. Pスーパー海物語IN沖縄6 (미들)
    "oki_sea_6": Machine(
        id="oki_sea_6",
        name_ja="Pスーパー海物語IN沖縄6",
        name_ko="P 슈퍼 바다이야기 IN 오키나와6",
        spec_type="미들 / 확변 루프 + ジンベェタイム",
        risk_grade="1/319",
        normal_prob=319.6,
        high_prob=31.9,
        normal_hit_dist=[
            Payout(balls=1500, weight=0.40, next_state="KAKUBEN"),
            Payout(balls=60, weight=0.20, next_state="KAKUBEN"),
            Payout(balls=1500, weight=0.40, next_state="JITAN", jitan_spins=100),
        ],
        st_hit_dist=[],
        jitan_hit_dist=[
            Payout(balls=1500, weight=0.01, next_state="JINBEE"),
            Payout(balls=1500, weight=0.51, next_state="KAKUBEN"),
            Payout(balls=60, weight=0.08, next_state="JINBEE"),
            Payout(balls=1500, weight=0.40, next_state="JITAN", jitan_spins=100),
        ],
        kakuben_hit_dist=[
            Payout(balls=1500, weight=0.01, next_state="JINBEE"),
            Payout(balls=1500, weight=0.51, next_state="KAKUBEN"),
            Payout(balls=60, weight=0.08, next_state="JINBEE"),
            Payout(balls=1500, weight=0.40, next_state="JITAN", jitan_spins=100),
        ],
        lt_hit_dist=[],
        jinbee_hit_dist=[
            Payout(balls=1500, weight=0.52, next_state="JINBEE"),
            Payout(balls=60, weight=0.08, next_state="JINBEE"),
            Payout(balls=1500, weight=0.40, next_state="JINBEE_JITAN", jitan_spins=200),
        ],
        simplification_notes="通常時 40% 10R確変/20% 2R確変/40% 10R通常. 電サポ中의 10R確変-A 1%와 2R確変 8%는 ジンベェタイム으로 분리.",
        spec_source="P-WORLD database/10321 / なな徹 / Pachiseven",
        confidence="high",
        notes="ジンベェタイム 중 通常当り 후 時短200을 JINBEE_JITAN 상태로 별도 모델링. 沖海3000BONUS 보류연 연출은 독립 당첨으로 처리.",
        is_estimated=False,
    ),

    # A-2. PAスーパー海物語 IN 沖縄5 with アイマリン (감데지)
    "oki_sea_5_imarine": Machine(
        id="oki_sea_5_imarine",
        name_ja="PAスーパー海物語 IN 沖縄5 with アイマリン",
        name_ko="PA 슈퍼 바다이야기 IN 오키나와5 with 아이마린",
        spec_type="감데지 / ST",
        risk_grade="1/99",
        normal_prob=99.9,
        high_prob=9.9,
        normal_hit_dist=[
            Payout(balls=1100, weight=0.10, next_state='ST', st_spins=5, jitan_spins=95),
            Payout(balls=550, weight=0.33, next_state='ST', st_spins=5, jitan_spins=45),
            Payout(balls=550, weight=0.57, next_state='ST', st_spins=5, jitan_spins=20)
        ],
        st_hit_dist=[
            Payout(balls=1100, weight=0.10, next_state='ST', st_spins=5, jitan_spins=95),
            Payout(balls=550, weight=0.33, next_state='ST', st_spins=5, jitan_spins=45),
            Payout(balls=550, weight=0.57, next_state='ST', st_spins=5, jitan_spins=20)
        ],
        jitan_hit_dist=[
            Payout(balls=1100, weight=0.10, next_state='ST', st_spins=5, jitan_spins=95),
            Payout(balls=550, weight=0.33, next_state='ST', st_spins=5, jitan_spins=45),
            Payout(balls=550, weight=0.57, next_state='ST', st_spins=5, jitan_spins=20)
        ],
        kakuben_hit_dist=[],
        lt_hit_dist=[],
        simplification_notes="ST 5회 소진 시 자동으로 남은 jitan_spins 만큼 시단(JITAN) 상태로 전환되도록 구현.",
        spec_source="P-WORLD database/9421 / なな徹 / Pachiseven",
        confidence="high",
        notes="ヘソ・電チュー共通 10R 10% / 5R時短45 57% / 5R時短20 33%를 반영.",
        is_estimated=False,
    ),

    # A-2b. PAスーパー海物語 IN 沖縄5 夜桜超旋風 99ver. (감데지)
    "oki_sea_5_yozakura_99": Machine(
        id="oki_sea_5_yozakura_99",
        name_ja="PAスーパー海物語 IN 沖縄5 夜桜超旋風 99ver.",
        name_ko="PA 슈퍼 바다이야기 IN 오키나와5 밤벚꽃 초선풍 99버전",
        spec_type="감데지 / 1種2種 RUSH",
        risk_grade="1/99",
        normal_prob=99.9,
        high_prob=3.99,
        normal_hit_dist=[
            Payout(balls=350, weight=0.50, next_state="ST", st_spins=8),
            Payout(balls=350, weight=0.50, next_state="NORMAL"),
        ],
        st_hit_dist=[
            Payout(balls=700, weight=0.10, next_state="ST", st_spins=8),
            Payout(balls=210, weight=0.90, next_state="ST", st_spins=8),
        ],
        jitan_hit_dist=[
        ],
        kakuben_hit_dist=[],
        lt_hit_dist=[],
        simplification_notes="初当り는 전부 5R이며 50%만 RUSH. RUSH는 6회+残保留2개를 8회로 합산하고, 오른쪽 10R 10%/3R 90%를 반영.",
        spec_source="P-WORLD database/9748 / DMM machines/4270 / Dechau",
        confidence="high",
        notes="1種2種의 V入賞 실패 가능성과 보류별 연출 차이는 모델링하지 않습니다.",
        is_estimated=False,
    ),

    # A-3. PA大海物語5ブラックLT99ver. (감데지 LT)
    "sea_5_black_lt": Machine(
        id="sea_5_black_lt",
        name_ja="PA大海物語5ブラックLT99ver.",
        name_ko="PA 대해물어5 블랙 LT 99버전",
        spec_type="감데지 / LT",
        risk_grade="1/99",
        normal_prob=99.9,
        high_prob=41.0,
        normal_hit_dist=[
            Payout(balls=330, weight=0.70, next_state='ST', st_spins=39),
            Payout(balls=330, weight=0.30, next_state='NORMAL')
        ],
        st_hit_dist=[
            Payout(balls=880, weight=0.10, next_state='LT', st_spins=110, is_lt=True), # 10% LT 진입
            Payout(balls=880, weight=0.30, next_state='ST', st_spins=39),
            Payout(balls=330, weight=0.60, next_state='ST', st_spins=39)
        ],
        jitan_hit_dist=[],
        kakuben_hit_dist=[],
        lt_hit_dist=[
            Payout(balls=880, weight=0.40, next_state='LT', st_spins=110, is_lt=True),
            Payout(balls=330, weight=0.60, next_state='LT', st_spins=110, is_lt=True)
        ],
        simplification_notes="初当り는 전부 3R이며 70%가 ST. 일반 ST는 35회+残保留4개를 39회로 합산, ST 중 大当り는 8R LT 10% / 8R ST 30% / 3R ST 60%. LT는 공개 継続期待値 약93%에 맞춰 110회로 모델링.",
        spec_source="P-WORLD database/10197 / DMM machines/4735",
        confidence="high",
        notes="LT 종료 후 잔보류 당첨의 일반 ST振分 예외는 보수적으로 제외.",
        is_estimated=False,
    ),

    # B-4. 新世紀エヴァンゲリオン〜未来への咆哮〜 (에바15 미들)
    "eva_15_roar": Machine(
        id="eva_15_roar",
        name_ja="新世紀エヴァンゲリオン〜未来への咆哮〜",
        name_ko="신세기 에반게리온 미래로의 포효 (에바15)",
        spec_type="미들 / V-ST",
        risk_grade="1/319",
        normal_prob=319.7,
        high_prob=99.4,
        normal_hit_dist=[
            Payout(balls=1500, weight=0.03, next_state="ST", st_spins=163),
            Payout(balls=450, weight=0.56, next_state="ST", st_spins=163),
            Payout(balls=450, weight=0.41, next_state="JITAN", jitan_spins=100, counts_as_rush=False),
        ],
        st_hit_dist=[
            Payout(balls=1500, weight=1.00, next_state="ST", st_spins=163)
        ],
        jitan_hit_dist=[
            Payout(balls=1500, weight=1.00, next_state="ST", st_spins=163)
        ],
        kakuben_hit_dist=[],
        lt_hit_dist=[],
        simplification_notes="特図1 10R確変 3% / 3R確変 56% / 3R通常 41%. 時短100 중 당첨 시 ST163으로 승격.",
        spec_source="P-WORLD / DMMぱちタウン / SANKYO",
        confidence="high",
        notes="残保留 4개引き戻し는 별도 보류 상태 없이 ST/時短 회전수에 일부 흡수.",
        is_estimated=False,
    ),

    # B-5. P新世紀エヴァンゲリオン〜未来への咆哮〜PREMIUM MODEL (에바15 프리미엄 1/129)
    "eva_15_premium": Machine(
        id="eva_15_premium",
        name_ja="P新世紀エヴァンゲリオン〜未来への咆哮〜PREMIUM MODEL",
        name_ko="P 신세기 에반게리온 미래로의 포효 프리미엄 모델",
        spec_type="라이트 / 돌파형 V-ST",
        risk_grade="1/129",
        normal_prob=129.8,
        high_prob=35.7,
        normal_hit_dist=[
            Payout(balls=1000, weight=0.10, next_state='ST', st_spins=30, jitan_spins=100),
            Payout(balls=300, weight=0.54, next_state='ST', st_spins=30, counts_as_rush=False),
            Payout(balls=300, weight=0.36, next_state='JITAN', jitan_spins=30, counts_as_rush=False),
        ],
        st_hit_dist=[
            Payout(balls=1000, weight=0.60, next_state='ST', st_spins=30, jitan_spins=100),
            Payout(balls=300, weight=0.40, next_state='ST', st_spins=30, jitan_spins=100)
        ],
        jitan_hit_dist=[
            Payout(balls=1000, weight=0.60, next_state='ST', st_spins=30, jitan_spins=100),
            Payout(balls=300, weight=0.40, next_state='ST', st_spins=30, jitan_spins=100)
        ],
        kakuben_hit_dist=[],
        lt_hit_dist=[],
        simplification_notes="ヘソ 10%는 RUSH 직행, 54%는 ST30 챌린지, 36%는 時短30 챌린지. 챌린지 중 당첨 시 RUSH(ST30+時短100)로 승격.",
        spec_source="P-WORLD database/9993 / DMMぱちタウン machines/4498",
        confidence="high",
        notes="残保留 4개引き戻し 약 3%는 별도 보류 상태 없이 챌린지/RUSH 회전수에 일부 흡수.",
        is_estimated=False,
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
            Payout(balls=1000, weight=0.005, next_state="LT", st_spins=127, is_lt=True),
            Payout(balls=300, weight=0.500, next_state="ST", st_spins=64),
            Payout(balls=300, weight=0.495, next_state="NORMAL"),
        ],
        st_hit_dist=[
            Payout(balls=1000, weight=0.10, next_state="LT", st_spins=127, is_lt=True),
            Payout(balls=1000, weight=0.90, next_state="ST", st_spins=64),
        ],
        jitan_hit_dist=[
        ],
        kakuben_hit_dist=[],
        lt_hit_dist=[
            Payout(balls=1000, weight=1.00, next_state="LT", st_spins=127, is_lt=True)
        ],
        simplification_notes="ヘソ 0.5% LT 직행, 50.0% RUSH, 49.5% 통상. RUSH는 60회+残保留4개, LT는 123회+残保留4개로 합산.",
        spec_source="P-WORLD database/10206 / DMM machines/4736 / なな徹",
        confidence="high",
        notes="오른쪽은 ALL 10R 1000발. RUSH 중 10% LT, LT 중 100% LT継続 분포 반영.",
        is_estimated=False,
    ),

    # B-7. e 新世紀エヴァンゲリオン ～はじまりの記憶～ (1/399)
    "eva_beginning": Machine(
        id="eva_beginning",
        name_ja="e新世紀エヴァンゲリオン ～はじまりの記憶～",
        name_ko="e 신세기 에반게리온 시작의 기억",
        spec_type="스마트 파친코 / 399 V-ST",
        risk_grade="1/399",
        normal_prob=399.9,
        high_prob=99.6,
        normal_hit_dist=[
            Payout(balls=1500, weight=0.005, next_state="ST", st_spins=157),
            Payout(balls=300, weight=0.500, next_state="ST", st_spins=157),
            Payout(balls=300, weight=0.495, next_state="JITAN", jitan_spins=100),
        ],
        st_hit_dist=[
            Payout(balls=4800, weight=0.005, next_state="ST", st_spins=157),
            Payout(balls=2400, weight=0.995, next_state="ST", st_spins=157),
        ],
        jitan_hit_dist=[
            Payout(balls=300, weight=1.00, next_state="ST", st_spins=157),
        ],
        kakuben_hit_dist=[],
        lt_hit_dist=[],
        simplification_notes="ヘソ는 0.5% 10R RUSH, 50.0% 2R RUSH, 49.5% 2R+時短100. 오른쪽은 8R×2=2400발 중심, 0.5%만 8R×4로 근사.",
        spec_source="P-WORLD database/10353 / 777パチガブ / SANKYO",
        confidence="medium",
        notes="チャージ込み大当り確率(約1/349.9)은 별도 상태로 구현하지 않았습니다. 399 고위험성은 유지하되 오른쪽 2400발 구조는 반영.",
    ),

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

MACHINES.update(
    {
        # DMM-confirmed Umi / Sea family additions.
        "sea_5": sea_kakuhen_10r(
            "sea_5",
            "P大海物語5",
            "P 대해물어5",
            "DMMぱちタウン machines/4293",
            confidence="high",
        ),
        "sea_5_special": Machine(
            id="sea_5_special",
            name_ja="P大海物語5スペシャル",
            name_ko="P 대해물어5 스페셜",
            spec_type="미들 / 확변 루프",
            risk_grade="1/319",
            normal_prob=319.6,
            high_prob=31.9,
            normal_hit_dist=[
                Payout(balls=1500, weight=0.54, next_state="KAKUBEN"),
                Payout(balls=1500, weight=0.46, next_state="JITAN", jitan_spins=100, counts_as_rush=False),
            ],
            st_hit_dist=[],
            jitan_hit_dist=[
                Payout(balls=1500, weight=0.54, next_state="KAKUBEN"),
                Payout(balls=1500, weight=0.46, next_state="JITAN", jitan_spins=200),
            ],
            kakuben_hit_dist=[
                Payout(balls=1500, weight=0.54, next_state="KAKUBEN"),
                Payout(balls=1500, weight=0.46, next_state="JITAN", jitan_spins=100),
            ],
            lt_hit_dist=[],
            simplification_notes="ヘソ/電チュー共通 54%確変・46%通常. 時短/遊タイム中の通常当り後だけ 時短200으로 분리.",
            spec_source="P-WORLD database/10112 / DMMぱちタウン",
            confidence="high",
            notes="遊タイム 950회 도달 후 時短350은 시작回転 입력 기능이 없어 미반영.",
            is_estimated=False,
        ),
        "sea_3r3": Machine(
            id="sea_3r3",
            name_ja="PA海物語3R3",
            name_ko="PA 바다이야기 3R3",
            spec_type="감데지 / 확변 루프",
            risk_grade="1/99",
            normal_prob=99.9,
            high_prob=16.9,
            normal_hit_dist=[
                Payout(balls=1000, weight=0.05, next_state="KAKUBEN"),
                Payout(balls=500, weight=0.46, next_state="KAKUBEN"),
                Payout(balls=500, weight=0.49, next_state="JITAN", jitan_spins=40, counts_as_rush=False),
            ],
            st_hit_dist=[],
            jitan_hit_dist=[
                Payout(balls=1000, weight=0.05, next_state="KAKUBEN"),
                Payout(balls=500, weight=0.46, next_state="KAKUBEN"),
                Payout(balls=500, weight=0.49, next_state="JITAN", jitan_spins=40),
            ],
            kakuben_hit_dist=[
                Payout(balls=1000, weight=0.05, next_state="KAKUBEN"),
                Payout(balls=500, weight=0.46, next_state="KAKUBEN"),
                Payout(balls=500, weight=0.49, next_state="JITAN", jitan_spins=40),
            ],
            lt_hit_dist=[],
            simplification_notes="ヘソ・電チュー共通の確変51% 루프. 通常49%는 時短40회로 분리하고, 時短 중 확률은 저확률 1/99.9로 처리.",
            spec_source="Pachiseven machines/7162 / DMMぱちタウン machines/4795",
            confidence="high",
            notes="DMM 표기 출옥 490/990개와 Pachiseven 지급 500/1000개 차이는 지급 기준 500/1000으로 통일.",
            is_estimated=False,
        ),
        "sea_5_black_199": Machine(
            id="sea_5_black_199",
            name_ja="P大海物語5 ブラック",
            name_ko="P 대해물어5 블랙",
            spec_type="라이트미들 / ST + GOLDパールRUSH",
            risk_grade="1/199",
            normal_prob=199.8,
            high_prob=44.0,
            normal_hit_dist=[
                Payout(balls=450, weight=1.00, next_state="ST", st_spins=54),
            ],
            st_hit_dist=[
                Payout(balls=1500, weight=0.04, next_state="UPPER", st_spins=90),
                Payout(balls=1500, weight=0.46, next_state="ST", st_spins=54),
                Payout(balls=450, weight=0.50, next_state="ST", st_spins=54),
            ],
            jitan_hit_dist=[],
            kakuben_hit_dist=[],
            lt_hit_dist=[],
            upper_hit_dist=[
                Payout(balls=1500, weight=0.50, next_state="UPPER", st_spins=90),
                Payout(balls=450, weight=0.50, next_state="UPPER", st_spins=90),
            ],
            simplification_notes="初当り後は通常ST 50回+残保留4. ST中大当り의 4%만 GOLDパールRUSH(86回+残保留4)로 승격.",
            spec_source="P-WORLD database/9916 / P-WORLD news",
            confidence="high",
            notes="GOLDパールRUSH는 LT가 아닌 상위ST로 집계하며, LT 진입률에는 포함하지 않습니다.",
            is_estimated=False,
        ),
        "sea_4_special_black": Machine(
            id="sea_4_special_black",
            name_ja="P大海物語4スペシャルBLACK",
            name_ko="P 대해물어4 스페셜 BLACK",
            spec_type="라이트미들 / ST",
            risk_grade="1/199",
            normal_prob=199.8,
            high_prob=40.6,
            normal_hit_dist=[
                Payout(balls=1500, weight=0.30, next_state="ST", st_spins=51),
                Payout(balls=750, weight=0.30, next_state="ST", st_spins=51),
                Payout(balls=450, weight=0.40, next_state="ST", st_spins=51),
            ],
            st_hit_dist=[
                Payout(balls=1500, weight=0.30, next_state="ST", st_spins=51),
                Payout(balls=750, weight=0.30, next_state="ST", st_spins=51),
                Payout(balls=450, weight=0.40, next_state="ST", st_spins=51),
            ],
            jitan_hit_dist=[],
            kakuben_hit_dist=[],
            lt_hit_dist=[],
            simplification_notes="ST突入率100%, ST51회(전サポ50회)를 하나의 ST 상태로 모델링. 10R30% / 5R30% / 3R40%를 반영.",
            spec_source="Pachiseven machines/6278 / Dechau machine/545",
            confidence="high",
            notes="1회전만 잠복ST가 되는 전サポ50회 표기는 실전 체감상 ST51회 추첨으로 합산.",
            is_estimated=False,
        ),
        "sea_4_special": Machine(
            id="sea_4_special",
            name_ja="P大海物語4スペシャル",
            name_ko="P 대해물어4 스페셜",
            spec_type="미들 / 확변 루프",
            risk_grade="1/319",
            normal_prob=319.6,
            high_prob=39.7,
            normal_hit_dist=[
                Payout(balls=1500, weight=0.52, next_state="KAKUBEN"),
                Payout(balls=1500, weight=0.48, next_state="JITAN", jitan_spins=100, counts_as_rush=False),
            ],
            st_hit_dist=[],
            jitan_hit_dist=[
                Payout(balls=1500, weight=0.52, next_state="KAKUBEN"),
                Payout(balls=1500, weight=0.48, next_state="JITAN", jitan_spins=120),
            ],
            kakuben_hit_dist=[
                Payout(balls=1500, weight=0.52, next_state="KAKUBEN"),
                Payout(balls=1500, weight=0.48, next_state="JITAN", jitan_spins=120),
            ],
            lt_hit_dist=[],
            simplification_notes="ヘソ・電チュー共通 10R確変52% / 10R通常48%. 非電サポ通常後は時短100, 電サポ中通常後는 時短120으로 분리.",
            spec_source="P-WORLD database/9256 / Pachiseven machines/6165 / なな徹",
            confidence="high",
            notes="遊タイム950회 도달 시 時短350은 시작 회전수 입력이 없어 미반영.",
            is_estimated=False,
        ),
        "sea_4_agnes": Machine(
            id="sea_4_agnes",
            name_ja="PA大海物語4スペシャル Withアグネス・ラム",
            name_ko="PA 대해물어4 스페셜 With 아그네스 램",
            spec_type="감데지 / ST+時短",
            risk_grade="1/99",
            normal_prob=99.9,
            high_prob=19.5,
            normal_hit_dist=[
                Payout(balls=1080, weight=0.04, next_state="ST", st_spins=10, jitan_spins=90),
                Payout(balls=648, weight=0.60, next_state="ST", st_spins=10, jitan_spins=40),
                Payout(balls=432, weight=0.06, next_state="ST", st_spins=10, jitan_spins=40),
                Payout(balls=432, weight=0.30, next_state="ST", st_spins=10, jitan_spins=15),
            ],
            st_hit_dist=[
                Payout(balls=1080, weight=0.04, next_state="ST", st_spins=10, jitan_spins=90),
                Payout(balls=648, weight=0.60, next_state="ST", st_spins=10, jitan_spins=40),
                Payout(balls=432, weight=0.06, next_state="ST", st_spins=10, jitan_spins=40),
                Payout(balls=432, weight=0.30, next_state="ST", st_spins=10, jitan_spins=15),
            ],
            jitan_hit_dist=[
                Payout(balls=1080, weight=0.04, next_state="ST", st_spins=10, jitan_spins=90),
                Payout(balls=648, weight=0.60, next_state="ST", st_spins=10, jitan_spins=40),
                Payout(balls=432, weight=0.06, next_state="ST", st_spins=10, jitan_spins=40),
                Payout(balls=432, weight=0.30, next_state="ST", st_spins=10, jitan_spins=15),
            ],
            kakuben_hit_dist=[],
            lt_hit_dist=[],
            simplification_notes="ST10회 + 時短15/40/90회. 공개振分 10R4%, 6R60%, 4R6%/30%를 반영.",
            spec_source="Pachiseven machines/6204 / なな徹",
            confidence="high",
            notes="遊タイム379회는 시작回転 입력이 없어 미반영.",
            is_estimated=False,
        ),
        "sea_extreme_japan": Machine(
            id="sea_extreme_japan",
            name_ja="P海物語 極JAPAN",
            name_ko="P 바다이야기 극 JAPAN",
            spec_type="미들 / 1種2種 ST",
            risk_grade="1/319",
            normal_prob=319.6,
            high_prob=73.9,
            normal_hit_dist=[
                Payout(balls=1500, weight=0.50, next_state="ST", st_spins=104),
                Payout(balls=1500, weight=0.50, next_state="ST", st_spins=24, counts_as_rush=False),
            ],
            st_hit_dist=[
                Payout(balls=3000, weight=0.20, next_state="ST", st_spins=104),
                Payout(balls=1500, weight=0.55, next_state="ST", st_spins=104),
                Payout(balls=300, weight=0.25, next_state="ST", st_spins=104),
            ],
            jitan_hit_dist=[],
            kakuben_hit_dist=[],
            lt_hit_dist=[],
            simplification_notes="初回はロングST100+残保留4이 50%, ショートST20+残保留4이 50%. ショートST 중 당첨은 ロングST로 승격된다고 모델링.",
            spec_source="P-WORLD database/10219 / Pachiseven machines/7123",
            confidence="high",
            notes="極ノ刻 토털 돌입률은 직행50%와 極チャンス引き戻し를 시뮬에서 자연 발생시킵니다.",
            is_estimated=False,
        ),
        "sea_extreme_japan_naginami": Machine(
            id="sea_extreme_japan_naginami",
            name_ja="PA海物語 極JAPAN Withナギナミ",
            name_ko="PA 바다이야기 극 JAPAN With 나기나미",
            spec_type="감데지 / 1種2種 ST",
            risk_grade="1/99",
            normal_prob=99.9,
            high_prob=56.2,
            normal_hit_dist=[
                Payout(balls=240, weight=0.50, next_state="ST", st_spins=74),
                Payout(balls=240, weight=0.50, next_state="ST", st_spins=20, counts_as_rush=False),
            ],
            st_hit_dist=[
                Payout(balls=800, weight=0.05, next_state="ST", st_spins=74),
                Payout(balls=240, weight=0.95, next_state="ST", st_spins=74),
            ],
            jitan_hit_dist=[],
            kakuben_hit_dist=[],
            lt_hit_dist=[],
            simplification_notes="初回은 ロングST70+残保留4 50%, ショートST16+残保留4 50%. ショートST 중 당첨은 ロングST로 승격.",
            spec_source="Pachiseven machines/7264 / なな徹",
            confidence="high",
            notes="P-WORLD/Pachiseven의 3R/10R 출옥 표기를 기준으로 10R 5%, 3R 95%를 반영.",
            is_estimated=False,
        ),
        "shinsea_99": Machine(
            id="shinsea_99",
            name_ja="PA新海物語",
            name_ko="PA 신 바다이야기",
            spec_type="감데지 / ST+時短+C時短",
            risk_grade="1/99",
            normal_prob=99.9,
            high_prob=9.9,
            normal_hit_dist=[
                Payout(balls=1000, weight=0.04, next_state="ST", st_spins=5, jitan_spins=678),
                Payout(balls=500, weight=0.06, next_state="ST", st_spins=5, jitan_spins=678),
                Payout(balls=500, weight=0.57, next_state="ST", st_spins=5, jitan_spins=45),
                Payout(balls=500, weight=0.33, next_state="ST", st_spins=5, jitan_spins=20),
            ],
            st_hit_dist=[
                Payout(balls=1000, weight=0.04, next_state="ST", st_spins=5, jitan_spins=678),
                Payout(balls=500, weight=0.06, next_state="ST", st_spins=5, jitan_spins=678),
                Payout(balls=500, weight=0.57, next_state="ST", st_spins=5, jitan_spins=45),
                Payout(balls=500, weight=0.33, next_state="ST", st_spins=5, jitan_spins=20),
            ],
            jitan_hit_dist=[
                Payout(balls=1000, weight=0.04, next_state="ST", st_spins=5, jitan_spins=678),
                Payout(balls=500, weight=0.06, next_state="ST", st_spins=5, jitan_spins=678),
                Payout(balls=500, weight=0.57, next_state="ST", st_spins=5, jitan_spins=45),
                Payout(balls=500, weight=0.33, next_state="ST", st_spins=5, jitan_spins=20),
            ],
            kakuben_hit_dist=[],
            lt_hit_dist=[],
            normal_support_prob=199.8,
            normal_support_dist=[
                Payout(balls=0, weight=0.01, next_state="JITAN", jitan_spins=379, counts_as_rush=False),
                Payout(balls=0, weight=0.09, next_state="JITAN", jitan_spins=100, counts_as_rush=False),
                Payout(balls=0, weight=0.40, next_state="JITAN", jitan_spins=40, counts_as_rush=False),
                Payout(balls=0, weight=0.50, next_state="JITAN", jitan_spins=20, counts_as_rush=False),
            ],
            simplification_notes="通常時は大当り1/99.9와 C時短1/199.8을 독립 경쟁 이벤트로 추첨. C時短은 출옥 없는 時短20/40/100/379회로 처리.",
            spec_source="P-WORLD database/9652 / なな徹 / 1geki",
            confidence="high",
            notes="10R/일부5R 후 긴 전サポ는 ST5+時短299 후 遊タイム379까지 이어지는 실질 683회로 반영. 일반 시작回転 기반 遊タイム狙い는 별도 미반영.",
            is_estimated=False,
        ),
        "ginpara_mugen_99": Machine(
            id="ginpara_mugen_99",
            name_ja="PAギンギラパラダイス 夢幻カーニバル 強99ver.",
            name_ko="PA 긴기라 파라다이스 몽환 카니발 강99",
            spec_type="감데지 / 遊タイム付き 1種2種",
            risk_grade="1/99",
            normal_prob=99.9,
            high_prob=37.9,
            normal_hit_dist=[
                Payout(balls=370, weight=0.49, next_state="ST", st_spins=19),
                Payout(balls=550, weight=0.49, next_state="ST", st_spins=19),
                Payout(balls=370, weight=0.01, next_state="ST", st_spins=49),
                Payout(balls=820, weight=0.01, next_state="ST", st_spins=49),
            ],
            st_hit_dist=[
                Payout(balls=370, weight=0.45, next_state="ST", st_spins=49),
                Payout(balls=370, weight=0.05, next_state="ST", st_spins=300),
                Payout(balls=820, weight=0.40, next_state="ST", st_spins=49),
                Payout(balls=820, weight=0.10, next_state="ST", st_spins=300),
            ],
            jitan_hit_dist=[],
            kakuben_hit_dist=[],
            lt_hit_dist=[],
            simplification_notes="初当り 15/45회+残保留4, 오른쪽 45/296회+残保留4를 ST 회전수로 합산. 遊タイム은 시작回転 입력이 없어 미반영.",
            spec_source="Pachiseven machines/6470 / PachinkoVillage / すろぬー",
            confidence="high",
            notes="右打ち振分의 296회 비율은 공개 표기 조합으로 근사. 유타임狙い는 별도 현장 회전수 입력 기능 필요.",
            is_estimated=False,
        ),
        "mawarun_sea_4_agnes_119": Machine(
            id="mawarun_sea_4_agnes_119",
            name_ja="Pまわるん大海物語4スペシャル Withアグネス・ラム 119ver.",
            name_ko="P 마와룽 대해물어4 스페셜 With 아그네스 램 119",
            spec_type="감데지 / ST+時短",
            risk_grade="1/119",
            normal_prob=119.8,
            high_prob=19.5,
            normal_hit_dist=[
                Payout(balls=1300, weight=0.04, next_state="ST", st_spins=10, jitan_spins=90),
                Payout(balls=780, weight=0.56, next_state="ST", st_spins=10, jitan_spins=40),
                Payout(balls=520, weight=0.07, next_state="ST", st_spins=10, jitan_spins=40),
                Payout(balls=520, weight=0.33, next_state="ST", st_spins=10, jitan_spins=20),
            ],
            st_hit_dist=[
                Payout(balls=1300, weight=0.04, next_state="ST", st_spins=10, jitan_spins=90),
                Payout(balls=780, weight=0.56, next_state="ST", st_spins=10, jitan_spins=40),
                Payout(balls=520, weight=0.07, next_state="ST", st_spins=10, jitan_spins=40),
                Payout(balls=520, weight=0.33, next_state="ST", st_spins=10, jitan_spins=20),
            ],
            jitan_hit_dist=[
                Payout(balls=1300, weight=0.04, next_state="ST", st_spins=10, jitan_spins=90),
                Payout(balls=780, weight=0.56, next_state="ST", st_spins=10, jitan_spins=40),
                Payout(balls=520, weight=0.07, next_state="ST", st_spins=10, jitan_spins=40),
                Payout(balls=520, weight=0.33, next_state="ST", st_spins=10, jitan_spins=20),
            ],
            kakuben_hit_dist=[],
            lt_hit_dist=[],
            simplification_notes="ST10회 + 時短20/40/90회. 119ver. 공개振分 10R4%, 6R56%, 4R7%/33%를 반영.",
            spec_source="P-WORLD database/9419 / Dechau machine/584",
            confidence="high",
            notes="遊タイム450회는 시작回転 입력이 없어 미반영.",
            is_estimated=False,
        ),
        "oki_sea_5_yozakura": Machine(
            id="oki_sea_5_yozakura",
            name_ja="Pスーパー海物語 IN 沖縄5 夜桜超旋風",
            name_ko="P 슈퍼 바다이야기 IN 오키나와5 밤벚꽃 초선풍",
            spec_type="미들 / 1種2種 RUSH",
            risk_grade="1/319",
            normal_prob=319.68,
            high_prob=3.99,
            normal_hit_dist=[
                Payout(balls=700, weight=0.58, next_state="ST", st_spins=8),
                Payout(balls=300, weight=0.42, next_state="ST", st_spins=8),
            ],
            st_hit_dist=[
                Payout(balls=1000, weight=0.20, next_state="ST", st_spins=8),
                Payout(balls=300, weight=0.80, next_state="ST", st_spins=8),
            ],
            jitan_hit_dist=[],
            kakuben_hit_dist=[],
            lt_hit_dist=[],
            simplification_notes="初当り後 RUSH 100%. RUSH는 6회+残保留2개를 8회로 합산, 오른쪽 10R 20%/3R 80% 반영.",
            spec_source="P-WORLD database/9625 / Dechau",
            confidence="high",
            notes="1種2種의 V入賞 실패 가능성과 보류별 연출 차이는 모델링하지 않습니다.",
            is_estimated=False,
        ),

        # Eva family additions.
        "shin_eva_type_rei": Machine(
            id="shin_eva_type_rei",
            name_ja="ぱちんこ シン・エヴァンゲリオン Type レイ",
            name_ko="P 신 에반게리온 Type 레이",
            spec_type="에바 / V-ST",
            risk_grade="1/319",
            normal_prob=319.7,
            high_prob=99.5,
            normal_hit_dist=[
                Payout(balls=1500, weight=0.01, next_state="ST", st_spins=163),
                Payout(balls=300, weight=0.62, next_state="ST", st_spins=163),
                Payout(balls=300, weight=0.37, next_state="JITAN", jitan_spins=100, counts_as_rush=False),
            ],
            st_hit_dist=[
                Payout(balls=1500, weight=1.00, next_state="ST", st_spins=163),
            ],
            jitan_hit_dist=[
                Payout(balls=1500, weight=1.00, next_state="ST", st_spins=163),
            ],
            kakuben_hit_dist=[],
            lt_hit_dist=[],
            simplification_notes="特図1のST割合 63%(うち10R 1%)와 時短100 37%를 분리. 時短引き戻し込み突入率 약73%.",
            spec_source="P-WORLD news / Pachiseven",
            confidence="high",
            notes="高ベース中の特図1通常当り時短500 예외는 별도 헤소誤入賞 상태가 없어 미반영.",
            is_estimated=False,
        ),
        "shin_eva_premium_99": Machine(
            id="shin_eva_premium_99",
            name_ja="ぱちんこ シン・エヴァンゲリオン PREMIUM MODEL",
            name_ko="P 신 에반게리온 프리미엄 모델",
            spec_type="감데지 / 돌파형 ST",
            risk_grade="1/99",
            normal_prob=99.9,
            high_prob=37.5,
            normal_hit_dist=[
                Payout(balls=1000, weight=0.01, next_state="ST", st_spins=30, jitan_spins=70),
                Payout(balls=300, weight=0.58, next_state="ST", st_spins=30, counts_as_rush=False),
                Payout(balls=300, weight=0.41, next_state="JITAN", jitan_spins=30, counts_as_rush=False),
            ],
            st_hit_dist=[
                Payout(balls=1000, weight=0.50, next_state="ST", st_spins=30, jitan_spins=70),
                Payout(balls=300, weight=0.50, next_state="ST", st_spins=30, jitan_spins=70),
            ],
            jitan_hit_dist=[
                Payout(balls=1000, weight=0.50, next_state="ST", st_spins=30, jitan_spins=70),
                Payout(balls=300, weight=0.50, next_state="ST", st_spins=30, jitan_spins=70),
            ],
            kakuben_hit_dist=[],
            lt_hit_dist=[],
            simplification_notes="DMM: 1/99.9, 고확 1/37.5, ST돌입 약 59%, RUSH돌입 약 46%, RUSH継続 약 79%.",
            spec_source="P-WORLD database/10331 / DMMぱちタウン machines/4865",
            confidence="high",
            notes="전サポ 30/100회 구조를 ST30+時短70으로 근사. 잔보류는 시뮬 회전수에 일부 흡수.",
            is_estimated=False,
        ),
        "eva_15_special_199": Machine(
            id="eva_15_special_199",
            name_ja="P新世紀エヴァンゲリオン〜未来への咆哮〜SPECIAL EDITION",
            name_ko="P 에바15 스페셜 에디션 199",
            spec_type="라이트미들 / 돌파형 V-ST",
            risk_grade="1/199",
            normal_prob=199.2,
            high_prob=82.6,
            normal_hit_dist=[
                Payout(balls=1100, weight=0.01, next_state="ST", st_spins=135),
                Payout(balls=330, weight=0.24, next_state="ST", st_spins=135),
                Payout(balls=330, weight=0.75, next_state="JITAN", jitan_spins=100, counts_as_rush=False),
            ],
            st_hit_dist=[
                Payout(balls=1100, weight=1.00, next_state="ST", st_spins=135),
            ],
            jitan_hit_dist=[
                Payout(balls=1100, weight=1.00, next_state="ST", st_spins=135),
            ],
            kakuben_hit_dist=[],
            lt_hit_dist=[],
            simplification_notes="特図1 1% 10R ST / 24% 3R ST / 75% 3R 時短100. 特図2는 ALL10R 1100발 ST135.",
            spec_source="P-WORLD database/9892 / DMMぱちタウン",
            confidence="high",
            notes="高ベース中의 特図1通常当り 時短200 예외는 헤소誤入賞 상태가 없어 미반영.",
            is_estimated=False,
        ),

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
)

MACHINES["hokuto_10"] = Machine(
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
)

MACHINES["sea_5_agnes"] = Machine(
    id="sea_5_agnes",
    name_ja="PA大海物語5 Withアグネス・ラム",
    name_ko="PA 대해물어5 With 아그네스 램",
    spec_type="감데지 / ST+時短",
    risk_grade="1/99",
    normal_prob=99.9,
    high_prob=19.5,
    normal_hit_dist=[
        Payout(balls=1080, weight=0.04, next_state="ST", st_spins=10, jitan_spins=110),
        Payout(balls=648, weight=0.60, next_state="ST", st_spins=10, jitan_spins=40),
        Payout(balls=432, weight=0.06, next_state="ST", st_spins=10, jitan_spins=40),
        Payout(balls=432, weight=0.30, next_state="ST", st_spins=10, jitan_spins=15),
    ],
    st_hit_dist=[
        Payout(balls=1080, weight=0.04, next_state="ST", st_spins=10, jitan_spins=110),
        Payout(balls=648, weight=0.60, next_state="ST", st_spins=10, jitan_spins=40),
        Payout(balls=432, weight=0.06, next_state="ST", st_spins=10, jitan_spins=40),
        Payout(balls=432, weight=0.30, next_state="ST", st_spins=10, jitan_spins=15),
    ],
    jitan_hit_dist=[
        Payout(balls=1080, weight=0.04, next_state="ST", st_spins=10, jitan_spins=110),
        Payout(balls=648, weight=0.60, next_state="ST", st_spins=10, jitan_spins=40),
        Payout(balls=432, weight=0.06, next_state="ST", st_spins=10, jitan_spins=40),
        Payout(balls=432, weight=0.30, next_state="ST", st_spins=10, jitan_spins=15),
    ],
    kakuben_hit_dist=[],
    lt_hit_dist=[],
    simplification_notes="ST10회 + 時短15/40/110회. P-WORLD 공개振分(10R 4%, 6R 60%, 4R 6%/30%)을 반영.",
    spec_source="P-WORLD database/9833 / DMMぱちタウン machines/4358",
    confidence="high",
    notes="ハピネスチャンス中 대당첨은 모두 120회 전サポ라는 예외는 별도 상태 없이 평균 분포로 근사.",
    is_estimated=False,
)
MACHINES["mediterranean_2_89"] = Machine(
    id="mediterranean_2_89",
    name_ja="PAスーパー海物語IN地中海2",
    name_ko="PA 슈퍼 바다이야기 IN 지중해2",
    spec_type="感デジ / LT搭載 一種二種",
    risk_grade="1/89",
    normal_prob=89.8,
    high_prob=34.8,
    normal_hit_dist=[
        Payout(balls=480, weight=0.50, next_state="ST", st_spins=24),
        Payout(balls=320, weight=0.50, next_state="ST", st_spins=24),
    ],
    st_hit_dist=[
        Payout(balls=800, weight=0.02, next_state="LT", st_spins=100, is_lt=True),
        Payout(balls=480, weight=0.48, next_state="ST", st_spins=48),
        Payout(balls=320, weight=0.50, next_state="ST", st_spins=48),
    ],
    jitan_hit_dist=[],
    kakuben_hit_dist=[],
    lt_hit_dist=[
        Payout(balls=800, weight=0.02, next_state="LT", st_spins=100, is_lt=True),
        Payout(balls=480, weight=0.48, next_state="LT", st_spins=100, is_lt=True),
        Payout(balls=320, weight=0.50, next_state="LT", st_spins=100, is_lt=True),
    ],
    simplification_notes="チャンスタイム은 20회+残保留4개, 地中海JOURNEY는 44회+残保留4개로 합산. PREMIUM VACATION(LT)은 공개 継続率 약94.5%에 맞춰 100회로 모델링.",
    spec_source="P-WORLD database/10055 / Dechau / 海まにあ",
    confidence="high",
    notes="PREMIUM VACATION 종료 후 残保留 당첨이 地中海JOURNEY振分으로 돌아가는 예외는 공개継続率에 맞춰 100회 모델로 보수화.",
    is_estimated=False,
)
