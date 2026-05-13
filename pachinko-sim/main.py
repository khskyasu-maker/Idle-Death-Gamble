import sys
from machines import MACHINES
from stores import STORE_INVENTORY
from stores import store_contexts_for_machine
from simulator import (
    BUDGET_CASES,
    PROFILE_BUDGET_CASES,
    SPIN_RATE_CASES,
    simulate_single,
    simulate_multiple,
    run_budget_matrix,
    run_matrix_simulation,
    run_strategy_matrix,
)
from store_comparison import STORE_COMPARISON_MODES, run_store_comparison
from result import (
    border_label,
    print_single_result,
    print_multiple_result,
    print_matrix_results,
    print_budget_matrix_results,
    print_model_profile_results,
    print_strategy_matrix_results,
    print_store_comparison_results,
    save_matrix_to_csv,
)

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


def get_int_input(prompt: str, min_val: int = None, max_val: int = None, default: int = None) -> int:
    while True:
        try:
            user_input = input(prompt).strip()
            if not user_input and default is not None:
                return default
            val = int(user_input)
            if min_val is not None and val < min_val:
                print(f"경고: 최소 {min_val} 이상이어야 합니다.")
                continue
            if max_val is not None and val > max_val:
                print(f"경고: 최대 {max_val} 이하여야 합니다.")
                continue
            return val
        except ValueError:
            print("경고: 올바른 숫자를 입력해주세요.")


def choose_strategy() -> str:
    print("\n[전략]")
    print("1: 노룰")
    print("2: 기본 손절")
    print("3: 이익 잠금")
    print("4: 공격형")
    strategy_choice = get_int_input("전략을 선택하세요 (1-4) [기본값: 1]: ", 1, 4, 1)
    strategy_map = {
        1: "no_rule",
        2: "basic_stop",
        3: "profit_lock",
        4: "aggressive",
    }
    return strategy_map[strategy_choice]


def choose_session_policy(default: int = 1) -> str:
    print("\n[세션 방식]")
    print("1: 예산 고정 회전수 (예산/1000엔 × 회전율까지만 비교)")
    print("2: 현금+보유구슬 소진 (예산을 쓰고, 당첨 구슬도 재사용)")
    policy_choice = get_int_input(f"세션 방식을 선택하세요 (1-2) [기본값: {default}]: ", 1, 2, default)
    return {
        1: "fixed_spin_cap",
        2: "play_until_budget_and_balls_gone",
    }[policy_choice]


def choose_store_comparison_mode(default: int = 1) -> str:
    print("\n[가게 비교 기준]")
    print("1: 동일 1000엔 회전수 - 각 가게에서 같은 현금 회전수를 실측했다고 가정")
    print("2: 동일 헤소 입상 품질 - 구슬 1발당 입상 확률을 같게 두고 레이트별 회전수 환산")
    mode_choice = get_int_input(f"비교 기준을 선택하세요 (1-2) [기본값: {default}]: ", 1, 2, default)
    return {
        1: "cash_rotation",
        2: "ball_quality",
    }[mode_choice]


def print_spin_rate_guide():
    print("\n[1000엔당 회전수 가이드]")
    print("매우 나쁨: 50회전 / 나쁨: 60회전 / 애매함: 70회전 / 최소 후보: 80회전 / 좋음: 90회전 / 매우 좋음: 100회전")
    print("입력값은 평균 회전수입니다. 실제 세션 회전수는 구슬->헤소 입상 확률로 표본 변동을 반영합니다.")

