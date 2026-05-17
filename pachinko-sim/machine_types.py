from dataclasses import dataclass, field
from typing import Dict, List


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
