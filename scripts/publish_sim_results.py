import argparse
import hashlib
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SIM_DIR = ROOT / "pachinko-sim"
sys.path.insert(0, str(SIM_DIR))

from machine_types import Machine  # noqa: E402
from machine_traits import machine_has_lt, machine_has_upper  # noqa: E402
from machines import MACHINES  # noqa: E402
from result_metrics import calculate_metrics  # noqa: E402
from result_public_export import (  # noqa: E402
    LATEST_SIM_RESULT_BASENAME,
    build_public_sim_result_payload,
    public_docs_dir_from_env,
    save_public_sim_payload,
    save_public_sim_results,
)
from simulator import SESSION_POLICIES, STRATEGIES, simulate_multiple  # noqa: E402
from stores import STORE_INVENTORY, store_contexts_for_machine  # noqa: E402


DEFAULT_BUDGETS = [10000, 15000, 20000]
DEFAULT_ITERATIONS = 5000
DEFAULT_SENSITIVITY_BUDGET = 10000
DEFAULT_SENSITIVITY_ITERATIONS = 3000
DEFAULT_RISK_REVIEW_BUDGET = 10000
DEFAULT_FIELD_ROTATION_MARGIN = 0.0
DEFAULT_EXCHANGE_RATE = 0.89
DEFAULT_BASE_SEED = 20260518
FALLBACK_SPINS_PER_1000Y = 70.0
FALLBACK_SENSITIVITY_SPINS = [60.0, 70.0, 80.0, 90.0]

CATEGORY_LABELS = {
    "daiumi": "대해물어",
    "eva": "에바",
    "other": "기타",
}
CATEGORY_ORDER = {"대해물어": 0, "에바": 1, "기타": 2}
STORE_ORDER = {"123_namba": 0, "arrow_namba_hips": 1, "rakuen_namba": 2}


def parse_budgets(value: str) -> list[int]:
    budgets = []
    for part in value.split(","):
        part = part.strip()
        if not part:
            continue
        budgets.append(int(part))
    if not budgets:
        raise argparse.ArgumentTypeError("at least one budget is required")
    return budgets


def parse_machine_ids(values: list[str] | None) -> list[str] | None:
    if not values:
        return None
    machine_ids = []
    for value in values:
        for part in value.split(","):
            machine_id = part.strip()
            if machine_id and machine_id not in machine_ids:
                machine_ids.append(machine_id)
    return machine_ids or None


def row_seed(base_seed: int, machine_id: str, budget: int, spins_per_1000y: float) -> int:
    payload = f"{base_seed}:{machine_id}:{budget}:{spins_per_1000y:.3f}".encode("utf-8")
    return int.from_bytes(hashlib.blake2b(payload, digest_size=8).digest(), "big")


def analysis_seed(base_seed: int, namespace: str, machine_id: str, budget: int, spins_per_1000y: float) -> int:
    payload = f"{base_seed}:{namespace}:{machine_id}:{budget}:{spins_per_1000y:.3f}".encode("utf-8")
    return int.from_bytes(hashlib.blake2b(payload, digest_size=8).digest(), "big")


def active_model_ids() -> list[str]:
    model_ids = []
    for store_id in sorted(STORE_INVENTORY.keys(), key=int):
        for row in STORE_INVENTORY[store_id]["machines"]:
            model_id = row["id"]
            if model_id not in model_ids:
                model_ids.append(model_id)
    return model_ids


def selected_active_model_ids(machine_ids: list[str] | None) -> list[str]:
    active_ids = active_model_ids()
    if not machine_ids:
        return active_ids
    active_id_set = set(active_ids)
    unknown_ids = [machine_id for machine_id in machine_ids if machine_id not in active_id_set]
    if unknown_ids:
        unknown_text = ", ".join(unknown_ids)
        raise ValueError(f"unknown or inactive machine id: {unknown_text}")
    return [machine_id for machine_id in active_ids if machine_id in machine_ids]


def preferred_context(machine_id: str) -> dict:
    contexts = [
        context
        for context in store_contexts_for_machine(machine_id, include_missing=False)
        if context.get("installed")
    ]
    one_yen_contexts = [context for context in contexts if context.get("rate") == "1yen"]
    candidates = one_yen_contexts or contexts
    if not candidates:
        raise ValueError(f"no installed low-rate context for {machine_id}")
    return sorted(candidates, key=lambda context: STORE_ORDER.get(context.get("store_id"), 99))[0]


