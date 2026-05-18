from html import escape
from typing import Any

from modeling_assumptions import public_model_limitations, reliability_summary_text
from result_formatting import yen


SECTION_LABELS = [
    ("model_structure", "모델 구성"),
    ("stochastic_model", "확률 처리"),
    ("ball_and_time_model", "구슬/시간 처리"),
    ("reliability_summary", "신뢰도 해석"),
    ("statistics", "통계 지표"),
    ("pre_sim_vs_actual_reading", "사전 유추와 실제 결과 비교 기준"),
    ("limits", "한계"),
]


def simulation_method_summary() -> dict[str, Any]:
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
            "공개 JSON에는 시간 추정 오차 가이드(play_time_uncertainty_pct)를 함께 둡니다",
            "표준 공개 실행은 9시간 소프트 스톱과 11시간 하드 캡을 사용합니다",
        ],
        "reliability_summary": reliability_summary_text(),
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
            *public_model_limitations(),
        ],
    }


def method_items(method: dict[str, Any], key: str) -> list[str]:
    items = method.get(key, [])
    if isinstance(items, list):
        return [str(item) for item in items]
    if items:
        return [str(items)]
    return []


def build_public_method_markdown(method: dict[str, Any]) -> str:
    if not method:
        return ""

    md = "## 시뮬 설계와 구성\n\n"
    md += f"- 요약: {method.get('summary', '')}\n"
    for key, label in SECTION_LABELS:
        items = method_items(method, key)
        if not items:
            continue
        md += f"- {label}: " + "; ".join(items) + "\n"
    md += "\n"
    return md


def build_public_method_html(method: dict[str, Any]) -> str:
    if not method:
        return ""

    html = [
        '<section class="note">',
        "<h2>시뮬 설계와 구성</h2>",
        f"<p>{escape(str(method.get('summary', '')))}</p>",
    ]
    for key, label in SECTION_LABELS:
        items = method_items(method, key)
        if not items:
            continue
        html.append(f"<h3>{escape(label)}</h3>")
        html.append("<ul>")
        html.extend(f"<li>{escape(item)}</li>" for item in items)
        html.append("</ul>")
    html.append("</section>")
    return "\n".join(html)


def build_rotation_sensitivity_markdown(analysis: dict[str, Any]) -> str:
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


def build_rotation_sensitivity_html(analysis: dict[str, Any]) -> str:
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


def build_tail_risk_review_markdown(analysis: dict[str, Any]) -> str:
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


def build_tail_risk_review_html(analysis: dict[str, Any]) -> str:
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


__all__ = [
    "build_public_method_html",
    "build_public_method_markdown",
    "build_rotation_sensitivity_html",
    "build_rotation_sensitivity_markdown",
    "build_tail_risk_review_html",
    "build_tail_risk_review_markdown",
    "method_items",
    "simulation_method_summary",
]
