from machines import Machine
from typing import Dict, Any, List
from model_checks import theoretical_hit_rate
from sim_terms import state_transition_label
from spec_benchmarks import PUBLIC_BENCHMARKS
from session_limits import (
    HARD_SESSION_TIME_LIMIT_HOURS,
    HARD_SESSION_TIME_LIMIT_MINUTES,
    SESSION_TIME_LIMIT_HOURS,
    SESSION_TIME_LIMIT_MINUTES,
)
from result_formatting import (
    build_ascii_bar,
    build_ascii_table,
    minutes_text,
    pct,
    yen,
)
from result_csv import save_matrix_to_csv as write_matrix_to_csv
from result_metrics import calculate_metrics
from result_output_helpers import (
    benchmark_judgement,
    benchmark_model_value,
    bilingual_ja_ko,
    border_delta,
    border_label,
    cash_burn_text,
    ci_pct,
    denominator_tail_rows,
    format_benchmark_value,
    installed_name_ja_from_results,
    installed_name_ko_from_results,
    lt_ci_text,
    lt_count_text,
    lt_rate_text,
    operating_warning,
    placement_summary_from_results,
    print_ascii_table,
    print_travel_satisfaction_grade,
    probability_text,
    profit_condition_table_rows,
    relative_score,
    remaining_value_text,
    rotation_condition_text,
    rotation_display_text,
    session_policy_label_from_results,
    spin_capacity_text,
    stay_rate_text,
    theoretical_no_hit_rate_from_results,
    time_profile_text,
    true_spin_rate_text,
    observed_spin_rate_text,
    upper_count_text,
    upper_rate_text,
    value_diff,
)
from result_store_views import build_store_comparison_view


