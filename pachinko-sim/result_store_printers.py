from typing import Any

from machines import Machine
from result_formatting import yen
from result_metrics import calculate_metrics
from result_output_helpers import (
    border_delta,
    lt_rate_text,
    operating_warning,
    print_ascii_table,
    print_travel_satisfaction_grade,
    rotation_condition_text,
    stay_rate_text,
    theoretical_no_hit_rate_from_results,
    upper_rate_text,
)
from result_store_views import build_store_comparison_view
from session_limits import SESSION_TIME_LIMIT_HOURS


def print_store_comparison_results(
    machine: Machine,
    comparison_results: list[dict[str, Any]],
    iterations: int,
):
    print("\n" + "=" * 86)
    print(f"=== {machine.name_ko} 가게별 같은 기종 비교 ({iterations}회) ===")
    print(f"기종 일본어: {machine.name_ja}")

    if not comparison_results:
        print("표시할 데이터가 없습니다.")
        return

    view = build_store_comparison_view(
        machine,
        comparison_results,
        iterations,
        calculate_metrics,
        operating_warning,
        theoretical_no_hit_rate_from_results,
        border_delta,
        rotation_condition_text,
        lt_rate_text,
        upper_rate_text,
        stay_rate_text,
    )
    print(f"비교 기준: {view['comparison_mode_label']}")
    print(f"기준 입력 회전수: {view['reference_rotation']}")
    print(f"예산/전략/세션: {yen(view['budget'])} / {view['strategy_label']} / {view['session_policy_label']}")
    print("비교 해석:", view["assumption_text"])

    if view["placement_summary"]:
        print(f"가게별 배치: {view['placement_summary']}")

    print_ascii_table(
        "ASCII 가게별 실설치명",
        ["가게", "한국어", "일본어"],
        view["name_rows"],
    )

    print_ascii_table(
        "ASCII 가게/레이트 조건표",
        ["가게", "레이트", "설치", "입력회전", "헤소/발", "보더+/-", "판정/보더비", "당첨", "0회", "이론0회", "RUSH", "LT/상위"],
        view["condition_rows"],
    )
    print_ascii_table(
        "ASCII 가게별 손익/체감표",
        [
            "가게",
            "플러스",
            "평균시간",
            f"{SESSION_TIME_LIMIT_HOURS}h+",
            "잔류액",
            "평균",
            "중앙",
            "하위10",
            "상위10",
            "회수80",
            "평균초당첨",
            "평균아타리/연",
            "실익조건",
            "주의",
        ],
        view["money_rows"],
    )

    print("주의: 가게 비교는 같은 기종과 입력 조건의 런타임 통계입니다. 실제 台番号(기기 번호)별 이력, 현장 못 상태, 시간 제약은 별도 확인 대상입니다.")
    print_travel_satisfaction_grade(machine)
    print("=" * 86)
