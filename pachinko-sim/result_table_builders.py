from typing import Any, Dict, List

from machines import Machine
from model_checks import theoretical_hit_rate
from result_formatting import build_ascii_bar, minutes_text, pct, yen
from result_metrics import calculate_metrics
from result_output_helpers import (
    benchmark_judgement,
    benchmark_model_value,
    bilingual_ja_ko,
    border_delta,
    border_label,
    cash_burn_text,
    ci_pct,
    format_benchmark_value,
    lt_ci_text,
    lt_count_text,
    lt_rate_text,
    operating_warning,
    probability_text,
    relative_score,
    remaining_value_text,
    rotation_condition_text,
    rotation_display_text,
    spin_capacity_text,
    stay_rate_text,
    theoretical_no_hit_rate_from_results,
    true_spin_rate_text,
    observed_spin_rate_text,
    upper_count_text,
    upper_rate_text,
    value_diff,
)
from session_limits import (
    HARD_SESSION_TIME_LIMIT_HOURS,
    HARD_SESSION_TIME_LIMIT_MINUTES,
    SESSION_TIME_LIMIT_HOURS,
    SESSION_TIME_LIMIT_MINUTES,
)
from sim_terms import state_transition_label
from spec_benchmarks import PUBLIC_BENCHMARKS


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


def multiple_summary_rows(machine: Machine, metrics: Dict[str, Any], theory_no_hit: float) -> List[List[Any]]:
    return [
        ["당첨 체험", pct(metrics["hit_rate"]), "최소 1회 당첨"],
        ["RUSH/ST 체험", pct(metrics["rush_rate"]), f"95% CI {ci_pct(metrics, 'rush_rate')}"],
        ["당첨 0회", pct(metrics["ruin_rate"]), f"95% CI {ci_pct(metrics, 'ruin_rate')} / 회전변동 이론 {theory_no_hit:.1f}%"],
        ["다이 품질 분포", true_spin_rate_text(metrics), f"품질 표준편차 {metrics['spin_rate_quality_stddev']:.1f}회"],
        ["헤소 입상 표본", observed_spin_rate_text(metrics), f"입상 {metrics['start_probability'] * 100:.2f}%/발"],
        ["시간 프로파일", metrics["time_profile"], metrics["time_profile_note"]],
        ["평균 체류 시간", minutes_text(metrics["avg_play_minutes"]), f"P50 {minutes_text(metrics['median_play_minutes'])} / P90 {minutes_text(metrics['p90_play_minutes'])}"],
        [f"{SESSION_TIME_LIMIT_HOURS}시간 정리", f"도달 {stay_rate_text(metrics, SESSION_TIME_LIMIT_HOURS)} / RUSH후정리 {pct(metrics['soft_stop_rate'])}", f"하드종료 {pct(metrics['hard_time_limit_stop_rate'])} / 현금마감 {pct(metrics['cash_input_cutoff_rate'])}"],
        ["최종 잔류액", remaining_value_text(metrics), f"P10~P90 {yen(metrics['p10_final_remaining_value'])}~{yen(metrics['p90_final_remaining_value'])} / 예산소진 {pct(metrics['budget_exhausted_rate'])}"],
        ["예산 소진 후", f"지속 {pct(metrics['post_budget_continue_rate'])} / 평균 {minutes_text(metrics['avg_post_budget_play_minutes'])}", f"지속된 경우 평균 {minutes_text(metrics['avg_post_budget_play_minutes_when_continued'])} / 완전소진정지 {pct(metrics['funds_exhausted_stop_rate'])}"],
        ["현금 없는 시간", f"{minutes_text(metrics['avg_cashless_play_minutes'])} ({metrics['avg_cashless_play_share']:.1f}%)", "당첨/우타치/보유구슬 재사용 시간"],
        ["현금 소모 속도", cash_burn_text(metrics), "시간은 발사/보류/연출 근사 포함"],
        ["플러스 마감", pct(metrics["positive_close_rate"]), f"95% CI {ci_pct(metrics, 'positive_close_rate')}"],
        ["실질 플러스 조건", metrics["profit_condition_summary"], "순이익>0 조건부 확률"],
        ["평균 차액", yen(metrics["avg_profit"], signed=True), f"95% CI {yen(metrics['avg_profit_ci_low'], signed=True)}~{yen(metrics['avg_profit_ci_high'], signed=True)}"],
        ["평균 표준오차", yen(metrics["avg_profit_standard_error"]), f"표준편차 {yen(metrics['profit_stddev'])} / 예산대비 {metrics['avg_profit_se_budget_pct']:.2f}% / {metrics['mean_ci_method']} CI"],
        ["중앙값", yen(metrics["median_profit"], signed=True), ""],
        ["중앙값 95% CI", f"{yen(metrics['median_profit_ci_low'], signed=True)}~{yen(metrics['median_profit_ci_high'], signed=True)}", "순위 기반 분위수 CI"],
        ["하위10% / 상위10%", f"{yen(metrics['worst_10_profit'], signed=True)} / {yen(metrics['top_10_profit'], signed=True)}", ""],
        ["CVaR10 / 상위10평균", f"{yen(metrics['cvar_10_profit'], signed=True)} / {yen(metrics['upper_tail_10_profit'], signed=True)}", "꼬리 평균"],
        ["회수 50/80/100", f"{pct(metrics['recovery_50_rate'])} / {pct(metrics['recovery_80_rate'])} / {pct(metrics['recovery_100_rate'])}", ""],
        ["LT 진입", lt_rate_text(machine, metrics), lt_ci_text(machine, metrics)],
        ["상위RUSH 진입", upper_rate_text(machine, metrics), "LT와 별도 집계"],
        ["최대 大当り(대당첨) / 연속", f"{metrics['max_hits']}회 / {metrics['max_streak_seen']}연", f"상위10% {metrics['p90_hits']}회 / {metrics['p90_streak']}연"],
    ]