def print_single_result(store_name: str, machine: Machine, res: Dict[str, Any], spins_per_1000y: int):
    print("\n" + "="*45)
    print("=== 오사카 난바 실제 설치기종 1엔 파친코 체감 모의 ===")

    first_hit = f"{res['first_hit_spin']}회전" if res['first_hit_spin'] is not None else "당첨 없음 (예산 전액 증발)"
    first_hit_total = (
        f"{res.get('first_hit_total_spins')}회전"
        if res.get('first_hit_total_spins') is not None
        else "당첨 없음"
    )
    print_ascii_table(
        "ASCII 플레이 요약",
        ["항목", "값"],
        [
            ["매장", store_name],
            ["기종", machine.name_ko],
            ["기종 일본어", machine.name_ja],
            ["실설치명(한국어)", installed_name_ko_from_results([res]) or "-"],
            ["실설치명(일본어)", installed_name_ja_from_results([res]) or "-"],
            ["가게별 배치", res.get("placement_summary", "-")],
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
        ],
    )

    events = res.get("hit_events", [])
    print("\n[실전식 大当り(대당첨) 로그]")
    if not events:
        print("당첨 기록 없음")
    else:
        event_rows = []
        for event in events:
            flags = []
            if event.get("rush_entry"):
                flags.append("RUSH/ST 진입")
            if event.get("lt_entry"):
                flags.append("LT 진입")
            if event.get("upper_entry"):
                flags.append("상위RUSH 진입")
            event_rows.append(
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
        print(build_ascii_table(
            ["#", "종류", "통상", "우타치", "상태", "확률", "출옥", "연속", "표시"],
            event_rows,
        ))

        ball_values = [int(event.get("bank_balls_after", 0)) for event in events]
        max_balls = max(ball_values) if ball_values else 0
        graph_rows = [
            [
                event["hit_no"],
                f"{int(event.get('bank_balls_after', 0)):,}발",
                build_ascii_bar(int(event.get("bank_balls_after", 0)), max_balls),
            ]
            for event in events
        ]
        print_ascii_table("ASCII 출옥 추이", ["#", "보유 구슬", "그래프"], graph_rows)

    print_travel_satisfaction_grade(machine)
    print("="*45)

def print_multiple_result(store_name: str, machine: Machine, results: List[Dict[str, Any]], iterations: int):
    m = calculate_metrics(results, iterations)
    theory_no_hit = theoretical_no_hit_rate_from_results(machine.normal_prob, results)
    session_policy_label = session_policy_label_from_results(results)
    placement_summary = placement_summary_from_results(results)
    installed_name_ko = installed_name_ko_from_results(results)
    installed_name_ja = installed_name_ja_from_results(results)

    print("\n" + "="*50)
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
        [
            ["당첨 체험", pct(m["hit_rate"]), "최소 1회 당첨"],
            ["RUSH/ST 체험", pct(m["rush_rate"]), f"95% CI {ci_pct(m, 'rush_rate')}"],
            ["당첨 0회", pct(m["ruin_rate"]), f"95% CI {ci_pct(m, 'ruin_rate')} / 회전변동 이론 {theory_no_hit:.1f}%"],
            ["다이 품질 분포", true_spin_rate_text(m), f"품질 표준편차 {m['spin_rate_quality_stddev']:.1f}회"],
            ["헤소 입상 표본", observed_spin_rate_text(m), f"입상 {m['start_probability'] * 100:.2f}%/발"],
            ["시간 프로파일", m["time_profile"], m["time_profile_note"]],
            ["평균 체류 시간", minutes_text(m["avg_play_minutes"]), f"P50 {minutes_text(m['median_play_minutes'])} / P90 {minutes_text(m['p90_play_minutes'])}"],
            [f"{SESSION_TIME_LIMIT_HOURS}시간 정리", f"도달 {stay_rate_text(m, SESSION_TIME_LIMIT_HOURS)} / RUSH후정리 {pct(m['soft_stop_rate'])}", f"하드종료 {pct(m['hard_time_limit_stop_rate'])} / 현금마감 {pct(m['cash_input_cutoff_rate'])}"],
            ["최종 잔류액", remaining_value_text(m), f"P10~P90 {yen(m['p10_final_remaining_value'])}~{yen(m['p90_final_remaining_value'])} / 예산소진 {pct(m['budget_exhausted_rate'])}"],
            ["예산 소진 후", f"지속 {pct(m['post_budget_continue_rate'])} / 평균 {minutes_text(m['avg_post_budget_play_minutes'])}", f"지속된 경우 평균 {minutes_text(m['avg_post_budget_play_minutes_when_continued'])} / 완전소진정지 {pct(m['funds_exhausted_stop_rate'])}"],
            ["현금 없는 시간", f"{minutes_text(m['avg_cashless_play_minutes'])} ({m['avg_cashless_play_share']:.1f}%)", "당첨/우타치/보유구슬 재사용 시간"],
            ["현금 소모 속도", cash_burn_text(m), "시간은 발사/보류/연출 근사 포함"],
            ["플러스 마감", pct(m["positive_close_rate"]), f"95% CI {ci_pct(m, 'positive_close_rate')}"],
            ["실질 플러스 조건", m["profit_condition_summary"], "순이익>0 조건부 확률"],
            ["평균 차액", yen(m["avg_profit"], signed=True), f"95% CI {yen(m['avg_profit_ci_low'], signed=True)}~{yen(m['avg_profit_ci_high'], signed=True)}"],
            ["평균 표준오차", yen(m["avg_profit_standard_error"]), f"표준편차 {yen(m['profit_stddev'])} / 예산대비 {m['avg_profit_se_budget_pct']:.2f}% / {m['mean_ci_method']} CI"],
            ["중앙값", yen(m["median_profit"], signed=True), ""],
            ["중앙값 95% CI", f"{yen(m['median_profit_ci_low'], signed=True)}~{yen(m['median_profit_ci_high'], signed=True)}", "순위 기반 분위수 CI"],
            ["하위10% / 상위10%", f"{yen(m['worst_10_profit'], signed=True)} / {yen(m['top_10_profit'], signed=True)}", ""],
            ["CVaR10 / 상위10평균", f"{yen(m['cvar_10_profit'], signed=True)} / {yen(m['upper_tail_10_profit'], signed=True)}", "꼬리 평균"],
            ["회수 50/80/100", f"{pct(m['recovery_50_rate'])} / {pct(m['recovery_80_rate'])} / {pct(m['recovery_100_rate'])}", ""],
            ["LT 진입", lt_rate_text(machine, m), lt_ci_text(machine, m)],
            ["상위RUSH 진입", upper_rate_text(machine, m), "LT와 별도 집계"],
            ["최대 大当り(대당첨) / 연속", f"{m['max_hits']}회 / {m['max_streak_seen']}연", f"상위10% {m['p90_hits']}회 / {m['p90_streak']}연"],
        ],
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
        [
            ["단발 종료", pct(m["single_hit_finish_rate"]), "1번 맞고 종료"],
            ["500발 이하 종료", pct(m["under_500_finish_rate"]), "소액 출옥 후 종료"],
            ["회수 50%", pct(m["recovery_50_rate"]), "투자금 절반 이상"],
            ["회수 80%", pct(m["recovery_80_rate"]), "투자금 80% 이상"],
            ["회수 100%", pct(m["recovery_100_rate"]), "투자금 이상"],
            ["최대 손실 / 이익", f"{yen(m['min_profit'], signed=True)} / {yen(m['max_profit'], signed=True)}", ""],
            ["최대 RUSH / LT", f"{m['max_rush_entries']}회 / {lt_count_text(machine, m['max_lt_entries'])}", f"최대 우타치 {m['max_right_spins']}회"],
            ["최대 상위RUSH", upper_count_text(machine, m["max_upper_entries"]), "비LT 상위 상태"],
            ["평균 현금 / 회수", f"{yen(m['avg_cash_spent'])} / {yen(m['avg_final_money'])}", ""],
            ["시간 구성", f"통상 {minutes_text(m['avg_normal_play_minutes'])} / 우타치 {minutes_text(m['avg_right_play_minutes'])}", f"당첨연출 {minutes_text(m['avg_hit_effect_minutes'])} / 보류대기 {minutes_text(m['avg_reserve_wait_minutes'])}"],
            ["가능 회전", spin_capacity_text(m), "구슬->헤소 입상 변동"],
            ["초당첨 위치", f"평균 {m['avg_first_hit']}회 / 중앙 {m['median_first_hit']}회", f"맞은 세션 기준 P90 {m['p90_first_hit']}회"],
            ["초당첨 총체감", f"평균 {m['avg_first_hit_total_spins']}회 / 중앙 {m['median_first_hit_total_spins']}회", f"통상+時短(시단)/우타치 포함 P90 {m['p90_first_hit_total_spins']}회"],
            ["초당첨 후 당첨", f"{m['avg_after_first_hits']:.2f}회", f"맞은 세션 평균 大当り(대당첨) {m['avg_hits_when_hit']:.2f}회"],
            ["평균 회전 / 당첨", f"{m['avg_spins']}회전 / {m['avg_hits']:.2f}회", f"RUSH {m['avg_rush_entries']:.2f}회 / LT {lt_count_text(machine, m['avg_lt_entries'])}"],
            ["평균 상위RUSH", upper_count_text(machine, m["avg_upper_entries"]), ""],
            ["익절 / 손절", f"{pct(m['profit_lock_trigger_rate'])} / {pct(m['stop_loss_trigger_rate'])}", ""],
        ],
    )

    print_travel_satisfaction_grade(machine)
    print("="*50)

