import json
from pathlib import Path

from machines import MACHINES


DATA_FILE = Path(__file__).resolve().parents[1] / "data" / "namba-actual-1yen-lineup.json"

STORE_CHOICES = {
    "1": {
        "store_id": "rakuen_namba",
        "name": "라쿠엔 난바점 (楽園なんば店)",
        "rental_rate_label": "1.111パチ (100円/90玉)",
        "rental_rate": 1.111,
        "source_url": "https://p-town.dmm.com/shops/osaka/12558",
        "dmm_low_rate_total_count": 170,
        "lineup_scope": "DMM 1.111円パチ 중 로컬 수동 후보",
    },
    "2": {
        "store_id": "123_namba",
        "name": "123 난바점 (123難波店)",
        "rental_rate_label": "1円パチ (1円/1玉)",
        "rental_rate": 1.0,
        "source_url": "https://p-town.dmm.com/shops/osaka/7568",
        "dmm_low_rate_total_count": 179,
        "lineup_scope": "DMM 1円パチ 중 로컬 수동 후보",
    },
    "3": {
        "store_id": "arrow_namba_hips",
        "name": "ARROW namBa HIPS",
        "rental_rate_label": "1円パチ (1円/1玉)",
        "rental_rate": 1.0,
        "source_url": "https://p-town.dmm.com/shops/osaka/7579",
        "dmm_low_rate_total_count": 136,
        "lineup_scope": "DMM 1円パチ 중 로컬 수동 후보",
    },
}

STORE_SHORT_LABELS = {
    "rakuen_namba": "라쿠엔",
    "123_namba": "123",
    "arrow_namba_hips": "HIPS",
}

STORE_ORDER = ("rakuen_namba", "123_namba", "arrow_namba_hips")

ACTIVE_OTHER_SIM_MODEL_IDS = {
    "hokuto_jibo",
    "re_zero_99",
    "re_zero_s2_129",
    "lupin_77_sweet",
    "kabaneri_2",
    "tokyo_ghoul",
}

# Only names in this map become selectable simulator models from the current
# store lineup. Extra reference models may remain in machines.py for spec checks.
MACHINE_NAME_TO_SIM_ID = {
    "PA大海物語5 Withアグネス・ラム": "sea_5_agnes",
    "P大海物語5": "sea_5",
    "P大海物語5スペシャル": "sea_5_special",
    "P大海物語5 ブラック": "sea_5_black_199",
    "PA大海物語5ブラックLT99ver.": "sea_5_black_lt",
    "P大海物語4スペシャルBLACK": "sea_4_special_black",
    "P大海物語4スペシャル": "sea_4_special",
    "PA大海物語4スペシャル Withアグネス・ラム": "sea_4_agnes",
    "Pまわるん大海物語4スペシャル Withアグネス・ラム 119ver.": "mawarun_sea_4_agnes_119",
    "新世紀エヴァンゲリオン〜未来への咆哮〜": "eva_15_roar",
    "P新世紀エヴァンゲリオン〜未来への咆哮〜PREMIUM MODEL": "eva_15_premium",
    "P新世紀エヴァンゲリオン〜未来への咆哮〜SPECIAL EDITION": "eva_15_special_199",
    "ぱちんこ シン・エヴァンゲリオン PREMIUM MODEL": "shin_eva_premium_99",
    "ぱちんこ シン・エヴァンゲリオン Type レイ": "shin_eva_type_rei",
    "ぱちんこ シン・エヴァンゲリオン 129 LT ver.": "shin_eva_129_lt",
    "e新世紀エヴァンゲリオン ～はじまりの記憶～": "eva_beginning",
    "P Re:ゼロから始める異世界生活 鬼がかり 99ver.": "re_zero_99",
    "P Re:ゼロから始める異世界生活 season2 129ver.": "re_zero_s2_129",
    "Pルパン三世 銭形からの招待状 77Sweet Ver.": "lupin_77_sweet",
    "e甲鉄城のカバネリ2 咲かせや燦然": "kabaneri_2",
    "e東京喰種": "tokyo_ghoul",
    "デジハネP北斗の拳 慈母": "hokuto_jibo",
}


