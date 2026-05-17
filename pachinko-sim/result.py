"""Compatibility exports for simulator result output.

New simulator code should import directly from the focused result modules:
`result_printers`, `result_metrics`, `result_output_helpers`,
`result_table_builders`, `result_csv`, or `result_public_export`.
"""

from result_metrics import calculate_metrics
from result_output_helpers import (
    benchmark_model_value,
    border_adjustment,
    border_delta,
    border_label,
    denominator_tail_rows,
    fall_state_continue_chance,
    operating_warning,
)
from result_printers import (
    print_budget_matrix_results,
    print_matrix_results,
    print_model_profile_results,
    print_multiple_result,
    print_single_result,
    print_store_comparison_results,
    print_strategy_matrix_results,
    save_matrix_to_csv,
)

__all__ = [
    "benchmark_model_value",
    "border_adjustment",
    "border_delta",
    "border_label",
    "calculate_metrics",
    "denominator_tail_rows",
    "fall_state_continue_chance",
    "operating_warning",
    "print_budget_matrix_results",
    "print_matrix_results",
    "print_model_profile_results",
    "print_multiple_result",
    "print_single_result",
    "print_store_comparison_results",
    "print_strategy_matrix_results",
    "save_matrix_to_csv",
]
