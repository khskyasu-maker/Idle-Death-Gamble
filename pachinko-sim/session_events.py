from typing import Any, Dict

from machines import Payout
from session_sampling import bilingual_hit_label


def build_hit_event(
    *,
    hit_no: int,
    previous_state: str,
    state_after: str,
    current_prob: float,
    payout: Payout,
    payout_balls: int,
    normal_spins: int,
    right_spins: int,
    streak: int,
    rush_entry_event: bool,
    lt_entry_event: bool,
    upper_entry_event: bool,
    bank_balls: float,
    locked_balls: float,
) -> Dict[str, Any]:
    hit_label_ja, hit_label_ko, hit_label = bilingual_hit_label(previous_state)
    return {
        "hit_no": hit_no,
        "label": hit_label,
        "label_ja": hit_label_ja,
        "label_ko": hit_label_ko,
        "normal_spins": normal_spins,
        "right_spins": right_spins,
        "state_before": previous_state,
        "state_after": state_after,
        "probability_denominator": current_prob,
        "payout_balls": payout_balls,
        "st_spins": payout.st_spins,
        "jitan_spins": payout.jitan_spins,
        "streak": streak,
        "rush_entry": rush_entry_event,
        "lt_entry": lt_entry_event,
        "upper_entry": upper_entry_event,
        "bank_balls_after": int(bank_balls),
        "locked_balls_after": int(locked_balls),
    }


__all__ = ["build_hit_event"]
