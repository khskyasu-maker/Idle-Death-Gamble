RATE_LABEL_KO = {
    "1.111パチ (100円/90玉)": "1.111엔 파칭코 (100엔/90발)",
    "1円パチ (1円/1玉)": "1엔 파칭코 (1엔/1발)",
}


def bilingual_rate_label(label: str) -> str:
    ko = RATE_LABEL_KO.get(label)
    if not ko:
        return label
    return f"{ko} / {label}"


def display_machine_name_ko(machine_name: str, machine_name_ko: str = "") -> str:
    return machine_name_ko or machine_name


def translate_border_unit(unit: str) -> str:
    return (
        unit.replace("円", "엔")
        .replace("玉", "발")
        .replace("fallback", "대체값")
        .replace("data", "데이터")
    )


def format_border_summary(m_info: dict) -> str:
    border = m_info.get("border_spins_per_1000yen")
    if border is None:
        return "보더: 미확정"
    unit = m_info.get("border_unit") or "data"
    confidence = m_info.get("border_confidence", "unknown")
    return f"보더: {border:.1f}회/1000엔 ({translate_border_unit(unit)} / {unit}, {confidence})"


def add_lineup_context(matrix_results, m_info: dict):
    for row in matrix_results:
        row["border_spins_per_1000yen"] = m_info.get("border_spins_per_1000yen")
        row["border_unit"] = m_info.get("border_unit")
        row["border_confidence"] = m_info.get("border_confidence")
        row["border_source"] = m_info.get("border_source")
        row["placement_summary"] = m_info.get("placement_summary")
        row["placement_detail"] = m_info.get("placement_detail")
        row["installed_full_name_ja"] = m_info.get("source_machine_name")
        row["installed_full_name_ko"] = m_info.get("machine_name_ko")


def add_single_result_context(result: dict, m_info: dict):
    result["border_spins_per_1000yen"] = m_info.get("border_spins_per_1000yen")
    result["placement_summary"] = m_info.get("placement_summary")
    result["placement_detail"] = m_info.get("placement_detail")
    result["installed_full_name_ja"] = m_info.get("source_machine_name")
    result["installed_full_name_ko"] = m_info.get("machine_name_ko")


def add_rotation_estimate_context(matrix_results, estimate):
    for row in matrix_results:
        row["rotation_basis"] = estimate.input_basis
        row["rotation_label"] = estimate.source_label
        row["border_margin"] = estimate.border_margin
