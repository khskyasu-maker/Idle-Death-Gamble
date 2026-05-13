from utils import logger, get_data_path, load_json, save_json, get_kst_now


PREFERRED_MACHINE_INFO_FILE = "namba-actual-1yen-lineup.json"


def load_machine_info_source():
    preferred_path = get_data_path(PREFERRED_MACHINE_INFO_FILE)
    preferred_raw = load_json(preferred_path, None)

    if isinstance(preferred_raw, dict) and isinstance(preferred_raw.get("machines"), list):
        logger.info(f"Using machine info source: data/{PREFERRED_MACHINE_INFO_FILE}")
        return preferred_raw, PREFERRED_MACHINE_INFO_FILE

    raise SystemExit(f"data/{PREFERRED_MACHINE_INFO_FILE} is missing or invalid.")


def main():
    logger.info("Performing analysis...")
    generated_at = get_kst_now().strftime("%Y-%m-%d %H:%M:%S KST")

    # Load corrected Namba low-rate machine info first.
    machine_info_raw, machine_info_source = load_machine_info_source()
    machine_info = machine_info_raw.get("machines", [])

    # Calculate store machine totals
    store_machine_totals_dict = {}
    eva_machine_totals_dict = {}

    border_ready_machine_count = 0
    missing_border_machine_count = 0
    missing_border_machines = []

    for m in machine_info:
        count = m.get("machine_count", 0)
        try:
            count = int(count)
        except (TypeError, ValueError):
            count = 0

        # 1. Border logic and conversion
        border_4yen = m.get("border_4yen_per_250")
        border_1yen = m.get("border_1yen_per_200")

        # Convert numeric values or treat as missing
        val_4yen = None
        val_1yen = None

        if border_4yen not in (None, "", "-"):
            try:
                v = float(border_4yen)
                if v > 0:
                    val_4yen = v
            except ValueError:
                pass

        if border_1yen not in (None, "", "-"):
            try:
                v = float(border_1yen)
                if v > 0:
                    val_1yen = v
            except ValueError:
                pass

        # 환산 로직
        if val_1yen is None and val_4yen is not None:
            val_1yen = round(val_4yen * 200 / 250, 1)
            m["border_1yen_per_200"] = val_1yen

        rate = m.get("rate", "")
        if rate == "1.111yen" and val_1yen is not None:
            m["border_1_111yen_per_180"] = round(val_1yen * 180 / 200, 1)

        # 보더 유무 판별 (둘 중 하나라도 숫자 값이 있으면 ready)
        if val_1yen is not None or val_4yen is not None:
            border_ready_machine_count += 1
        else:
            missing_border_machine_count += 1
            if border_4yen in (None, "", "-") and border_1yen in (None, "", "-"):
                missing_reason = "원본 기종 데이터에 보더 값 없음"
            else:
                missing_reason = "보더 값이 숫자 양수로 입력되지 않음"
            missing_border_machines.append(
                {
                    "store_id": m.get("store_id", ""),
                    "store_name": m.get("store_name", ""),
                    "store_name_ko": m.get("store_name_ko", ""),
                    "machine_name": m.get("machine_name", ""),
                    "machine_name_ko": m.get("machine_name_ko", ""),
                    "rate": rate,
                    "machine_count": count,
                    "missing_border_reason": missing_reason,
                    "memo": m.get("memo", ""),
                }
            )

        sid = m.get("store_id")
        if not sid:
            continue

        store_key = f"{sid}:{m.get('rate', '')}"
        if store_key not in store_machine_totals_dict:
            store_machine_totals_dict[store_key] = {
                "store_id": sid,
                "store_name": m.get("store_name", ""),
                "store_name_ko": m.get("store_name_ko", ""),
                "rate": m.get("rate", ""),
                "total_machine_count": 0,
            }
        store_machine_totals_dict[store_key]["total_machine_count"] += count

        category = m.get("category", "")
        if category.startswith("eva"):
            if store_key not in eva_machine_totals_dict:
                eva_machine_totals_dict[store_key] = {
                    "store_id": sid,
                    "store_name": m.get("store_name", ""),
                    "store_name_ko": m.get("store_name_ko", ""),
                    "rate": m.get("rate", ""),
                    "total_machine_count": 0,
                }
            eva_machine_totals_dict[store_key]["total_machine_count"] += count

    store_machine_totals = list(store_machine_totals_dict.values())
    eva_machine_totals = list(eva_machine_totals_dict.values())

    latest_data = {
        "generated_at": generated_at,
        "machine_info_source": machine_info_source,
        "machine_info": machine_info,
        "store_machine_totals": store_machine_totals,
        "eva_machine_totals": eva_machine_totals,
        "border_ready_machine_count": border_ready_machine_count,
        "missing_border_machine_count": missing_border_machine_count,
        "missing_border_machines": missing_border_machines,
    }

    save_json(latest_data, get_data_path("latest.json"))
    logger.info("Analysis finished.")


if __name__ == "__main__":
    main()