def print_matrix_results(machine: Machine, matrix_results: List[Dict[str, Any]], iterations: int):
    print("\n" + "="*60)
    print(f"=== {machine.name_ko} 매트릭스 리스크 분석 ({iterations}회) ===")
    print(f"기종 일본어: {machine.name_ja}")
    if matrix_results and matrix_results[0].get("installed_full_name_ko"):
        print(f"실설치명(한국어): {installed_name_ko_from_results(matrix_results)}")
    if matrix_results and matrix_results[0].get("installed_full_name_ja"):
        print(f"실설치명(일본어): {installed_name_ja_from_results(matrix_results)}")
    if matrix_results and matrix_results[0].get("placement_summary"):
        print(f"가게별 배치: {matrix_results[0]['placement_summary']}")

    summary_rows = []
    risk_rows = []
    for mr in matrix_results:
        b = mr['budget']
        s = mr['spins_per_1000y']
        rotation_display = rotation_display_text(mr)
        m = calculate_metrics(mr['results'], iterations)
        border_spins = mr.get("border_spins_per_1000yen")
        warning = operating_warning(machine.confidence, s, border_spins)
        theory_no_hit = theoretical_no_hit_rate_from_results(machine.normal_prob, mr["results"])
        summary_rows.append([
            rotation_display,
            spin_capacity_text(m),
            minutes_text(m["avg_play_minutes"]),
            border_delta(s, border_spins),
            rotation_condition_text(s, border_spins),
            pct(m["positive_close_rate"]),
            yen(m["avg_profit"], signed=True),
            yen(m["median_profit"], signed=True),
            yen(m["worst_10_profit"], signed=True),
            yen(m["top_10_profit"], signed=True),
            m["profit_condition_summary"],
            warning or "-",
        ])
        risk_rows.append([
            rotation_display,
            pct(m["hit_rate"]),
            pct(m["ruin_rate"]),
            f"{theory_no_hit:.1f}%",
            pct(m["rush_rate"]),
            lt_rate_text(machine, m),
            upper_rate_text(machine, m),
            f"{pct(m['recovery_50_rate'])}/{pct(m['recovery_80_rate'])}/{pct(m['recovery_100_rate'])}",
            f"{m['max_hits']}회/{m['max_streak_seen']}연",
            f"{m['p90_hits']}회/{m['p90_streak']}연",
        ])

    print_ascii_table(
        "ASCII 조건 수익표",
        ["입력회전", "가능회전", "평균시간", "보더+/-", "판정/보더비", "플러스", "평균", "중앙", "하위10", "상위10", "실익조건", "주의"],
        summary_rows,
    )
    print_ascii_table(
        "ASCII 조건 체감표",
        ["회전", "당첨", "0회", "이론0회", "RUSH", "LT", "상위RUSH", "회수50/80/100", "최대당/연", "상위10당/연"],
        risk_rows,
    )

    print_travel_satisfaction_grade(machine)
    print("="*60)