def store_short_label(store_id: str) -> str:
    return STORE_SHORT_LABELS.get(store_id, store_id)


def build_machine_placements(actual_machines: list[dict]) -> dict:
    placements = {}
    for row in actual_machines:
        sim_id = MACHINE_NAME_TO_SIM_ID.get(row.get("machine_name", ""))
        if not sim_id or sim_id not in MACHINES:
            continue
        placements.setdefault(sim_id, []).append(
            {
                "store_id": row.get("store_id", ""),
                "store_label": store_short_label(row.get("store_id", "")),
                "store_name": row.get("store_name", ""),
                "store_name_ko": row.get("store_name_ko", ""),
                "machine_name": row.get("machine_name", ""),
                "machine_name_ko": row.get("machine_name_ko", ""),
                "rate": row.get("rate", ""),
                "count": int(row.get("machine_count", 0) or 0),
                "checked_at": row.get("checked_at", ""),
            }
        )
    return placements


def placement_summary(sim_id: str, placements: dict) -> str:
    by_store = {
        row["store_id"]: row
        for row in placements.get(sim_id, [])
    }
    parts = []
    for store_id in STORE_ORDER:
        row = by_store.get(store_id)
        label = store_short_label(store_id)
        if row:
            parts.append(f"{label} {row['count']}대/{row['rate']}")
        else:
            parts.append(f"{label} 없음")
    return " / ".join(parts)


def placement_detail(sim_id: str, placements: dict) -> list[dict]:
    rows = placements.get(sim_id, [])
    return sorted(rows, key=lambda row: STORE_ORDER.index(row["store_id"]) if row["store_id"] in STORE_ORDER else 99)


def store_contexts_for_machine(sim_id: str, include_missing: bool = False) -> list[dict]:
    """Return per-store simulator context for one machine id.

    The returned rows keep objective store/rate/count data together so runtime
    comparison code does not need to infer 1円 vs 1.111円 handling from names.
    """
    contexts = []
    installed_rows = [
        row
        for store in STORE_INVENTORY.values()
        for row in store.get("machines", [])
        if row.get("id") == sim_id
    ]
    shared_placement_summary = (
        installed_rows[0].get("placement_summary", "") if installed_rows else ""
    )
    for choice in sorted(STORE_INVENTORY.keys(), key=int):
        store = STORE_INVENTORY[choice]
        machine_row = next(
            (row for row in store.get("machines", []) if row.get("id") == sim_id),
            None,
        )
        if not machine_row and not include_missing:
            continue

        contexts.append(
            {
                "choice": choice,
                "store_id": store.get("store_id", ""),
                "store_name": store.get("name", ""),
                "store_short_label": store_short_label(store.get("store_id", "")),
                "rental_rate_label": store.get("rental_rate_label", ""),
                "rental_rate": store.get("rental_rate", 0.0),
                "source_url": store.get("source_url", ""),
                "installed": machine_row is not None,
                "machine": machine_row,
                "count": int(machine_row.get("count", 0) or 0) if machine_row else 0,
                "rate": machine_row.get("rate", "") if machine_row else "",
                "border_spins_per_1000yen": (
                    machine_row.get("border_spins_per_1000yen") if machine_row else None
                ),
                "border_unit": machine_row.get("border_unit") if machine_row else None,
                "border_confidence": machine_row.get("border_confidence") if machine_row else None,
                "border_source": machine_row.get("border_source") if machine_row else None,
                "placement_summary": (
                    machine_row.get("placement_summary") if machine_row else shared_placement_summary
                ),
                "placement_detail": machine_row.get("placement_detail") if machine_row else [],
                "installed_full_name_ja": (
                    machine_row.get("source_machine_name") if machine_row else MACHINES[sim_id].name_ja
                ),
                "installed_full_name_ko": (
                    machine_row.get("machine_name_ko") if machine_row else MACHINES[sim_id].name_ko
                ),
            }
        )
    return contexts


def is_umi_family(machine_name: str) -> bool:
    return any(token in machine_name for token in ("海物語", "大海", "スーパー海", "新海", "ギンギラ"))