def row_category(context: dict) -> str:
    raw_category = (context.get("machine") or {}).get("lineup_category") or ""
    return CATEGORY_LABELS.get(raw_category, raw_category or "기타")


def machine_label(machine: Machine) -> str:
    return (
        machine.name_ko
        .replace("신세기 에반게리온 ", "에바 ")
        .replace("P 신세기 에반게리온 ", "P 에바 ")
    )


def summary_machine() -> Machine:
    return Machine(
        id="namba_low_rate_all_models_budget_matrix",
        name_ja="Namba low-rate supported models budget matrix",
        name_ko="난바 저대여 활성 시뮬 모델 예산별 비교",
        spec_type="multi-machine budget matrix",
        risk_grade="mixed",
        normal_prob=0.0,
        high_prob=0.0,
        normal_hit_dist=[],
        st_hit_dist=[],
        jitan_hit_dist=[],
        kakuben_hit_dist=[],
        lt_hit_dist=[],
        confidence="mixed",
        notes="Synthetic metadata object used only for latest public aggregate export.",
    )


def format_minutes_range(min_minutes: float, max_minutes: float) -> str:
    return f"{min_minutes:.0f}~{max_minutes:.0f}분"


def format_minutes_value(minutes: float) -> str:
    return f"{minutes:.0f}분"


def format_pct_range(min_pct: float, max_pct: float) -> str:
    return f"{min_pct:.1f}~{max_pct:.1f}%"


def format_pct_value(value: float) -> str:
    return f"{value:.1f}%"


def format_yen_range(min_yen: int, max_yen: int) -> str:
    return f"{min_yen:+,}엔~{max_yen:+,}엔"


def rotation_sensitivity_cases(border: float | None) -> list[tuple[str, float]]:
    if border is None:
        return [(f"{spins:.0f}회/1000엔", spins) for spins in FALLBACK_SENSITIVITY_SPINS]
    return [
        ("보더-5", max(1.0, border - 5.0)),
        ("보더±0", border),
        ("보더+5", border + 5.0),
        ("보더+10", border + 10.0),
    ]


def sensitivity_label(plus_range: float, median_time_range: float, exhausted_range: float) -> str:
    if plus_range >= 25.0 or median_time_range >= 240.0 or exhausted_range >= 30.0:
        return "높음"
    if plus_range >= 12.0 or median_time_range >= 90.0 or exhausted_range >= 15.0:
        return "중간"
    return "낮음"


def rotation_margin_label(margin: float) -> str:
    if abs(margin) < 0.05:
        return "보더±0"
    sign = "+" if margin > 0 else ""
    return f"보더{sign}{margin:g}"


def tail_risk_label(
    *,
    has_lt: bool,
    budget: int,
    median_profit: int,
    cvar_10_profit: int,
    mean_median_gap: int,
    p25_play_minutes: float,
    funds_exhausted_rate: float,
) -> str:
    deep_median_loss = median_profit <= -0.7 * budget
    deep_tail_loss = cvar_10_profit <= -0.9 * budget
    large_tail_lift = mean_median_gap >= 0.35 * budget
    short_lower_quartile = p25_play_minutes < 240.0
    high_exhaustion = funds_exhausted_rate >= 50.0

    if has_lt and deep_median_loss and large_tail_lift:
        return "LT꼬리의존"
    if deep_median_loss and (high_exhaustion or short_lower_quartile):
        return "하방큼"
    if deep_tail_loss and high_exhaustion:
        return "소진주의"
    if large_tail_lift:
        return "꼬리의존"
    return "보통"


def simulate_case(
    *,
    machine: Machine,
    context: dict,
    budget: int,
    spins_per_1000y: float,
    exchange_rate: float,
    iterations: int,
    seed: int,
    border: float | None,
) -> list[dict]:
    return simulate_multiple(
        machine,
        budget=budget,
        lend_rate=float(context.get("rental_rate") or 1.0),
        spins_per_1000y=spins_per_1000y,
        exchange_rate=exchange_rate,
        iterations=iterations,
        strategy="no_rule",
        session_policy="play_until_budget_and_balls_gone",
        start_variance=True,
        border_spins_per_1000y=border,
        seed=seed,
    )