def print_budget_matrix_results(store_name: str, machine: Machine, matrix_results: List[Dict[str, Any]], iterations: int):
    print("\n" + "="*70)
    print(f"=== {store_name} / {machine.name_ko} 예산별 리스크 분석 ({iterations}회) ===")
    print(f"기종 일본어: {machine.name_ja}")
    if matrix_results and matrix_results[0].get("installed_full_name_ko"):
        print(f"실설치명(한국어): {installed_name_ko_from_results(matrix_results)}")
    if matrix_results and matrix_results[0].get("installed_full_name_ja"):
        print(f"실설치명(일본어): {installed_name_ja_from_results(matrix_results)}")
    if matrix_results and matrix_results[0].get("placement_summary"):
        print(f"가게별 배치: {matrix_results[0]['placement_summary']}")
    if matrix_results:
        print(f"세션 방식: {session_policy_label_from_results(matrix_results[0]['results'])}")
        print(f"시간 프로파일: {time_profile_text(matrix_results[0]['results'])}")

    money_rows = []
    risk_rows = []
    time_rows = []
    stay_rows = []
    remaining_rows = []
    stats_rows = []
    for mr in matrix_results:
        budget = mr["budget"]
        spins = mr["spins_per_1000y"]
        border_spins = mr.get("border_spins_per_1000yen")
        m = calculate_metrics(mr["results"], iterations)
        theory_no_hit = theoretical_no_hit_rate_from_results(machine.normal_prob, mr["results"])
        money_rows.append([
            yen(budget),
            spin_capacity_text(m),
            m["avg_spins"],
            rotation_condition_text(spins, border_spins),
            pct(m["positive_close_rate"]),
            yen(m["avg_profit"], signed=True),
            yen(m["median_profit"], signed=True),
            yen(m["worst_10_profit"], signed=True),
            yen(m["top_10_profit"], signed=True),
            m["profit_condition_summary"],
            yen(m["avg_cash_spent"]),
        ])
        risk_rows.append([
            yen(budget),
            pct(m["hit_rate"]),
            pct(m["ruin_rate"]),
            f"{theory_no_hit:.1f}%",
            pct(m["rush_rate"]),
            lt_rate_text(machine, m),
            upper_rate_text(machine, m),
            f"{pct(m['recovery_50_rate'])}/{pct(m['recovery_80_rate'])}/{pct(m['recovery_100_rate'])}",
            f"{m['max_hits']}회/{m['max_streak_seen']}연",
        ])
        time_rows.append([
            yen(budget),
            minutes_text(m["avg_play_minutes"]),
            f"{minutes_text(m['median_play_minutes'])}/{minutes_text(m['p90_play_minutes'])}",
            minutes_text(m["avg_cashless_play_minutes"]),
            f"{m['avg_cashless_play_share']:.1f}%",
            minutes_text(m["avg_post_budget_play_minutes"]),
            minutes_text(m["avg_normal_play_minutes"]),
            minutes_text(m["avg_right_play_minutes"]),
            minutes_text(m["avg_hit_effect_minutes"]),
            minutes_text(m["avg_reserve_wait_minutes"]),
            cash_burn_text(m),
        ])
        stay_rows.append([
            yen(budget),
            stay_rate_text(m, 1),
            stay_rate_text(m, 2),
            stay_rate_text(m, 3),
            stay_rate_text(m, 4),
            stay_rate_text(m, 6),
            stay_rate_text(m, 8),
            stay_rate_text(m, SESSION_TIME_LIMIT_HOURS),
            pct(m["time_limit_stop_rate"]),
            pct(m["hard_time_limit_stop_rate"]),
            pct(m["cash_input_cutoff_rate"]),
        ])
        remaining_rows.append([
            yen(budget),
            pct(m["budget_exhausted_rate"]),
            yen(m["avg_unused_cash"]),
            yen(m["avg_final_money"]),
            yen(m["avg_final_remaining_value"]),
            f"{yen(m['p10_final_remaining_value'])}/{yen(m['median_final_remaining_value'])}/{yen(m['p90_final_remaining_value'])}",
            yen(m["avg_final_remaining_balance"], signed=True),
            pct(m["funds_exhausted_stop_rate"]),
        ])
        stats_rows.append([
            yen(budget),
            yen(m["avg_profit_standard_error"]),
            f"{yen(m['avg_profit_ci_low'], signed=True)}~{yen(m['avg_profit_ci_high'], signed=True)}",
            f"{yen(m['median_profit_ci_low'], signed=True)}~{yen(m['median_profit_ci_high'], signed=True)}",
            f"{yen(m['worst_10_profit_ci_low'], signed=True)}~{yen(m['worst_10_profit_ci_high'], signed=True)}",
            yen(m["cvar_10_profit"], signed=True),
            f"{yen(m['top_10_profit_ci_low'], signed=True)}~{yen(m['top_10_profit_ci_high'], signed=True)}",
        ])

    print_ascii_table(
        "ASCII 예산 손익표",
        ["예산", "가능회전", "평균회전", "판정/보더비", "플러스", "평균", "중앙", "하위10", "상위10", "실익조건", "평균현금"],
        money_rows,
    )
    print_ascii_table(
        "ASCII 예산 체감표",
        ["예산", "당첨", "0회", "이론0회", "RUSH", "LT", "상위RUSH", "회수50/80/100", "최대당/연"],
        risk_rows,
    )
    print_ascii_table(
        "ASCII 예산 체류 시간표",
        ["예산", "평균시간", "P50/P90", "현금없는", "무현금비율", "소진후", "통상", "우타치", "당첨연출", "보류대기", "현금속도"],
        time_rows,
    )
    print_ascii_table(
        "ASCII 체류 도달률표",
        ["예산", "1h+", "2h+", "3h+", "4h+", "6h+", "8h+", f"{SESSION_TIME_LIMIT_HOURS}h+", f"{SESSION_TIME_LIMIT_HOURS}h정리", f"{HARD_SESSION_TIME_LIMIT_HOURS}h하드", "현금마감"],
        stay_rows,
    )
    print_ascii_table(
        "ASCII 최종 잔류액표",
        ["예산", "예산소진", "미사용현금", "교환가능", "최종잔류", "P10/P50/P90", "잔류손익", "완전소진"],
        remaining_rows,
    )
    print_ascii_table(
        "ASCII 통계 신뢰도",
        ["예산", "평균SE", "평균95CI", "중앙95CI", "하위10 95CI", "CVaR10", "상위10 95CI"],
        stats_rows,
    )

    print_travel_satisfaction_grade(machine)
    print("="*70)


