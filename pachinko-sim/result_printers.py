"""Public printer exports for simulator CLI output."""

from typing import Any

from machines import Machine
from result_basic_printers import print_multiple_result, print_single_result
from result_csv import save_matrix_to_csv as write_matrix_to_csv
from result_matrix_printers import (
    print_budget_matrix_results,
    print_matrix_results,
    print_model_profile_results,
    print_strategy_matrix_results,
)
from result_metrics import calculate_metrics
from result_store_printers import print_store_comparison_results


def save_matrix_to_csv(
    machine: Machine,
    matrix_results: list[dict[str, Any]],
    iterations: int,
    filepath: str = "results.csv",
):
    write_matrix_to_csv(machine, matrix_results, iterations, calculate_metrics, filepath)
    print(f"\n[안내] 최신 매트릭스 분석 결과가 {filepath} 에 저장되었습니다. 기존 파일은 덮어썼습니다.")


__all__ = [
    "print_budget_matrix_results",
    "print_matrix_results",
    "print_model_profile_results",
    "print_multiple_result",
    "print_single_result",
    "print_store_comparison_results",
    "print_strategy_matrix_results",
    "save_matrix_to_csv",
]