def multiple_risk_detail_rows(machine: Machine, metrics: Dict[str, Any]) -> List[List[Any]]:
    return [
        ["단발 종료", pct(metrics["single_hit_finish_rate"]), "1번 맞고 종료"],
        ["500발 이하 종료", pct(metrics["under_500_finish_rate"]), "소액 출옥 후 종료"],
        ["회수 50%", pct(metrics["recovery_50_rate"]), "투자금 절반 이상"],
        ["회수 80%", pct(metrics["recovery_80_rate"]), "투자금 80% 이상"],
        ["회수 100%", pct(metrics["recovery_100_rate"]), "투자금 이상"],
        ["최대 손실 / 이익", f"{yen(metrics['min_profit'], signed=True)} / {yen(metrics['max_profit'], signed=True)}", ""],
        ["최대 RUSH / LT", f"{metrics['max_rush_entries']}회 / {lt_count_text(machine, metrics['max_lt_entries'])}", f"최대 우타치 {metrics['max_right_spins']}회"],
        ["최대 상위RUSH", upper_count_text(machine, metrics["max_upper_entries"]), "비LT 상위 상태"],
        ["평균 현금 / 회수", f"{yen(metrics['avg_cash_spent'])} / {yen(metrics['avg_final_money'])}", ""],
        ["시간 구성", f"통상 {minutes_text(metrics['avg_normal_play_minutes'])} / 우타치 {minutes_text(metrics['avg_right_play_minutes'])}", f"당첨연출 {minutes_text(metrics['avg_hit_effect_minutes'])} / 보류대기 {minutes_text(metrics['avg_reserve_wait_minutes'])}"],
        ["가능 회전", spin_capacity_text(metrics), "구슬->헤소 입상 변동"],
        ["초당첨 위치", f"평균 {metrics['avg_first_hit']}회 / 중앙 {metrics['median_first_hit']}회", f"맞은 세션 기준 P90 {metrics['p90_first_hit']}회"],
        ["초당첨 총체감", f"평균 {metrics['avg_first_hit_total_spins']}회 / 중앙 {metrics['median_first_hit_total_spins']}회", f"통상+時短(시단)/우타치 포함 P90 {metrics['p90_first_hit_total_spins']}회"],
        ["초당첨 후 당첨", f"{metrics['avg_after_first_hits']:.2f}회", f"맞은 세션 평균 大当り(대당첨) {metrics['avg_hits_when_hit']:.2f}회"],
        ["평균 회전 / 당첨", f"{metrics['avg_spins']}회전 / {metrics['avg_hits']:.2f}회", f"RUSH {metrics['avg_rush_entries']:.2f}회 / LT {lt_count_text(machine, metrics['avg_lt_entries'])}"],
        ["평균 상위RUSH", upper_count_text(machine, metrics["avg_upper_entries"]), ""],
        ["익절 / 손절", f"{pct(metrics['profit_lock_trigger_rate'])} / {pct(metrics['stop_loss_trigger_rate'])}", ""],
    ]


