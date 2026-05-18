from dataclasses import dataclass

from machines import Machine, Payout
from session_sampling import effective_support_spins


RIGHT_RUSH_STATES = ("ST", "LT", "UPPER")
JITAN_STATES = ("JITAN", "LT_JITAN", "UPPER_JITAN", "JINBEE_JITAN")


@dataclass(frozen=True)
class SupportWindow:
    state: str
    spins_left: int
    jitan_reserve: int


def reserve_state_for(state: str) -> str:
    if state == "LT":
        return "LT_JITAN"
    if state == "UPPER":
        return "UPPER_JITAN"
    if state == "JINBEE":
        return "JINBEE_JITAN"
    return "JITAN"


def jitan_state_after_support(state: str) -> str:
    if state == "LT":
        return "LT_JITAN"
    if state == "UPPER":
        return "UPPER_JITAN"
    return "JITAN"


def support_spins_for_state(machine: Machine, state: str, spins: int) -> int:
    return effective_support_spins(machine, state, spins)


def support_window_for_payout(machine: Machine, payout: Payout) -> SupportWindow:
    state = payout.next_state
    if state in RIGHT_RUSH_STATES:
        return SupportWindow(
            state=state,
            spins_left=effective_support_spins(machine, state, payout.st_spins),
            jitan_reserve=effective_support_spins(machine, reserve_state_for(state), payout.jitan_spins),
        )
    if state in JITAN_STATES:
        return SupportWindow(
            state=state,
            spins_left=effective_support_spins(machine, state, payout.jitan_spins or payout.st_spins),
            jitan_reserve=0,
        )
    return SupportWindow(state=state, spins_left=0, jitan_reserve=0)


def hit_distribution_for_state(machine: Machine, state: str) -> list[Payout]:
    if state == "NORMAL":
        return machine.normal_hit_dist
    if state == "ST":
        return machine.st_hit_dist
    if state == "JITAN":
        return machine.jitan_hit_dist
    if state == "LT_JITAN":
        return machine.lt_hit_dist
    if state == "KAKUBEN":
        return machine.kakuben_hit_dist
    if state == "LT":
        return machine.lt_hit_dist
    if state in ("UPPER", "UPPER_JITAN"):
        return machine.upper_hit_dist
    if state in ("JINBEE", "JINBEE_JITAN"):
        return machine.jinbee_hit_dist
    raise ValueError(f"unsupported simulator state: {state}")


__all__ = [
    "JITAN_STATES",
    "RIGHT_RUSH_STATES",
    "SupportWindow",
    "hit_distribution_for_state",
    "jitan_state_after_support",
    "reserve_state_for",
    "support_spins_for_state",
    "support_window_for_payout",
]