def is_eva_family(machine_name: str) -> bool:
    return "エヴァ" in machine_name or "エヴァンゲリオン" in machine_name


def is_re_zero_family(machine_name: str) -> bool:
    return "Re:ゼロ" in machine_name


def is_lt_machine(row: dict) -> bool:
    return "LT" in row.get("machine_name", "") or "LT" in row.get("rush_type", "") or "LT" in row.get("spec_type", "")


def temporary_category(row: dict) -> str:
    name = row.get("machine_name", "")
    spec = row.get("spec_type", "")
    probability = row.get("initial_probability", "")
    if "399" in probability or "396" in probability:
        return "heavy399"
    if "349" in probability:
        return "heavy349"
    if "319" in probability or "299" in probability:
        return "middle319"
    if "199" in probability:
        return "light199"
    if "129" in probability or "119" in probability:
        return "light129"
    if "99" in probability or "89" in probability or "甘" in spec:
        return "ama99"
    if "LT" in name or "lt" in spec.lower():
        return "lt_unknown"
    return "unknown"


def risk_level(category: str, lt: bool, count: int) -> str:
    if category in {"heavy399", "heavy349"}:
        return "high"
    if lt or category in {"middle319"}:
        return "medium_high"
    if category in {"light199", "light129"}:
        return "medium"
    if count <= 1:
        return "medium"
    return "low"


def first_test_budget(category: str, lt: bool) -> int:
    if category in {"heavy399", "heavy349"} or lt:
        return 500
    return 1000


def to_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def border_info(row: dict) -> dict:
    """JSON의 보더값을 시뮬 입력 단위인 1000엔당 회전수로 환산합니다."""
    rate = row.get("rate", "")
    border_1yen = to_float(row.get("border_1yen_per_200"))
    border_1111 = to_float(row.get("border_1_111yen_per_180"))
    border_source = row.get("border_source", "")
    border_note = row.get("border_note", "")
    confidence = row.get("border_confidence")
    known_confidence = confidence if confidence in {"known", "web_verified", "estimated", "converted"} else "known"

    if rate == "1.111yen":
        if border_1111 is not None:
            return {
                "border_spins_per_1000yen": round(border_1111 * 5, 1),
                "border_unit_value": border_1111,
                "border_unit": "200円/180玉",
                "border_source": border_source,
                "border_confidence": known_confidence,
                "border_note": border_note or "1.111円 환산 보더 사용",
            }
        if border_1yen is not None:
            return {
                "border_spins_per_1000yen": round(border_1yen * 4.5, 1),
                "border_unit_value": border_1yen,
                "border_unit": "1円/200玉 fallback",
                "border_source": border_source,
                "border_confidence": "converted" if confidence != "estimated" else "estimated",
                "border_note": border_note or "1円 보더를 1.111円/900玉 기준으로 환산",
            }
    else:
        if border_1yen is not None:
            return {
                "border_spins_per_1000yen": round(border_1yen * 5, 1),
                "border_unit_value": border_1yen,
                "border_unit": "200円/200玉",
                "border_source": border_source,
                "border_confidence": known_confidence,
                "border_note": border_note or "1円 보더 사용",
            }
        if border_1111 is not None:
            return {
                "border_spins_per_1000yen": round(border_1111 * (1000 / 180), 1),
                "border_unit_value": border_1111,
                "border_unit": "1.111円/180玉 fallback",
                "border_source": border_source,
                "border_confidence": "converted" if confidence != "estimated" else "estimated",
                "border_note": border_note or "1.111円 보더를 1円/1000玉 기준으로 역환산",
            }

    return {
        "border_spins_per_1000yen": None,
        "border_unit_value": None,
        "border_unit": None,
        "border_source": border_source,
        "border_confidence": "unknown",
        "border_note": border_note or "보더 미확정. 현장 회전수 기준으로만 판단",
    }


def border_judgement(spins_per_1000yen: int, border_spins_per_1000yen) -> str:
    if border_spins_per_1000yen is None:
        return "보더 미확정"
    margin = spins_per_1000yen - border_spins_per_1000yen
    if margin < -5:
        return "보더 미만"
    if margin < 0:
        return "보더 근처이나 부족"
    if margin < 5:
        return "보더 근처"
    if margin < 15:
        return "보더 상회"
    return "보더 크게 상회"