def print_model_profile_results(
    store_name: str,
    machine: Machine,
    matrix_results: List[Dict[str, Any]],
    iterations: int,
):
    print("\n" + "="*86)
    print(f"=== {store_name} / {machine.name_ko} 모델 프로파일·위화감 검증 ({iterations}회) ===")
    print(f"기종 일본어: {machine.name_ja}")
    if matrix_results and matrix_results[0].get("installed_full_name_ko"):
        print(f"실설치명(한국어): {installed_name_ko_from_results(matrix_results)}")
    if matrix_results and matrix_results[0].get("installed_full_name_ja"):
        print(f"실설치명(일본어): {installed_name_ja_from_results(matrix_results)}")
    if matrix_results and matrix_results[0].get("placement_summary"):
        print(f"가게별 배치: {matrix_results[0]['placement_summary']}")

    if not matrix_results:
        print("표시할 데이터가 없습니다.")
        return

    first_row = matrix_results[0]
    first_result = first_row["results"][0] if first_row.get("results") else {}
    time_assumptions = first_result.get("time_assumptions", {})
    lend_rate = first_result.get("lend_rate", 1.0)
    rented_balls = int(1000 / lend_rate) if lend_rate else 0
    base_return_rate = max(
        0.0,
        min(0.90, float(time_assumptions.get("normal_base_return_rate", 0.0) or 0.0)),
    )
    gross_balls_per_1000y = rented_balls / max(0.10, 1.0 - base_return_rate) if lend_rate else 0.0
    print(f"시간 프로파일: {time_profile_text(first_row.get('results', []))}")
    spins_per_1000y = first_row["spins_per_1000y"]
    border_spins = first_row.get("border_spins_per_1000yen")
    first_metrics = calculate_metrics(first_row["results"], iterations)
    one_k_hit = theoretical_hit_rate(machine.normal_prob, spins_per_1000y)
    one_k_no_hit = theoretical_no_hit_rate_from_results(machine.normal_prob, first_row["results"])
    one_k_hit_with_variance = 100.0 - one_k_no_hit

    print_ascii_table(
        "ASCII 1000엔 기준 체감",
        ["항목", "값", "해석"],
        [
            ["대여 구슬", f"{rented_balls:,}발", f"{lend_rate:.3f}엔/발 기준"],
            [
                "ベース(반환)",
                f"{base_return_rate * 100:.0f}%",
                "통상시 반환구슬을 감안한 체류시간 보정값",
            ],
            [
                "총 발사 추정",
                f"{gross_balls_per_1000y:.0f}발",
                "표시 회전수의 순소모 구슬을 실제 발사구슬로 환산",
            ],
            ["입력 회전수", f"{spins_per_1000y}회/1000엔", "현장 1000엔 테스트 입력값"],
            ["헤소 입상", f"{first_metrics['start_probability'] * 100:.2f}%/발", "구슬 1발이 헤소에 들어가 회전이 생기는 확률"],
            ["다이 품질", true_spin_rate_text(first_metrics), "釘(못)/風車(풍차)/ステージ(스테이지) 등을 회전율 분포로 근사"],
            ["입상 표본", observed_spin_rate_text(first_metrics), "같은 다이라도 1000엔마다 고정 회전이 아니라 표본 변동"],
            ["입력회전 당첨", pct(one_k_hit), f"{probability_text(machine.normal_prob)}에서 입력 {spins_per_1000y}회 고정 기준"],
            ["표본회전 당첨", pct(one_k_hit_with_variance), "다이 품질/헤소 입상 표본 변동 반영"],
            ["표본회전 무당첨", pct(one_k_no_hit), "회전 변동까지 반영한 1000엔 무당첨 확률"],
            ["보더 대비", border_label(spins_per_1000y, border_spins), "1엔/1.111엔 혼동 방지"],
        ],
    )

    print_ascii_table(
        "ASCII 독립시행 분모 초과 확률",
        ["기준", "회전수", "무당첨", "1회 이상", "해석"],
        denominator_tail_rows(machine),
    )

    feel_rows = []
    time_rows = []
    stay_rows = []
    for mr in matrix_results:
        budget = mr["budget"]
        m = calculate_metrics(mr["results"], iterations)
        theory_hit = 100.0 - theoretical_no_hit_rate_from_results(machine.normal_prob, mr["results"])
        feel_rows.append(
            [
                yen(budget),
                spin_capacity_text(m),
                f"{theory_hit:.1f}%",
                pct(m["hit_rate"]),
                f"{m['avg_first_hit']}회",
                f"{m['median_first_hit']}/{m['p90_first_hit']}회",
                f"{m['median_first_hit_total_spins']}/{m['p90_first_hit_total_spins']}회",
                f"{m['avg_hits']:.2f}회",
                f"{m['avg_after_first_hits']:.2f}회",
                f"{m['avg_streak']:.2f}연",
                f"{m['avg_right_spins']}회",
                pct(m["rush_rate"]),
                lt_rate_text(machine, m),
                upper_rate_text(machine, m),
                m["profit_condition_summary"],
                yen(m["median_profit"], signed=True),
                yen(m["worst_10_profit"], signed=True),
            ]
        )
        time_rows.append(
            [
                yen(budget),
                minutes_text(m["avg_play_minutes"]),
                f"{minutes_text(m['median_play_minutes'])}/{minutes_text(m['p90_play_minutes'])}",
                minutes_text(m["avg_cashless_play_minutes"]),
                f"{m['avg_cashless_play_share']:.1f}%",
                minutes_text(m["avg_post_budget_play_minutes"]),
                minutes_text(m["avg_normal_play_minutes"]),
                minutes_text(m["avg_right_play_minutes"]),
                minutes_text(m["avg_hit_effect_minutes"]),
                minutes_text(m["avg_reserve_wait_minutes"]),
                cash_burn_text(m),
            ]
        )
        stay_rows.append(
            [
                yen(budget),
                stay_rate_text(m, 1),
                stay_rate_text(m, 2),
                stay_rate_text(m, 3),
                stay_rate_text(m, 4),
                stay_rate_text(m, 6),
                stay_rate_text(m, 8),
                stay_rate_text(m, SESSION_TIME_LIMIT_HOURS),
                remaining_value_text(m),
            ]
        )

    print_ascii_table(
        "ASCII 예산별 아타리/연속 주요 지표",
        ["예산", "가능회전", "이론당첨", "시뮬당첨", "평균초당첨", "초당첨P50/P90", "총체감P50/P90", "평균아타리", "초당첨후", "평균연속", "평균우타치", "RUSH", "LT", "상위RUSH", "실익조건", "중앙", "하위10"],
        feel_rows,
    )
    print_ascii_table(
        "ASCII 예산별 체류 시간",
        ["예산", "평균시간", "P50/P90", "현금없는", "무현금비율", "소진후", "통상", "우타치", "당첨연출", "보류대기", "현금속도"],
        time_rows,
    )
    print_ascii_table(
        "ASCII 예산별 체류 도달률",
        ["예산", "1h+", "2h+", "3h+", "4h+", "6h+", "8h+", f"{SESSION_TIME_LIMIT_HOURS}h+", "최종잔류"],
        stay_rows,
    )

    benchmark_rows = []
    for benchmark in PUBLIC_BENCHMARKS.get(machine.id, []):
        model_value = benchmark_model_value(machine, benchmark)
        public_value = float(benchmark["public"])
        diff = value_diff(model_value, public_value)
        unit = benchmark["unit"]
        diff_text = f"{diff:+.1f}" if unit == "denom" else f"{diff:+.1f}pt"
        benchmark_rows.append(
            [
                bilingual_ja_ko(benchmark["label_ja"], benchmark["label_ko"]),
                format_benchmark_value(public_value, unit),
                format_benchmark_value(model_value, unit),
                diff_text,
                benchmark_judgement(diff, unit),
                benchmark.get("source", "-"),
            ]
        )

    print_ascii_table(
        "ASCII 공개 일본 스펙값 대비 위화감 체크",
        ["지표", "공개/일본값", "모델값", "차이", "판정", "출처"],
        benchmark_rows or [["등록 벤치마크", "-", "-", "-", "없음", "-"]],
    )
    print("판정 기준: OK는 모델값과 공개값 차이가 작다는 뜻이고, 실제 수익 보장을 의미하지 않습니다.")

    print_travel_satisfaction_grade(machine)
    print("="*86)


