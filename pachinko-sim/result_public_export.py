import json
import os
from datetime import datetime
from html import escape
from pathlib import Path
from typing import Any, Callable, Dict, List
from zoneinfo import ZoneInfo

from machine_traits import machine_has_lt, machine_has_upper
from machines import Machine
from result_formatting import minutes_text, pct, spins_text, yen
from session_limits import SESSION_TIME_LIMIT_HOURS


DEFAULT_DOCS_DIR = Path(__file__).resolve().parents[1] / "docs"
PUBLIC_EXPORT_DIR_ENV = "PACHINKO_SIM_PUBLIC_DOCS_DIR"
LATEST_SIM_RESULT_BASENAME = "latest-sim-results"
LEGACY_PUBLIC_SIM_PATTERNS = (
    "sim-results-*.json",
    "sim-results-*.md",
    "sim-results-*.html",
)


MetricsFn = Callable[[List[Dict[str, Any]], int], Dict[str, Any]]


def kst_now_text() -> str:
    return datetime.now(ZoneInfo("Asia/Seoul")).strftime("%Y-%m-%d %H:%M:%S KST")


def public_docs_dir_from_env(default_docs_dir: Path = DEFAULT_DOCS_DIR) -> Path:
    env_value = os.environ.get(PUBLIC_EXPORT_DIR_ENV)
    if not env_value:
        return default_docs_dir
    return Path(env_value)


def clean_legacy_public_sim_results(docs_dir: Path) -> None:
    for pattern in LEGACY_PUBLIC_SIM_PATTERNS:
        for path in docs_dir.glob(pattern):
            if path.is_file():
                path.unlink()


def simulation_method_summary() -> Dict[str, Any]:
    return {
        "summary": "공개 기종 스펙을 상태 전이 모델로 옮긴 뒤, 공개된 예산/회전수/교환율/중단 규칙 조건에서 Monte Carlo로 반복 집계합니다.",
        "model_structure": [
            "기종 스펙은 Machine/Payout 데이터로 보관하고 통상, RUSH/ST, LT, 루프, 転落(전락) 상태를 분리합니다",
            "에바와 大海物語(대해물어)처럼 흐름이 비슷한 계열은 공통 템플릿을 재사용하고 확률/출옥/전이값만 기종별로 교체합니다",
            "짧은 챌린지나 時短(시단)은 실제 RUSH 진입 지표와 섞이지 않도록 Payout.counts_as_rush로 분리합니다",
        ],
        "stochastic_model": [
            "통상 회전은 구슬이 ヘソ(헤소)에 들어가는 표본 과정을 거친 뒤, 각 회전을 독립 大当り(대당첨) 시행으로 처리합니다",
            "RUSH/ST/LT는 단일 베르누이 지름길이 아니라 통상→우타치→종료/상위 상태의 전이로 시뮬레이션합니다",
            "지원되는 기종은 우타치 계속, 転落(전락) 선착순, 残保留(잔보류) 복귀 경로를 기종 계열별로 반영합니다",
        ],
        "ball_and_time_model": [
            "보유구슬은 새 현금 투입 전에 재사용하므로, 당첨으로 얻은 구슬은 추가 현금 없이 체류 시간을 늘릴 수 있습니다",
            "통상 플레이는 순소모 구슬과 총발사 구슬을 분리하고 계열별 ベース(반환) 가정을 사용합니다",
            "시간 추정은 발사 속도, 변동 표시 시간, 우타치 시간, 출옥/연출 시간, 보류 대기 효과를 합산합니다",
            "표준 공개 실행은 9시간 소프트 스톱과 11시간 하드 캡을 사용합니다",
        ],
        "inputs": [
            "공개 스펙의 확률과 출옥 분포",
            "저대여 설치 맥락과 1000円당 회전수로 환산한 보더",
            "실행 시점의 예산, 교환율, 회전수 가정, 전략, 세션 정책",
        ],
        "statistics": [
            "공개 표는 평균, 중앙값, 꼬리 손실, 체류 시간, 당첨, RUSH, 플러스 마감, 연속 지표를 보여줍니다",
            "플러스 마감률은 Wilson 방식 95% 신뢰구간을 함께 표시합니다",
            "평균 손익은 표준오차를 함께 공개해 불안정한 행과 안정적인 행을 구분할 수 있게 합니다",
            "하방/꼬리 리스크 요약은 P10/P25 체류, CVaR10, 평균-중앙 손익 차이, LT 진입률을 함께 봅니다",
            "초반 소진 진단용으로 1~3시간 도달률, 첫 당첨 전 완전소진률, 첫 당첨까지 평균/중앙 현금 사용액을 함께 공개합니다",
            "회전율 민감도는 원시 표본을 저장하지 않고 기종별 요약 범위만 공개합니다",
            "JSON에는 행별 simulation_seed를 저장해 같은 조건을 재현할 수 있게 합니다",
        ],
        "pre_sim_vs_actual_reading": [
            "시뮬 전 정성 유추는 라이트 기종은 체류가 길고 LT/e기 계열은 꼬리가 넓다는 식의 가설로만 사용합니다",
            "실제 판단은 Monte Carlo 표에서 중앙 체류 시간, 플러스율 신뢰구간, 손익 표준오차가 함께 움직이는지로 확인합니다",
            "최대연과 상위 꼬리값은 스트레스 지표로만 보며, 당첨률/중앙 체류/표준오차보다 수렴이 느립니다",
        ],
        "limits": [
            "집계 추정치일 뿐 당첨 예측이나 방문 지시가 아닙니다",
            "원시 표본 세션, 개인 여행 데이터, 실제 지출/손익 기록은 공개하지 않습니다",
            "점포 표기는 설치/레이트 대표 맥락이며 점포 순위가 아닙니다",
            "현장 회전율, 대기, 착석 가능성, 점포 규칙 차이는 모델 가정보다 더 크게 작용할 수 있습니다",
        ],
    }


