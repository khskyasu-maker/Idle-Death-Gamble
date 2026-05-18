from typing import Any

from machines import Machine
from rotation import ABSOLUTE_SPIN_RATE_CASES, border_case_rates
from session_accounting import STRATEGIES, normalize_session_policy
from time_model import TimeAssumptions


SPIN_RATE_CASES = ABSOLUTE_SPIN_RATE_CASES
BUDGET_CASES = [5000, 10000, 15000, 20000]
PROFILE_BUDGET_CASES = [1000, 5000, 10000, 15000, 20000]


def absolute_spin_cases(spin_rates: list[int]) -> list[dict[str, Any]]:
    return [
        {
            "rotation_basis": "absolute",
            "rotation_label": f"{spins}회",
            "spins_per_1000y": float(spins),
            "border_margin": None,
        }
        for spins in spin_rates
    ]


def rotation_cases(spin_rates: list[int] | None, border_spins_per_1000y: float | None) -> list[dict[str, Any]]:
    return (
        border_case_rates(border_spins_per_1000y)
        if spin_rates is None
        else absolute_spin_cases(spin_rates)
    )


def run_matrix_simulation(
    machine: Machine,
    lend_rate: float,
    exchange_rate: float,
    iterations: int,
    budget: int = 10000,
    strategy: str = "no_rule",
    spin_rates: list[int] | None = None,
    session_policy: str = "fixed_spin_cap",
    start_variance: bool = True,
    border_spins_per_1000y: float | None = None,
    spin_rate_quality_stddev: float = 3.0,
    time_assumptions: TimeAssumptions | None = None,
) -> list[dict[str, Any]]:
    """예산과 회전율에 따른 매트릭스 시뮬레이션을 수행합니다."""
    from simulator import simulate_multiple

    spin_cases = rotation_cases(spin_rates, border_spins_per_1000y)
    matrix_results = []

    for spin_case in spin_cases:
        spins = spin_case["spins_per_1000y"]
        results = simulate_multiple(
            machine,
            budget,
            lend_rate,
            spins,
            exchange_rate,
            iterations,
            strategy=strategy,
            session_policy=session_policy,
            start_variance=start_variance,
            border_spins_per_1000y=border_spins_per_1000y,
            spin_rate_quality_stddev=spin_rate_quality_stddev,
            time_assumptions=time_assumptions,
        )
        matrix_results.append(
            {
                "budget": budget,
                "spins_per_1000y": spins,
                "border_spins_per_1000yen": border_spins_per_1000y,
                "rotation_basis": spin_case["rotation_basis"],
                "rotation_label": spin_case["rotation_label"],
                "border_margin": spin_case["border_margin"],
                "strategy": strategy,
                "session_policy": session_policy,
                "start_variance": start_variance,
                "results": results,
            }
        )
    return matrix_results


def run_budget_matrix(
    machine: Machine,
    lend_rate: float,
    exchange_rate: float,
    iterations: int,
    budgets: list[int] | None = None,
    spins_per_1000y: int = 80,
    strategy: str = "no_rule",
    session_policy: str = "fixed_spin_cap",
    max_normal_spin_multiplier: int | None = None,
    start_variance: bool = True,
    border_spins_per_1000y: float | None = None,
    spin_rate_quality_stddev: float = 3.0,
    time_assumptions: TimeAssumptions | None = None,
) -> list[dict[str, Any]]:
    from simulator import simulate_multiple

    budgets = budgets or BUDGET_CASES
    session_policy = normalize_session_policy(session_policy)
    matrix_results = []

    for budget in budgets:
        max_normal_spins = None
        if (
            session_policy == "play_until_budget_and_balls_gone"
            and max_normal_spin_multiplier is not None
        ):
            max_normal_spins = int((budget / 1000) * spins_per_1000y * max_normal_spin_multiplier)
        results = simulate_multiple(
            machine,
            budget,
            lend_rate,
            spins_per_1000y,
            exchange_rate,
            iterations,
            strategy=strategy,
            session_policy=session_policy,
            max_normal_spins=max_normal_spins,
            start_variance=start_variance,
            border_spins_per_1000y=border_spins_per_1000y,
            spin_rate_quality_stddev=spin_rate_quality_stddev,
            time_assumptions=time_assumptions,
        )
        matrix_results.append(
            {
                "budget": budget,
                "spins_per_1000y": spins_per_1000y,
                "border_spins_per_1000yen": border_spins_per_1000y,
                "strategy": strategy,
                "session_policy": session_policy,
                "start_variance": start_variance,
                "results": results,
            }
        )
    return matrix_results


def run_strategy_matrix(
    machine: Machine,
    lend_rate: float,
    exchange_rate: float,
    budget: int,
    iterations: int,
    spin_rates: list[int] | None = None,
    strategies: list[str] | None = None,
    session_policy: str = "fixed_spin_cap",
    start_variance: bool = True,
    border_spins_per_1000y: float | None = None,
    spin_rate_quality_stddev: float = 3.0,
    time_assumptions: TimeAssumptions | None = None,
) -> list[dict[str, Any]]:
    from simulator import simulate_multiple

    spin_cases = rotation_cases(spin_rates, border_spins_per_1000y)
    strategies = strategies or list(STRATEGIES.keys())
    rows = []
    for strategy in strategies:
        for spin_case in spin_cases:
            spins = spin_case["spins_per_1000y"]
            rows.append(
                {
                    "budget": budget,
                    "spins_per_1000y": spins,
                    "border_spins_per_1000yen": border_spins_per_1000y,
                    "rotation_basis": spin_case["rotation_basis"],
                    "rotation_label": spin_case["rotation_label"],
                    "border_margin": spin_case["border_margin"],
                    "strategy": strategy,
                    "strategy_label": STRATEGIES[strategy],
                    "session_policy": session_policy,
                    "start_variance": start_variance,
                    "results": simulate_multiple(
                        machine,
                        budget,
                        lend_rate,
                        spins,
                        exchange_rate,
                        iterations,
                        strategy=strategy,
                        session_policy=session_policy,
                        start_variance=start_variance,
                        border_spins_per_1000y=border_spins_per_1000y,
                        spin_rate_quality_stddev=spin_rate_quality_stddev,
                        time_assumptions=time_assumptions,
                    ),
                }
            )
    return rows


__all__ = [
    "BUDGET_CASES",
    "PROFILE_BUDGET_CASES",
    "SPIN_RATE_CASES",
    "absolute_spin_cases",
    "rotation_cases",
    "run_budget_matrix",
    "run_matrix_simulation",
    "run_strategy_matrix",
]
