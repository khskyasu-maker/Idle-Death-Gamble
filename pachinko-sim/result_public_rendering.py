from html import escape
from typing import Any

from result_formatting import minutes_text, pct, spins_text, yen
from result_public_sections import (
    build_public_method_html,
    build_public_method_markdown,
    build_rotation_sensitivity_html,
    build_rotation_sensitivity_markdown,
    build_tail_risk_review_html,
    build_tail_risk_review_markdown,
)
from session_limits import SESSION_TIME_LIMIT_HOURS


PUBLIC_TABLE_HEADERS = [
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


def markdown_row_text(row: dict[str, Any]) -> list[str]:
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


def build_public_sim_result_markdown(payload: dict[str, Any]) -> str:
    machine = payload["machine"]
    md = "# 최신 공개 시뮬 결과\n\n"
    md += f"- 생성 시각: {payload['generated_at']}\n"
    md += f"- 모드: {payload['mode']}\n"
    md += f"- 점포: {payload['store_name']}\n"
    md += f"- 기종: {machine['name_ko']} / {machine['name_ja']}\n"
    modeling_notes = machine.get("modeling_notes", [])
    if modeling_notes:
        md += "- 모델 주의: " + "; ".join(str(note) for note in modeling_notes) + "\n"
    md += f"- 반복: {payload['iterations']}회\n"
    md += "- 범위: 공개용 최신 1개 집계표입니다. 원시 표본, 개인 일정, 실제 지출/손익은 포함하지 않습니다.\n\n"
    md += build_public_method_markdown(payload.get("simulation_method", {}))
    md += build_rotation_sensitivity_markdown(payload.get("analysis", {}))
    md += build_tail_risk_review_markdown(payload.get("analysis", {}))
    md += "|" + "|".join(PUBLIC_TABLE_HEADERS) + "|\n"
    md += "|" + "|".join("---" for _ in PUBLIC_TABLE_HEADERS) + "|\n"
    for row in payload["rows"]:
        values = [str(value).replace("|", "/") for value in markdown_row_text(row)]
        md += "|" + "|".join(values) + "|\n"
    return md


def build_public_sim_result_html(payload: dict[str, Any]) -> str:
    markdown_rows = [markdown_row_text(row) for row in payload["rows"]]
    head_cells = "".join(f"<th>{escape(header)}</th>" for header in PUBLIC_TABLE_HEADERS)
    body_rows = []
    for row in markdown_rows:
        body_rows.append("<tr>" + "".join(f"<td>{escape(str(value))}</td>" for value in row) + "</tr>")

    machine = payload["machine"]
    modeling_notes = machine.get("modeling_notes", [])
    modeling_note_html = ""
    if modeling_notes:
        modeling_note_html = (
            '<div class="note"><strong>모델 주의:</strong><ul>'
            + "".join(f"<li>{escape(str(note))}</li>" for note in modeling_notes)
            + "</ul></div>"
        )
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
  {modeling_note_html}
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


__all__ = [
    "PUBLIC_TABLE_HEADERS",
    "build_public_sim_result_html",
    "build_public_sim_result_markdown",
    "markdown_row_text",
]