def matrix_result_rows(machine: Machine, matrix_results: List[Dict[str, Any]], iterations: int) -> Dict[str, List[List[Any]]]:
    summary_rows = []
    risk_rows = []
    for mr in matrix_results:
        spins = mr["spins_per_1000y"]
        rotation_display = rotation_display_text(mr)
        metrics = calculate_metrics(mr["results"], iterations)
        border_spins = mr.get("border_spins_per_1000yen")
        warning = operating_warning(machine.confidence, spins, border_spins)
        theory_no_hit = theoretical_no_hit_rate_from_results(machine.normal_prob, mr["results"])
        summary_rows.append([
            rotation_display,
            spin_capacity_text(metrics),
            minutes_text(metrics["avg_play_minutes"]),
            border_delta(spins, border_spins),
            rotation_condition_text(spins, border_spins),
            pct(metrics["positive_close_rate"]),
            yen(metrics["avg_profit"], signed=True),
            yen(metrics["median_profit"], signed=True),
            yen(metrics["worst_10_profit"], signed=True),
            yen(metrics["top_10_profit"], signed=True),
            metrics["profit_condition_summary"],
            warning or "-",
        ])
        risk_rows.append([
            rotation_display,
            pct(metrics["hit_rate"]),
            pct(metrics["ruin_rate"]),
            f"{theory_no_hit:.1f}%",
            pct(metrics["rush_rate"]),
            lt_rate_text(machine, metrics),
            upper_rate_text(machine, metrics),
            f"{pct(metrics['recovery_50_rate'])}/{pct(metrics['recovery_80_rate'])}/{pct(metrics['recovery_100_rate'])}",
            f"{metrics['max_hits']}회/{metrics['max_streak_seen']}연",
            f"{metrics['p90_hits']}회/{metrics['p90_streak']}연",
        ])
    return {"summary": summary_rows, "risk": risk_rows}