def print_strategy_matrix_results(store_name: str, machine: Machine, matrix_results: List[Dict[str, Any]], iterations: int):
    print("\n" + "="*80)
    print(f"=== {store_name} / {machine.name_ko} 회전율·전략 비교 ({iterations}회) ===")
    print(f"모델 신뢰도: {machine.confidence} | 추정 여부: {'예' if machine.is_estimated else '아니오'}")
    print(f"기종 일본어: {machine.name_ja}")
    if matrix_results and matrix_results[0].get("installed_full_name_ko"):
        print(f"실설치명(한국어): {installed_name_ko_from_results(matrix_results)}")
    if matrix_results and matrix_results[0].get("installed_full_name_ja"):
        print(f"실설치명(일본어): {installed_name_ja_from_results(matrix_results)}")
    if matrix_results and matrix_results[0].get("placement_summary"):
        print(f"가게별 배치: {matrix_results[0]['placement_summary']}")

    ranked = []
    core_rows = []
    condition_rows = []
    for mr in matrix_results:
        m = calculate_metrics(mr["results"], iterations)
        border_spins = mr.get("border_spins_per_1000yen")
        score = relative_score(m, mr["budget"], machine.confidence, mr["spins_per_1000y"], border_spins)
        ranked.append((score, mr, m))
        strategy_label = mr.get("strategy_label", mr["strategy"])
        rotation_display = rotation_display_text(mr)
        warning = operating_warning(machine.confidence, mr["spins_per_1000y"], border_spins)
        core_rows.append([
            strategy_label,
            rotation_display,
            f"{score:.2f}",
            pct(m["positive_close_rate"]),
            minutes_text(m["avg_play_minutes"]),
            yen(m["avg_profit"], signed=True),
            yen(m["median_profit"], signed=True),
            yen(m["worst_10_profit"], signed=True),
            pct(m["ruin_rate"]),
            pct(m["rush_rate"]),
            lt_rate_text(machine, m),
            upper_rate_text(machine, m),
        ])
        condition_rows.append([
            strategy_label,
            rotation_display,
            border_delta(mr["spins_per_1000y"], border_spins),
            rotation_condition_text(mr["spins_per_1000y"], border_spins),
            warning or "-",
            f"{m['max_hits']}회/{m['max_streak_seen']}연",
            pct(m["recovery_50_rate"]),
            pct(m["recovery_80_rate"]),
            pct(m["recovery_100_rate"]),
            m["profit_condition_summary"],
            pct(m["profit_lock_trigger_rate"]),
            pct(m["stop_loss_trigger_rate"]),
        ])

    print_ascii_table(
        "ASCII 전략 핵심 비교",
        ["전략", "회전", "점수", "플러스", "평균시간", "평균", "중앙", "하위10", "0회", "RUSH", "LT", "상위RUSH"],
        core_rows,
    )
    print_ascii_table(
        "ASCII 전략 조건/발동",
        ["전략", "회전", "보더+/-", "판정/보더비", "주의", "최대당/연", "회수50", "회수80", "회수100", "실익조건", "익절", "손절"],
        condition_rows,
    )

    top_rows = []
    for rank, (score, mr, m) in enumerate(sorted(ranked, key=lambda row: row[0], reverse=True)[:5], 1):
        warning = operating_warning(machine.confidence, mr["spins_per_1000y"], mr.get("border_spins_per_1000yen"))
        strategy_label = mr.get("strategy_label", mr["strategy"])
        top_rows.append([
            rank,
            strategy_label,
            rotation_display_text(mr),
            f"{score:.2f}",
            pct(m["positive_close_rate"]),
            yen(m["avg_profit"], signed=True),
            yen(m["worst_10_profit"], signed=True),
            border_delta(mr["spins_per_1000y"], mr.get("border_spins_per_1000yen")),
            warning or "-",
        ])
    print_ascii_table(
        "ASCII 조건 비교 상위 5개",
        ["순위", "전략", "회전", "점수", "플러스", "평균", "하위10", "보더+/-", "주의"],
        top_rows,
    )

    print_travel_satisfaction_grade(machine)
    print("="*80)


def print_store_comparison_results(
    machine: Machine,
    comparison_results: List[Dict[str, Any]],
    iterations: int,
):
    print("\n" + "="*86)
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
        ["가게", "플러스", "평균시간", f"{SESSION_TIME_LIMIT_HOURS}h+", "잔류액", "평균", "중앙", "하위10", "상위10", "회수80", "평균초당첨", "평균아타리/연", "실익조건", "주의"],
        view["money_rows"],
    )

    print("주의: 가게 비교는 같은 기종과 입력 조건의 런타임 통계입니다. 실제 台番号(기기 번호)별 이력, 현장 못 상태, 시간 제약은 별도 확인 대상입니다.")
    print_travel_satisfaction_grade(machine)
    print("="*86)


def save_matrix_to_csv(machine: Machine, matrix_results: List[Dict[str, Any]], iterations: int, filepath="results.csv"):
    write_matrix_to_csv(machine, matrix_results, iterations, calculate_metrics, filepath)
    print(f"\n[안내] 최신 매트릭스 분석 결과가 {filepath} 에 저장되었습니다. 기존 파일은 덮어썼습니다.")
