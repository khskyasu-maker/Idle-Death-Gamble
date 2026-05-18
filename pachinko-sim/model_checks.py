import math
from typing import Dict, Iterable, List

from machines import Machine
from machine_traits import DISTRIBUTION_FIELDS


VALID_STATES = {
    "NORMAL",
    "ST",
    "JITAN",
    "KAKUBEN",
    "LT",
    "LT_JITAN",
    "UPPER",
    "UPPER_JITAN",
    "JINBEE",
    "JINBEE_JITAN",
}
VALID_CONFIDENCE_LEVELS = {"high", "medium", "low"}

KNOWN_SPEC_EXPECTATIONS = {
    "oki_sea_6": {
        "normal_prob": 319.6,
        "high_prob": 31.9,
        "normal_weights": [0.40, 0.20, 0.40],
        "jitan_weights": [0.01, 0.51, 0.08, 0.40],
        "kakuben_weights": [0.01, 0.51, 0.08, 0.40],
        "jinbee_weights": [0.52, 0.08, 0.40],
    },
    "sea_5_special": {
        "normal_prob": 319.6,
        "high_prob": 31.9,
        "normal_weights": [0.54, 0.46],
        "normal_states": ["KAKUBEN", "JITAN"],
        "normal_counts_as_rush": [True, False],
        "jitan_weights": [0.54, 0.46],
        "kakuben_weights": [0.54, 0.46],
    },
    "sea_5": {
        "normal_prob": 319.6,
        "high_prob": 31.9,
        "normal_weights": [0.60, 0.40],
        "normal_states": ["KAKUBEN", "JITAN"],
        "normal_counts_as_rush": [True, False],
        "jitan_weights": [0.60, 0.40],
        "kakuben_weights": [0.60, 0.40],
    },
    "sea_5_black_199": {
        "normal_prob": 199.8,
        "high_prob": 44.0,
        "normal_weights": [1.00],
        "st_weights": [0.04, 0.46, 0.50],
        "upper_weights": [0.50, 0.50],
    },
    "sea_4_special_black": {
        "normal_prob": 199.8,
        "high_prob": 40.6,
        "normal_weights": [0.30, 0.30, 0.40],
        "normal_states": ["ST", "ST", "ST"],
        "st_weights": [0.30, 0.30, 0.40],
    },
    "sea_4_special": {
        "normal_prob": 319.6,
        "high_prob": 39.7,
        "normal_weights": [0.52, 0.48],
        "normal_states": ["KAKUBEN", "JITAN"],
        "normal_counts_as_rush": [True, False],
        "jitan_weights": [0.52, 0.48],
        "kakuben_weights": [0.52, 0.48],
    },
    "sea_4_agnes": {
        "normal_prob": 99.9,
        "high_prob": 19.5,
        "normal_weights": [0.04, 0.60, 0.06, 0.30],
        "normal_states": ["ST", "ST", "ST", "ST"],
        "st_weights": [0.04, 0.60, 0.06, 0.30],
        "jitan_weights": [0.04, 0.60, 0.06, 0.30],
    },
    "sea_3r3": {
        "normal_prob": 99.9,
        "high_prob": 16.9,
        "normal_weights": [0.05, 0.46, 0.49],
        "normal_states": ["KAKUBEN", "KAKUBEN", "JITAN"],
        "normal_counts_as_rush": [True, True, False],
        "jitan_weights": [0.05, 0.46, 0.49],
        "kakuben_weights": [0.05, 0.46, 0.49],
    },
    "sea_extreme_japan": {
        "normal_prob": 319.6,
        "high_prob": 73.9,
        "normal_weights": [0.50, 0.50],
        "normal_states": ["ST", "ST"],
        "normal_counts_as_rush": [True, False],
        "st_weights": [0.20, 0.55, 0.25],
    },
    "sea_extreme_japan_naginami": {
        "normal_prob": 99.9,
        "high_prob": 56.2,
        "normal_weights": [0.50, 0.50],
        "normal_states": ["ST", "ST"],
        "normal_counts_as_rush": [True, False],
        "st_weights": [0.05, 0.70, 0.25],
    },
    "shinsea_99": {
        "normal_prob": 99.9,
        "high_prob": 9.9,
        "normal_support_prob": 199.8,
        "normal_weights": [0.04, 0.06, 0.57, 0.33],
        "normal_states": ["ST", "ST", "ST", "ST"],
        "st_weights": [0.04, 0.06, 0.57, 0.33],
        "jitan_weights": [0.04, 0.06, 0.57, 0.33],
        "normal_support_weights": [0.01, 0.09, 0.40, 0.50],
    },
    "eva_15_roar": {
        "normal_prob": 319.7,
        "high_prob": 99.4,
        "normal_weights": [0.03, 0.56, 0.41],
        "normal_states": ["ST", "ST", "JITAN"],
        "normal_counts_as_rush": [True, True, False],
    },
    "eva_15_premium": {
        "normal_prob": 129.8,
        "high_prob": 35.7,
        "normal_weights": [0.10, 0.54, 0.36],
        "normal_states": ["ST", "ST", "JITAN"],
        "normal_counts_as_rush": [True, False, False],
        "st_weights": [0.60, 0.40],
        "jitan_weights": [0.60, 0.40],
    },
    "shin_eva_129_lt": {
        "normal_prob": 129.8,
        "high_prob": 54.4,
        "normal_weights": [0.005, 0.500, 0.495],
        "normal_states": ["LT", "ST", "NORMAL"],
        "normal_counts_as_rush": [True, True, False],
        "st_weights": [0.10, 0.90],
        "lt_weights": [1.00],
    },
    "eva_beginning": {
        "normal_prob": 349.9,
        "high_prob": 99.6,
        "jitan_prob": 399.9,
        "normal_weights": [0.005, 0.500, 0.495],
        "normal_states": ["LT", "LT", "JITAN"],
        "normal_counts_as_rush": [True, True, False],
        "jitan_weights": [1.00],
        "lt_weights": [0.005, 0.995],
    },
    "sea_5_black_lt": {
        "normal_prob": 99.9,
        "high_prob": 41.0,
        "normal_weights": [0.70, 0.30],
        "normal_states": ["ST", "NORMAL"],
        "st_weights": [0.10, 0.30, 0.60],
        "lt_weights": [0.40, 0.60],
    },
    "sea_5_agnes": {
        "normal_prob": 99.9,
        "high_prob": 19.5,
        "normal_weights": [0.04, 0.60, 0.06, 0.30],
        "normal_states": ["UPPER", "ST", "ST", "ST"],
        "st_weights": [0.04, 0.60, 0.06, 0.30],
        "jitan_weights": [0.04, 0.60, 0.06, 0.30],
        "upper_weights": [0.04, 0.60, 0.36],
    },
    "oki_sea_5_imarine": {
        "normal_prob": 99.9,
        "high_prob": 9.9,
        "normal_weights": [0.10, 0.57, 0.33],
        "normal_states": ["ST", "ST", "ST"],
        "st_weights": [0.10, 0.57, 0.33],
        "jitan_weights": [0.10, 0.57, 0.33],
    },
    "ginpara_mugen_99": {
        "normal_prob": 99.9,
        "high_prob": 37.9,
        "normal_weights": [0.49, 0.49, 0.01, 0.01],
        "normal_states": ["ST", "ST", "ST", "ST"],
        "st_weights": [0.45, 0.05, 0.40, 0.10],
    },
    "mawarun_sea_4_agnes_119": {
        "normal_prob": 119.8,
        "high_prob": 19.5,
        "normal_weights": [0.04, 0.56, 0.07, 0.33],
        "normal_states": ["ST", "ST", "ST", "ST"],
        "st_weights": [0.04, 0.56, 0.07, 0.33],
        "jitan_weights": [0.04, 0.56, 0.07, 0.33],
    },
    "shin_eva_premium_99": {
        "normal_prob": 99.9,
        "high_prob": 37.5,
        "normal_weights": [0.01, 0.58, 0.41],
        "normal_states": ["ST", "ST", "JITAN"],
        "normal_counts_as_rush": [True, False, False],
        "st_weights": [0.50, 0.50],
        "jitan_weights": [0.50, 0.50],
    },
    "shin_eva_type_rei": {
        "normal_prob": 319.7,
        "high_prob": 99.5,
        "normal_weights": [0.01, 0.62, 0.37],
        "normal_states": ["ST", "ST", "JITAN"],
        "normal_counts_as_rush": [True, True, False],
        "st_weights": [1.00],
        "jitan_weights": [1.00],
    },
    "eva_15_special_199": {
        "normal_prob": 199.2,
        "high_prob": 82.6,
        "normal_weights": [0.01, 0.24, 0.75],
        "normal_states": ["ST", "ST", "JITAN"],
        "normal_counts_as_rush": [True, True, False],
        "st_weights": [1.00],
        "jitan_weights": [1.00],
    },
    "re_zero_99": {
        "normal_prob": 99.9,
        "high_prob": 79.9,
        "normal_weights": [0.50, 0.50],
        "st_weights": [0.25, 0.50, 0.05, 0.20],
    },
    "re_zero_199": {
        "normal_prob": 199.8,
        "high_prob": 105.9,
        "normal_weights": [0.55, 0.45],
        "st_weights": [0.40, 0.40, 0.20],
    },
    "re_zero_319": {
        "normal_prob": 319.6,
        "high_prob": 99.9,
        "normal_weights": [0.55, 0.45],
        "st_weights": [0.25, 0.55, 0.06, 0.14],
    },
    "re_zero_s2_349": {
        "normal_prob": 349.9,
        "high_prob": 99.9,
        "normal_weights": [0.55, 0.45],
        "st_weights": [0.25, 0.55, 0.20],
    },
    "re_zero_s2_129": {
        "normal_prob": 129.9,
        "high_prob": 99.9,
        "normal_weights": [0.50, 0.50],
        "st_weights": [0.03225, 0.02450, 0.01850, 0.02450, 0.02525, 0.12500, 0.55000, 0.20000],
    },
    "lupin_77_sweet": {
        "normal_prob": 77.7,
        "high_prob": 37.3,
        "normal_weights": [0.51, 0.49],
        "normal_states": ["ST", "NORMAL"],
        "normal_counts_as_rush": [True, False],
        "st_weights": [0.15, 0.85],
        "lt_weights": [1.00],
    },
    "kabaneri_2": {
        "normal_prob": 319.7,
        "high_prob": 98.3,
        "normal_weights": [0.50, 0.50],
        "normal_states": ["LT", "NORMAL"],
        "normal_counts_as_rush": [True, False],
        "lt_weights": [0.062, 0.738, 0.200],
    },
    "tokyo_ghoul": {
        "normal_prob": 199.9,
        "high_prob": 95.3,
        "normal_weights": [0.250, 0.005, 0.245, 0.500],
        "normal_states": ["LT", "LT", "NORMAL", "NORMAL"],
        "normal_counts_as_rush": [True, True, False, False],
        "lt_weights": [0.03, 0.97],
    },
    "hokuto_jibo": {
        "normal_prob": 79.9,
        "high_prob": 7.99,
        "normal_weights": [0.012, 0.788, 0.200],
        "normal_states": ["ST", "ST", "ST"],
        "st_weights": [0.010, 0.002, 0.788, 0.200],
        "jitan_weights": [0.010, 0.002, 0.788, 0.200],
        "lt_weights": [0.012, 0.788, 0.200],
    },
    "hokuto_10": {
        "normal_prob": 348.6,
        "high_prob": 40.0,
        "normal_weights": [0.05, 0.70, 0.01, 0.04, 0.20],
        "normal_states": ["ST", "ST", "LT", "ST", "NORMAL"],
        "normal_counts_as_rush": [True, True, True, True, False],
        "st_weights": [0.126, 0.574, 0.300],
        "lt_weights": [0.70, 0.30],
    },
    "mediterranean_2_89": {
        "normal_prob": 89.8,
        "high_prob": 34.8,
        "normal_weights": [0.50, 0.50],
        "normal_states": ["ST", "ST"],
        "st_weights": [0.02, 0.48, 0.50],
        "lt_weights": [0.02, 0.48, 0.50],
    },
}


