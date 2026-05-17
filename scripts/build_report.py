import json
from html import escape

from utils import logger, get_data_path, get_docs_path, load_json, write_text, save_json
from term_notes import annotate_japanese_terms, term_glossary


def text(value):
    return "" if value is None else str(value)


def note_terms(value):
    return annotate_japanese_terms(text(value))


def has_value(value):
    return value not in (None, "", "-")


def border_cells(machine):
    b_1yen = machine.get("border_1yen_per_200")
    b_1_111yen = machine.get("border_1_111yen_per_180")
    rate = machine.get("rate", "")

    disp_1yen = text(b_1yen) if has_value(b_1yen) else "-"
    disp_1_111yen = text(b_1_111yen) if has_value(b_1_111yen) else "-"
    judgment = "-"

    if rate == "1yen" and has_value(b_1yen):
        judgment = f"200玉당 {text(b_1yen)}회 이상"
    elif rate == "1.111yen" and has_value(b_1_111yen):
        judgment = f"180玉당 {text(b_1_111yen)}회 이상"

    return disp_1yen, disp_1_111yen, judgment


def int_count(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def probability_denominator(machine):
    probability = text(machine.get("initial_probability", ""))
    if not probability.startswith("1/"):
        return None

    try:
        return float(probability.split("/", 1)[1])
    except ValueError:
        return None


def is_eva_machine(machine):
    category = text(machine.get("category", ""))
    machine_name = text(machine.get("machine_name", ""))
    machine_name_ko = text(machine.get("machine_name_ko", ""))
    return category == "eva" or "エヴァ" in machine_name or "에반게리온" in machine_name_ko


def is_umi_machine(machine):
    category = text(machine.get("category", ""))
    machine_name = text(machine.get("machine_name", ""))
    machine_name_ko = text(machine.get("machine_name_ko", ""))
    return category == "daiumi" or "大海物語" in machine_name or "대해물어" in machine_name_ko


def is_ama_like_machine(machine):
    spec_type = text(machine.get("spec_type", ""))
    denominator = probability_denominator(machine)
    return "ama" in spec_type or (denominator is not None and denominator <= 119.9)


def has_rate_border(machine):
    return border_cells(machine)[2] != "-"


def onsite_unit_label(rate):
    if rate == "1.111yen":
        return "180玉"
    if rate == "1yen":
        return "200玉"
    return "-"


def grouped_by_store(machines):
    grouped = {}
    for machine in machines:
        store_id = machine.get("store_id", "")
        if store_id not in grouped:
            grouped[store_id] = []
        grouped[store_id].append(machine)
    return grouped


def store_quick_stats(machines):
    rows = []
    for store_id, store_machines in grouped_by_store(machines).items():
        first = store_machines[0]
        total = sum(int_count(m.get("machine_count")) for m in store_machines)
        border_machine_count = sum(
            int_count(m.get("machine_count")) for m in store_machines if has_rate_border(m)
        )
        rows.append(
            {
                "store_id": store_id,
                "store_name": first.get("store_name", ""),
                "store_name_ko": first.get("store_name_ko", ""),
                "rate": first.get("rate", ""),
                "onsite_unit": onsite_unit_label(first.get("rate", "")),
                "entry_count": len(store_machines),
                "total_machine_count": total,
                "eva_machine_count": sum(
                    int_count(m.get("machine_count"))
                    for m in store_machines
                    if is_eva_machine(m)
                ),
                "daiumi_machine_count": sum(
                    int_count(m.get("machine_count"))
                    for m in store_machines
                    if is_umi_machine(m)
                ),
                "other_machine_count": sum(
                    int_count(m.get("machine_count"))
                    for m in store_machines
                    if text(m.get("category", "")) == "other"
                ),
                "ama_like_machine_count": sum(
                    int_count(m.get("machine_count"))
                    for m in store_machines
                    if is_ama_like_machine(m)
                ),
                "border_entry_count": sum(1 for m in store_machines if has_rate_border(m)),
                "border_machine_count": border_machine_count,
                "missing_border_machine_count": total - border_machine_count,
            }
        )
    return rows


def compact_machine_row(machine):
    _, _, judgment = border_cells(machine)
    return {
        "store_id": machine.get("store_id", ""),
        "store_name": machine.get("store_name", ""),
        "store_name_ko": machine.get("store_name_ko", ""),
        "rate": machine.get("rate", ""),
        "machine_name": machine.get("machine_name", ""),
        "machine_name_ko": machine.get("machine_name_ko", ""),
        "initial_probability": machine.get("initial_probability", ""),
        "machine_count": int_count(machine.get("machine_count")),
        "onsite_unit": onsite_unit_label(machine.get("rate", "")),
        "onsite_judgment": judgment,
        "checked_at": machine.get("checked_at", ""),
    }


def top_count_machines_by_store(machines, limit=5):
    rows = []
    for store_machines in grouped_by_store(machines).values():
        sorted_rows = sorted(
            store_machines,
            key=lambda m: (-int_count(m.get("machine_count")), m.get("machine_name", "")),
        )
        rows.extend(compact_machine_row(m) for m in sorted_rows[:limit])
    return rows


def border_ready_machines_by_count(machines, limit=15):
    rows = [m for m in machines if has_rate_border(m)]
    rows = sorted(
        rows,
        key=lambda m: (-int_count(m.get("machine_count")), m.get("store_id", ""), m.get("machine_name", "")),
    )
    return [compact_machine_row(m) for m in rows[:limit]]


def missing_border_machines_by_count(machines):
    rows = [m for m in machines if not has_rate_border(m)]
    rows = sorted(
        rows,
        key=lambda m: (-int_count(m.get("machine_count")), m.get("store_id", ""), m.get("machine_name", "")),
    )
    return [compact_machine_row(m) for m in rows]


def glossary_items(latest):
    return latest.get("term_glossary") or term_glossary()


def build_markdown(latest):
    md = "# 난바 1엔/저대여 기종 정보\n\n"
    md += f"**생성 시각:** {latest.get('generated_at', 'Unknown')}\n\n"
    if latest.get("machine_info_source"):
        md += f"**기종 정보 원본:** `data/{latest.get('machine_info_source')}`\n\n"

    machines = latest.get("machine_info", [])
    store_machine_totals = latest.get("store_machine_totals", [])
    category_machine_totals = latest.get("category_machine_totals", [])
    border_ready_count = latest.get("border_ready_machine_count", 0)
    missing_border_count = latest.get("missing_border_machine_count", 0)

    if not machines:
        return md + "수동 입력 기종 정보가 없습니다.\n"

    md += f"**기종 등록 수:** {len(machines)}건\n\n"
    md += f"**보더 등록 기종:** {border_ready_count}건\n\n"
    md += f"**보더 미입력 기종:** {missing_border_count}건\n\n"
    md += "- [현장 압축 요약 보기](#quick-summary)\n"
    md += "- [보더라인 참고표 보기](#border-table)\n"
    md += "- [보더 미입력 기종 보기](#missing-border-table)\n"
    md += "- [AI 컨텍스트](ai-context.md)\n"
    md += "- [시뮬레이터 AI 컨텍스트](simulator-ai-context.md)\n"
    md += "- [현장 입력 템플릿](onsite-input-template.md)\n\n"

    # 1. 점포별 전체 1엔 후보 총합
    md += "## 1. 점포별 전체 1엔 후보 총합\n\n"
    summary_headers = [
        "점포 ID",
        "일본어 점포명",
        "한국어 점포명",
        "레이트",
        "전체 후보 총 대수",
    ]
    md += "| " + " | ".join(summary_headers) + " |\n"
    md += "| " + " | ".join(["---", "---", "---", "---", "---:"]) + " |\n"

    for data in store_machine_totals:
        row = [
            f"`{data.get('store_id', '')}`",
            f"`{data.get('store_name', '')}`",
            data.get("store_name_ko", ""),
            f"`{data.get('rate', '')}`",
            f"**{data.get('total_machine_count', 0)}대**",
        ]
        md += "| " + " | ".join(row) + " |\n"

    md += "\n---\n\n"

    # 2. 점포별 3분류 총합
    md += "## 2. 점포별 3분류 총합\n\n"
    category_headers = [
        "점포 ID",
        "일본어 점포명",
        "한국어 점포명",
        "레이트",
        "에바",
        "대해물어",
        "기타",
        "전체",
    ]
    md += "| " + " | ".join(category_headers) + " |\n"
    md += "| " + " | ".join(["---", "---", "---", "---", "---:", "---:", "---:", "---:"]) + " |\n"

    for data in category_machine_totals:
        row = [
            f"`{data.get('store_id', '')}`",
            f"`{data.get('store_name', '')}`",
            data.get("store_name_ko", ""),
            f"`{data.get('rate', '')}`",
            str(data.get("eva_machine_count", 0)),
            str(data.get("daiumi_machine_count", 0)),
            str(data.get("other_machine_count", 0)),
            f"**{data.get('total_machine_count', 0)}대**",
        ]
        md += "| " + " | ".join(row) + " |\n"

    md += "\n---\n\n"

    # 3. 현장 압축 요약
    md += '<h2 id="quick-summary">3. 현장 압축 요약</h2>\n\n'
    md += "방문 순위가 아니라, 현장에서 빠르게 대조하기 위한 객관 요약입니다.\n\n"

    quick_headers = [
        "점포",
        "레이트",
        "현장 회전 단위",
        "전체 대수",
        "에바",
        "대해물어",
        "기타",
        "1/99·감데지",
        "보더 입력 대수",
        "보더 미입력 대수",
    ]
    md += "| " + " | ".join(quick_headers) + " |\n"
    md += "| " + " | ".join(["---", "---", "---", "---:", "---:", "---:", "---:", "---:", "---:", "---:"]) + " |\n"
    for row_data in store_quick_stats(machines):
        row = [
            f"{row_data.get('store_name_ko', '')} (`{row_data.get('store_name', '')}`)",
            f"`{row_data.get('rate', '')}`",
            row_data.get("onsite_unit", "-"),
            str(row_data.get("total_machine_count", 0)),
            str(row_data.get("eva_machine_count", 0)),
            str(row_data.get("daiumi_machine_count", 0)),
            str(row_data.get("other_machine_count", 0)),
            str(row_data.get("ama_like_machine_count", 0)),
            f"{row_data.get('border_machine_count', 0)}대 / {row_data.get('border_entry_count', 0)}종",
            str(row_data.get("missing_border_machine_count", 0)),
        ]
        md += "| " + " | ".join(row) + " |\n"

    md += "\n### 3-1. 점포별 대수순 확인 후보\n\n"
    count_headers = ["점포", "기종명", "확률대", "대수", "현장 기준"]
    md += "| " + " | ".join(count_headers) + " |\n"
    md += "| " + " | ".join(["---", "---", "---", "---:", "---"]) + " |\n"
    for row_data in top_count_machines_by_store(machines):
        row = [
            row_data.get("store_name_ko", ""),
            f"`{row_data.get('machine_name', '')}`",
            f"`{row_data.get('initial_probability', '')}`",
            str(row_data.get("machine_count", 0)),
            row_data.get("onsite_judgment", "-"),
        ]
        md += "| " + " | ".join(row) + " |\n"

    md += "\n### 3-2. 보더 확인 가능 기종 대수순\n\n"
    md += "| " + " | ".join(count_headers) + " |\n"
    md += "| " + " | ".join(["---", "---", "---", "---:", "---"]) + " |\n"
    for row_data in border_ready_machines_by_count(machines):
        row = [
            row_data.get("store_name_ko", ""),
            f"`{row_data.get('machine_name', '')}`",
            f"`{row_data.get('initial_probability', '')}`",
            str(row_data.get("machine_count", 0)),
            row_data.get("onsite_judgment", "-"),
        ]
        md += "| " + " | ".join(row) + " |\n"

    md += "\n### 3-3. 보더 미입력 기종 대수순\n\n"
    md += "| " + " | ".join(["점포", "기종명", "확률대", "대수", "현장 단위"]) + " |\n"
    md += "| " + " | ".join(["---", "---", "---", "---:", "---"]) + " |\n"
    for row_data in missing_border_machines_by_count(machines):
        row = [
            row_data.get("store_name_ko", ""),
            f"`{row_data.get('machine_name', '')}`",
            f"`{row_data.get('initial_probability', '')}`",
            str(row_data.get("machine_count", 0)),
            row_data.get("onsite_unit", "-"),
        ]
        md += "| " + " | ".join(row) + " |\n"

    md += "\n---\n\n"

    # 4. 기종 상세표
    md += "## 4. 기종 상세표\n\n"
    headers = [
        "점포명",
        "한국어 점포명",
        "레이트",
        "일본어 기종명",
        "한국어 기종명",
        "분류",
        "스펙 타입",
        "확률대",
        "대수",
        "1円 200玉 보더",
        "1.111円 180玉 보더",
        "현장 판단 기준",
        "설치 출처",
        "스펙 출처",
        "확인일",
        "메모",
    ]
    md += "| " + " | ".join(headers) + " |\n"
    md += "| " + " | ".join(["---"] * len(headers)) + " |\n"

    for m in machines:
        disp_1yen, disp_1_111yen, judgment = border_cells(m)
        row = [
            f"`{m.get('store_name', '')}`",
            m.get("store_name_ko", ""),
            f"`{m.get('rate', '')}`",
            f"`{m.get('machine_name', '')}`",
            m.get("machine_name_ko", ""),
            m.get("category", ""),
            m.get("spec_type", ""),
            f"`{m.get('initial_probability', '')}`",
            str(m.get("machine_count", 0)),
            disp_1yen,
            disp_1_111yen,
            judgment,
            m.get("install_source", m.get("source_type", "")),
            m.get("spec_source", ""),
            m.get("checked_at", ""),
            m.get("memo", ""),
        ]
        md += "| " + " | ".join(row) + " |\n"

    md += "\n---\n\n"

    # 5. 보더라인 참고표
    md += '<h2 id="border-table">보더라인 참고표</h2>\n\n'
    md += "楽園なんば店의 1.111円은 200円=180玉 기준입니다. 일반 1円의 200円=200玉 기준과 다르므로, 라쿠엔은 1.111円 환산 보더를 기준으로 확인하세요.\n\n"
    border_headers = [
        "점포명",
        "한국어 점포명",
        "레이트",
        "일본어 기종명",
        "한국어 기종명",
        "확률대",
        "대수",
        "1円 200玉 보더",
        "1.111円 180玉 보더",
        "현장 판단 기준",
        "보더 출처",
        "메모",
    ]
    md += "| " + " | ".join(border_headers) + " |\n"
    md += "| " + " | ".join(["---"] * len(border_headers)) + " |\n"

    for m in machines:
        rate = m.get("rate", "")
        disp_1yen, disp_1_111yen, judgment = border_cells(m)
        if rate == "1.111yen" and disp_1_111yen != "-":
            disp_1_111yen = f"**{disp_1_111yen}**"

        row = [
            f"`{m.get('store_name', '')}`",
            m.get("store_name_ko", ""),
            f"`{rate}`",
            f"`{m.get('machine_name', '')}`",
            m.get("machine_name_ko", ""),
            f"`{m.get('initial_probability', '')}`",
            str(m.get("machine_count", 0)),
            disp_1yen,
            disp_1_111yen,
            judgment,
            m.get("border_source", ""),
            m.get("border_note", m.get("memo", "")),
        ]
        md += "| " + " | ".join(row) + " |\n"

    md += "\n> **회전율 참고 기준**입니다.\n\n"
    md += "---\n\n"

    # 6. 보더라인 미입력 기종
    md += '<h2 id="missing-border-table">보더라인 미입력 기종</h2>\n\n'
    missing_border_machines = latest.get("missing_border_machines", [])
    if not missing_border_machines:
        md += "보더라인 미입력 기종이 없습니다.\n"
    else:
        missing_headers = [
            "점포명",
            "한국어 점포명",
            "일본어 기종명",
            "한국어 기종명",
            "레이트",
            "대수",
            "미입력 사유",
            "메모",
        ]
        md += "| " + " | ".join(missing_headers) + " |\n"
        md += "| " + " | ".join(["---"] * len(missing_headers)) + " |\n"
        for m in missing_border_machines:
            row = [
                f"`{m.get('store_name', '')}`",
                m.get("store_name_ko", ""),
                f"`{m.get('machine_name', '')}`",
                m.get("machine_name_ko", ""),
                f"`{m.get('rate', '')}`",
                str(m.get("machine_count", 0)),
                m.get("missing_border_reason", "-"),
                m.get("memo", ""),
            ]
            md += "| " + " | ".join(row) + " |\n"

    md += "\n---\n\n"
    md += "## 7. 현장 체크리스트\n\n"
    checklist_items = onsite_checklist_items()
    for item in checklist_items:
        md += f"- {item}\n"

    md += "\n---\n\n"
    md += "## 8. 공개 웹 정보원 메모\n\n"
    source_headers = ["구분", "확인처", "웹에서 확인 가능한 정보", "사용 기준"]
    md += "| " + " | ".join(source_headers) + " |\n"
    md += "| " + " | ".join(["---"] * len(source_headers)) + " |\n"
    for source in public_web_source_notes():
        row = [
            source["category"],
            source["name"],
            source["available_info"],
            source["usage"],
        ]
        md += "| " + " | ".join(row) + " |\n"

    md += "\n## 9. 관리 범위 메모\n\n"
    for item in focus_scope_notes():
        md += f"- {item}\n"

    return md


def onsite_checklist_items():
    return [
        "점포 입장 전 공개 페이지의 레이트와 설치 기종이 현장 표기와 같은지 확인",
        "1円은 200玉 단위, 1.111円은 180玉 단위로 실제 회전수를 기록",
        "첫 1,000円 또는 200円 단위 회전수가 보더 기준에 크게 못 미치면 다른 후보 확인",
        "기종명 뒤의 버전명, LT, 129ver, PREMIUM MODEL 여부를 현장 표기와 대조",
        "앱 전용 台番号별 大当り, 総回転, 差玉, スランプグラフ는 GitHub에 기록하지 않음",
        "개인 예산, 시간, 이동 동선 판단은 공개 리포트가 아니라 로컬 메모나 대화에서만 처리",
    ]


def public_web_source_notes():
    return [
        {
            "category": "공식/준공식 점포",
            "name": "P-WORLD",
            "available_info": "점포 주소, 영업시간, 레이트, 설치 기종, 설비, 일부 점포의 공지",
            "usage": "점포 URL과 레이트 확인에 사용. 台番号별 데이터 수집에는 사용하지 않음",
        },
        {
            "category": "공식/준공식 점포",
            "name": "DMMぱちタウン",
            "available_info": "점포 기본정보, 설치 기종, 기종 스펙, 일부 보더 정보",
            "usage": "설치 기종과 보더 출처 확인에 사용. 앱 전용 데이터는 공개 저장소에 넣지 않음",
        },
        {
            "category": "기종 보더",
            "name": "なな徹 / Pガブ / ちょんぼりすた",
            "available_info": "기종 스펙, 4円 보더, 1円 보더, 도입일, 일부 연출 정보",
            "usage": "출처가 확인된 보더만 수동 입력. 출처 불명 값은 입력하지 않음",
        },
        {
            "category": "커뮤니티",
            "name": "みんパチ",
            "available_info": "점포 후기, 설비, 환전 관련 단서,旧イベント日 관련 사용자 정보",
            "usage": "비공식 보조 참고만 가능. 동적 판단 데이터로 저장하지 않음",
        },
        {
            "category": "한국어 웹",
            "name": "파칭코사이트인포 등 공개 글",
            "available_info": "한국어 점포 소개, 리뉴얼/영업 관련 설명",
            "usage": "한국어 설명 보조 참고. 최신 설치 대수는 공식 점포 페이지로 재확인",
        },
    ]


def focus_scope_notes():
    return [
        "현재 공개 리포트의 중심 범위는 123難波店, 楽園なんば店, ARROW namBa HIPS입니다.",
        "라쿠엔은 1.111円パチ(200円=180玉), 123 난바와 HIPS는 1円パチ 기준으로 구분합니다.",
        "다른 점포는 필요할 때 별도 데이터로 추가하고, 기본 리포트에는 난바권 3개 점포 정보만 유지합니다.",
    ]


def unique_list(values):
    seen = set()
    rows = []
    for value in values:
        if value in (None, ""):
            continue
        value = str(value)
        if value in seen:
            continue
        seen.add(value)
        rows.append(value)
    return rows


def family_tags(machine):
    tags = []
    category = text(machine.get("category", ""))
    spec_type = text(machine.get("spec_type", ""))
    rush_type = text(machine.get("rush_type", ""))
    machine_name = text(machine.get("machine_name", ""))

    if is_eva_machine(machine):
        tags.append("eva")
    if is_umi_machine(machine):
        tags.append("daiumi")
    if "Re:ゼロ" in machine_name:
        tags.append("re_zero")
    if "北斗" in machine_name:
        tags.append("hokuto")
    if is_ama_like_machine(machine):
        tags.append("ama_like")
    if "middle" in spec_type:
        tags.append("middle")
    if "LT" in machine_name or "lt" in spec_type.lower() or "LT" in rush_type:
        tags.append("lt")
    if "high_variance" in category or "399" in text(machine.get("initial_probability", "")):
        tags.append("high_variance")

    return unique_list(tags)


def machine_aliases(machine):
    name_ja = text(machine.get("machine_name", ""))
    name_ko = text(machine.get("machine_name_ko", ""))
    aliases = [name_ja, name_ko]

    if is_eva_machine(machine):
        aliases.extend(["에바", "エヴァ", "eva"])
    if "シン・エヴァ" in name_ja or "신 에반게리온" in name_ko:
        aliases.extend(["신에바", "シンエヴァ", "shin_eva"])
    if "未来への咆哮" in name_ja or "미래로의 포효" in name_ko:
        aliases.extend(["에바15", "エヴァ15", "eva15"])
    if "PREMIUM MODEL" in name_ja:
        aliases.extend(["프리미엄", "premium"])
    if "SPECIAL EDITION" in name_ja:
        aliases.extend(["스페셜", "special"])
    if "Type レイ" in name_ja:
        aliases.extend(["레이", "type_rei"])
    if is_umi_machine(machine):
        aliases.extend(["대해물어", "大海物語", "daiumi"])
    if "大海物語5" in name_ja:
        aliases.extend(["대해5", "大海5"])
    if "沖縄" in name_ja:
        aliases.extend(["오키나와", "沖海"])
    if "Re:ゼロ" in name_ja:
        aliases.extend(["리제로", "rezero"])
    if "北斗" in name_ja:
        aliases.extend(["북두", "hokuto"])

    return unique_list(aliases)[:12]


def source_summary(machine):
    return {
        "install_source": machine.get("install_source", machine.get("source_type", "")),
        "spec_source": machine.get("spec_source", ""),
        "border_source": machine.get("border_source", ""),
        "spec_source_url": machine.get("spec_source_url", ""),
        "border_reference_url": machine.get("border_reference_url", ""),
        "checked_at": machine.get("checked_at", ""),
    }


def checked_at_summary(machines):
    dates = sorted(unique_list(m.get("checked_at", "") for m in machines))
    return {
        "earliest_checked_at": dates[0] if dates else "",
        "latest_checked_at": dates[-1] if dates else "",
        "checked_dates": dates,
    }


def ai_compact_machine_row(machine):
    _, _, judgment = border_cells(machine)
    return {
        "store_id": machine.get("store_id", ""),
        "store_name": machine.get("store_name", ""),
        "store_name_ko": machine.get("store_name_ko", ""),
        "rate": machine.get("rate", ""),
        "onsite_unit": onsite_unit_label(machine.get("rate", "")),
        "machine_name": machine.get("machine_name", ""),
        "machine_name_ko": machine.get("machine_name_ko", ""),
        "aliases": machine_aliases(machine),
        "tags": family_tags(machine),
        "category": machine.get("category", ""),
        "spec_type": machine.get("spec_type", ""),
        "rush_type": machine.get("rush_type", ""),
        "initial_probability": machine.get("initial_probability", ""),
        "machine_count": int_count(machine.get("machine_count")),
        "border_spins_per_1000yen": machine.get("border_spins_per_1000yen"),
        "border_unit": machine.get("border_unit"),
        "border_unit_value": machine.get("border_unit_value"),
        "border_confidence": machine.get("border_confidence", ""),
        "onsite_judgment": judgment,
        "source": source_summary(machine),
        "memo": machine.get("memo", ""),
    }


def ai_compact_machines(machines):
    store_order = {
        "rakuen_namba": 1,
        "123_namba": 2,
        "arrow_namba_hips": 3,
    }
    rows = sorted(
        machines,
        key=lambda m: (
            store_order.get(m.get("store_id", ""), 99),
            -int_count(m.get("machine_count")),
            m.get("machine_name", ""),
        ),
    )
    return [ai_compact_machine_row(machine) for machine in rows]


def onsite_observation_template():
    return {
        "store_id": "",
        "store_name_seen": "",
        "rate_seen": "1yen or 1.111yen",
        "machine_name_seen": "",
        "machine_name_matches_report": None,
        "empty_seat_count_seen": None,
        "observed_spins_per_1000yen": None,
        "observed_spins_by_unit": "",
        "onsite_unit": "200玉 or 180玉",
        "version_markers_seen": "",
        "public_lineup_mismatch": "",
        "private_note_location": "Keep personal budget/time/movement notes outside public docs.",
    }


def build_simulator_context():
    return {
        "purpose": "Public AI-readable guide for interpreting local pachinko-sim output without publishing personal trip decisions.",
        "public_safe_to_commit": [
            "simulator purpose, assumptions, and metric definitions",
            "reproducible local commands",
            "fixed public machine specs and store/rate lineup context",
            "blank result-sharing template for conversation use",
        ],
        "do_not_commit": [
            "per-run Monte Carlo result tables or CSV files",
            "visit rankings, go-here-today instructions, or final decisions",
            "personal movement, lodging, booking, passport, or spending records",
            "screenshots or app/member-only 台番号별 data",
        ],
        "default_assumptions": {
            "exchange_rate_yen_per_ball": 0.89,
            "spin_rate_cases_per_1000yen": [50, 60, 70, 80, 90, 100],
            "budget_cases_yen": [5000, 10000, 15000, 20000],
            "profile_budget_cases_yen": [1000, 5000, 10000, 15000, 20000],
            "default_strategy": "no_rule",
            "default_session_policy": "fixed_spin_cap",
            "start_variance": True,
            "time_model": {
                "launch_balls_per_minute": 100,
                "normal_seconds_per_start": 6.0,
                "rush_seconds_per_spin": "1.10~1.60 by state",
                "payout_balls_per_minute": 900,
                "reserve_wait": "normal display time beyond active launch time",
            },
        },
        "rate_rules": [
            "1yen uses 200玉 per 200円 and 1000玉 per 1000円.",
            "1.111yen uses 180玉 per 200円 and 900玉 per 1000円.",
            "Compare stores either by identical observed spins per 1000円 or by identical start-gate quality, but do not mix the two.",
        ],
        "local_commands": [
            "cd pachinko-sim && python3 main.py",
            "python3 -m unittest discover -s tests",
            "python3 scripts/validate_data.py",
        ],
        "local_output_metrics": {
            "avg_profit": "Monte Carlo sample average net result in yen; local estimate only.",
            "median_profit": "Median net result in yen; often more useful than average for skewed payout distributions.",
            "worst_10_profit": "Lower 10% percentile value in yen.",
            "cvar10": "Average of the lower 10% tail outcomes.",
            "positive_close_rate": "Share of sampled sessions ending above zero; not a real-world guarantee.",
            "hit_rate": "Share of sampled sessions with at least one 大当り(대당첨); not a next-spin prediction.",
            "rush_entry_rate": "Sampled RUSH entry share.",
            "lt_entry_rate": "Sampled LT entry share; non-LT machines should be interpreted as not applicable.",
            "avg_play_minutes": "Estimated stay/play time, including ball firing, reserve waiting, right-side spins, and hit effects.",
            "avg_cashless_play_minutes": "Estimated time continuing without new cash input through right-side play, hit effects, and reusable held balls.",
        },
        "ai_interpretation_rules": [
            "Treat all simulator outputs as local estimates, not predictions.",
            "Use observed spins per 1000円, rate, remaining time, and budget as conversation-time inputs only.",
            "Past 大当り count, current graph shape, and previous misses do not change the next-spin probability.",
            "Prefer explaining risk and assumptions over ranking stores or machines in public files.",
            "Keep final go/stop decisions in chat or private notes, not in GitHub Pages.",
        ],
        "conversation_result_template": {
            "source": "local pachinko-sim CLI output",
            "store_id": "",
            "store_name_seen": "",
            "rate_seen": "1yen or 1.111yen",
            "machine_name_seen": "",
            "mode": "matrix or budget_matrix or profile or store_comparison",
            "assumptions": {
                "spins_per_1000yen": None,
                "budget_yen": None,
                "exchange_rate_yen_per_ball": 0.89,
                "strategy": "no_rule",
                "session_policy": "fixed_spin_cap",
                "iterations": None,
            },
            "metrics_to_paste_temporarily": {
                "avg_profit": None,
                "median_profit": None,
                "worst_10_profit": None,
                "cvar10": None,
                "positive_close_rate": None,
                "hit_rate": None,
                "rush_entry_rate": None,
                "lt_entry_rate": None,
            },
            "publication_note": "Do not commit filled results if they include personal budget, schedule, or decisions.",
        },
    }


def build_simulator_context_markdown():
    context = build_simulator_context()
    assumptions = context["default_assumptions"]
    md = "# Simulator AI Context\n\n"
    md += "이 파일은 GitHub에서 `pachinko-sim/` 결과를 읽는 AI가 참고할 공개용 해석 규칙입니다.\n"
    md += "실제 실행 결과, 방문 판단, 개인 운영 메모는 공개 파일에 고정하지 않습니다.\n\n"

    md += "## 공개 가능\n\n"
    for item in context["public_safe_to_commit"]:
        md += f"- {item}\n"

    md += "\n## 공개 금지\n\n"
    for item in context["do_not_commit"]:
        md += f"- {item}\n"

    md += "\n## 기본 가정\n\n"
    md += f"- 교환율 기본값: `{assumptions['exchange_rate_yen_per_ball']}`엔/발\n"
    md += f"- 회전수 케이스: `{assumptions['spin_rate_cases_per_1000yen']}`회/1000엔\n"
    md += f"- 예산 케이스: `{assumptions['budget_cases_yen']}`엔\n"
    md += f"- 프로파일 예산 케이스: `{assumptions['profile_budget_cases_yen']}`엔\n"
    md += f"- 기본 전략: `{assumptions['default_strategy']}`\n"
    md += f"- 기본 세션 방식: `{assumptions['default_session_policy']}`\n"
    md += f"- 스타트 입상 변동 반영: `{assumptions['start_variance']}`\n"

    md += "\n## 레이트 규칙\n\n"
    for item in context["rate_rules"]:
        md += f"- {item}\n"

    md += "\n## 로컬 재현 명령\n\n"
    for command in context["local_commands"]:
        md += f"- `{command}`\n"

    md += "\n## 로컬 출력 지표\n\n"
    for key, note in context["local_output_metrics"].items():
        md += f"- `{key}`: {note}\n"

    md += "\n## AI 해석 규칙\n\n"
    for item in context["ai_interpretation_rules"]:
        md += f"- {item}\n"

    md += "\n## 대화용 결과 입력 템플릿\n\n"
    md += "아래 템플릿은 채팅에 임시로 붙여 넣기 위한 형식입니다. 채운 값을 public `docs/`나 `data/`에 저장하지 않습니다.\n\n"
    md += "```json\n"
    md += json.dumps(context["conversation_result_template"], ensure_ascii=False, indent=2)
    md += "\n```\n"
    return md


def build_ai_context(latest):
    machines = latest.get("machine_info", [])
    return {
        "purpose": "AI input data for Namba low-rate pachinko store and machine comparison.",
        "use_for": [
            "store/machine lookup",
            "rate and border cross-checking",
            "onsite observation comparison",
            "conversation-time dynamic analysis",
        ],
        "do_not_use_for": [
            "jackpot prediction",
            "fixed visit ranking in public files",
            "win-rate or profit guarantee",
            "personal trip, booking, passport, lodging, or spending records",
        ],
        "field_notes": {
            "rate": "1yen uses 200玉 per 200円. 1.111yen uses 180玉 per 200円.",
            "border_spins_per_1000yen": "Converted reference rotations per 1000円 for simulator and AI comparison.",
            "onsite_judgment": "Rotation threshold reference only, not a result prediction.",
            "aliases": "Search/display helpers derived from objective machine names.",
            "checked_at": "Manual/public-source check date. Re-check onsite if stale.",
        },
        "data_freshness": {
            "generated_at": latest.get("generated_at", ""),
            **checked_at_summary(machines),
        },
        "category_machine_totals": latest.get("category_machine_totals", []),
        "simulator_context_path": "simulator-ai-context.md",
        "onsite_observation_template": onsite_observation_template(),
    }


def build_ai_context_markdown(latest):
    context = build_ai_context(latest)
    freshness = context["data_freshness"]
    md = "# AI Context\n\n"
    md += "이 파일은 `docs/latest.json`을 AI 대화에 넣을 때 함께 참고하는 짧은 규칙입니다.\n\n"
    md += "## 사용 목적\n\n"
    for item in context["use_for"]:
        md += f"- {item}\n"
    md += "\n## 금지\n\n"
    for item in context["do_not_use_for"]:
        md += f"- {item}\n"
    md += "\n## 핵심 필드\n\n"
    for key, note in context["field_notes"].items():
        md += f"- `{key}`: {note}\n"
    md += "\n## 최신성\n\n"
    md += f"- 생성 시각: {freshness.get('generated_at', '')}\n"
    md += f"- 가장 오래된 확인일: {freshness.get('earliest_checked_at', '')}\n"
    md += f"- 가장 최신 확인일: {freshness.get('latest_checked_at', '')}\n"
    md += "\n## AI 사용 메모\n\n"
    md += "- 공개 JSON에는 객관 데이터만 있습니다.\n"
    md += "- 현장 관찰값은 대화 중 임시 입력으로만 사용하고 공개 파일에 저장하지 않습니다.\n"
    md += "- 라쿠엔 `1.111yen`과 일반 `1yen`의 회전 단위를 반드시 분리합니다.\n"
    md += "- 시뮬레이터 해석 규칙은 `simulator-ai-context.md`를 함께 봅니다.\n"
    return md


def build_onsite_input_template_markdown():
    template = onsite_observation_template()
    md = "# Onsite Input Template\n\n"
    md += "AI에게 현장 관찰값을 전달할 때 쓰는 빈 템플릿입니다. 개인 일정, 예약 정보, 지출 메모는 넣지 않습니다.\n\n"
    md += "```json\n"
    md += json.dumps(template, ensure_ascii=False, indent=2)
    md += "\n"
    md += "```\n"
    return md


def build_html(latest, md_content):
    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pachinko Osaka Report</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; padding: 20px; max-width: 1400px; margin: 0 auto; color: #333; background: #ffffff; }}
        h1, h2, h3 {{ color: #2c3e50; }}
        h1 {{ font-size: 1.8rem; }}
        .meta {{ background: #e9ecef; padding: 10px; border-radius: 5px; margin-bottom: 20px; font-size: 0.9em; }}
        .meta-links a {{ display: inline-block; margin-right: 12px; }}
        .table-wrap {{ overflow-x: auto; margin-bottom: 30px; }}
        table {{ border-collapse: collapse; width: 100%; min-width: 1000px; }}
        th, td {{ border: 1px solid #dee2e6; padding: 8px; text-align: left; vertical-align: top; }}
        th {{ background: #f1f3f5; }}
        td.right {{ text-align: right; }}
        .note-list {{ margin-bottom: 30px; }}
    </style>
</head>
<body>
    <h1>난바 1엔/저대여 기종 정보</h1>

    <div class="meta">
        <p><strong>생성 시각:</strong> {escape(text(latest.get('generated_at', 'Unknown')))}</p>
        <p><strong>기종 정보 원본:</strong> <code>data/{escape(text(latest.get('machine_info_source', '')))}</code></p>
        <p><strong>기종 등록 수:</strong> {escape(text(len(latest.get('machine_info', []))))}건</p>
        <p><strong>보더 등록 기종:</strong> {escape(text(latest.get('border_ready_machine_count', 0)))}건</p>
        <p><strong>보더 미입력 기종:</strong> {escape(text(latest.get('missing_border_machine_count', 0)))}건</p>
        <p class="meta-links">
            <a href="#quick-summary">현장 압축 요약 보기</a>
            <a href="#border-table">보더라인 참고표 보기</a>
            <a href="#missing-border-table">보더 미입력 기종 보기</a>
            <a href="ai-context.md">AI 컨텍스트</a>
            <a href="simulator-ai-context.md">시뮬레이터 AI 컨텍스트</a>
            <a href="onsite-input-template.md">현장 입력 템플릿</a>
        </p>
    </div>

"""
    html += build_machine_data_table_html(latest)
    html += """
</body>
</html>
"""
    return html


def compact_machine_table_html(rows, include_judgment=True):
    if include_judgment:
        final_header = "현장 기준"
    else:
        final_header = "현장 단위"

    html = f"""    <div class="table-wrap">
        <table>
            <thead>
                <tr>
                    <th>점포</th>
                    <th>기종명</th>
                    <th class="right">확률대</th>
                    <th class="right">대수</th>
                    <th>{final_header}</th>
                </tr>
            </thead>
            <tbody>
"""
    for row in rows:
        final_value = row.get("onsite_judgment", "-") if include_judgment else row.get("onsite_unit", "-")
        html += f"""                <tr>
                    <td>{escape(row.get('store_name_ko', ''))}</td>
                    <td><code>{escape(row.get('machine_name', ''))}</code></td>
                    <td class="right"><code>{escape(row.get('initial_probability', ''))}</code></td>
                    <td class="right">{row.get('machine_count', 0)}</td>
                    <td>{escape(final_value)}</td>
                </tr>
"""
    html += """            </tbody>
        </table>
    </div>
"""
    return html


def build_machine_data_table_html(latest):
    machines = latest.get("machine_info", [])
    store_machine_totals = latest.get("store_machine_totals", [])
    category_machine_totals = latest.get("category_machine_totals", [])

    if not machines:
        return "    <p>수동 입력 기종 정보가 없습니다.</p>\n"

    html = "    <h2>1. 점포별 전체 1엔 후보 총합</h2>\n"
    html += """    <div class="table-wrap">
        <table>
            <thead>
                <tr>
                    <th>점포 ID</th>
                    <th>일본어 점포명</th>
                    <th>한국어 점포명</th>
                    <th>레이트</th>
                    <th class="right">전체 후보 총 대수</th>
                </tr>
            </thead>
            <tbody>
"""
    for data in store_machine_totals:
        html += f"""                <tr>
                    <td><code>{escape(str(data.get('store_id', '')))}</code></td>
                    <td><code>{escape(str(data.get('store_name', '')))}</code></td>
                    <td>{escape(str(data.get('store_name_ko', '')))}</td>
                    <td><code>{escape(str(data.get('rate', '')))}</code></td>
                    <td class="right"><strong>{data.get('total_machine_count', 0)}대</strong></td>
                </tr>
"""
    html += """            </tbody>
        </table>
    </div>
"""

    html += "    <h2>2. 점포별 3분류 총합</h2>\n"
    html += """    <div class="table-wrap">
        <table>
            <thead>
                <tr>
                    <th>점포 ID</th>
                    <th>일본어 점포명</th>
                    <th>한국어 점포명</th>
                    <th>레이트</th>
                    <th class="right">에바</th>
                    <th class="right">대해물어</th>
                    <th class="right">기타</th>
                    <th class="right">전체</th>
                </tr>
            </thead>
            <tbody>
"""
    for data in category_machine_totals:
        html += f"""                <tr>
                    <td><code>{escape(str(data.get('store_id', '')))}</code></td>
                    <td><code>{escape(str(data.get('store_name', '')))}</code></td>
                    <td>{escape(str(data.get('store_name_ko', '')))}</td>
                    <td><code>{escape(str(data.get('rate', '')))}</code></td>
                    <td class="right">{data.get('eva_machine_count', 0)}</td>
                    <td class="right">{data.get('daiumi_machine_count', 0)}</td>
                    <td class="right">{data.get('other_machine_count', 0)}</td>
                    <td class="right"><strong>{data.get('total_machine_count', 0)}대</strong></td>
                </tr>
"""
    html += """            </tbody>
        </table>
    </div>
"""

    html += '    <h2 id="quick-summary">3. 현장 압축 요약</h2>\n'
    html += "    <p>방문 순위가 아니라, 현장에서 빠르게 대조하기 위한 객관 요약입니다.</p>\n"
    html += """    <div class="table-wrap">
        <table>
            <thead>
                <tr>
                    <th>점포</th>
                    <th>레이트</th>
                    <th>현장 회전 단위</th>
                    <th class="right">전체 대수</th>
                    <th class="right">에바</th>
                    <th class="right">대해물어</th>
                    <th class="right">기타</th>
                    <th class="right">1/99·감데지</th>
                    <th class="right">보더 입력 대수</th>
                    <th class="right">보더 미입력 대수</th>
                </tr>
            </thead>
            <tbody>
"""
    for row_data in store_quick_stats(machines):
        html += f"""                <tr>
                    <td>{escape(row_data.get('store_name_ko', ''))} (<code>{escape(row_data.get('store_name', ''))}</code>)</td>
                    <td><code>{escape(row_data.get('rate', ''))}</code></td>
                    <td>{escape(row_data.get('onsite_unit', '-'))}</td>
                    <td class="right">{row_data.get('total_machine_count', 0)}</td>
                    <td class="right">{row_data.get('eva_machine_count', 0)}</td>
                    <td class="right">{row_data.get('daiumi_machine_count', 0)}</td>
                    <td class="right">{row_data.get('other_machine_count', 0)}</td>
                    <td class="right">{row_data.get('ama_like_machine_count', 0)}</td>
                    <td class="right">{row_data.get('border_machine_count', 0)}대 / {row_data.get('border_entry_count', 0)}종</td>
                    <td class="right">{row_data.get('missing_border_machine_count', 0)}</td>
                </tr>
"""
    html += """            </tbody>
        </table>
    </div>
"""

    html += "    <h3>3-1. 점포별 대수순 확인 후보</h3>\n"
    html += compact_machine_table_html(top_count_machines_by_store(machines), include_judgment=True)

    html += "    <h3>3-2. 보더 확인 가능 기종 대수순</h3>\n"
    html += compact_machine_table_html(border_ready_machines_by_count(machines), include_judgment=True)

    html += "    <h3>3-3. 보더 미입력 기종 대수순</h3>\n"
    html += compact_machine_table_html(missing_border_machines_by_count(machines), include_judgment=False)

    html += "    <h2>4. 기종 상세표</h2>\n"
    html += """    <div class="table-wrap">
        <table>
            <thead>
                <tr>
                    <th>점포명</th>
                    <th>한국어 점포명</th>
                    <th>레이트</th>
                    <th>일본어 기종명</th>
                    <th>한국어 기종명</th>
                    <th>분류</th>
                    <th>스펙 타입</th>
                    <th class="right">확률대</th>
                    <th class="right">대수</th>
                    <th class="right">1円 200玉 보더</th>
                    <th class="right">1.111円 180玉 보더</th>
                    <th>현장 판단 기준</th>
                    <th>설치 출처</th>
                    <th>스펙 출처</th>
                    <th>확인일</th>
                    <th>메모</th>
                </tr>
            </thead>
            <tbody>
"""
    for m in machines:
        disp_1yen, disp_1_111yen, judgment = border_cells(m)
        html += f"""                <tr>
                    <td><code>{escape(m.get('store_name', ''))}</code></td>
                    <td>{escape(m.get('store_name_ko', ''))}</td>
                    <td><code>{escape(m.get('rate', ''))}</code></td>
                    <td><code>{escape(m.get('machine_name', ''))}</code></td>
                    <td>{escape(m.get('machine_name_ko', ''))}</td>
                    <td>{escape(m.get('category', ''))}</td>
                    <td>{escape(m.get('spec_type', ''))}</td>
                    <td class="right"><code>{escape(m.get('initial_probability', ''))}</code></td>
                    <td class="right">{m.get('machine_count', 0)}</td>
                    <td class="right">{escape(disp_1yen)}</td>
                    <td class="right">{escape(disp_1_111yen)}</td>
                    <td>{escape(judgment)}</td>
                    <td>{escape(m.get('install_source', m.get('source_type', '')))}</td>
                    <td>{escape(m.get('spec_source', ''))}</td>
                    <td>{escape(m.get('checked_at', ''))}</td>
                    <td>{escape(m.get('memo', ''))}</td>
                </tr>
"""
    html += """            </tbody>
        </table>
    </div>
"""

    html += '    <h2 id="border-table">5. 보더라인 참고표</h2>\n'
    html += "    <p>楽園なんば店의 1.111円은 200円=180玉 기준입니다. 일반 1円의 200円=200玉 기준과 다르므로, 라쿠엔은 1.111円 환산 보더를 기준으로 확인하세요.</p>\n"
    html += "    <p><strong>회전율 참고 기준</strong>입니다.</p>\n"
    html += """    <div class="table-wrap">
        <table>
            <thead>
                <tr>
                    <th>점포명</th>
                    <th>한국어 점포명</th>
                    <th>레이트</th>
                    <th>일본어 기종명</th>
                    <th>한국어 기종명</th>
                    <th class="right">확률대</th>
                    <th class="right">대수</th>
                    <th class="right">1円 200玉 보더</th>
                    <th class="right">1.111円 180玉 보더</th>
                    <th>현장 판단 기준</th>
                    <th>보더 출처</th>
                    <th>메모</th>
                </tr>
            </thead>
            <tbody>
"""
    for m in machines:
        rate = m.get("rate", "")
        disp_1yen, disp_1_111yen, judgment = border_cells(m)
        disp_1yen = escape(disp_1yen)
        disp_1_111yen = escape(disp_1_111yen)
        if rate == "1.111yen" and disp_1_111yen != "-":
            disp_1_111yen = f"<strong>{disp_1_111yen}</strong>"

        html += f"""                <tr>
                    <td><code>{escape(m.get('store_name', ''))}</code></td>
                    <td>{escape(m.get('store_name_ko', ''))}</td>
                    <td><code>{escape(rate)}</code></td>
                    <td><code>{escape(m.get('machine_name', ''))}</code></td>
                    <td>{escape(m.get('machine_name_ko', ''))}</td>
                    <td class="right"><code>{escape(m.get('initial_probability', ''))}</code></td>
                    <td class="right">{m.get('machine_count', 0)}</td>
                    <td class="right">{disp_1yen}</td>
                    <td class="right">{disp_1_111yen}</td>
                    <td>{escape(judgment)}</td>
                    <td>{escape(m.get('border_source', ''))}</td>
                    <td>{escape(m.get('border_note', m.get('memo', '')))}</td>
                </tr>
"""
    html += """            </tbody>
        </table>
    </div>
"""

    html += '    <h2 id="missing-border-table">6. 보더라인 미입력 기종</h2>\n'
    missing_border_machines = latest.get("missing_border_machines", [])
    if not missing_border_machines:
        html += "    <p>보더라인 미입력 기종이 없습니다.</p>\n"
    else:
        html += """    <div class="table-wrap">
        <table>
            <thead>
                <tr>
                    <th>점포명</th>
                    <th>한국어 점포명</th>
                    <th>일본어 기종명</th>
                    <th>한국어 기종명</th>
                    <th>레이트</th>
                    <th class="right">대수</th>
                    <th>미입력 사유</th>
                    <th>메모</th>
                </tr>
            </thead>
            <tbody>
"""
        for m in missing_border_machines:
            html += f"""                <tr>
                    <td><code>{escape(m.get('store_name', ''))}</code></td>
                    <td>{escape(m.get('store_name_ko', ''))}</td>
                    <td><code>{escape(m.get('machine_name', ''))}</code></td>
                    <td>{escape(m.get('machine_name_ko', ''))}</td>
                    <td><code>{escape(m.get('rate', ''))}</code></td>
                    <td class="right">{m.get('machine_count', 0)}</td>
                    <td>{escape(m.get('missing_border_reason', '-'))}</td>
                    <td>{escape(m.get('memo', ''))}</td>
                </tr>
"""
        html += """            </tbody>
        </table>
    </div>
"""

    html += "    <h2>7. 현장 체크리스트</h2>\n"
    html += "    <ul class=\"note-list\">\n"
    for item in onsite_checklist_items():
        html += f"        <li>{escape(item)}</li>\n"
    html += "    </ul>\n"

    html += "    <h2>8. 공개 웹 정보원 메모</h2>\n"
    html += """    <div class="table-wrap">
        <table>
            <thead>
                <tr>
                    <th>구분</th>
                    <th>확인처</th>
                    <th>웹에서 확인 가능한 정보</th>
                    <th>사용 기준</th>
                </tr>
            </thead>
            <tbody>
"""
    for source in public_web_source_notes():
        html += f"""                <tr>
                    <td>{escape(source['category'])}</td>
                    <td>{escape(source['name'])}</td>
                    <td>{escape(source['available_info'])}</td>
                    <td>{escape(source['usage'])}</td>
                </tr>
"""
    html += """            </tbody>
        </table>
    </div>
"""

    html += "    <h2>9. 관리 범위 메모</h2>\n"
    html += "    <ul class=\"note-list\">\n"
    for item in focus_scope_notes():
        html += f"        <li>{escape(item)}</li>\n"
    html += "    </ul>\n"

    return html


def build_public_latest(latest):
    machines = latest.get("machine_info", [])
    return {
        "generated_at": latest.get("generated_at", ""),
        "machine_info_source": latest.get("machine_info_source", ""),
        "ai_context": build_ai_context(latest),
        "simulator_context": build_simulator_context(),
        "ai_compact_machines": ai_compact_machines(machines),
        "store_machine_totals": latest.get("store_machine_totals", []),
        "eva_machine_totals": latest.get("eva_machine_totals", []),
        "store_quick_stats": store_quick_stats(machines),
        "high_count_machines_by_store": top_count_machines_by_store(machines),
        "border_ready_machines_by_count": border_ready_machines_by_count(machines),
        "missing_border_machines_by_count": missing_border_machines_by_count(machines),
        "border_ready_machine_count": latest.get("border_ready_machine_count", 0),
        "missing_border_machine_count": latest.get("missing_border_machine_count", 0),
        "missing_border_machines": latest.get("missing_border_machines", []),
        "machine_info": machines,
    }


def main():
    latest = load_json(get_data_path("latest.json"), {})
    if not latest:
        logger.error("latest.json is empty. Aborting report build.")
        return

    md_content = build_markdown(latest).rstrip() + "\n"
    html_content = build_html(latest, md_content)
    ai_context_md = build_ai_context_markdown(latest).rstrip() + "\n"
    simulator_context_md = build_simulator_context_markdown().rstrip() + "\n"
    onsite_template_md = build_onsite_input_template_markdown().rstrip() + "\n"

    write_text(md_content, get_data_path("latest-report.md"))
    write_text(md_content, get_docs_path("latest-report.md"))
    write_text(html_content, get_docs_path("index.html"))
    write_text(ai_context_md, get_docs_path("ai-context.md"))
    write_text(simulator_context_md, get_docs_path("simulator-ai-context.md"))
    write_text(onsite_template_md, get_docs_path("onsite-input-template.md"))
    save_json(build_public_latest(latest), get_docs_path("latest.json"))

    logger.info("Reports successfully built in data/ and docs/")


if __name__ == "__main__":
    main()
