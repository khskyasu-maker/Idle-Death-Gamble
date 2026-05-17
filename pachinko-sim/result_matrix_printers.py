from typing import Any

from machines import Machine
from result_metrics import calculate_metrics
from result_output_helpers import (
    denominator_tail_rows,
    print_ascii_table,
)
from result_matrix_sections import (
    print_budget_tables,
    print_matrix_tables,
    print_profile_tables,
    print_strategy_tables,
)
from result_printer_common import (
    print_machine_context,
    print_result_footer,
    print_section_header,
    print_session_context,
)
from result_table_builders import (
    benchmark_rows,
    budget_result_tables,
    matrix_result_rows,
    model_profile_intro_rows,
    model_profile_result_tables,
    strategy_result_tables,
)


def print_matrix_results(machine: Machine, matrix_results: list[dict[str, Any]], iterations: int):
    print_section_header(f"=== {machine.name_ko} 매트릭스 리스크 분석 ({iterations}회) ===", 60)
    print_machine_context(machine, matrix_results)

    rows = matrix_result_rows(machine, matrix_results, iterations)
    print_matrix_tables(rows)

    print_result_footer(machine, 60)


def print_budget_matrix_results(
    store_name: str,
    machine: Machine,
    matrix_results: list[dict[str, Any]],
    iterations: int,
):
    print_section_header(f"=== {store_name} / {machine.name_ko} 예산별 리스크 분석 ({iterations}회) ===", 70)
    print_machine_context(machine, matrix_results)
    if matrix_results:
        print_session_context(matrix_results[0]["results"], include_time_profile=True)

    tables = budget_result_tables(machine, matrix_results, iterations)
    print_budget_tables(tables)

    print_result_footer(machine, 70)


def print_model_profile_results(
    store_name: str,
    machine: Machine,
    matrix_results: list[dict[str, Any]],
    iterations: int,
):
    print_section_header(f"=== {store_name} / {machine.name_ko} 모델 프로파일·위화감 검증 ({iterations}회) ===", 86)
    print_machine_context(machine, matrix_results)

    if not matrix_results:
        print("표시할 데이터가 없습니다.")
        return

    first_row = matrix_results[0]
    print_session_context(
        first_row.get("results", []),
        include_session_policy=False,
        include_time_profile=True,
    )
    first_metrics = calculate_metrics(first_row["results"], iterations)

    print_ascii_table(
        "ASCII 1000엔 기준 체감",
        ["항목", "값", "해석"],
        model_profile_intro_rows(machine, first_row, first_metrics),
    )

    print_ascii_table(
        "ASCII 독립시행 분모 초과 확률",
        ["기준", "회전수", "무당첨", "1회 이상", "해석"],
        denominator_tail_rows(machine),
    )

    tables = model_profile_result_tables(machine, matrix_results, iterations)
    print_profile_tables(tables, benchmark_rows(machine) or [["등록 벤치마크", "-", "-", "-", "없음", "-"]])
    print("판정 기준: OK는 모델값과 공개값 차이가 작다는 뜻이고, 실제 수익 보장을 의미하지 않습니다.")

    print_result_footer(machine, 86)


def print_strategy_matrix_results(
    store_name: str,
    machine: Machine,
    matrix_results: list[dict[str, Any]],
    iterations: int,
):
    print_section_header(f"=== {store_name} / {machine.name_ko} 회전율·전략 비교 ({iterations}회) ===", 80)
    print_machine_context(machine, matrix_results, include_confidence=True)

    tables = strategy_result_tables(machine, matrix_results, iterations)
    print_strategy_tables(tables)

    print_result_footer(machine, 80)