def method_items(method: Dict[str, Any], key: str) -> List[str]:
    items = method.get(key, [])
    if isinstance(items, list):
        return [str(item) for item in items]
    if items:
        return [str(items)]
    return []


def build_public_method_markdown(method: Dict[str, Any]) -> str:
    if not method:
        return ""

    section_labels = [
        ("model_structure", "모델 구성"),
        ("stochastic_model", "확률 처리"),
        ("ball_and_time_model", "구슬/시간 처리"),
        ("statistics", "통계 지표"),
        ("pre_sim_vs_actual_reading", "사전 유추와 실제 결과 비교 기준"),
        ("limits", "한계"),
    ]

    md = "## 시뮬 설계와 구성\n\n"
    md += f"- 요약: {method.get('summary', '')}\n"
    for key, label in section_labels:
        items = method_items(method, key)
        if not items:
            continue
        md += f"- {label}: " + "; ".join(items) + "\n"
    md += "\n"
    return md


def build_public_method_html(method: Dict[str, Any]) -> str:
    if not method:
        return ""

    section_labels = [
        ("model_structure", "모델 구성"),
        ("stochastic_model", "확률 처리"),
        ("ball_and_time_model", "구슬/시간 처리"),
        ("statistics", "통계 지표"),
        ("pre_sim_vs_actual_reading", "사전 유추와 실제 결과 비교 기준"),
        ("limits", "한계"),
    ]
    html = [
        '<section class="note">',
        "<h2>시뮬 설계와 구성</h2>",
        f"<p>{escape(str(method.get('summary', '')))}</p>",
    ]
    for key, label in section_labels:
        items = method_items(method, key)
        if not items:
            continue
        html.append(f"<h3>{escape(label)}</h3>")
        html.append("<ul>")
        html.extend(f"<li>{escape(item)}</li>" for item in items)
        html.append("</ul>")
    html.append("</section>")
    return "\n".join(html)


