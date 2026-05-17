from typing import Any

from machines import Machine
from result_output_helpers import (
    installed_name_ja_from_results,
    installed_name_ko_from_results,
    placement_summary_from_results,
    print_travel_satisfaction_grade,
    session_policy_label_from_results,
    time_profile_text,
)


def print_section_header(title: str, width: int):
    print("\n" + "=" * width)
    print(title)


def print_machine_context(
    machine: Machine,
    results: list[dict[str, Any]] | None = None,
    *,
    include_korean_name: bool = False,
    include_confidence: bool = False,
):
    if include_korean_name:
        print(f"기종: {machine.name_ko}")
    if include_confidence:
        print(f"모델 신뢰도: {machine.confidence} | 추정 여부: {'예' if machine.is_estimated else '아니오'}")
    print(f"기종 일본어: {machine.name_ja}")

    if not results:
        return

    installed_name_ko = installed_name_ko_from_results(results)
    installed_name_ja = installed_name_ja_from_results(results)
    placement_summary = placement_summary_from_results(results)
    if installed_name_ko:
        print(f"실설치명(한국어): {installed_name_ko}")
    if installed_name_ja:
        print(f"실설치명(일본어): {installed_name_ja}")
    if placement_summary:
        print(f"점포별 배치: {placement_summary}")


def print_session_context(
    results: list[dict[str, Any]],
    *,
    include_session_policy: bool = True,
    include_time_profile: bool = False,
):
    session_policy_label = session_policy_label_from_results(results)
    if include_session_policy and session_policy_label:
        print(f"세션 방식: {session_policy_label}")
    if include_time_profile:
        print(f"시간 프로파일: {time_profile_text(results)}")


def print_result_footer(machine: Machine, width: int):
    print_travel_satisfaction_grade(machine)
    print("=" * width)
