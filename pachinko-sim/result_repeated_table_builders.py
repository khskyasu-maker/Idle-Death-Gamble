from typing import Any, Dict, List

from machines import Machine
from result_formatting import minutes_text, pct, yen
from result_output_helpers import (
    cash_burn_text,
    ci_pct,
    lt_ci_text,
    lt_count_text,
    lt_rate_text,
    observed_spin_rate_text,
    remaining_value_text,
    spin_capacity_text,
    stay_rate_text,
    true_spin_rate_text,
    upper_count_text,
    upper_rate_text,
)
from session_limits import SESSION_TIME_LIMIT_HOURS


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


__all__ = ["multiple_risk_detail_rows", "multiple_summary_rows"]