def budget_result_tables(machine: Machine, matrix_results: List[Dict[str, Any]], iterations: int) -> Dict[str, List[List[Any]]]:
    tables = {
        "money": [],
        "risk": [],
        "time": [],
        "stay": [],
        "remaining": [],
        "stats": [],
    }
    for mr in matrix_results:
        budget = mr["budget"]
        spins = mr["spins_per_1000y"]
        border_spins = mr.get("border_spins_per_1000yen")
        metrics = calculate_metrics(mr["results"], iterations)
        theory_no_hit = theoretical_no_hit_rate_from_results(machine.normal_prob, mr["results"])
        tables["money"].append([
            yen(budget),
            spin_capacity_text(metrics),
            metrics["avg_spins"],
            rotation_condition_text(spins, border_spins),
            pct(metrics["positive_close_rate"]),
            yen(metrics["avg_profit"], signed=True),
            yen(metrics["median_profit"], signed=True),
            yen(metrics["worst_10_profit"], signed=True),
            yen(metrics["top_10_profit"], signed=True),
            metrics["profit_condition_summary"],
            yen(metrics["avg_cash_spent"]),
        ])
        tables["risk"].append([
            yen(budget),
            pct(metrics["hit_rate"]),
            pct(metrics["ruin_rate"]),
            f"{theory_no_hit:.1f}%",
            pct(metrics["rush_rate"]),
            lt_rate_text(machine, metrics),
            upper_rate_text(machine, metrics),
            f"{pct(metrics['recovery_50_rate'])}/{pct(metrics['recovery_80_rate'])}/{pct(metrics['recovery_100_rate'])}",
            f"{metrics['max_hits']}회/{metrics['max_streak_seen']}연",
        ])
        tables["time"].append([
            yen(budget),
            minutes_text(metrics["avg_play_minutes"]),
            f"{minutes_text(metrics['median_play_minutes'])}/{minutes_text(metrics['p90_play_minutes'])}",
            minutes_text(metrics["avg_cashless_play_minutes"]),
            f"{metrics['avg_cashless_play_share']:.1f}%",
            minutes_text(metrics["avg_post_budget_play_minutes"]),
            minutes_text(metrics["avg_normal_play_minutes"]),
            minutes_text(metrics["avg_right_play_minutes"]),
            minutes_text(metrics["avg_hit_effect_minutes"]),
            minutes_text(metrics["avg_reserve_wait_minutes"]),
            cash_burn_text(metrics),
        ])
        tables["stay"].append([
            yen(budget),
            stay_rate_text(metrics, 1),
            stay_rate_text(metrics, 2),
            stay_rate_text(metrics, 3),
            stay_rate_text(metrics, 4),
            stay_rate_text(metrics, 6),
            stay_rate_text(metrics, 8),
            stay_rate_text(metrics, SESSION_TIME_LIMIT_HOURS),
            pct(metrics["time_limit_stop_rate"]),
            pct(metrics["hard_time_limit_stop_rate"]),
            pct(metrics["cash_input_cutoff_rate"]),
        ])
        tables["remaining"].append([
            yen(budget),
            pct(metrics["budget_exhausted_rate"]),
            yen(metrics["avg_unused_cash"]),
            yen(metrics["avg_final_money"]),
            yen(metrics["avg_final_remaining_value"]),
            f"{yen(metrics['p10_final_remaining_value'])}/{yen(metrics['median_final_remaining_value'])}/{yen(metrics['p90_final_remaining_value'])}",
            yen(metrics["avg_final_remaining_balance"], signed=True),
            pct(metrics["funds_exhausted_stop_rate"]),
        ])
        tables["stats"].append([
            yen(budget),
            yen(metrics["avg_profit_standard_error"]),
            f"{yen(metrics['avg_profit_ci_low'], signed=True)}~{yen(metrics['avg_profit_ci_high'], signed=True)}",
            f"{yen(metrics['median_profit_ci_low'], signed=True)}~{yen(metrics['median_profit_ci_high'], signed=True)}",
            f"{yen(metrics['worst_10_profit_ci_low'], signed=True)}~{yen(metrics['worst_10_profit_ci_high'], signed=True)}",
            yen(metrics["cvar_10_profit"], signed=True),
            f"{yen(metrics['top_10_profit_ci_low'], signed=True)}~{yen(metrics['top_10_profit_ci_high'], signed=True)}",
        ])
    return tables


