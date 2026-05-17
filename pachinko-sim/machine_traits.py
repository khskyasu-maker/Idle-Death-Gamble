from typing import Iterable, Tuple

from machines import Machine, Payout


DISTRIBUTION_FIELDS = (
    "normal_hit_dist",
    "st_hit_dist",
    "jitan_hit_dist",
    "kakuben_hit_dist",
    "lt_hit_dist",
    "upper_hit_dist",
    "jinbee_hit_dist",
    "normal_support_dist",
)


def payout_distributions(machine: Machine) -> Tuple[Iterable[Payout], ...]:
    return tuple(getattr(machine, field_name) for field_name in DISTRIBUTION_FIELDS)


def iter_payouts(machine: Machine):
    for distribution in payout_distributions(machine):
        yield from distribution


def machine_has_lt(machine: Machine) -> bool:
    return any(payout.is_lt or payout.next_state in {"LT", "LT_JITAN"} for payout in iter_payouts(machine))


def machine_has_upper(machine: Machine) -> bool:
    return any(payout.next_state == "UPPER" for payout in iter_payouts(machine))
