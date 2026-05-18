from machine_definitions.eva import EVA_ADDITION_MACHINES, EVA_INITIAL_MACHINES
from machine_definitions.other import OTHER_ADDITION_MACHINES, OTHER_TRAILING_MACHINES
from machine_definitions.rezero import REZERO_ADDITION_MACHINES, REZERO_INITIAL_MACHINES
from machine_definitions.sea import SEA_ADDITION_MACHINES, SEA_INITIAL_MACHINES, SEA_TRAILING_MACHINES


MACHINE_GROUPS = (
    SEA_INITIAL_MACHINES,
    EVA_INITIAL_MACHINES,
    REZERO_INITIAL_MACHINES,
    SEA_ADDITION_MACHINES,
    EVA_ADDITION_MACHINES,
    REZERO_ADDITION_MACHINES,
    OTHER_ADDITION_MACHINES,
    OTHER_TRAILING_MACHINES,
    SEA_TRAILING_MACHINES,
)


def build_machines():
    machines = {}
    for group in MACHINE_GROUPS:
        machines.update(group)
    return machines


__all__ = ["build_machines", "MACHINE_GROUPS"]
