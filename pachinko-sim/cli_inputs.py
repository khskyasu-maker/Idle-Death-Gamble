from rotation import (
    border_case_rates,
    estimate_from_absolute_spins,
    estimate_from_ball_unit,
    estimate_from_border_margin,
    estimate_from_yen_observation,
    estimate_summary,
    rented_balls_per_1000yen,
)
from session_limits import (
    HARD_SESSION_TIME_LIMIT_HOURS,
    LAST_CASH_INPUT_CUTOFF_HOURS,
    SESSION_TIME_LIMIT_HOURS,
)


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


def get_float_input(prompt: str, min_val: float = None, max_val: float = None, default: float = None) -> float:
    while True:
        try:
            user_input = input(prompt).strip()
            if not user_input and default is not None:
                return float(default)
            val = float(user_input)
            if min_val is not None and val < min_val:
                print(f"경고: 최소 {min_val:g} 이상이어야 합니다.")
                continue
            if max_val is not None and val > max_val:
                print(f"경고: 최대 {max_val:g} 이하여야 합니다.")
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
    print(
        "2: 현금+보유구슬 소진 "
        f"({SESSION_TIME_LIMIT_HOURS}시간 이후 RUSH 종료 시 정리, "
        f"{LAST_CASH_INPUT_CUTOFF_HOURS}시간 이후 추가 현금 없음, 하드 {HARD_SESSION_TIME_LIMIT_HOURS}시간)"
    )
    policy_choice = get_int_input(f"세션 방식을 선택하세요 (1-2) [기본값: {default}]: ", 1, 2, default)
    return {
        1: "fixed_spin_cap",
        2: "play_until_budget_and_balls_gone",
    }[policy_choice]


def choose_store_comparison_mode(default: int = 1) -> str:
    print("\n[점포 보조 비교 기준]")
    print("1: 동일 1000엔 회전수 - 각 점포에서 같은 현금 회전수를 실측했다고 가정")
    print("2: 동일 헤소 입상 품질 - 구슬 1발당 입상 확률을 같게 두고 레이트별 회전수 환산")
    print("3: 동일 보더 마진 - 각 점포의 보더 대비 같은 +/- 회전수로 비교")
    mode_choice = get_int_input(f"비교 기준을 선택하세요 (1-3) [기본값: {default}]: ", 1, 3, default)
    return {
        1: "cash_rotation",
        2: "ball_quality",
        3: "border_margin",
    }[mode_choice]


def default_spin_rate_for_border(border_spins_per_1000yen) -> int:
    if border_spins_per_1000yen is None:
        return 70
    return int(round(border_spins_per_1000yen))


def print_spin_rate_guide(border_spins_per_1000yen=None):
    print("\n[1000엔당 회전수 가이드]")
    if border_spins_per_1000yen is not None:
        cases = border_case_rates(border_spins_per_1000yen)
        case_text = " / ".join(
            f"{case['rotation_label']}={case['spins_per_1000y']:.1f}회"
            for case in cases
        )
        print(f"선택 기종 보더 기준: {case_text}")
    print("보더가 없을 때 절대값 참고: 위험 50회 이하 / 타협 60회 / 합격 70회 / 우수 80회 이상")
    print("입력값은 평균 회전수입니다. 실제 세션 회전수는 구슬->헤소 입상 확률로 표본 변동을 반영합니다.")


def choose_rotation_estimate(lend_rate: float, border_spins_per_1000yen=None):
    default_spins = default_spin_rate_for_border(border_spins_per_1000yen)
    rented_balls = rented_balls_per_1000yen(lend_rate)
    default_200yen_spins = default_spins / 5.0
    default_250ball_spins = default_spins / (rented_balls / 250.0) if rented_balls else default_spins / 4.0

    print_spin_rate_guide(border_spins_per_1000yen)
    print("\n[회전율 입력 방식]")
    print("1: 1000엔당 회전수")
    print("2: 200엔당 회전수 (라쿠엔 1.111엔은 200엔=180玉 기준)")
    print("3: 250玉당 회전수")
    print("4: 사용 금액 + 실제 회전수")
    if border_spins_per_1000yen is not None:
        print("5: 보더 기준 +/- 회전")
    mode_max = 5 if border_spins_per_1000yen is not None else 4
    choice = get_int_input(f"입력 방식을 선택하세요 (1-{mode_max}) [기본값: 1]: ", 1, mode_max, 1)

    if choice == 2:
        spins = get_float_input(
            f"200엔당 회전수를 입력하세요 [기본값: {default_200yen_spins:.1f}]: ",
            0.1,
            80.0,
            default_200yen_spins,
        )
        estimate = estimate_from_yen_observation(spins, 200)
    elif choice == 3:
        spins = get_float_input(
            f"250玉당 회전수를 입력하세요 [기본값: {default_250ball_spins:.1f}]: ",
            0.1,
            80.0,
            default_250ball_spins,
        )
        estimate = estimate_from_ball_unit(spins, 250, lend_rate)
    elif choice == 4:
        yen = get_float_input("사용 금액을 입력하세요 [기본값: 1000]: ", 1.0, 200000.0, 1000.0)
        default_observed_spins = default_spins * (yen / 1000.0)
        spins = get_float_input(
            f"그 금액으로 실제 돈 회전수를 입력하세요 [기본값: {default_observed_spins:.1f}]: ",
            0.0,
            20000.0,
            default_observed_spins,
        )
        estimate = estimate_from_yen_observation(spins, yen)
    elif choice == 5:
        margin = get_float_input("보더 대비 +/- 회전수를 입력하세요 [기본값: 0]: ", -50.0, 80.0, 0.0)
        estimate = estimate_from_border_margin(border_spins_per_1000yen, margin)
    else:
        spins = get_float_input(
            f"1000엔당 회전수를 입력하세요 [기본값: {default_spins}]: ",
            1.0,
            250.0,
            default_spins,
        )
        estimate = estimate_from_absolute_spins(spins)

    print(f"환산 회전율: {estimate_summary(estimate, border_spins_per_1000yen)}")
    return estimate