def build_result_rows(
    *,
    budgets: list[int],
    iterations: int,
    exchange_rate: float,
    base_seed: int,
    field_rotation_margin: float,
    machine_ids: list[str] | None = None,
) -> list[dict]:
    sort_items = []
    for machine_id in selected_active_model_ids(machine_ids):
        machine = MACHINES[machine_id]
        context = preferred_context(machine_id)
        category = row_category(context)
        border = context.get("border_spins_per_1000yen")
        if border is not None:
            border = float(border)
            spins_per_1000y = max(1.0, border + field_rotation_margin)
            rotation_label = rotation_margin_label(field_rotation_margin)
        else:
            spins_per_1000y = FALLBACK_SPINS_PER_1000Y
            rotation_label = "70회/1000엔"

        for budget in budgets:
            seed = row_seed(base_seed, machine_id, budget, spins_per_1000y)
            results = simulate_case(
                machine=machine,
                context=context,
                budget=budget,
                spins_per_1000y=spins_per_1000y,
                exchange_rate=exchange_rate,
                iterations=iterations,
                seed=seed,
                border=border,
            )
            metrics = calculate_metrics(results, iterations)
            store = context.get("store_short_label", context.get("store_name", "-"))
            count = context.get("count", 0)
            row = {
                "category": category,
                "machine_id": machine_id,
                "machine_label": machine_label(machine),
                "has_lt": machine_has_lt(machine),
                "has_upper_rush": machine_has_upper(machine),
                "store_short_label": f"{store}/{count}대",
                "case_label": f"{rotation_label} / 노룰 / 9h정리",
                "budget": budget,
                "spins_per_1000y": spins_per_1000y,
                "border_spins_per_1000yen": border,
                "strategy": "no_rule",
                "strategy_label": STRATEGIES["no_rule"],
                "session_policy": "play_until_budget_and_balls_gone",
                "session_policy_label": SESSION_POLICIES["play_until_budget_and_balls_gone"],
                "simulation_seed": seed,
                "results": results,
                "_metrics": metrics,
            }
            sort_items.append((row, metrics))
            print(
                f"done\t{category}\t{machine_id}\t{budget}\t{store}/{count}대\t"
                f"seed={seed}\tspins={spins_per_1000y:.1f}\t"
                f"avg={metrics['avg_play_minutes']:.1f}\tplus={metrics['positive_close_rate']:.1f}",
                flush=True,
            )

    return [
        row
        for row, _metrics in sorted(
            sort_items,
            key=lambda item: (
                CATEGORY_ORDER.get(item[0]["category"], 99),
                item[0]["machine_label"],
                item[0]["budget"],
            ),
        )
    ]