def build_rotation_sensitivity_markdown(analysis: Dict[str, Any]) -> str:
    sensitivity = analysis.get("rotation_sensitivity") if analysis else None
    if not sensitivity:
        return ""

    rows = sensitivity.get("rows", [])
    if not rows:
        return ""

    md = "## 회전율 민감도 요약\n\n"
    md += f"- 예산: {yen(sensitivity.get('budget_yen', 0))}\n"
    md += f"- 반복: {sensitivity.get('iterations', 0)}회\n"
    md += "- 목적: 실제 현장 결과가 아니라 여행 전 입력 회전수 오차가 체류/손익 지표를 얼마나 흔드는지 보는 사전 분석입니다.\n"
    md += "- 해석: 민감도가 높을수록 현장 첫 1,000円 회전수 확인이 더 중요합니다. 점포 순위나 방문 지시가 아닙니다.\n\n"

    headers = [
        "분류",
        "기종",
        "점포",
        "회전범위",
        "P50시간범위",
        "플러스범위",
        "완전소진범위",
        "중앙손익범위",
        "민감도",
    ]
    md += "|" + "|".join(headers) + "|\n"
    md += "|" + "|".join("---" for _ in headers) + "|\n"
    for row in rows:
        values = [
            row.get("category", ""),
            row.get("machine", ""),
            row.get("store", ""),
            row.get("rotation_range_text", ""),
            row.get("median_time_range_text", ""),
            row.get("plus_range_text", ""),
            row.get("funds_exhausted_range_text", ""),
            row.get("median_profit_range_text", ""),
            row.get("sensitivity_label", ""),
        ]
        md += "|" + "|".join(str(value).replace("|", "/") for value in values) + "|\n"
    md += "\n"
    return md


def build_rotation_sensitivity_html(analysis: Dict[str, Any]) -> str:
    sensitivity = analysis.get("rotation_sensitivity") if analysis else None
    if not sensitivity:
        return ""

    rows = sensitivity.get("rows", [])
    if not rows:
        return ""

    headers = [
        "분류",
        "기종",
        "점포",
        "회전범위",
        "P50시간범위",
        "플러스범위",
        "완전소진범위",
        "중앙손익범위",
        "민감도",
    ]
    head_cells = "".join(f"<th>{escape(header)}</th>" for header in headers)
    body_rows = []
    for row in rows:
        values = [
            row.get("category", ""),
            row.get("machine", ""),
            row.get("store", ""),
            row.get("rotation_range_text", ""),
            row.get("median_time_range_text", ""),
            row.get("plus_range_text", ""),
            row.get("funds_exhausted_range_text", ""),
            row.get("median_profit_range_text", ""),
            row.get("sensitivity_label", ""),
        ]
        body_rows.append("<tr>" + "".join(f"<td>{escape(str(value))}</td>" for value in values) + "</tr>")

    return f"""
  <section class="note">
    <h2>회전율 민감도 요약</h2>
    <p><strong>예산:</strong> {escape(yen(sensitivity.get('budget_yen', 0)))} / <strong>반복:</strong> {escape(str(sensitivity.get('iterations', 0)))}회</p>
    <p>실제 현장 결과가 아니라 여행 전 입력 회전수 오차가 체류/손익 지표를 얼마나 흔드는지 보는 사전 분석입니다. 민감도가 높을수록 현장 첫 1,000円 회전수 확인이 더 중요합니다.</p>
    <table>
      <thead><tr>{head_cells}</tr></thead>
      <tbody>{''.join(body_rows)}</tbody>
    </table>
  </section>
"""


