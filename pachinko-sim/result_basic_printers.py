from typing import Any

from machines import Machine
from result_formatting import build_ascii_table
from result_metrics import calculate_metrics
from result_output_helpers import (
    denominator_tail_rows,
    installed_name_ja_from_results,
    installed_name_ko_from_results,
    placement_summary_from_results,
    print_ascii_table,
    print_travel_satisfaction_grade,
    profit_condition_table_rows,
    session_policy_label_from_results,
    theoretical_no_hit_rate_from_results,
)
from result_table_builders import (
    ball_graph_rows,
    hit_event_rows,
    multiple_risk_detail_rows,
    multiple_summary_rows,
    single_summary_rows,
)


def print_single_result(
    store_name: str,
    machine: Machine,
    res: dict[str, Any],
    spins_per_1000y: int,
):
    print("\n" + "=" * 45)
    print("=== 오사카 난바 실제 설치기종 1엔 파친코 체감 모의 ===")

    print_ascii_table(
        "ASCII 플레이 요약",
        ["항목", "값"],
        single_summary_rows(store_name, machine, res, spins_per_1000y),
    )

    events = res.get("hit_events", [])
    print("\n[실전식 大当り(대당첨) 로그]")
    if not events:
        print("당첨 기록 없음")
    else:
        print(
            build_ascii_table(
                ["#", "종류", "통상", "우타치", "상태", "확률", "출옥", "연속", "표시"],
                hit_event_rows(events),
            )
        )

        print_ascii_table("ASCII 출옥 추이", ["#", "보유 구슬", "그래프"], ball_graph_rows(events))

    print_travel_satisfaction_grade(machine)
    print("=" * 45)


def print_multiple_result(
    store_name: str,
    machine: Machine,
    results: list[dict[str, Any]],
    iterations: int,
):
    m = calculate_metrics(results, iterations)
    theory_no_hit = theoretical_no_hit_rate_from_results(machine.normal_prob, results)
    session_policy_label = session_policy_label_from_results(results)
    placement_summary = placement_summary_from_results(results)
    installed_name_ko = installed_name_ko_from_results(results)
    installed_name_ja = installed_name_ja_from_results(results)

    print("\n" + "=" * 50)
    print(f"=== {iterations}회 반복 리스크 평가 결과 ===")
    print(f"기종: {machine.name_ko}")
    print(f"기종 일본어: {machine.name_ja}")
    if installed_name_ko:
        print(f"실설치명(한국어): {installed_name_ko}")
    if installed_name_ja:
        print(f"실설치명(일본어): {installed_name_ja}")
    if placement_summary:
        print(f"가게별 배치: {placement_summary}")
    if session_policy_label:
        print(f"세션 방식: {session_policy_label}")
    print_ascii_table(
        "ASCII 핵심 요약",
        ["지표", "값", "참고"],
        multiple_summary_rows(machine, m, theory_no_hit),
    )

    print_ascii_table(
        "ASCII 실질 플러스 조건",
        ["조건", "표본/발생률", "플러스", "95% CI", "중앙", "평균", "판정"],
        profit_condition_table_rows(m),
    )

    print_ascii_table(
        "ASCII 독립시행 분모 초과 확률",
        ["기준", "회전수", "무당첨", "1회 이상", "해석"],
        denominator_tail_rows(machine),
    )

    print_ascii_table(
        "ASCII 리스크 상세",
        ["항목", "값", "참고"],
        multiple_risk_detail_rows(machine, m),
    )

    print_travel_satisfaction_grade(machine)
    print("=" * 50)