def build_rotation_sensitivity(
    *,
    budget: int,
    iterations: int,
    exchange_rate: float,
    base_seed: int,
    machine_ids: list[str] | None = None,
) -> dict:
    rows = []
    for machine_id in selected_active_model_ids(machine_ids):
        machine = MACHINES[machine_id]
        context = preferred_context(machine_id)
        category = row_category(context)
        border = context.get("border_spins_per_1000yen")
        border = float(border) if border is not None else None
        case_metrics = []
        for label, spins_per_1000y in rotation_sensitivity_cases(border):
            seed = analysis_seed(base_seed, "rotation_sensitivity", machine_id, budget, spins_per_1000y)
            results = simulate_case(
                machine=machine,
                context=context,
                budget=budget,
                spins_per_1000y=spins_per_1000y,
                exchange_rate=exchange_rate,
                iterations=iterations,
                seed=seed,
                border=border,
            )
            metrics = calculate_metrics(results, iterations)
            case_metrics.append(
                {
                    "label": label,
                    "spins_per_1000yen": round(spins_per_1000y, 2),
                    "simulation_seed": seed,
                    "median_play_minutes": round(metrics["median_play_minutes"], 2),
                    "positive_close_rate_pct": round(metrics["positive_close_rate"], 1),
                    "positive_close_rate_ci_low_pct": round(metrics["positive_close_rate_ci_low"], 1),
                    "positive_close_rate_ci_high_pct": round(metrics["positive_close_rate_ci_high"], 1),
                    "funds_exhausted_stop_rate_pct": round(metrics["funds_exhausted_stop_rate"], 1),
                    "median_profit_yen": metrics["median_profit"],
                    "avg_profit_standard_error_yen": metrics["avg_profit_standard_error"],
                }
            )
            print(
                f"sensitivity\t{category}\t{machine_id}\t{label}\t{budget}\t"
                f"seed={seed}\tspins={spins_per_1000y:.1f}\t"
                f"p50={metrics['median_play_minutes']:.1f}\tplus={metrics['positive_close_rate']:.1f}",
                flush=True,
            )

        median_times = [case["median_play_minutes"] for case in case_metrics]
        plus_rates = [case["positive_close_rate_pct"] for case in case_metrics]
        exhausted_rates = [case["funds_exhausted_stop_rate_pct"] for case in case_metrics]
        median_profits = [case["median_profit_yen"] for case in case_metrics]
        rotation_min = min(case["spins_per_1000yen"] for case in case_metrics)
        rotation_max = max(case["spins_per_1000yen"] for case in case_metrics)
        median_time_range = max(median_times) - min(median_times)
        plus_range = max(plus_rates) - min(plus_rates)
        exhausted_range = max(exhausted_rates) - min(exhausted_rates)
        store = context.get("store_short_label", context.get("store_name", "-"))
        count = context.get("count", 0)
        rows.append(
            {
                "category": category,
                "machine_id": machine_id,
                "machine": machine_label(machine),
                "store": f"{store}/{count}대",
                "budget_yen": budget,
                "rotation_range_text": f"{rotation_min:g}-{rotation_max:g}회/1000엔",
                "median_time_range_text": format_minutes_range(min(median_times), max(median_times)),
                "plus_range_text": format_pct_range(min(plus_rates), max(plus_rates)),
                "funds_exhausted_range_text": format_pct_range(min(exhausted_rates), max(exhausted_rates)),
                "median_profit_range_text": format_yen_range(min(median_profits), max(median_profits)),
                "sensitivity_label": sensitivity_label(plus_range, median_time_range, exhausted_range),
                "case_metrics": case_metrics,
            }
        )

    rows.sort(
        key=lambda row: (
            CATEGORY_ORDER.get(row["category"], 99),
            row["machine"],
        )
    )
    return {
        "budget_yen": budget,
        "iterations": iterations,
        "scope": "rotation-input sensitivity summary, not actual play results",
        "rows": rows,
    }


def public_row_key(row: dict) -> tuple:
    return (
        row.get("machine_id"),
        row.get("assumption_budget_yen"),
        row.get("strategy"),
        row.get("session_policy"),
        row.get("case"),
    )


def sort_public_rows(rows: list[dict]) -> list[dict]:
    return sorted(
        rows,
        key=lambda row: (
            CATEGORY_ORDER.get(row.get("category", ""), 99),
            row.get("machine", ""),
            row.get("assumption_budget_yen") or 0,
        ),
    )


def merge_public_rows(existing_rows: list[dict], new_rows: list[dict]) -> list[dict]:
    new_keys = {public_row_key(row) for row in new_rows}
    merged_rows = [row for row in existing_rows if public_row_key(row) not in new_keys]
    merged_rows.extend(new_rows)
    return sort_public_rows(merged_rows)


def merge_named_analysis_rows(
    existing_section: dict | None,
    new_section: dict,
    *,
    sort_key,
) -> dict:
    if not existing_section:
        return new_section
    new_machine_ids = {
        row.get("machine_id")
        for row in new_section.get("rows", [])
        if row.get("machine_id")
    }
    new_machine_names = {
        row.get("machine")
        for row in new_section.get("rows", [])
        if row.get("machine")
    }
    merged_rows = [
        row
        for row in existing_section.get("rows", [])
        if row.get("machine_id") not in new_machine_ids
        and row.get("machine") not in new_machine_names
    ]
    merged_rows.extend(new_section.get("rows", []))
    merged_section = dict(existing_section)
    merged_section.update({key: value for key, value in new_section.items() if key != "rows"})
    merged_section["rows"] = sorted(merged_rows, key=sort_key)
    return merged_section


def sort_tail_risk_rows(rows: list[dict]) -> list[dict]:
    return sorted(rows, key=tail_risk_sort_key)