def build_tail_risk_review_markdown(analysis: Dict[str, Any]) -> str:
    review = analysis.get("tail_risk_review") if analysis else None
    if not review:
        return ""

    rows = review.get("rows", [])
    if not rows:
        return ""

    md = "## 하방/꼬리 리스크 요약\n\n"
    md += f"- 예산: {yen(review.get('budget_yen', 0))}\n"
    md += f"- 반복: {review.get('iterations', 0)}회\n"
    md += "- 목적: LT/e기처럼 평균과 상위 꼬리가 좋은 기종의 고평가를 줄이기 위한 사전 통계 검토입니다.\n"
    md += "- 해석: P10/P25 시간이 짧거나 CVaR10이 깊고 평균-중앙 손익 차이가 크면 일부 대박 표본이 평균을 끌어올린 구조일 수 있습니다.\n\n"

    headers = [
        "분류",
        "기종",
        "점포",
        "P10시간",
        "P25시간",
        "완전소진",
        "중앙손익",
        "CVaR10",
        "평균-중앙",
        "LT진입",
        "리스크",
    ]
    md += "|" + "|".join(headers) + "|\n"
    md += "|" + "|".join("---" for _ in headers) + "|\n"
    for row in rows:
        values = [
            row.get("category", ""),
            row.get("machine", ""),
            row.get("store", ""),
            row.get("p10_play_text", ""),
            row.get("p25_play_text", ""),
            row.get("funds_exhausted_text", ""),
            row.get("median_profit_text", ""),
            row.get("cvar10_text", ""),
            row.get("mean_median_gap_text", ""),
            row.get("lt_entry_text", ""),
            row.get("risk_label", ""),
        ]
        md += "|" + "|".join(str(value).replace("|", "/") for value in values) + "|\n"
    md += "\n"
    return md


def build_tail_risk_review_html(analysis: Dict[str, Any]) -> str:
    review = analysis.get("tail_risk_review") if analysis else None
    if not review:
        return ""

    rows = review.get("rows", [])
    if not rows:
        return ""

    headers = [
        "분류",
        "기종",
        "점포",
        "P10시간",
        "P25시간",
        "완전소진",
        "중앙손익",
        "CVaR10",
        "평균-중앙",
        "LT진입",
        "리스크",
    ]
    head_cells = "".join(f"<th>{escape(header)}</th>" for header in headers)
    body_rows = []
    for row in rows:
        values = [
            row.get("category", ""),
            row.get("machine", ""),
            row.get("store", ""),
            row.get("p10_play_text", ""),
            row.get("p25_play_text", ""),
            row.get("funds_exhausted_text", ""),
            row.get("median_profit_text", ""),
            row.get("cvar10_text", ""),
            row.get("mean_median_gap_text", ""),
            row.get("lt_entry_text", ""),
            row.get("risk_label", ""),
        ]
        body_rows.append("<tr>" + "".join(f"<td>{escape(str(value))}</td>" for value in values) + "</tr>")

    return f"""
  <section class="note">
    <h2>하방/꼬리 리스크 요약</h2>
    <p><strong>예산:</strong> {escape(yen(review.get('budget_yen', 0)))} / <strong>반복:</strong> {escape(str(review.get('iterations', 0)))}회</p>
    <p>LT/e기처럼 평균과 상위 꼬리가 좋은 기종의 고평가를 줄이기 위한 사전 통계 검토입니다. P10/P25 시간이 짧거나 CVaR10이 깊고 평균-중앙 손익 차이가 크면 일부 대박 표본이 평균을 끌어올린 구조일 수 있습니다.</p>
    <table>
      <thead><tr>{head_cells}</tr></thead>
      <tbody>{''.join(body_rows)}</tbody>
    </table>
  </section>
"""


def public_case_label(row: Dict[str, Any]) -> str:
    if row.get("case_label"):
        return str(row["case_label"])

    labels = []
    if row.get("store_short_label"):
        labels.append(str(row["store_short_label"]))
    if row.get("rotation_label"):
        labels.append(str(row["rotation_label"]))
    elif row.get("reference_rotation_label"):
        labels.append(str(row["reference_rotation_label"]))
    elif row.get("comparison_mode_label"):
        labels.append(str(row["comparison_mode_label"]))
    strategy = row.get("strategy_label") or row.get("strategy")
    if strategy:
        labels.append(str(strategy))
    if not labels:
        labels.append(f"{spins_text(row.get('spins_per_1000y'))}/1000엔")
    return " / ".join(labels)