def build_lineup_row(row: dict, sim_id: str | None, source_url: str) -> dict:
    machine_name = row.get("machine_name", "")
    machine_name_ko = row.get("machine_name_ko", "")
    count = int(row.get("machine_count", 0) or 0)
    category = temporary_category(row)
    lt = is_lt_machine(row)
    supported = bool(sim_id and sim_id in MACHINES)
    machine = MACHINES[sim_id] if supported else None
    border = border_info(row)
    return {
        "machine_name": machine_name,
        "machine_name_ja": machine_name,
        "machine_name_ko": machine_name_ko,
        "display_name_ko": machine_name_ko or machine_name,
        "count": count,
        "rate": row.get("rate", ""),
        "rate_type": row.get("rate", ""),
        "source": "DMMぱちタウン",
        "source_url": source_url,
        "source_checked_at": row.get("checked_at", ""),
        "lineup_category": row.get("category", ""),
        "sim_supported": supported,
        "sim_model_key": sim_id if supported else None,
        "spec_confidence": machine.confidence if machine else None,
        "lineup_confidence": "high" if row.get("source_type") == "dmm" else "medium",
        "temporary_category": category,
        "risk_level": risk_level(category, lt, count),
        "first_test_budget": first_test_budget(category, lt),
        "keep_condition": "1000엔당 80회 이상",
        "quit_condition": "1000엔당 70회 미만",
        "is_eva": is_eva_family(machine_name),
        "is_umi": is_umi_family(machine_name),
        "is_re_zero": is_re_zero_family(machine_name),
        "is_lt": lt,
        "unsupported_reason": None if supported else "machine spec model not implemented",
        "notes": row.get("memo", "") or "DMM 저대여 section 기준",
        **border,
    }


def load_actual_lineup():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        raw = json.load(f)
    return raw.get("machines", []), raw.get("updated_at", "")


def build_store_inventory():
    actual_machines, updated_at = load_actual_lineup()
    placements = build_machine_placements(actual_machines)
    inventory = {}

    for choice, store in STORE_CHOICES.items():
        store_id = store["store_id"]
        source_url = store["source_url"]
        rows = [m for m in actual_machines if m.get("store_id") == store_id]
        supported = []
        unsupported = []
        full_lineup = []

        for row in rows:
            machine_name = row.get("machine_name", "")
            sim_id = MACHINE_NAME_TO_SIM_ID.get(machine_name)
            lineup_row = build_lineup_row(row, sim_id, source_url)
            full_lineup.append(lineup_row)

            if lineup_row["sim_supported"]:
                sim_id = lineup_row["sim_model_key"]
                supported.append(
                    {
                        "id": sim_id,
                        "count": lineup_row["count"],
                        "status": "시뮬 지원",
                        "source_machine_name": machine_name,
                        "checked_at": row.get("checked_at", ""),
                        "placement_summary": placement_summary(sim_id, placements),
                        "placement_detail": placement_detail(sim_id, placements),
                        **lineup_row,
                    }
                )
            else:
                unsupported.append(
                    {
                        "machine_name": machine_name,
                        "machine_name_ko": row.get("machine_name_ko", ""),
                        "count": lineup_row["count"],
                        "reason": "아직 시뮬레이션 모델 없음",
                        **lineup_row,
                    }
                )

        local_count = sum(int(m.get("machine_count", 0) or 0) for m in rows)
        supported_count = sum(m["count"] for m in supported)
        inventory[choice] = {
            **store,
            "verified_date": updated_at or "unknown",
            "lineup": full_lineup,
            "machines": supported,
            "unsupported_machines": unsupported,
            "total_actual_machine_count": local_count,
            "dmm_gap_machine_count": max(0, store["dmm_low_rate_total_count"] - local_count),
            "supported_machine_count": supported_count,
            "unsupported_machine_count": local_count - supported_count,
            "lineup_source": str(DATA_FILE),
        }

    return inventory


STORE_INVENTORY = build_store_inventory()
