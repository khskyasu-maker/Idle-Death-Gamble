import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List
from zoneinfo import ZoneInfo

from machine_traits import machine_has_lt, machine_has_upper
from machines import Machine
from modeling_assumptions import machine_modeling_notes, reliability_summary_rows
from result_formatting import spins_text
from result_public_rendering import build_public_sim_result_html, build_public_sim_result_markdown
from result_public_sections import simulation_method_summary
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
                "support_spin_efficiency": row.get("support_spin_efficiency", machine.support_spin_efficiency),
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
                "play_time_uncertainty_pct": round(metrics.get("play_time_uncertainty_pct", 0.0), 1),
                "avg_play_minutes_low_estimate": round(metrics.get("avg_play_minutes_low_estimate", 0.0), 2),
                "avg_play_minutes_high_estimate": round(metrics.get("avg_play_minutes_high_estimate", 0.0), 2),
                "median_play_minutes": round(metrics.get("median_play_minutes", 0.0), 2),
                "median_play_minutes_low_estimate": round(metrics.get("median_play_minutes_low_estimate", 0.0), 2),
                "median_play_minutes_high_estimate": round(metrics.get("median_play_minutes_high_estimate", 0.0), 2),
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
                "avg_right_spins": metrics.get("avg_right_spins", 0),
                "avg_right_balls_spent": metrics.get("avg_right_balls_spent", 0),
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
        "schema_version": 6,
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
            "modeling_notes": machine_modeling_notes(machine),
        },
        "model_reliability_summary": reliability_summary_rows(),
        "iterations": iterations,
        "analysis": extra_analysis or {},
        "rows": public_result_rows(machine, result_rows, iterations, calculate_metrics_fn),
    }


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