def public_result_rows(
    machine: Machine,
    result_rows: List[Dict[str, Any]],
    iterations: int,
    calculate_metrics_fn: MetricsFn,
) -> List[Dict[str, Any]]:
    public_rows = []
    default_has_lt = machine_has_lt(machine)
    default_has_upper_rush = machine_has_upper(machine)
    for row in result_rows:
        if row.get("installed") is False:
            public_rows.append(
                {
                    "category": row.get("category", ""),
                    "machine": row.get("machine_label", machine.name_ko),
                    "store": row.get("store_short_label", row.get("store_name", "")),
                    "case": public_case_label(row),
                    "status": "not_installed",
                    "note": "설치 없음",
                }
            )
            continue

        metrics = row.get("_metrics") or calculate_metrics_fn(row["results"], iterations)
        has_lt = bool(row.get("has_lt")) if "has_lt" in row else default_has_lt
        has_upper_rush = (
            bool(row.get("has_upper_rush"))
            if "has_upper_rush" in row
            else default_has_upper_rush
        )
        public_rows.append(
            {
                "category": row.get("category", ""),
                "machine": row.get("machine_label", machine.name_ko),
                "store": row.get("store_short_label", row.get("store_name", "")),
                "case": public_case_label(row),
                "status": "simulated",
                "simulation_seed": row.get("simulation_seed"),
                "machine_id": row.get("machine_id"),
                "has_lt": has_lt,
                "has_upper_rush": has_upper_rush,
                "assumption_budget_yen": row.get("budget"),
                "assumption_spins_per_1000yen": row.get("spins_per_1000y"),
                "border_spins_per_1000yen": row.get("border_spins_per_1000yen"),
                "strategy": row.get("strategy_label") or row.get("strategy", ""),
                "session_policy": row.get("session_policy_label") or row.get("session_policy", ""),
                "hit_rate_pct": round(metrics["hit_rate"], 1),
                "no_hit_rate_pct": round(metrics["ruin_rate"], 1),
                "rush_rate_pct": round(metrics["rush_rate"], 1),
                "positive_close_rate_pct": round(metrics["positive_close_rate"], 1),
                "positive_close_rate_ci_low_pct": round(metrics["positive_close_rate_ci_low"], 1),
                "positive_close_rate_ci_high_pct": round(metrics["positive_close_rate_ci_high"], 1),
                "avg_profit_standard_error_yen": metrics["avg_profit_standard_error"],
                "avg_profit_se_budget_pct": round(metrics["avg_profit_se_budget_pct"], 2),
                "avg_play_minutes": round(metrics["avg_play_minutes"], 2),
                "median_play_minutes": round(metrics.get("median_play_minutes", 0.0), 2),
                "1h_reach_rate_pct": round(metrics.get("stay_reach_rates", {}).get(1, 0.0), 1),
                "2h_reach_rate_pct": round(metrics.get("stay_reach_rates", {}).get(2, 0.0), 1),
                "3h_reach_rate_pct": round(metrics.get("stay_reach_rates", {}).get(3, 0.0), 1),
                f"{SESSION_TIME_LIMIT_HOURS}h_reach_rate_pct": round(
                    metrics.get("stay_reach_rates", {}).get(SESSION_TIME_LIMIT_HOURS, 0.0),
                    1,
                ),
                "first_hit_miss_funds_exhausted_rate_pct": round(
                    metrics.get("first_hit_miss_funds_exhausted_rate", metrics["ruin_rate"]),
                    1,
                ),
                "avg_first_hit_cash_spent_yen": metrics.get("avg_first_hit_cash_spent", 0),
                "median_first_hit_cash_spent_yen": metrics.get("median_first_hit_cash_spent", 0),
                "avg_first_hit_play_minutes": round(metrics.get("avg_first_hit_play_minutes", 0.0), 2),
                "avg_final_remaining_value_yen": metrics["avg_final_remaining_value"],
                "avg_profit_yen": metrics["avg_profit"],
                "median_profit_yen": metrics["median_profit"],
                "worst_10_profit_yen": metrics["worst_10_profit"],
                "worst_25_profit_yen": metrics["worst_25_profit"],
                "cvar_10_profit_yen": metrics["cvar_10_profit"],
                "mean_median_profit_gap_yen": metrics["avg_profit"] - metrics["median_profit"],
                "top_10_profit_yen": metrics["top_10_profit"],
                "funds_exhausted_stop_rate_pct": round(metrics["funds_exhausted_stop_rate"], 1),
                "p10_play_minutes": round(metrics.get("p10_play_minutes", 0.0), 2),
                "p25_play_minutes": round(metrics.get("p25_play_minutes", 0.0), 2),
                "avg_first_hit_spins": metrics["avg_first_hit"],
                "lt_success_rate_pct": round(metrics["lt_success_rate"], 1) if has_lt else None,
                "lt_success_rate_ci_low_pct": round(metrics["lt_success_rate_ci_low"], 1) if has_lt else None,
                "lt_success_rate_ci_high_pct": round(metrics["lt_success_rate_ci_high"], 1) if has_lt else None,
                "avg_hits": round(metrics["avg_hits"], 2),
                "avg_streak": round(metrics["avg_streak"], 2),
                "p90_streak": metrics.get("p90_streak", 0),
                "max_streak_seen": metrics.get("max_streak_seen", 0),
                "profit_condition_summary": metrics["profit_condition_summary"],
            }
        )
    return public_rows