def theoretical_no_hit_rate(probability_denominator: float, spins: int) -> float:
    """Return normal-only no-hit probability as a percentage."""
    if probability_denominator <= 1 or spins <= 0:
        return 0.0
    return ((1.0 - (1.0 / probability_denominator)) ** spins) * 100.0


def theoretical_hit_rate(probability_denominator: float, spins: int) -> float:
    return 100.0 - theoretical_no_hit_rate(probability_denominator, spins)


def state_hit_rate(probability_denominator: float, spins: int) -> float:
    """Return chance of at least one hit inside a limited ST/LT/UPPER-like state."""
    return theoretical_hit_rate(probability_denominator, spins)


def distribution_weight(distribution: Iterable) -> float:
    return sum(payout.weight for payout in distribution)


def weighted_average_balls(distribution: Iterable) -> float:
    return sum(payout.balls * payout.weight for payout in distribution)


def _check_float(path: str, actual: float, expected: float, tolerance: float, issues: List[str]):
    if not math.isclose(actual, expected, abs_tol=tolerance):
        issues.append(f"{path}: expected {expected}, got {actual}")


def _check_distribution_values(
    machine: Machine,
    field_name: str,
    expected_key: str,
    expectation: Dict,
    tolerance: float,
    issues: List[str],
):
    if expected_key not in expectation:
        return
    actual = getattr(machine, field_name)
    expected = expectation[expected_key]
    path = f"{machine.id}.{field_name}"
    if len(actual) != len(expected):
        issues.append(f"{path}: expected {len(expected)} entries, got {len(actual)}")
        return
    for index, expected_weight in enumerate(expected):
        _check_float(f"{path}[{index}].weight", actual[index].weight, expected_weight, tolerance, issues)