def model_profile_intro_rows(
    machine: Machine,
    first_row: Dict[str, Any],
    first_metrics: Dict[str, Any],
) -> List[List[Any]]:
    first_result = first_row["results"][0] if first_row.get("results") else {}
    time_assumptions = first_result.get("time_assumptions", {})
    lend_rate = first_result.get("lend_rate", 1.0)
    rented_balls = int(1000 / lend_rate) if lend_rate else 0
    base_return_rate = max(
        0.0,
        min(0.90, float(time_assumptions.get("normal_base_return_rate", 0.0) or 0.0)),
    )
    gross_balls_per_1000y = rented_balls / max(0.10, 1.0 - base_return_rate) if lend_rate else 0.0
    spins_per_1000y = first_row["spins_per_1000y"]
    border_spins = first_row.get("border_spins_per_1000yen")
    one_k_hit = theoretical_hit_rate(machine.normal_prob, spins_per_1000y)
    one_k_no_hit = theoretical_no_hit_rate_from_results(machine.normal_prob, first_row["results"])
    one_k_hit_with_variance = 100.0 - one_k_no_hit
    return [
        ["대여 구슬", f"{rented_balls:,}발", f"{lend_rate:.3f}엔/발 기준"],
        ["ベース(반환)", f"{base_return_rate * 100:.0f}%", "통상시 반환구슬을 감안한 체류시간 보정값"],
        ["총 발사 추정", f"{gross_balls_per_1000y:.0f}발", "표시 회전수의 순소모 구슬을 실제 발사구슬로 환산"],
        ["입력 회전수", f"{spins_per_1000y}회/1000엔", "현장 1000엔 테스트 입력값"],
        ["헤소 입상", f"{first_metrics['start_probability'] * 100:.2f}%/발", "구슬 1발이 헤소에 들어가 회전이 생기는 확률"],
        ["다이 품질", true_spin_rate_text(first_metrics), "釘(못)/風車(풍차)/ステージ(스테이지) 등을 회전율 분포로 근사"],
        ["입상 표본", observed_spin_rate_text(first_metrics), "같은 다이라도 1000엔마다 고정 회전이 아니라 표본 변동"],
        ["입력회전 당첨", pct(one_k_hit), f"{probability_text(machine.normal_prob)}에서 입력 {spins_per_1000y}회 고정 기준"],
        ["표본회전 당첨", pct(one_k_hit_with_variance), "다이 품질/헤소 입상 표본 변동 반영"],
        ["표본회전 무당첨", pct(one_k_no_hit), "회전 변동까지 반영한 1000엔 무당첨 확률"],
        ["보더 대비", border_label(spins_per_1000y, border_spins), "1엔/1.111엔 혼동 방지"],
    ]


def model_profile_result_tables(machine: Machine, matrix_results: List[Dict[str, Any]], iterations: int) -> Dict[str, List[List[Any]]]:
    tables = {"feel": [], "time": [], "stay": []}
    for mr in matrix_results:
        budget = mr["budget"]
        metrics = calculate_metrics(mr["results"], iterations)
        theory_hit = 100.0 - theoretical_no_hit_rate_from_results(machine.normal_prob, mr["results"])
        tables["feel"].append(
            [
                yen(budget),
                spin_capacity_text(metrics),
                f"{theory_hit:.1f}%",
                pct(metrics["hit_rate"]),
                f"{metrics['avg_first_hit']}회",
                f"{metrics['median_first_hit']}/{metrics['p90_first_hit']}회",
                f"{metrics['median_first_hit_total_spins']}/{metrics['p90_first_hit_total_spins']}회",
                f"{metrics['avg_hits']:.2f}회",
                f"{metrics['avg_after_first_hits']:.2f}회",
                f"{metrics['avg_streak']:.2f}연",
                f"{metrics['avg_right_spins']}회",
                pct(metrics["rush_rate"]),
                lt_rate_text(machine, metrics),
                upper_rate_text(machine, metrics),
                metrics["profit_condition_summary"],
                yen(metrics["median_profit"], signed=True),
                yen(metrics["worst_10_profit"], signed=True),
            ]
        )
        tables["time"].append(
            [
                yen(budget),
                minutes_text(metrics["avg_play_minutes"]),
                f"{minutes_text(metrics['median_play_minutes'])}/{minutes_text(metrics['p90_play_minutes'])}",
                minutes_text(metrics["avg_cashless_play_minutes"]),
                f"{metrics['avg_cashless_play_share']:.1f}%",
                minutes_text(metrics["avg_post_budget_play_minutes"]),
                minutes_text(metrics["avg_normal_play_minutes"]),
                minutes_text(metrics["avg_right_play_minutes"]),
                minutes_text(metrics["avg_hit_effect_minutes"]),
                minutes_text(metrics["avg_reserve_wait_minutes"]),
                cash_burn_text(metrics),
            ]
        )
        tables["stay"].append(
            [
                yen(budget),
                stay_rate_text(metrics, 1),
                stay_rate_text(metrics, 2),
                stay_rate_text(metrics, 3),
                stay_rate_text(metrics, 4),
                stay_rate_text(metrics, 6),
                stay_rate_text(metrics, 8),
                stay_rate_text(metrics, SESSION_TIME_LIMIT_HOURS),
                remaining_value_text(metrics),
            ]
        )
    return tables


