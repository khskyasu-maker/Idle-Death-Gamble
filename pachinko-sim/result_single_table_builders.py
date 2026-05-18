from typing import Any, Dict, List

from machines import Machine
from result_formatting import build_ascii_bar, minutes_text, yen
from result_output_helpers import lt_count_text, upper_count_text
from session_limits import HARD_SESSION_TIME_LIMIT_MINUTES, SESSION_TIME_LIMIT_MINUTES
from sim_terms import state_transition_label


def single_summary_rows(store_name: str, machine: Machine, res: Dict[str, Any], spins_per_1000y: int) -> List[List[Any]]:
    first_hit = f"{res['first_hit_spin']}회전" if res["first_hit_spin"] is not None else "당첨 없음 (예산 전액 증발)"
    first_hit_total = (
        f"{res.get('first_hit_total_spins')}회전"
        if res.get("first_hit_total_spins") is not None
        else "당첨 없음"
    )
    return [
        ["매장", store_name],
        ["기종", machine.name_ko],
        ["기종 일본어", machine.name_ja],
        ["실설치명(한국어)", res.get("installed_full_name_ko") or res.get("installed_full_name_ja") or "-"],
        ["실설치명(일본어)", res.get("installed_full_name_ja") or "-"],
        ["점포별 배치", res.get("placement_summary", "-")],
        ["투자금", yen(res["budget"])],
        ["입력 회전율", f"{spins_per_1000y}회/1000yen"],
        ["세션 회전율", f"{res.get('observed_spins_per_1000y', spins_per_1000y):.1f}회/1000yen"],
        ["헤소 입상 확률", f"{res.get('start_probability', 0.0) * 100:.2f}%/발"],
        ["세션 방식", res.get("session_policy_label", res.get("session_policy", ""))],
        ["전략", res.get("strategy_label", "노룰")],
        ["현금 사용", yen(res.get("cash_spent", res["budget"]))],
        ["최종 잔류액", f"{yen(res.get('final_remaining_value', res.get('final_money', 0)))} (미사용 {yen(res.get('unused_cash', 0))} + 교환 {yen(res.get('final_money', 0))})"],
        ["예산 소진 후", f"소진 {res.get('cash_budget_exhausted', False)} / 이후 {minutes_text(res.get('post_budget_play_minutes', 0.0))}", f"완전소진정지 {res.get('funds_exhausted_triggered', False)}"],
        ["현실 시간 제한", f"소프트 {res.get('soft_stop_minutes', SESSION_TIME_LIMIT_MINUTES):.0f}분 / 하드 {res.get('session_time_limit_minutes', HARD_SESSION_TIME_LIMIT_MINUTES):.0f}분 / 현금마감 {res.get('cash_input_cutoff_minutes', 0):.0f}분", f"RUSH후정리 {res.get('soft_stop_triggered', False)} / 하드종료 {res.get('time_limit_triggered', False)} / 현금차단 {res.get('cash_input_cutoff_triggered', False)}"],
        ["시간 프로파일", res.get("time_assumptions", {}).get("profile_name", "generic")],
        ["예상 체류 시간", minutes_text(res.get("play_minutes", 0.0))],
        ["현금 없는 시간", f"{minutes_text(res.get('cashless_play_minutes', 0.0))} ({res.get('cashless_play_share', 0.0):.1f}%)"],
        ["시간 구성", f"통상 {minutes_text(res.get('normal_play_minutes', 0.0))} / 우타치 {minutes_text(res.get('right_play_minutes', 0.0))} / 당첨연출 {minutes_text(res.get('hit_effect_minutes', 0.0))}"],
        ["보류/연출 대기", minutes_text(res.get("reserve_wait_minutes", 0.0))],
        ["최초 당첨", first_hit],
        ["최초 당첨 총체감", first_hit_total],
        ["총 당첨", f"{res['total_hits']}회"],
        ["최대 연속", f"{res['max_streak']}연"],
        ["RUSH/ST 체험", "YES" if res["experienced_rush"] else "NO"],
        ["RUSH / LT 진입", f"{res.get('rush_entries', 0)}회 / {lt_count_text(machine, res.get('lt_entries', 0))}"],
        ["상위RUSH 진입", upper_count_text(machine, res.get("upper_entries", 0))],
        ["총 획득 구슬", f"{res['total_out_balls']:,}발"],
        ["최종/잠금 구슬", f"{res.get('final_balls', 0):,}발 / {res.get('locked_balls', 0):,}발"],
        ["최종 차액", yen(res["net_profit"], signed=True)],
    ]


def hit_event_rows(events: List[Dict[str, Any]]) -> List[List[Any]]:
    rows = []
    for event in events:
        flags = []
        if event.get("rush_entry"):
            flags.append("RUSH/ST 진입")
        if event.get("lt_entry"):
            flags.append("LT 진입")
        if event.get("upper_entry"):
            flags.append("상위RUSH 진입")
        rows.append(
            [
                event["hit_no"],
                event["label"],
                event["normal_spins"],
                event["right_spins"],
                state_transition_label(event["state_before"], event["state_after"]),
                f"1/{event['probability_denominator']:.1f}",
                f"{event['payout_balls']:,}발",
                f"{event['streak']}연",
                " / ".join(flags) if flags else "-",
            ]
        )
    return rows


def ball_graph_rows(events: List[Dict[str, Any]]) -> List[List[Any]]:
    ball_values = [int(event.get("bank_balls_after", 0)) for event in events]
    max_balls = max(ball_values) if ball_values else 0
    return [
        [
            event["hit_no"],
            f"{int(event.get('bank_balls_after', 0)):,}발",
            build_ascii_bar(int(event.get("bank_balls_after", 0)), max_balls),
        ]
        for event in events
    ]


__all__ = ["ball_graph_rows", "hit_event_rows", "single_summary_rows"]
