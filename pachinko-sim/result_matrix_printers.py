from typing import Any

from machines import Machine
from result_metrics import calculate_metrics
from result_output_helpers import (
    denominator_tail_rows,
    print_ascii_table,
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
from session_limits import (
    HARD_SESSION_TIME_LIMIT_HOURS,
    SESSION_TIME_LIMIT_HOURS,
)


def print_matrix_results(machine: Machine, matrix_results: list[dict[str, Any]], iterations: int):
    print_section_header(f"=== {machine.name_ko} 매트릭스 리스크 분석 ({iterations}회) ===", 60)
    print_machine_context(machine, matrix_results)

    rows = matrix_result_rows(machine, matrix_results, iterations)

    print_ascii_table(
        "ASCII 조건 수익표",
        [
            "입력회전",
            "가능회전",
            "평균시간",
            "보더+/-",
            "판정/보더비",
            "플러스",
            "평균",
            "중앙",
            "하위10",
            "상위10",
            "실익조건",
            "주의",
        ],
        rows["summary"],
    )
    print_ascii_table(
        "ASCII 조건 체감표",
        ["회전", "당첨", "0회", "이론0회", "RUSH", "LT", "상위RUSH", "회수50/80/100", "최대당/연", "상위10당/연"],
        rows["risk"],
    )

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

    print_ascii_table(
        "ASCII 예산 손익표",
        ["예산", "가능회전", "평균회전", "판정/보더비", "플러스", "평균", "중앙", "하위10", "상위10", "실익조건", "평균현금"],
        tables["money"],
    )
    print_ascii_table(
        "ASCII 예산 체감표",
        ["예산", "당첨", "0회", "이론0회", "RUSH", "LT", "상위RUSH", "회수50/80/100", "최대당/연"],
        tables["risk"],
    )
    print_ascii_table(
        "ASCII 예산 체류 시간표",
        ["예산", "평균시간", "P50/P90", "현금없는", "무현금비율", "소진후", "통상", "우타치", "당첨연출", "보류대기", "현금속도"],
        tables["time"],
    )
    print_ascii_table(
        "ASCII 체류 도달률표",
        [
            "예산",
            "1h+",
            "2h+",
            "3h+",
            "4h+",
            "6h+",
            "8h+",
            f"{SESSION_TIME_LIMIT_HOURS}h+",
            f"{SESSION_TIME_LIMIT_HOURS}h정리",
            f"{HARD_SESSION_TIME_LIMIT_HOURS}h하드",
            "현금마감",
        ],
        tables["stay"],
    )
    print_ascii_table(
        "ASCII 최종 잔류액표",
        ["예산", "예산소진", "미사용현금", "교환가능", "최종잔류", "P10/P50/P90", "잔류손익", "완전소진"],
        tables["remaining"],
    )
    print_ascii_table(
        "ASCII 통계 신뢰도",
        ["예산", "평균SE", "평균95CI", "중앙95CI", "하위10 95CI", "CVaR10", "상위10 95CI"],
        tables["stats"],
    )

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

    print_ascii_table(
        "ASCII 예산별 아타리/연속 주요 지표",
        [
            "예산",
            "가능회전",
            "이론당첨",
            "시뮬당첨",
            "평균초당첨",
            "초당첨P50/P90",
            "총체감P50/P90",
            "평균아타리",
            "초당첨후",
            "평균연속",
            "평균우타치",
            "RUSH",
            "LT",
            "상위RUSH",
            "실익조건",
            "중앙",
            "하위10",
        ],
        tables["feel"],
    )
    print_ascii_table(
        "ASCII 예산별 체류 시간",
        ["예산", "평균시간", "P50/P90", "현금없는", "무현금비율", "소진후", "통상", "우타치", "당첨연출", "보류대기", "현금속도"],
        tables["time"],
    )
    print_ascii_table(
        "ASCII 예산별 체류 도달률",
        ["예산", "1h+", "2h+", "3h+", "4h+", "6h+", "8h+", f"{SESSION_TIME_LIMIT_HOURS}h+", "최종잔류"],
        tables["stay"],
    )

    print_ascii_table(
        "ASCII 공개 일본 스펙값 대비 위화감 체크",
        ["지표", "공개/일본값", "모델값", "차이", "판정", "출처"],
        benchmark_rows(machine) or [["등록 벤치마크", "-", "-", "-", "없음", "-"]],
    )
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

    print_ascii_table(
        "ASCII 전략 핵심 비교",
        ["전략", "회전", "점수", "플러스", "평균시간", "평균", "중앙", "하위10", "0회", "RUSH", "LT", "상위RUSH"],
        tables["core"],
    )
    print_ascii_table(
        "ASCII 전략 조건/발동",
        ["전략", "회전", "보더+/-", "판정/보더비", "주의", "최대당/연", "회수50", "회수80", "회수100", "실익조건", "익절", "손절"],
        tables["condition"],
    )

    print_ascii_table(
        "ASCII 조건 비교 상위 5개",
        ["순위", "전략", "회전", "점수", "플러스", "평균", "하위10", "보더+/-", "주의"],
        tables["top"],
    )

    print_result_footer(machine, 80)