def validate_known_spec_expectation(machine: Machine, tolerance: float = 0.001) -> List[str]:
    issues = []
    expectation = KNOWN_SPEC_EXPECTATIONS.get(machine.id)
    if not expectation:
        return issues

    _check_float(f"{machine.id}.normal_prob", machine.normal_prob, expectation["normal_prob"], tolerance, issues)
    _check_float(f"{machine.id}.high_prob", machine.high_prob, expectation["high_prob"], tolerance, issues)
    if "jitan_prob" in expectation:
        _check_float(
            f"{machine.id}.jitan_prob",
            machine.jitan_prob,
            expectation["jitan_prob"],
            tolerance,
            issues,
        )
    if "normal_support_prob" in expectation:
        _check_float(
            f"{machine.id}.normal_support_prob",
            machine.normal_support_prob,
            expectation["normal_support_prob"],
            tolerance,
            issues,
        )
    for field_name, expected_key in (
        ("normal_hit_dist", "normal_weights"),
        ("st_hit_dist", "st_weights"),
        ("jitan_hit_dist", "jitan_weights"),
        ("kakuben_hit_dist", "kakuben_weights"),
        ("lt_hit_dist", "lt_weights"),
        ("upper_hit_dist", "upper_weights"),
        ("jinbee_hit_dist", "jinbee_weights"),
        ("normal_support_dist", "normal_support_weights"),
    ):
        _check_distribution_values(machine, field_name, expected_key, expectation, tolerance, issues)

    if "normal_states" in expectation and len(machine.normal_hit_dist) == len(expectation["normal_states"]):
        for index, expected_state in enumerate(expectation["normal_states"]):
            actual_state = machine.normal_hit_dist[index].next_state
            if actual_state != expected_state:
                issues.append(
                    f"{machine.id}.normal_hit_dist[{index}].next_state: expected {expected_state}, got {actual_state}"
                )

    if (
        "normal_counts_as_rush" in expectation
        and len(machine.normal_hit_dist) == len(expectation["normal_counts_as_rush"])
    ):
        for index, expected_flag in enumerate(expectation["normal_counts_as_rush"]):
            actual_flag = machine.normal_hit_dist[index].counts_as_rush
            if actual_flag != expected_flag:
                issues.append(
                    f"{machine.id}.normal_hit_dist[{index}].counts_as_rush: expected {expected_flag}, got {actual_flag}"
                )

    return issues


