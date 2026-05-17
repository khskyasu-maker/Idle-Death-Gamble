import argparse
import hashlib
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SIM_DIR = ROOT / "pachinko-sim"
sys.path.insert(0, str(SIM_DIR))

from machine_types import Machine  # noqa: E402
from machines import MACHINES  # noqa: E402
from result_metrics import calculate_metrics  # noqa: E402
from result_public_export import save_public_sim_results  # noqa: E402
from simulator import SESSION_POLICIES, STRATEGIES, simulate_multiple  # noqa: E402
from stores import STORE_INVENTORY, store_contexts_for_machine  # noqa: E402


DEFAULT_BUDGETS = [10000, 15000, 20000]
DEFAULT_ITERATIONS = 5000
DEFAULT_EXCHANGE_RATE = 0.89
DEFAULT_BASE_SEED = 20260518
FALLBACK_SPINS_PER_1000Y = 70.0

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


def row_seed(base_seed: int, machine_id: str, budget: int, spins_per_1000y: float) -> int:
    payload = f"{base_seed}:{machine_id}:{budget}:{spins_per_1000y:.3f}".encode("utf-8")
    return int.from_bytes(hashlib.blake2b(payload, digest_size=8).digest(), "big")


def active_model_ids() -> list[str]:
    model_ids = []
    for store_id in sorted(STORE_INVENTORY.keys(), key=int):
        for row in STORE_INVENTORY[store_id]["machines"]:
            model_id = row["id"]
            if model_id not in model_ids:
                model_ids.append(model_id)
    return model_ids


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


def build_result_rows(
    *,
    budgets: list[int],
    iterations: int,
    exchange_rate: float,
    base_seed: int,
) -> list[dict]:
    sort_items = []
    for machine_id in active_model_ids():
        machine = MACHINES[machine_id]
        context = preferred_context(machine_id)
        category = row_category(context)
        border = context.get("border_spins_per_1000yen")
        if border is not None:
            border = float(border)
            spins_per_1000y = border + 5.0
            rotation_label = "보더+5"
        else:
            spins_per_1000y = FALLBACK_SPINS_PER_1000Y
            rotation_label = "70회/1000엔"

        for budget in budgets:
            seed = row_seed(base_seed, machine_id, budget, spins_per_1000y)
            results = simulate_multiple(
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
            metrics = calculate_metrics(results, iterations)
            store = context.get("store_short_label", context.get("store_name", "-"))
            count = context.get("count", 0)
            row = {
                "category": category,
                "machine_label": machine_label(machine),
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


def main() -> int:
    parser = argparse.ArgumentParser(description="Publish latest sanitized simulator aggregate table.")
    parser.add_argument("--iterations", type=int, default=DEFAULT_ITERATIONS)
    parser.add_argument("--budgets", type=parse_budgets, default=DEFAULT_BUDGETS)
    parser.add_argument("--exchange-rate", type=float, default=DEFAULT_EXCHANGE_RATE)
    parser.add_argument("--base-seed", type=int, default=DEFAULT_BASE_SEED)
    args = parser.parse_args()

    rows = build_result_rows(
        budgets=args.budgets,
        iterations=args.iterations,
        exchange_rate=args.exchange_rate,
        base_seed=args.base_seed,
    )
    paths = save_public_sim_results(
        "대표 저대여 설치 조건(점포 순위 아님)",
        "대해물어/에바/기타 활성 모델 예산별 10k/15k/20k 비교",
        summary_machine(),
        rows,
        args.iterations,
        calculate_metrics,
    )
    print(f"saved {paths}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