def tail_risk_sort_key(row: dict) -> tuple:
    risk_order = {"LT꼬리의존": 0, "하방큼": 1, "소진주의": 2, "꼬리의존": 3, "보통": 4}
    return (
        risk_order.get(row.get("risk_label", ""), 99),
        row.get("p25_play_minutes", 0),
        row.get("median_profit_yen", 0),
    )


def merge_extra_analysis(existing_analysis: dict, new_analysis: dict) -> dict:
    merged_analysis = dict(existing_analysis or {})
    if "rotation_sensitivity" in new_analysis:
        merged_analysis["rotation_sensitivity"] = merge_named_analysis_rows(
            merged_analysis.get("rotation_sensitivity"),
            new_analysis["rotation_sensitivity"],
            sort_key=lambda row: (
                CATEGORY_ORDER.get(row.get("category", ""), 99),
                row.get("machine", ""),
            ),
        )
    if "tail_risk_review" in new_analysis:
        merged_analysis["tail_risk_review"] = merge_named_analysis_rows(
            merged_analysis.get("tail_risk_review"),
            new_analysis["tail_risk_review"],
            sort_key=tail_risk_sort_key,
        )
        merged_analysis["tail_risk_review"]["rows"] = sort_tail_risk_rows(
            merged_analysis["tail_risk_review"].get("rows", [])
        )
    return merged_analysis


def merge_existing_payload(existing_payload: dict, new_payload: dict) -> dict:
    if existing_payload.get("iterations") != new_payload.get("iterations"):
        raise ValueError(
            "existing latest-sim-results.json uses a different iterations value; "
            "rerun without --merge-existing or match --iterations"
        )
    merged_payload = dict(existing_payload)
    for key in (
        "generated_at",
        "publication_scope",
        "simulation_method",
        "privacy_policy",
        "mode",
        "store_name",
        "machine",
        "iterations",
    ):
        merged_payload[key] = new_payload.get(key)
    merged_payload["rows"] = merge_public_rows(
        existing_payload.get("rows", []),
        new_payload.get("rows", []),
    )
    merged_payload["analysis"] = merge_extra_analysis(
        existing_payload.get("analysis", {}),
        new_payload.get("analysis", {}),
    )
    return merged_payload


def load_existing_public_payload() -> dict:
    json_path = public_docs_dir_from_env() / f"{LATEST_SIM_RESULT_BASENAME}.json"
    if not json_path.exists():
        raise FileNotFoundError(f"{json_path} does not exist")
    return json.loads(json_path.read_text(encoding="utf-8"))