def validate_machine_model(machine: Machine, tolerance: float = 0.001) -> List[str]:
    """Return human-readable warnings for one model's internal consistency."""
    issues = []

    if machine.normal_prob <= 1:
        issues.append(f"{machine.id}: normal_prob must be greater than 1")
    if machine.high_prob <= 1:
        issues.append(f"{machine.id}: high_prob must be greater than 1")
    if machine.normal_support_dist and machine.normal_support_prob <= 1:
        issues.append(f"{machine.id}: normal_support_prob must be greater than 1 when support distribution exists")
    if machine.confidence not in VALID_CONFIDENCE_LEVELS:
        issues.append(
            f"{machine.id}: confidence must be one of {sorted(VALID_CONFIDENCE_LEVELS)}, got {machine.confidence!r}"
        )
    if not isinstance(machine.spec_source, str) or not machine.spec_source.strip():
        issues.append(f"{machine.id}: spec_source must identify the fixed public spec source")
    if not isinstance(machine.is_estimated, bool):
        issues.append(f"{machine.id}: is_estimated must be a boolean")
    elif machine.confidence == "high" and machine.is_estimated:
        issues.append(f"{machine.id}: high-confidence fixed spec models must set is_estimated=False")
    if not isinstance(machine.simplification_notes, str):
        issues.append(f"{machine.id}: simplification_notes must be a string")
    if not isinstance(machine.notes, str):
        issues.append(f"{machine.id}: notes must be a string")

    for state, spend in machine.right_spend_per_spin.items():
        if state not in VALID_STATES and state != "RUSH":
            issues.append(f"{machine.id}.right_spend_per_spin[{state!r}]: unknown state")
        if spend < 0:
            issues.append(f"{machine.id}.right_spend_per_spin[{state!r}]: spend must not be negative")

    for state, probability_denominator in machine.fall_prob.items():
        if state not in VALID_STATES:
            issues.append(f"{machine.id}.fall_prob[{state!r}]: unknown state")
        if probability_denominator <= 1:
            issues.append(f"{machine.id}.fall_prob[{state!r}]: denominator must be greater than 1")

    for state, reserve_spins in machine.fall_reserve_spins.items():
        if state not in VALID_STATES:
            issues.append(f"{machine.id}.fall_reserve_spins[{state!r}]: unknown state")
        if reserve_spins < 0:
            issues.append(f"{machine.id}.fall_reserve_spins[{state!r}]: reserve spins must not be negative")

    for field_name in DISTRIBUTION_FIELDS:
        distribution = getattr(machine, field_name)
        if not distribution:
            continue

        weight = distribution_weight(distribution)
        if not math.isclose(weight, 1.0, abs_tol=tolerance):
            issues.append(
                f"{machine.id}.{field_name}: payout weights sum to {weight:.5f}, expected 1.0"
            )

        for index, payout in enumerate(distribution):
            path = f"{machine.id}.{field_name}[{index}]"
            if payout.weight < 0:
                issues.append(f"{path}: weight must not be negative")
            if payout.balls < 0:
                issues.append(f"{path}: balls must not be negative")
            if payout.next_state not in VALID_STATES:
                issues.append(f"{path}: invalid next_state {payout.next_state!r}")
            if payout.st_spins < 0 or payout.jitan_spins < 0:
                issues.append(f"{path}: state spin counts must not be negative")
            if payout.ball_variance < 0:
                issues.append(f"{path}: ball_variance must not be negative")
            if not isinstance(payout.counts_as_rush, bool):
                issues.append(f"{path}: counts_as_rush must be a boolean")
            if payout.next_state == "LT" and not payout.is_lt:
                issues.append(f"{path}: LT state transitions must set is_lt=True")

    has_lt_state = any(
        payout.next_state == "LT"
        for field_name in DISTRIBUTION_FIELDS
        for payout in getattr(machine, field_name)
    )
    if has_lt_state and not machine.lt_hit_dist:
        issues.append(f"{machine.id}: LT state transitions require lt_hit_dist")

    issues.extend(validate_known_spec_expectation(machine, tolerance))
    return issues


def validate_all_machine_models(machines: Dict[str, Machine]) -> List[str]:
    issues = []
    for machine in machines.values():
        issues.extend(validate_machine_model(machine))
    return issues