def benchmark_rows(machine: Machine) -> List[List[Any]]:
    rows = []
    for benchmark in PUBLIC_BENCHMARKS.get(machine.id, []):
        model_value = benchmark_model_value(machine, benchmark)
        public_value = float(benchmark["public"])
        diff = value_diff(model_value, public_value)
        unit = benchmark["unit"]
        diff_text = f"{diff:+.1f}" if unit == "denom" else f"{diff:+.1f}pt"
        rows.append(
            [
                bilingual_ja_ko(benchmark["label_ja"], benchmark["label_ko"]),
                format_benchmark_value(public_value, unit),
                format_benchmark_value(model_value, unit),
                diff_text,
                benchmark_judgement(diff, unit),
                benchmark.get("source", "-"),
            ]
        )
    return rows


def strategy_result_tables(machine: Machine, matrix_results: List[Dict[str, Any]], iterations: int) -> Dict[str, List[List[Any]]]:
    ranked = []
    core_rows = []
    condition_rows = []
    for mr in matrix_results:
        metrics = calculate_metrics(mr["results"], iterations)
        border_spins = mr.get("border_spins_per_1000yen")
        score = relative_score(metrics, mr["budget"], machine.confidence, mr["spins_per_1000y"], border_spins)
        ranked.append((score, mr, metrics))
        strategy_label = mr.get("strategy_label", mr["strategy"])
        rotation_display = rotation_display_text(mr)
        warning = operating_warning(machine.confidence, mr["spins_per_1000y"], border_spins)
        core_rows.append([
            strategy_label,
            rotation_display,
            f"{score:.2f}",
            pct(metrics["positive_close_rate"]),
            minutes_text(metrics["avg_play_minutes"]),
            yen(metrics["avg_profit"], signed=True),
            yen(metrics["median_profit"], signed=True),
            yen(metrics["worst_10_profit"], signed=True),
            pct(metrics["ruin_rate"]),
            pct(metrics["rush_rate"]),
            lt_rate_text(machine, metrics),
            upper_rate_text(machine, metrics),
        ])
        condition_rows.append([
            strategy_label,
            rotation_display,
            border_delta(mr["spins_per_1000y"], border_spins),
            rotation_condition_text(mr["spins_per_1000y"], border_spins),
            warning or "-",
            f"{metrics['max_hits']}회/{metrics['max_streak_seen']}연",
            pct(metrics["recovery_50_rate"]),
            pct(metrics["recovery_80_rate"]),
            pct(metrics["recovery_100_rate"]),
            metrics["profit_condition_summary"],
            pct(metrics["profit_lock_trigger_rate"]),
            pct(metrics["stop_loss_trigger_rate"]),
        ])

    top_rows = []
    for rank, (score, mr, metrics) in enumerate(sorted(ranked, key=lambda row: row[0], reverse=True)[:5], 1):
        warning = operating_warning(machine.confidence, mr["spins_per_1000y"], mr.get("border_spins_per_1000yen"))
        strategy_label = mr.get("strategy_label", mr["strategy"])
        top_rows.append([
            rank,
            strategy_label,
            rotation_display_text(mr),
            f"{score:.2f}",
            pct(metrics["positive_close_rate"]),
            yen(metrics["avg_profit"], signed=True),
            yen(metrics["worst_10_profit"], signed=True),
            border_delta(mr["spins_per_1000y"], mr.get("border_spins_per_1000yen")),
            warning or "-",
        ])
    return {"core": core_rows, "condition": condition_rows, "top": top_rows}
