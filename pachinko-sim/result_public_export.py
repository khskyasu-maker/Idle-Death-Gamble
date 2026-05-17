import json
import os
from datetime import datetime
from html import escape
from pathlib import Path
from typing import Any, Callable, Dict, List
from zoneinfo import ZoneInfo

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
        "summary": "Public machine specs are encoded as Monte Carlo state transitions, then run against visible budget, rotation, exchange, and stop-rule assumptions.",
        "inputs": [
            "machine probability and payout distributions from public specs",
            "low-rate store installation context and converted border spins per 1000円",
            "runtime budget, exchange rate, rotation assumption, strategy, and session policy",
        ],
        "runtime_model": [
            "normal-start spins are sampled from a ball-to-start gate model around the input rotation",
            "held balls can be reused for normal play before adding new cash",
            "right-side RUSH/LT/時短 time and average ball spend are modeled by machine family",
            "sessions use a 9-hour soft stop and an 11-hour hard cap",
        ],
        "limits": [
            "aggregate estimate only, not jackpot prediction or a visit instruction",
            "no raw sample sessions, personal trip data, or actual spending/profit records are published",
            "store labels are representative installation/rate context, not store ranking",
        ],
    }


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

        metrics = calculate_metrics_fn(row["results"], iterations)
        public_rows.append(
            {
                "category": row.get("category", ""),
                "machine": row.get("machine_label", machine.name_ko),
                "store": row.get("store_short_label", row.get("store_name", "")),
                "case": public_case_label(row),
                "status": "simulated",
                "assumption_budget_yen": row.get("budget"),
                "assumption_spins_per_1000yen": row.get("spins_per_1000y"),
                "border_spins_per_1000yen": row.get("border_spins_per_1000yen"),
                "strategy": row.get("strategy_label") or row.get("strategy", ""),
                "session_policy": row.get("session_policy_label") or row.get("session_policy", ""),
                "hit_rate_pct": round(metrics["hit_rate"], 1),
                "no_hit_rate_pct": round(metrics["ruin_rate"], 1),
                "rush_rate_pct": round(metrics["rush_rate"], 1),
                "positive_close_rate_pct": round(metrics["positive_close_rate"], 1),
                "avg_play_minutes": round(metrics["avg_play_minutes"], 2),
                "median_play_minutes": round(metrics.get("median_play_minutes", 0.0), 2),
                f"{SESSION_TIME_LIMIT_HOURS}h_reach_rate_pct": round(
                    metrics.get("stay_reach_rates", {}).get(SESSION_TIME_LIMIT_HOURS, 0.0),
                    1,
                ),
                "avg_final_remaining_value_yen": metrics["avg_final_remaining_value"],
                "avg_profit_yen": metrics["avg_profit"],
                "median_profit_yen": metrics["median_profit"],
                "worst_10_profit_yen": metrics["worst_10_profit"],
                "top_10_profit_yen": metrics["top_10_profit"],
                "funds_exhausted_stop_rate_pct": round(metrics["funds_exhausted_stop_rate"], 1),
                "avg_first_hit_spins": metrics["avg_first_hit"],
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
) -> Dict[str, Any]:
    return {
        "schema_version": 2,
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
        minutes_text(row.get("avg_play_minutes", 0.0)),
        minutes_text(row.get("median_play_minutes", 0.0)),
        pct(row.get(f"{SESSION_TIME_LIMIT_HOURS}h_reach_rate_pct", 0.0)),
        pct(row.get("funds_exhausted_stop_rate_pct", 0.0)),
        yen(row.get("avg_final_remaining_value_yen", 0)),
        yen(row.get("median_profit_yen", 0), signed=True),
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
        "평균시간",
        "P50시간",
        f"{SESSION_TIME_LIMIT_HOURS}h+",
        "완전소진",
        "잔류액",
        "중앙손익",
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
    method = payload.get("simulation_method", {})
    if method:
        md += "## 시뮬 구현 요약\n\n"
        md += f"- 방식: {method.get('summary', '')}\n"
        md += "- 입력: 기종 스펙, 설치/레이트/보더, 예산, 회전수, 교환율, 중단 규칙\n"
        md += "- 구슬/시간: 헤소 입상 표본, 보유구슬 재사용, 우타치/RUSH/LT 시간, 9시간 소프트 스톱을 반영\n"
        md += "- 한계: 집계 추정치일 뿐 당첨 예측, 방문 지시, 점포 순위가 아닙니다.\n\n"
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
        "평균시간",
        "P50시간",
        f"{SESSION_TIME_LIMIT_HOURS}h+",
        "완전소진",
        "잔류액",
        "중앙손익",
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
    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>최신 공개 시뮬 결과</title>
  <style>
    body {{ font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 16px; color: #1f2937; }}
    table {{ border-collapse: collapse; width: 100%; font-size: 14px; }}
    th, td {{ border: 1px solid #d1d5db; padding: 8px; text-align: left; vertical-align: top; }}
    th {{ background: #f3f4f6; }}
    .meta {{ color: #4b5563; font-size: 14px; line-height: 1.5; }}
    .note {{ background: #fff7ed; border: 1px solid #fed7aa; padding: 10px; margin: 12px 0; }}
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
  <section class="note">
    <strong>시뮬 구현 요약:</strong>
    공개 스펙의 확률/출옥 분포를 상태 전이로 모델링하고, 보더+회전수, 예산, 교환율, 보유구슬 재사용,
    우타치/RUSH/LT 시간, 9시간 소프트 스톱을 적용한 Monte Carlo 집계입니다.
    당첨 예측, 방문 지시, 점포 순위가 아닙니다.
  </section>
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
    )
    json_path = docs_dir / f"{LATEST_SIM_RESULT_BASENAME}.json"
    md_path = docs_dir / f"{LATEST_SIM_RESULT_BASENAME}.md"
    html_path = docs_dir / f"{LATEST_SIM_RESULT_BASENAME}.html"

    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(build_public_sim_result_markdown(payload).rstrip() + "\n", encoding="utf-8")
    html_path.write_text(build_public_sim_result_html(payload), encoding="utf-8")
    return {"json": json_path, "markdown": md_path, "html": html_path}