def build_public_sim_result_payload(
    store_name: str,
    mode_label: str,
    machine: Machine,
    result_rows: List[Dict[str, Any]],
    iterations: int,
    calculate_metrics_fn: MetricsFn,
    generated_at: str | None = None,
    extra_analysis: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    return {
        "schema_version": 5,
        "generated_at": generated_at or kst_now_text(),
        "publication_scope": "latest sanitized aggregate simulator result only",
        "simulation_method": simulation_method_summary(),
        "privacy_policy": {
            "latest_only": True,
            "raw_sample_sessions_included": False,
            "personal_trip_data_included": False,
            "actual_spending_or_profit_included": False,
            "notes": [
                "Rows contain hypothetical simulator assumptions and aggregate Monte Carlo metrics.",
                "Do not treat this as jackpot prediction, visit instruction, or personal spending history.",
            ],
        },
        "mode": mode_label,
        "store_name": store_name,
        "machine": {
            "id": machine.id,
            "name_ko": machine.name_ko,
            "name_ja": machine.name_ja,
            "spec_type": machine.spec_type,
            "confidence": machine.confidence,
        },
        "iterations": iterations,
        "analysis": extra_analysis or {},
        "rows": public_result_rows(machine, result_rows, iterations, calculate_metrics_fn),
    }


def markdown_row_text(row: Dict[str, Any]) -> List[str]:
    if row.get("status") != "simulated":
        return [
            row.get("category", ""),
            row.get("machine", ""),
            row.get("store", ""),
            row.get("case", ""),
            row.get("note", "설치 없음"),
            "-",
            "-",
            "-",
            "-",
            "-",
            "-",
            "-",
            "-",
            "-",
            "-",
            "-",
            "-",
            "-",
            "-",
            "-",
            "-",
            "-",
            "-",
            "-",
            "-",
            "-",
            "-",
            "-",
        ]
    return [
        row.get("category", ""),
        row.get("machine", ""),
        row.get("store", ""),
        row.get("case", ""),
        yen(row.get("assumption_budget_yen", 0)),
        f"{spins_text(row.get('assumption_spins_per_1000yen'))}/1000엔",
        pct(row.get("hit_rate_pct", 0.0)),
        pct(row.get("no_hit_rate_pct", 0.0)),
        pct(row.get("rush_rate_pct", 0.0)),
        pct(row.get("positive_close_rate_pct", 0.0)),
        f"{pct(row.get('positive_close_rate_ci_low_pct', 0.0))}-{pct(row.get('positive_close_rate_ci_high_pct', 0.0))}",
        minutes_text(row.get("avg_play_minutes", 0.0)),
        minutes_text(row.get("median_play_minutes", 0.0)),
        pct(row.get(f"{SESSION_TIME_LIMIT_HOURS}h_reach_rate_pct", 0.0)),
        pct(row.get("1h_reach_rate_pct", 0.0)),
        pct(row.get("2h_reach_rate_pct", 0.0)),
        pct(row.get("3h_reach_rate_pct", 0.0)),
        pct(row.get("funds_exhausted_stop_rate_pct", 0.0)),
        pct(row.get("first_hit_miss_funds_exhausted_rate_pct", 0.0)),
        yen(row.get("avg_first_hit_cash_spent_yen", 0)),
        yen(row.get("avg_final_remaining_value_yen", 0)),
        yen(row.get("median_profit_yen", 0), signed=True),
        yen(row.get("avg_profit_standard_error_yen", 0)),
        f"{row.get('avg_hits', 0.0):.2f}",
        f"{row.get('avg_streak', 0.0):.2f}",
        str(row.get("p90_streak", 0)),
        str(row.get("max_streak_seen", 0)),
    ]


def build_public_sim_result_markdown(payload: Dict[str, Any]) -> str:
    machine = payload["machine"]
    headers = [
        "분류",
        "기종",
        "점포",
        "조건",
        "예산",
        "회전",
        "당첨",
        "0회",
        "RUSH",
        "플러스",
        "플러스95%CI",
        "평균시간",
        "P50시간",
        f"{SESSION_TIME_LIMIT_HOURS}h+",
        "1h+",
        "2h+",
        "3h+",
        "완전소진",
        "초당첨전소진",
        "초당첨평균현금",
        "잔류액",
        "중앙손익",
        "손익SE",
        "평균당첨",
        "평균최대연",
        "P90연",
        "최대연",
    ]
    md = "# 최신 공개 시뮬 결과\n\n"
    md += f"- 생성 시각: {payload['generated_at']}\n"
    md += f"- 모드: {payload['mode']}\n"
    md += f"- 점포: {payload['store_name']}\n"
    md += f"- 기종: {machine['name_ko']} / {machine['name_ja']}\n"
    md += f"- 반복: {payload['iterations']}회\n"
    md += "- 범위: 공개용 최신 1개 집계표입니다. 원시 표본, 개인 일정, 실제 지출/손익은 포함하지 않습니다.\n\n"
    md += build_public_method_markdown(payload.get("simulation_method", {}))
    md += build_rotation_sensitivity_markdown(payload.get("analysis", {}))
    md += build_tail_risk_review_markdown(payload.get("analysis", {}))
    md += "|" + "|".join(headers) + "|\n"
    md += "|" + "|".join("---" for _ in headers) + "|\n"
    for row in payload["rows"]:
        values = [str(value).replace("|", "/") for value in markdown_row_text(row)]
        md += "|" + "|".join(values) + "|\n"
    return md


def build_public_sim_result_html(payload: Dict[str, Any]) -> str:
    markdown_rows = [markdown_row_text(row) for row in payload["rows"]]
    headers = [
        "분류",
        "기종",
        "점포",
        "조건",
        "예산",
        "회전",
        "당첨",
        "0회",
        "RUSH",
        "플러스",
        "플러스95%CI",
        "평균시간",
        "P50시간",
        f"{SESSION_TIME_LIMIT_HOURS}h+",
        "1h+",
        "2h+",
        "3h+",
        "완전소진",
        "초당첨전소진",
        "초당첨평균현금",
        "잔류액",
        "중앙손익",
        "손익SE",
        "평균당첨",
        "평균최대연",
        "P90연",
        "최대연",
    ]
    head_cells = "".join(f"<th>{escape(header)}</th>" for header in headers)
    body_rows = []
    for row in markdown_rows:
        body_rows.append("<tr>" + "".join(f"<td>{escape(str(value))}</td>" for value in row) + "</tr>")

    machine = payload["machine"]
    method_html = build_public_method_html(payload.get("simulation_method", {}))
    sensitivity_html = build_rotation_sensitivity_html(payload.get("analysis", {}))
    tail_risk_html = build_tail_risk_review_html(payload.get("analysis", {}))
    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="alternate" type="application/json" href="latest-sim-results.json" title="Latest simulator aggregate JSON">
  <link rel="alternate" type="text/markdown" href="latest-sim-results.md" title="Latest simulator aggregate Markdown">
  <link rel="index" type="application/json" href="public-data-index.json" title="AI public data index">
  <title>최신 공개 시뮬 결과</title>
  <style>
    body {{ font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 16px; color: #1f2937; }}
    table {{ border-collapse: collapse; width: 100%; font-size: 14px; }}
    th, td {{ border: 1px solid #d1d5db; padding: 8px; text-align: left; vertical-align: top; }}
    th {{ background: #f3f4f6; }}
    .meta {{ color: #4b5563; font-size: 14px; line-height: 1.5; }}
    .note {{ background: #fff7ed; border: 1px solid #fed7aa; padding: 10px; margin: 12px 0; }}
    .note h2 {{ margin: 0 0 8px; font-size: 18px; }}
    .note h3 {{ margin: 12px 0 4px; font-size: 15px; }}
    .note ul {{ margin: 6px 0 0 20px; padding: 0; }}
  </style>
</head>
<body>
  <h1>최신 공개 시뮬 결과</h1>
  <div class="meta">
    <p><strong>생성 시각:</strong> {escape(payload['generated_at'])}</p>
    <p><strong>모드:</strong> {escape(payload['mode'])}</p>
    <p><strong>점포:</strong> {escape(payload['store_name'])}</p>
    <p><strong>기종:</strong> {escape(machine['name_ko'])} / {escape(machine['name_ja'])}</p>
    <p><strong>반복:</strong> {escape(str(payload['iterations']))}회</p>
  </div>
  <div class="note">공개용 최신 1개 집계표입니다. 원시 표본, 개인 일정, 실제 지출/손익은 포함하지 않습니다.</div>
  {method_html}
{sensitivity_html}
{tail_risk_html}
  <table>
    <thead><tr>{head_cells}</tr></thead>
    <tbody>{''.join(body_rows)}</tbody>
  </table>
</body>
</html>
"""


def save_public_sim_results(
    store_name: str,
    mode_label: str,
    machine: Machine,
    result_rows: List[Dict[str, Any]],
    iterations: int,
    calculate_metrics_fn: MetricsFn,
    docs_dir: Path | None = None,
    generated_at: str | None = None,
    extra_analysis: Dict[str, Any] | None = None,
) -> Dict[str, Path]:
    docs_dir = docs_dir or public_docs_dir_from_env()
    docs_dir.mkdir(parents=True, exist_ok=True)
    clean_legacy_public_sim_results(docs_dir)
    payload = build_public_sim_result_payload(
        store_name,
        mode_label,
        machine,
        result_rows,
        iterations,
        calculate_metrics_fn,
        generated_at=generated_at,
        extra_analysis=extra_analysis,
    )
    return save_public_sim_payload(payload, docs_dir=docs_dir)


def save_public_sim_payload(
    payload: Dict[str, Any],
    docs_dir: Path | None = None,
) -> Dict[str, Path]:
    docs_dir = docs_dir or public_docs_dir_from_env()
    docs_dir.mkdir(parents=True, exist_ok=True)
    clean_legacy_public_sim_results(docs_dir)
    json_path = docs_dir / f"{LATEST_SIM_RESULT_BASENAME}.json"
    md_path = docs_dir / f"{LATEST_SIM_RESULT_BASENAME}.md"
    html_path = docs_dir / f"{LATEST_SIM_RESULT_BASENAME}.html"

    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(build_public_sim_result_markdown(payload).rstrip() + "\n", encoding="utf-8")
    html_path.write_text(build_public_sim_result_html(payload), encoding="utf-8")
    return {"json": json_path, "markdown": md_path, "html": html_path}