def main():
    print("=== 오사카 난바 실제 설치기종 1엔 파친코 체감 모의 ===")
    print("본 프로그램은 수익 예측이 아닌, 여행지에서의 실질적인 체감 리스크와 만족도를 비교하기 위한 도구입니다.\n")
    
    # 1. 매장 선택
    print("[1엔/저대여 파친코 매장 선택]")
    store_choices = sorted(STORE_INVENTORY.keys(), key=int)
    for choice in store_choices:
        info = STORE_INVENTORY[choice]
        print(f"{choice}: {info['name']} ({bilingual_rate_label(info['rental_rate_label'])})")
    store_choice = str(
        get_int_input(f"매장을 선택하세요 (1-{len(store_choices)}): ", 1, len(store_choices))
    )
    
    store_info = STORE_INVENTORY[store_choice]
    store_name = store_info["name"]
    rental_rate = store_info["rental_rate"]
    
    # 2. 기종 선택
    print(f"\n[{store_name} 1엔/저대여 설치 라인업]")
    print(
        "라인업 출처: data/namba-actual-1yen-lineup.json | "
        f"시뮬 지원 {store_info['supported_machine_count']}대 / "
        f"로컬 등록 {store_info['total_actual_machine_count']}대 / "
        f"DMM 저대여 전체 {store_info['dmm_low_rate_total_count']}대"
    )
    if store_info["dmm_gap_machine_count"]:
        print(
            f"주의: DMM 전체 대비 로컬 JSON 미등록 가능 대수 "
            f"{store_info['dmm_gap_machine_count']}대가 있습니다. "
            "현재 선택지는 에바/바다/리제로 중심 수동 후보입니다."
        )
    if store_info["unsupported_machine_count"]:
        print(
            f"미지원 모델 {len(store_info['unsupported_machines'])}종 "
            f"({store_info['unsupported_machine_count']}대)은 선택지에서 제외됩니다."
        )

    available_machines = store_info["machines"]
    if not available_machines:
        print("현재 이 점포에는 시뮬레이션 가능한 모델이 없습니다.")
        return

    for idx, m_info in enumerate(available_machines, 1):
        m = MACHINES[m_info["id"]]
        print(
            f"{idx}. {m_info.get('display_name_ko') or m.name_ko} | 대수: {m_info['count']}대 | "
            f"{m_info['status']} | 신뢰도: {m.confidence} | {format_border_summary(m_info)} | "
            f"일본어: {m_info['source_machine_name']} | "
            f"배치: {m_info.get('placement_summary', '-')}"
        )

    if store_info["unsupported_machines"]:
        print("\n[시뮬 미지원 / 현장 관찰 후보]")
        for m_info in store_info["unsupported_machines"]:
            marker = []
            if m_info.get("is_eva"):
                marker.append("에바")
            if m_info.get("is_umi"):
                marker.append("바다")
            if m_info.get("is_re_zero"):
                marker.append("리제로")
            if m_info.get("is_lt"):
                marker.append("LT")
            marker_label = "/".join(marker) if marker else "기타"
            print(
                f"- {display_machine_name_ko(m_info['machine_name'], m_info.get('machine_name_ko', ''))} | {m_info['count']}대 | "
                f"일본어: {m_info['machine_name']} | "
                f"{m_info['temporary_category']} | {marker_label} | "
                f"{format_border_summary(m_info)} | "
                f"첫 테스트 {m_info['first_test_budget']}엔 | "
                f"{m_info['quit_condition']}이면 이동"
            )
        
    machine_idx = get_int_input(f"기종을 선택하세요 (1-{len(available_machines)}): ", 1, len(available_machines))
    selected_machine_info = available_machines[machine_idx - 1]
    selected_machine_id = selected_machine_info["id"]
    machine = MACHINES[selected_machine_id]
    selected_border_spins = selected_machine_info.get("border_spins_per_1000yen")
    
    # 3. 실행 모드
    print("\n[실행 모드]")
    print("1: 단일 시뮬레이션 (1회 방문 체험)")
    print("2: 리스크 평가 테스트 (1000회 반복)")
    print("3: 회전율 매트릭스 (50/60/70/80/90/100회 비교)")
    print("4: 전략 비교 (노룰/손절/이익잠금/공격형)")
    print("5: 예산 비교 (10000/20000/30000/40000/50000엔)")
    print("6: 모델 프로파일/위화감 검증 (1000엔 체감 + 공개 일본값 비교)")
    print("7: 가게별 같은 기종 비교 (라쿠엔/123/HIPS, 레이트 보정)")
    mode = get_int_input("실행 모드를 선택하세요 (1-7): ", 1, 7)
    
    default_exchange_rate = 0.89
    exchange_rate_input = get_int_input(
        "\n교환율을 입력하세요. 0.89엔/발이면 89 입력 [기본값: 89]: ",
        50,
        120,
        int(default_exchange_rate * 100),
    )
    exchange_rate = exchange_rate_input / 100.0
    
    if mode == 3:
        budget = get_int_input("\n예산을 입력하세요 [기본값: 10000]: ", 1000, 200000, 10000)
        iterations = get_int_input("반복 횟수를 입력하세요 [기본값: 5000]: ", 100, 100000, 5000)
        session_policy = choose_session_policy(default=1)
        print(f"\n[매트릭스 모드 실행 중...] 회전율 {SPIN_RATE_CASES} 조건을 비교합니다.")
        matrix_results = run_matrix_simulation(
            machine,
            rental_rate,
            exchange_rate,
            iterations,
            budget=budget,
            strategy="no_rule",
            session_policy=session_policy,
            border_spins_per_1000y=selected_border_spins,
        )
        add_lineup_context(matrix_results, selected_machine_info)
        print_matrix_results(machine, matrix_results, iterations)
        save_csv = get_int_input("CSV에 추가 저장할까요? 1=예, 0=아니오 [기본값: 0]: ", 0, 1, 0)
        if save_csv:
            save_matrix_to_csv(machine, matrix_results, iterations, filepath="results.csv")
    elif mode == 4:
        budget = get_int_input("\n예산을 입력하세요 [기본값: 10000]: ", 1000, 200000, 10000)
        iterations = get_int_input("반복 횟수를 입력하세요 [기본값: 5000]: ", 100, 100000, 5000)
        session_policy = choose_session_policy(default=1)
        print(f"\n[전략 비교 실행 중...] 회전율 {SPIN_RATE_CASES}, 전략 4종을 비교합니다.")
        matrix_results = run_strategy_matrix(
            machine,
            rental_rate,
            exchange_rate,
            budget,
            iterations,
            session_policy=session_policy,
            border_spins_per_1000y=selected_border_spins,
        )
        add_lineup_context(matrix_results, selected_machine_info)
        print_strategy_matrix_results(store_name, machine, matrix_results, iterations)
    elif mode == 5:
        print_spin_rate_guide()
        spins_per_1000y = get_int_input("1000엔당 회전수를 입력하세요 [기본값: 80]: ", 10, 200, 80)
        iterations = get_int_input("반복 횟수를 입력하세요 [기본값: 1000]: ", 100, 100000, 1000)
        strategy = choose_strategy()
        session_policy = choose_session_policy(default=1)
        print(f"\n[예산 비교 실행 중...] 예산 {BUDGET_CASES}엔, {spins_per_1000y}회/1000엔 조건을 비교합니다.")
        matrix_results = run_budget_matrix(
            machine,
            rental_rate,
            exchange_rate,
            iterations,
            budgets=BUDGET_CASES,
            spins_per_1000y=spins_per_1000y,
            strategy=strategy,
            session_policy=session_policy,
            border_spins_per_1000y=selected_border_spins,
        )
        add_lineup_context(matrix_results, selected_machine_info)
        print_budget_matrix_results(store_name, machine, matrix_results, iterations)
    elif mode == 6:
        print_spin_rate_guide()
        spins_per_1000y = get_int_input("1000엔당 회전수를 입력하세요 [기본값: 80]: ", 10, 200, 80)
        iterations = get_int_input("반복 횟수를 입력하세요 [기본값: 20000]: ", 100, 200000, 20000)
        print(
            f"\n[모델 프로파일 실행 중...] 예산 {PROFILE_BUDGET_CASES}엔, "
            f"{spins_per_1000y}회/1000엔 조건을 비교합니다."
        )
        matrix_results = []
        for budget in PROFILE_BUDGET_CASES:
            matrix_results.append(
                {
                    "budget": budget,
                    "spins_per_1000y": spins_per_1000y,
                    "strategy": "no_rule",
                    "session_policy": "fixed_spin_cap",
                    "results": simulate_multiple(
                        machine,
                        budget,
                        rental_rate,
                        spins_per_1000y,
                        exchange_rate,
                        iterations,
                        strategy="no_rule",
                        session_policy="fixed_spin_cap",
                        border_spins_per_1000y=selected_border_spins,
                    ),
                }
            )
        add_lineup_context(matrix_results, selected_machine_info)
        print_model_profile_results(store_name, machine, matrix_results, iterations)
    elif mode == 7:
        print_spin_rate_guide()
        budget = get_int_input("\n예산을 입력하세요 [기본값: 10000]: ", 1000, 200000, 10000)
        spins_per_1000y = get_int_input("기준 1000엔당 회전수를 입력하세요 [기본값: 80]: ", 10, 200, 80)
        iterations = get_int_input("반복 횟수를 입력하세요 [기본값: 5000]: ", 100, 100000, 5000)
        strategy = choose_strategy()
        session_policy = choose_session_policy(default=1)
        comparison_mode = choose_store_comparison_mode(default=1)
        print(
            f"\n[가게별 비교 실행 중...] {STORE_COMPARISON_MODES[comparison_mode]}, "
            f"예산 {budget}엔, 기준 {spins_per_1000y}회/1000엔 조건을 비교합니다."
        )
        comparison_results = run_store_comparison(
            machine,
            store_contexts_for_machine(selected_machine_id, include_missing=True),
            rental_rate,
            spins_per_1000y,
            budget,
            exchange_rate,
            iterations,
            strategy=strategy,
            session_policy=session_policy,
            comparison_mode=comparison_mode,
        )
        print_store_comparison_results(machine, comparison_results, iterations)
    else:
        budget = get_int_input("\n예산을 입력하세요 (예: 10000, 20000) [기본값: 10000]: ", 1000, 200000, 10000)
        print_spin_rate_guide()
        spins_per_1000y = get_int_input("1000엔당 회전수를 입력하세요 [기본값: 50]: ", 10, 200, 50)
        strategy = choose_strategy()
        session_policy = choose_session_policy(default=1)
        
        if mode == 1:
            res = simulate_single(
                machine,
                budget,
                rental_rate,
                spins_per_1000y,
                exchange_rate,
                strategy=strategy,
                record_events=True,
                session_policy=session_policy,
                border_spins_per_1000y=selected_border_spins,
            )
            add_single_result_context(res, selected_machine_info)
            print(
                f"\n[보더라인 기준] "
                f"{border_label(spins_per_1000y, selected_machine_info.get('border_spins_per_1000yen'))}"
            )
            print_single_result(store_name, machine, res, spins_per_1000y)
        elif mode == 2:
            iterations = 1000
            results = simulate_multiple(
                machine,
                budget,
                rental_rate,
                spins_per_1000y,
                exchange_rate,
                iterations,
                strategy=strategy,
                session_policy=session_policy,
                border_spins_per_1000y=selected_border_spins,
            )
            for result in results:
                add_single_result_context(result, selected_machine_info)
            print(
                f"\n[보더라인 기준] "
                f"{border_label(spins_per_1000y, selected_machine_info.get('border_spins_per_1000yen'))}"
            )
            print_multiple_result(store_name, machine, results, iterations)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n시뮬레이터를 종료합니다.")
        sys.exit(0)