def build_tail_risk_review(
    *,
    result_rows: list[dict],
    budget: int,
    iterations: int,
) -> dict:
    rows = []
    for row in result_rows:
        if row.get("budget") != budget:
            continue
        metrics = row.get("_metrics") or calculate_metrics(row["results"], iterations)
        mean_median_gap = metrics["avg_profit"] - metrics["median_profit"]
        has_lt = bool(row.get("has_lt"))
        rows.append(
            {
                "category": row.get("category", ""),
                "machine_id": row.get("machine_id", ""),
                "machine": row.get("machine_label", ""),
                "store": row.get("store_short_label", ""),
                "budget_yen": budget,
                "p10_play_minutes": round(metrics["p10_play_minutes"], 2),
                "p25_play_minutes": round(metrics["p25_play_minutes"], 2),
                "p10_play_text": format_minutes_value(metrics["p10_play_minutes"]),
                "p25_play_text": format_minutes_value(metrics["p25_play_minutes"]),
                "funds_exhausted_rate_pct": round(metrics["funds_exhausted_stop_rate"], 1),
                "funds_exhausted_text": format_pct_value(metrics["funds_exhausted_stop_rate"]),
                "median_profit_yen": metrics["median_profit"],
                "median_profit_text": f"{metrics['median_profit']:+,}엔",
                "cvar10_yen": metrics["cvar_10_profit"],
                "cvar10_text": f"{metrics['cvar_10_profit']:+,}엔",
                "mean_median_gap_yen": mean_median_gap,
                "mean_median_gap_text": f"{mean_median_gap:+,}엔",
                "lt_entry_rate_pct": round(metrics["lt_success_rate"], 1) if has_lt else None,
                "lt_entry_text": (
                    f"{metrics['lt_success_rate']:.1f}%"
                    if has_lt
                    else "해당없음"
                ),
                "risk_label": tail_risk_label(
                    has_lt=has_lt,
                    budget=budget,
                    median_profit=metrics["median_profit"],
                    cvar_10_profit=metrics["cvar_10_profit"],
                    mean_median_gap=mean_median_gap,
                    p25_play_minutes=metrics["p25_play_minutes"],
                    funds_exhausted_rate=metrics["funds_exhausted_stop_rate"],
                ),
            }
        )

    risk_order = {"LT꼬리의존": 0, "하방큼": 1, "소진주의": 2, "꼬리의존": 3, "보통": 4}
    rows.sort(
        key=lambda row: (
            risk_order.get(row["risk_label"], 99),
            row["p25_play_minutes"],
            row["median_profit_yen"],
        )
    )
    return {
        "budget_yen": budget,
        "iterations": iterations,
        "scope": "lower-tail risk summary, not actual play results",
        "rows": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Publish latest sanitized simulator aggregate table.")
    parser.add_argument("--iterations", type=int, default=DEFAULT_ITERATIONS)
    parser.add_argument("--budgets", type=parse_budgets, default=DEFAULT_BUDGETS)
    parser.add_argument("--sensitivity-budget", type=int, default=DEFAULT_SENSITIVITY_BUDGET)
    parser.add_argument("--sensitivity-iterations", type=int, default=DEFAULT_SENSITIVITY_ITERATIONS)
    parser.add_argument("--risk-review-budget", type=int, default=DEFAULT_RISK_REVIEW_BUDGET)
    parser.add_argument("--field-rotation-margin", type=float, default=DEFAULT_FIELD_ROTATION_MARGIN)
    parser.add_argument("--skip-sensitivity", action="store_true")
    parser.add_argument("--skip-risk-review", action="store_true")
    parser.add_argument("--exchange-rate", type=float, default=DEFAULT_EXCHANGE_RATE)
    parser.add_argument("--base-seed", type=int, default=DEFAULT_BASE_SEED)
    parser.add_argument(
        "--machine-id",
        action="append",
        dest="machine_id_values",
        help="Limit regeneration to one active machine id. Repeat or comma-separate for multiple ids.",
    )
    parser.add_argument(
        "--merge-existing",
        action="store_true",
        help="Replace only regenerated machine rows inside existing latest-sim-results output.",
    )
    args = parser.parse_args()
    machine_ids = parse_machine_ids(args.machine_id_values)
    if args.merge_existing and not machine_ids:
        raise SystemExit("--merge-existing requires at least one --machine-id")
    if machine_ids and not args.merge_existing:
        raise SystemExit("--machine-id requires --merge-existing to avoid publishing a partial table")

    rows = build_result_rows(
        budgets=args.budgets,
        iterations=args.iterations,
        exchange_rate=args.exchange_rate,
        base_seed=args.base_seed,
        field_rotation_margin=args.field_rotation_margin,
        machine_ids=machine_ids,
    )
    extra_analysis = {}
    if not args.skip_sensitivity:
        extra_analysis["rotation_sensitivity"] = build_rotation_sensitivity(
            budget=args.sensitivity_budget,
            iterations=args.sensitivity_iterations,
            exchange_rate=args.exchange_rate,
            base_seed=args.base_seed,
            machine_ids=machine_ids,
        )
    if not args.skip_risk_review:
        extra_analysis["tail_risk_review"] = build_tail_risk_review(
            result_rows=rows,
            budget=args.risk_review_budget,
            iterations=args.iterations,
        )
    store_name = "대표 저대여 설치 조건(점포 순위 아님)"
    mode_label = (
        "대해물어/에바/기타 활성 모델 예산별 10k/15k/20k 비교 "
        f"({rotation_margin_label(args.field_rotation_margin)} 기준)"
    )
    if args.merge_existing:
        new_payload = build_public_sim_result_payload(
            store_name,
            mode_label,
            summary_machine(),
            rows,
            args.iterations,
            calculate_metrics,
            extra_analysis=extra_analysis,
        )
        merged_payload = merge_existing_payload(load_existing_public_payload(), new_payload)
        paths = save_public_sim_payload(merged_payload)
    else:
        paths = save_public_sim_results(
            store_name,
            mode_label,
            summary_machine(),
            rows,
            args.iterations,
            calculate_metrics,
            extra_analysis=extra_analysis,
        )
    print(f"saved {paths}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
