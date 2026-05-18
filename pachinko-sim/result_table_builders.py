"""Compatibility exports for simulator result table row builders."""

from result_matrix_table_builders import budget_result_tables, matrix_result_rows
from result_profile_table_builders import benchmark_rows, model_profile_intro_rows, model_profile_result_tables
from result_repeated_table_builders import multiple_risk_detail_rows, multiple_summary_rows
from result_single_table_builders import ball_graph_rows, hit_event_rows, single_summary_rows
from result_strategy_table_builders import strategy_result_tables


__all__ = [
    "ball_graph_rows",
    "benchmark_rows",
    "budget_result_tables",
    "hit_event_rows",
    "matrix_result_rows",
    "model_profile_intro_rows",
    "model_profile_result_tables",
    "multiple_risk_detail_rows",
    "multiple_summary_rows",
    "single_summary_rows",
    "strategy_result_tables",
]
