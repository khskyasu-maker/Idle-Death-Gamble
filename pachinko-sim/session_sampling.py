import math
import random

from machines import Machine, Payout
from start_gate import sample_truncated_normal


HIT_LABELS = {
    "NORMAL": ("初当り", "초당첨"),
    "JITAN": ("時短当り", "시단 당첨"),
    "KAKUBEN": ("確変当り", "확변 당첨"),
    "LT": ("LT当り", "LT 당첨"),
    "LT_JITAN": ("LT時短当り", "LT 시단 당첨"),
    "UPPER": ("上位RUSH当り", "상위 러시 당첨"),
    "UPPER_JITAN": ("上位RUSH時短当り", "상위 러시 시단 당첨"),
    "JINBEE": ("ジンベェ当り", "진베에 타임 당첨"),
    "JINBEE_JITAN": ("ジンベェ当り", "진베에 시단 당첨"),
}


def bilingual_hit_label(state: str) -> tuple[str, str, str]:
    label_ja, label_ko = HIT_LABELS.get(state, ("RUSH/ST当り", "러시/ST 당첨"))
    return label_ja, label_ko, f"{label_ja}({label_ko})"


def jitan_denominator(machine: Machine) -> float:
    return machine.jitan_prob if machine.jitan_prob > 1 else machine.normal_prob


def get_payout(payouts: list[Payout]) -> Payout:
    """확률 가중치에 따라 출옥 수 및 상태 전이 정보를 추첨합니다."""
    if not payouts:
        return Payout(balls=0, weight=1.0, next_state="NORMAL")

    draw = random.random()
    cumulative = 0.0
    for payout in payouts:
        cumulative += payout.weight
        if draw <= cumulative:
            return payout
    return payouts[-1]


def sample_payout_balls(payout: Payout) -> int:
    """Sample realized payout around the nominal ball count."""
    if payout.balls <= 0:
        return 0

    variance = max(0.0, payout.ball_variance)
    if variance <= 0.0:
        return int(payout.balls)

    low = max(0, int(payout.balls * (1.0 - variance)))
    high = max(low, int(payout.balls * (1.0 + variance)))
    stddev = max(1.0, (payout.balls * variance) / 2.0)
    return int(round(sample_truncated_normal(payout.balls, stddev, low, high)))


def spins_until_hit(probability_denominator: float) -> int:
    """Sample the spin count until the next hit for independent Bernoulli spins."""
    hit_probability = 1.0 / probability_denominator
    if hit_probability >= 1.0:
        return 1
    return int(math.log1p(-random.random()) / math.log1p(-hit_probability)) + 1


__all__ = [
    "HIT_LABELS",
    "bilingual_hit_label",
    "get_payout",
    "jitan_denominator",
    "sample_payout_balls",
    "spins_until_hit",
]
