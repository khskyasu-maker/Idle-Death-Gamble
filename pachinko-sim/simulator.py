import math
import random
from typing import Dict, Any, List
from machines import Machine, Payout
from start_gate import (
    observed_rate_per_1000yen,
    rented_balls_per_1000yen,
    sample_start_spins,
    sample_session_spin_rate,
    sample_truncated_normal,
    start_probability_from_rate,
)
from rotation import ABSOLUTE_SPIN_RATE_CASES, border_case_rates
from session_limits import (
    HARD_SESSION_TIME_LIMIT_MINUTES,
    LAST_CASH_INPUT_CUTOFF_MINUTES,
    SESSION_TIME_LIMIT_MINUTES,
)
from time_model import (
    TimeAssumptions,
    assumption_dict,
    hit_effect_seconds as hit_effect_time_seconds,
    minutes,
    normal_time_components,
    right_seconds,
    time_assumptions_for_machine,
)


SPIN_RATE_CASES = ABSOLUTE_SPIN_RATE_CASES
BUDGET_CASES = [5000, 10000, 15000, 20000]
PROFILE_BUDGET_CASES = [1000, 5000, 10000, 15000, 20000]

SESSION_POLICIES = {
    "fixed_spin_cap": "예산 고정 회전수",
    "play_until_budget_and_balls_gone": f"현금+보유구슬 소진({SESSION_TIME_LIMIT_MINUTES // 60}시간 후 RUSH 종료 시 정리)",
}

STRATEGIES = {
    "no_rule": "노룰",
    "basic_stop": "기본 손절",
    "profit_lock": "이익 잠금",
    "aggressive": "공격형",
}


HIT_LABELS = {
    "NORMAL": ("初当り", "초당첨"),
    "JITAN": ("時短当り", "시단 당첨"),
    "KAKUBEN": ("確変当り", "확변 당첨"),
    "LT": ("LT当り", "LT 당첨"),
    "UPPER": ("上位RUSH当り", "상위 러시 당첨"),
    "JINBEE": ("ジンベェ当り", "진베에 타임 당첨"),
    "JINBEE_JITAN": ("ジンベェ当り", "진베에 시단 당첨"),
}


def bilingual_hit_label(state: str) -> tuple[str, str, str]:
    label_ja, label_ko = HIT_LABELS.get(state, ("RUSH/ST当り", "러시/ST 당첨"))
    return label_ja, label_ko, f"{label_ja}({label_ko})"


def get_payout(payouts: List[Payout]) -> Payout:
    """확률 가중치에 따라 출옥 수 및 상태 전이 정보를 추첨합니다."""
    if not payouts:
        return Payout(balls=0, weight=1.0, next_state='NORMAL')
        
    r = random.random()
    cumulative = 0.0
    for p in payouts:
        cumulative += p.weight
        if r <= cumulative:
            return p
    return payouts[-1] # fallback


def sample_payout_balls(payout: Payout) -> int:
    """Sample realized payout around the nominal ball count.

    Round distribution is fixed by the machine spec, while actual counted balls
    vary slightly from award/over入賞(오버입상)/round-loss effects. A truncated
    normal keeps values centred on the public payout and inside the configured
    plausible range.
    """
    if payout.balls <= 0:
        return 0

    variance = max(0.0, payout.ball_variance)
    if variance <= 0.0:
        return int(payout.balls)

    low = max(0, int(payout.balls * (1.0 - variance)))
    high = max(low, int(payout.balls * (1.0 + variance)))
    stddev = max(1.0, (payout.balls * variance) / 2.0)
    return int(round(sample_truncated_normal(payout.balls, stddev, low, high)))


def spins_until_hit(probability_denominator: float) -> int:
    """Sample the spin count until the next hit for independent Bernoulli spins."""
    hit_probability = 1.0 / probability_denominator
    if hit_probability >= 1.0:
        return 1
    return int(math.log1p(-random.random()) / math.log1p(-hit_probability)) + 1


def normalize_strategy(strategy: str) -> str:
    if strategy in STRATEGIES:
        return strategy
    return "no_rule"


def normalize_session_policy(session_policy: str) -> str:
    if session_policy in SESSION_POLICIES:
        return session_policy
    return "fixed_spin_cap"


def current_profit_balls(bank_balls: float, locked_balls: float, cash_spent: float, lend_rate: float) -> float:
    spent_balls_equivalent = cash_spent / lend_rate
    return bank_balls + locked_balls - spent_balls_equivalent


def apply_strategy_rules(
    strategy: str,
    bank_balls: float,
    locked_balls: float,
    cash_spent: float,
    lend_rate: float,
    flags: Dict[str, bool],
) -> tuple[float, float, bool]:
    """익절/공격형 잠금 규칙을 적용하고 종료 요청 여부를 반환합니다."""
    stop_requested = False
    profit_balls = current_profit_balls(bank_balls, locked_balls, cash_spent, lend_rate)

    if strategy == "profit_lock":
        if profit_balls >= 2000 and not flags.get("lock_2000"):
            lock_amount = bank_balls * 0.5
            bank_balls -= lock_amount
            locked_balls += lock_amount
            flags["lock_2000"] = True
            flags["profit_lock_triggered"] = True

        if profit_balls >= 5000 and locked_balls < 3000:
            lock_amount = min(bank_balls, 3000 - locked_balls)
            bank_balls -= lock_amount
            locked_balls += lock_amount
            flags["profit_lock_triggered"] = True

        if profit_balls >= 8000:
            stop_requested = True
            flags["profit_exit_triggered"] = True

    elif strategy == "aggressive":
        if profit_balls >= 5000:
            keep_for_redeploy = 3000
            if bank_balls > keep_for_redeploy:
                lock_amount = bank_balls - keep_for_redeploy
                bank_balls -= lock_amount
                locked_balls += lock_amount
                flags["profit_lock_triggered"] = True
            flags["aggressive_redeploy_triggered"] = True

    return bank_balls, locked_balls, stop_requested


def simulate_single(
    machine: Machine,
    budget: int,
    lend_rate: float,
    spins_per_1000y: int,
    exchange_rate: float,
    strategy: str = "no_rule",
    card_reuse: bool = True,
    stop_loss_spin_threshold: int = 70,
    stop_loss_probe_yen: int = 1000,
    record_events: bool = False,
    session_policy: str = "fixed_spin_cap",
    max_normal_spins: int = None,
    start_variance: bool = True,
    border_spins_per_1000y: float = None,
    spin_rate_quality_stddev: float = 3.0,
    spin_rate_min: float = None,
    spin_rate_max: float = None,
    time_assumptions: TimeAssumptions = None,
    session_time_limit_minutes: float = HARD_SESSION_TIME_LIMIT_MINUTES,
    cash_input_cutoff_minutes: float = LAST_CASH_INPUT_CUTOFF_MINUTES,
    soft_stop_minutes: float = SESSION_TIME_LIMIT_MINUTES,
) -> Dict[str, Any]:
    """단일 시뮬레이션: 현금 투입, 보유 구슬, 우타치 소모, 전략을 함께 반영합니다."""

    strategy = normalize_strategy(strategy)
    session_policy = normalize_session_policy(session_policy)
    time_assumptions = time_assumptions or time_assumptions_for_machine(machine)

    true_spins_per_1000y = float(spins_per_1000y)
    effective_quality_stddev = spin_rate_quality_stddev if start_variance else 0.0
    if start_variance:
        true_spins_per_1000y = sample_session_spin_rate(
            spins_per_1000y,
            border_spins_per_1000y=border_spins_per_1000y,
            quality_stddev=effective_quality_stddev,
            min_spins_per_1000y=spin_rate_min,
            max_spins_per_1000y=spin_rate_max,
        )

    start_probability = start_probability_from_rate(lend_rate, true_spins_per_1000y)
    rented_balls_1000 = rented_balls_per_1000yen(lend_rate)
    expected_total_spins_possible = int((budget / 1000) * true_spins_per_1000y)

    if start_variance and session_policy == "fixed_spin_cap":
        total_budget_balls = budget / lend_rate
        total_spins_possible = sample_start_spins(total_budget_balls, start_probability)
        observed_spins_per_1000y = observed_rate_per_1000yen(total_spins_possible, budget)
    elif start_variance:
        sampled_1000y_spins = sample_start_spins(rented_balls_1000, start_probability)
        observed_spins_per_1000y = float(sampled_1000y_spins)
        total_spins_possible = int((budget / 1000) * observed_spins_per_1000y)
    else:
        observed_spins_per_1000y = float(spins_per_1000y)
        total_spins_possible = expected_total_spins_possible

    stop_loss_probe_budget = max(0, min(int(stop_loss_probe_yen), int(budget)))
    if stop_loss_probe_budget > 0:
        if start_variance:
            stop_loss_probe_spins = sample_start_spins(stop_loss_probe_budget / lend_rate, start_probability)
        else:
            stop_loss_probe_spins = int(round((stop_loss_probe_budget / 1000.0) * spins_per_1000y))
        stop_loss_probe_rate = observed_rate_per_1000yen(stop_loss_probe_spins, stop_loss_probe_budget)
    else:
        stop_loss_probe_spins = 0
        stop_loss_probe_rate = 0.0

    normal_spin_cap = total_spins_possible if session_policy == "fixed_spin_cap" else max_normal_spins
    stop_loss_normal_spin_cap = None
    if strategy == "basic_stop" and stop_loss_probe_budget > 0 and stop_loss_probe_rate < stop_loss_spin_threshold:
        stop_loss_normal_spin_cap = min(total_spins_possible, stop_loss_probe_spins)

    spins_used = 0
    right_spins = 0
    total_out_balls = 0.0
    normal_balls_fired = 0.0
    bank_balls = 0.0
    locked_balls = 0.0
    cash_spent = 0.0
    normal_play_seconds = 0.0
    active_launch_seconds = 0.0
    normal_display_seconds = 0.0
    reserve_wait_seconds = 0.0
    right_play_seconds = 0.0
    hit_effect_seconds_total = 0.0
    support_event_seconds = 0.0
    cashless_play_seconds = 0.0

    first_hit_spin = None
    first_hit_total_spins = None
    total_hits = 0
    max_streak = 0
    streak = 0
    rush_entries = 0
    lt_entries = 0
    upper_entries = 0
    hit_events = []
    rush_active = False

    state = 'NORMAL'
    spins_left = 0
    jitan_reserve = 0
    stop_requested = False
    flags = {
        "lock_2000": False,
        "profit_lock_triggered": False,
        "profit_exit_triggered": False,
        "stop_loss_triggered": False,
        "aggressive_redeploy_triggered": False,
        "time_limit_triggered": False,
        "cash_input_cutoff_triggered": False,
        "soft_stop_triggered": False,
        "funds_exhausted_triggered": False,
    }
    cash_budget_exhausted_seconds = None

    effective_spins_per_1000y = max(1.0, observed_spins_per_1000y)
    spin_cost_balls = rented_balls_1000 / effective_spins_per_1000y
    spin_cost_yen = 1000.0 / effective_spins_per_1000y
    session_time_limit_seconds = (
        max(0.0, float(session_time_limit_minutes)) * 60.0
        if session_time_limit_minutes is not None and session_time_limit_minutes > 0
        else None
    )
    cash_input_cutoff_seconds = (
        max(0.0, float(cash_input_cutoff_minutes)) * 60.0
        if cash_input_cutoff_minutes is not None and cash_input_cutoff_minutes >= 0
        else None
    )
    soft_stop_seconds = (
        max(0.0, float(soft_stop_minutes)) * 60.0
        if soft_stop_minutes is not None and soft_stop_minutes > 0
        else None
    )
    safety_counter = 0

    def elapsed_seconds() -> float:
        return normal_play_seconds + right_play_seconds + hit_effect_seconds_total + support_event_seconds

    def mark_cash_budget_exhausted():
        nonlocal cash_budget_exhausted_seconds
        if cash_budget_exhausted_seconds is None and cash_spent >= budget - spin_cost_yen:
            cash_budget_exhausted_seconds = elapsed_seconds()

    def session_seconds_remaining() -> float | None:
        if session_time_limit_seconds is None:
            return None
        return session_time_limit_seconds - elapsed_seconds()

    def cash_input_allowed() -> bool:
        if cash_input_cutoff_seconds is None:
            return True
        return elapsed_seconds() < cash_input_cutoff_seconds

    def soft_stop_reached() -> bool:
        return soft_stop_seconds is not None and elapsed_seconds() >= soft_stop_seconds

    def soft_stop_seconds_remaining() -> float | None:
        if soft_stop_seconds is None:
            return None
        return soft_stop_seconds - elapsed_seconds()

    def normal_seconds_per_spin() -> float:
        active_per_spin = (
            (spin_cost_balls / time_assumptions.launch_balls_per_minute) * 60.0
            if time_assumptions.launch_balls_per_minute > 0
            else 0.0
        )
        return max(active_per_spin, time_assumptions.normal_seconds_per_start)

    def cap_normal_spins_by_cash_cutoff(spin_count: int) -> tuple[int, bool]:
        if cash_input_cutoff_seconds is None or elapsed_seconds() >= cash_input_cutoff_seconds:
            return spin_count, False
        if cash_spent >= budget:
            return spin_count, False

        planned_ball_cost = spin_cost_balls * spin_count
        needs_new_cash = (not card_reuse) or bank_balls < planned_ball_cost
        if not needs_new_cash:
            return spin_count, False

        seconds_to_cutoff = cash_input_cutoff_seconds - elapsed_seconds()
        capped = int(seconds_to_cutoff // normal_seconds_per_spin())
        if 0 < capped < spin_count:
            flags["cash_input_cutoff_triggered"] = True
            return capped, True
        return spin_count, False

    def cap_normal_spins_by_soft_stop(spin_count: int) -> tuple[int, bool]:
        remaining_seconds = soft_stop_seconds_remaining()
        if remaining_seconds is None:
            return spin_count, False
        if remaining_seconds <= 0:
            flags["soft_stop_triggered"] = True
            return 0, True
        capped = int(remaining_seconds // normal_seconds_per_spin())
        if capped < spin_count:
            flags["soft_stop_triggered"] = True
            return max(0, capped), True
        return spin_count, False

    def cap_spins_by_time(spin_count: int, seconds_per_spin: float) -> tuple[int, bool]:
        remaining_seconds = session_seconds_remaining()
        if remaining_seconds is None:
            return spin_count, False
        if remaining_seconds <= 0:
            return 0, True
        if seconds_per_spin <= 0:
            return spin_count, False
        capped = int(remaining_seconds // seconds_per_spin)
        if capped < spin_count:
            return max(0, capped), True
        return spin_count, False

    def add_right_time(state_name: str, spin_count: int):
        nonlocal right_play_seconds, cashless_play_seconds
        seconds = right_seconds(state_name, spin_count, time_assumptions)
        right_play_seconds += seconds
        cashless_play_seconds += seconds

    def take_right_spins(state_name: str, spin_count: int) -> tuple[int, bool]:
        nonlocal bank_balls, right_spins
        capped_spins, limited_by_time = cap_spins_by_time(
            spin_count,
            right_seconds(state_name, 1, time_assumptions),
        )
        if capped_spins <= 0:
            if limited_by_time:
                flags["time_limit_triggered"] = True
            return 0, limited_by_time
        if limited_by_time and capped_spins < spin_count:
            flags["time_limit_triggered"] = True
        right_spins += capped_spins
        add_right_time(state_name, capped_spins)
        bank_balls = max(
            0.0,
            bank_balls - (machine.right_spend_per_spin.get(state_name, 0.0) * capped_spins),
        )
        return capped_spins, limited_by_time

    def pay_normal_spins(spin_count: int) -> int:
        nonlocal bank_balls, cash_spent, normal_balls_fired
        nonlocal normal_play_seconds, active_launch_seconds, normal_display_seconds
        nonlocal reserve_wait_seconds, cashless_play_seconds
        if spin_count <= 0:
            return 0

        if card_reuse:
            if cash_input_allowed():
                remaining_cash_balls = max(0.0, (budget - cash_spent) / lend_rate)
            else:
                remaining_cash_balls = 0.0
                if cash_spent < budget:
                    flags["cash_input_cutoff_triggered"] = True
            max_affordable = int((bank_balls + remaining_cash_balls) / spin_cost_balls)
        else:
            if cash_input_allowed():
                max_affordable = int((budget - cash_spent) / spin_cost_yen)
            else:
                max_affordable = 0
                if cash_spent < budget:
                    flags["cash_input_cutoff_triggered"] = True

        playable_spins = max(0, min(spin_count, max_affordable))
        if playable_spins <= 0:
            remaining_cash_balls = max(0.0, (budget - cash_spent) / lend_rate) if card_reuse else 0.0
            remaining_cash_yen = max(0.0, budget - cash_spent)
            no_playable_cash_or_balls = (
                (bank_balls + remaining_cash_balls) < spin_cost_balls
                if card_reuse
                else remaining_cash_yen < spin_cost_yen
            )
            if no_playable_cash_or_balls and cash_input_allowed():
                flags["funds_exhausted_triggered"] = True
                mark_cash_budget_exhausted()
            return 0

        ball_cost = 0.0
        reusable_balls = 0.0
        if card_reuse:
            ball_cost = spin_cost_balls * playable_spins
            reusable_balls = min(bank_balls, ball_cost)
            bank_balls -= reusable_balls
            cash_spent += (ball_cost - reusable_balls) * lend_rate
            normal_balls_fired += ball_cost
        else:
            cash_cost = spin_cost_yen * playable_spins
            cash_spent += cash_cost
            ball_cost = cash_cost / lend_rate
            normal_balls_fired += ball_cost

        time_parts = normal_time_components(playable_spins, ball_cost, time_assumptions)
        normal_play_seconds += time_parts["elapsed_seconds"]
        active_launch_seconds += time_parts["active_launch_seconds"]
        normal_display_seconds += time_parts["display_seconds"]
        reserve_wait_seconds += time_parts["reserve_wait_seconds"]
        if ball_cost > 0:
            cashless_play_seconds += time_parts["elapsed_seconds"] * (reusable_balls / ball_cost)

        if cash_spent > budget and cash_spent - budget < 0.000001:
            cash_spent = float(budget)
        mark_cash_budget_exhausted()
        if playable_spins < spin_count and cash_input_allowed():
            remaining_cash_balls_after = max(0.0, (budget - cash_spent) / lend_rate) if card_reuse else 0.0
            remaining_cash_yen_after = max(0.0, budget - cash_spent)
            no_playable_cash_or_balls = (
                (bank_balls + remaining_cash_balls_after) < spin_cost_balls
                if card_reuse
                else remaining_cash_yen_after < spin_cost_yen
            )
            if no_playable_cash_or_balls:
                flags["funds_exhausted_triggered"] = True
                mark_cash_budget_exhausted()
        return playable_spins

    def settle_stop_loss_probe_cost():
        """If a bad first-1000yen probe produced no hit, charge that spent probe."""
        nonlocal cash_spent, normal_balls_fired
        if total_hits > 0 or stop_loss_probe_budget <= 0:
            return
        target_cash_spent = min(float(budget), float(stop_loss_probe_budget))
        if cash_spent < target_cash_spent:
            normal_balls_fired += (target_cash_spent - cash_spent) / lend_rate
            cash_spent = target_cash_spent
            mark_cash_budget_exhausted()

    while True:
        safety_counter += 1
        if safety_counter > 100000:
            flags["safety_stopped"] = True
            break
        if session_seconds_remaining() is not None and session_seconds_remaining() <= 0:
            flags["time_limit_triggered"] = True
            break
        if (
            cash_input_cutoff_seconds is not None
            and elapsed_seconds() >= cash_input_cutoff_seconds
            and cash_spent < budget
        ):
            flags["cash_input_cutoff_triggered"] = True

        current_prob = machine.normal_prob

        if state == 'NORMAL':
            if soft_stop_reached():
                flags["soft_stop_triggered"] = True
                break
            if stop_requested:
                break

            remaining_normal_spins = None
            if normal_spin_cap is not None:
                remaining_normal_spins = normal_spin_cap - spins_used

            if remaining_normal_spins is not None and remaining_normal_spins <= 0:
                flags["normal_spin_cap_triggered"] = True
                break

            if stop_loss_normal_spin_cap is not None:
                stop_loss_remaining = stop_loss_normal_spin_cap - spins_used
                if stop_loss_remaining <= 0:
                    flags["stop_loss_triggered"] = True
                    settle_stop_loss_probe_cost()
                    break
                if remaining_normal_spins is None:
                    remaining_normal_spins = stop_loss_remaining
                else:
                    remaining_normal_spins = min(remaining_normal_spins, stop_loss_remaining)

            wait_to_hit = spins_until_hit(machine.normal_prob)
            wait_to_support = None
            if machine.normal_support_prob > 1 and machine.normal_support_dist:
                wait_to_support = spins_until_hit(machine.normal_support_prob)

            next_normal_event = wait_to_hit
            support_event = False
            if wait_to_support is not None and wait_to_support < wait_to_hit:
                next_normal_event = wait_to_support
                support_event = True

            spins_to_take = next_normal_event
            if remaining_normal_spins is not None:
                spins_to_take = min(spins_to_take, remaining_normal_spins)
            spins_to_take, limited_by_time = cap_spins_by_time(
                spins_to_take,
                normal_seconds_per_spin(),
            )
            spins_to_take, limited_by_soft_stop = cap_normal_spins_by_soft_stop(spins_to_take)
            spins_to_take, limited_by_cash_cutoff = cap_normal_spins_by_cash_cutoff(spins_to_take)
            if spins_to_take <= 0:
                break

            played_spins = pay_normal_spins(spins_to_take)
            spins_used += played_spins
            if played_spins < spins_to_take:
                break

            if played_spins < next_normal_event:
                if flags.get("funds_exhausted_triggered"):
                    break
                elif limited_by_soft_stop:
                    flags["soft_stop_triggered"] = True
                    break
                elif limited_by_time:
                    flags["time_limit_triggered"] = True
                elif limited_by_cash_cutoff:
                    flags["cash_input_cutoff_triggered"] = True
                    continue
                elif stop_loss_normal_spin_cap is not None and spins_used >= stop_loss_normal_spin_cap:
                    flags["stop_loss_triggered"] = True
                    settle_stop_loss_probe_cost()
                elif normal_spin_cap is not None and spins_used >= normal_spin_cap:
                    flags["normal_spin_cap_triggered"] = True
                break

            if support_event:
                payout = get_payout(machine.normal_support_dist)
                support_event_seconds += time_assumptions.normal_support_event_seconds
                cashless_play_seconds += time_assumptions.normal_support_event_seconds
                state = payout.next_state
                if state in ['ST', 'LT', 'UPPER']:
                    spins_left = payout.st_spins
                    jitan_reserve = payout.jitan_spins
                elif state in ['JITAN', 'JINBEE_JITAN']:
                    spins_left = payout.jitan_spins or payout.st_spins
                    jitan_reserve = 0
                elif state in ['KAKUBEN', 'JINBEE']:
                    spins_left = 0
                    jitan_reserve = 0
                else:
                    spins_left = 0
                    jitan_reserve = 0
                continue

        if state in ['ST', 'LT', 'UPPER']:
            current_prob = machine.high_prob
            fall_denominator = machine.fall_prob.get(state)
            if fall_denominator:
                wait_to_hit = spins_until_hit(machine.high_prob)
                wait_to_fall = spins_until_hit(fall_denominator)

                if wait_to_hit <= wait_to_fall:
                    right_spins_to_take, limited_by_time = take_right_spins(state, wait_to_hit)
                    if limited_by_time and right_spins_to_take < wait_to_hit:
                        break
                else:
                    right_spins_to_take, limited_by_time = take_right_spins(state, wait_to_fall)
                    if limited_by_time and right_spins_to_take < wait_to_fall:
                        break

                    reserve_spins = machine.fall_reserve_spins.get(state, 0)
                    if reserve_spins <= 0:
                        state = 'NORMAL'
                        streak = 0
                        rush_active = False
                        continue

                    wait_to_reserve_hit = spins_until_hit(machine.high_prob)
                    reserve_spins_to_take = min(wait_to_reserve_hit, reserve_spins)
                    reserve_spins_to_take, limited_by_time = take_right_spins(state, reserve_spins_to_take)
                    if limited_by_time and reserve_spins_to_take < min(wait_to_reserve_hit, reserve_spins):
                        break
                    if reserve_spins_to_take < wait_to_reserve_hit:
                        state = 'NORMAL'
                        streak = 0
                        rush_active = False
                        continue
            elif spins_left > 0:
                wait_to_hit = spins_until_hit(machine.high_prob)
                right_spins_to_take = min(wait_to_hit, spins_left)
                spins_left -= right_spins_to_take
                right_spins_to_take, limited_by_time = take_right_spins(state, right_spins_to_take)
                if limited_by_time and right_spins_to_take < min(wait_to_hit, spins_left + right_spins_to_take):
                    break
                if right_spins_to_take < wait_to_hit:
                    continue
            else:
                if jitan_reserve > 0:
                    state = 'JITAN'
                    spins_left = jitan_reserve
                    jitan_reserve = 0
                    continue # 이번 턴은 당첨 추첨 없이 상태 전환만 처리
                else:
                    state = 'NORMAL'
                    streak = 0
                    rush_active = False
                    continue

        elif state in ['JITAN', 'JINBEE_JITAN']:
            current_prob = machine.normal_prob
            if spins_left > 0:
                wait_to_hit = spins_until_hit(machine.normal_prob)
                right_spins_to_take = min(wait_to_hit, spins_left)
                spins_left -= right_spins_to_take
                right_spins_to_take, limited_by_time = take_right_spins(state, right_spins_to_take)
                if limited_by_time and right_spins_to_take < min(wait_to_hit, spins_left + right_spins_to_take):
                    break
                if right_spins_to_take < wait_to_hit:
                    continue
            else:
                state = 'NORMAL'
                streak = 0
                rush_active = False
                continue
                
        elif state in ['KAKUBEN', 'JINBEE']:
            current_prob = machine.high_prob
            wait_to_hit = spins_until_hit(machine.high_prob)
            right_spins_to_take, limited_by_time = take_right_spins(state, wait_to_hit)
            if limited_by_time and right_spins_to_take < wait_to_hit:
                break

        # 당첨 추첨
        if True:
            total_hits += 1
            if first_hit_spin is None:
                first_hit_spin = spins_used
            if first_hit_total_spins is None:
                first_hit_total_spins = spins_used + right_spins
                
            streak += 1
            if streak > max_streak:
                max_streak = streak
                
            # 출옥 및 다음 상태 결정
            if state == 'NORMAL':
                payout = get_payout(machine.normal_hit_dist)
            elif state == 'ST':
                payout = get_payout(machine.st_hit_dist)
            elif state == 'JITAN':
                payout = get_payout(machine.jitan_hit_dist)
            elif state == 'KAKUBEN':
                payout = get_payout(machine.kakuben_hit_dist)
            elif state == 'LT':
                payout = get_payout(machine.lt_hit_dist)
            elif state == 'UPPER':
                payout = get_payout(machine.upper_hit_dist)
            elif state in ['JINBEE', 'JINBEE_JITAN']:
                payout = get_payout(machine.jinbee_hit_dist)

            previous_state = state
            payout_balls = sample_payout_balls(payout)
            total_out_balls += payout_balls
            bank_balls += payout_balls
            hit_seconds = hit_effect_time_seconds(payout_balls, previous_state, time_assumptions)
            hit_effect_seconds_total += hit_seconds
            cashless_play_seconds += hit_seconds
            
            # 다음 상태 전이 반영
            state = payout.next_state
            rush_entry_event = False
            lt_entry_event = False
            upper_entry_event = False
            
            if state in ['ST', 'LT', 'UPPER']:
                if payout.counts_as_rush and not rush_active:
                    rush_entries += 1
                    rush_entry_event = True
                    rush_active = True
                if state == 'UPPER' and previous_state != 'UPPER':
                    upper_entries += 1
                    upper_entry_event = True
                spins_left = payout.st_spins
                jitan_reserve = payout.jitan_spins
            elif state == 'JITAN':
                spins_left = payout.jitan_spins
                jitan_reserve = 0
            elif state == 'KAKUBEN':
                if payout.counts_as_rush and not rush_active:
                    rush_entries += 1
                    rush_entry_event = True
                    rush_active = True
                spins_left = 0
                jitan_reserve = 0
            elif state == 'JINBEE':
                if payout.counts_as_rush and not rush_active:
                    rush_entries += 1
                    rush_entry_event = True
                    rush_active = True
                spins_left = 0
                jitan_reserve = 0
            elif state == 'JINBEE_JITAN':
                if payout.counts_as_rush and not rush_active:
                    rush_entries += 1
                    rush_entry_event = True
                    rush_active = True
                spins_left = payout.jitan_spins or payout.st_spins
                jitan_reserve = 0
            elif state == 'NORMAL':
                spins_left = 0
                jitan_reserve = 0
                rush_active = False
                
            # LT 플래그는 진입 횟수 집계용입니다. 일부 기종의 LT는 별도
            # 전サポ 상태가 아니라 대량 출옥 보너스 후 RUSH로 복귀합니다.
            if payout.is_lt:
                if previous_state != 'LT':
                    lt_entries += 1
                    lt_entry_event = True
                if payout.next_state == 'LT':
                    state = 'LT'

            if record_events:
                hit_label_ja, hit_label_ko, hit_label = bilingual_hit_label(previous_state)

                hit_events.append(
                    {
                        "hit_no": total_hits,
                        "label": hit_label,
                        "label_ja": hit_label_ja,
                        "label_ko": hit_label_ko,
                        "normal_spins": spins_used,
                        "right_spins": right_spins,
                        "state_before": previous_state,
                        "state_after": state,
                        "probability_denominator": current_prob,
                        "payout_balls": payout_balls,
                        "st_spins": payout.st_spins,
                        "jitan_spins": payout.jitan_spins,
                        "streak": streak,
                        "rush_entry": rush_entry_event,
                        "lt_entry": lt_entry_event,
                        "upper_entry": upper_entry_event,
                        "bank_balls_after": int(bank_balls),
                        "locked_balls_after": int(locked_balls),
                    }
                )

            bank_balls, locked_balls, strategy_stop = apply_strategy_rules(
                strategy,
                bank_balls,
                locked_balls,
                cash_spent,
                lend_rate,
                flags,
            )
            stop_requested = stop_requested or strategy_stop

        elif state == 'NORMAL':
            bank_balls, locked_balls, strategy_stop = apply_strategy_rules(
                strategy,
                bank_balls,
                locked_balls,
                cash_spent,
                lend_rate,
                flags,
            )
            stop_requested = stop_requested or strategy_stop

    final_balls = max(0.0, bank_balls + locked_balls)
    final_money = int(final_balls * exchange_rate)
    unused_cash = max(0.0, float(budget) - cash_spent)
    final_remaining_value = int(unused_cash + final_money)
    net_profit = int(final_money - cash_spent)
    exchange_loss = int(final_balls * lend_rate - final_money)
    play_seconds = (
        normal_play_seconds
        + right_play_seconds
        + hit_effect_seconds_total
        + support_event_seconds
    )
    post_budget_play_seconds = (
        max(0.0, play_seconds - cash_budget_exhausted_seconds)
        if cash_budget_exhausted_seconds is not None
        else 0.0
    )
    cashless_share = (
        (cashless_play_seconds / play_seconds) * 100.0
        if play_seconds > 0
        else 0.0
    )
    
    return {
        "budget": budget,
        "total_spins_possible": total_spins_possible,
        "expected_total_spins_possible": expected_total_spins_possible,
        "normal_spin_cap": normal_spin_cap,
        "stop_loss_probe_yen": stop_loss_probe_budget,
        "stop_loss_probe_spins": stop_loss_probe_spins,
        "stop_loss_probe_rate": stop_loss_probe_rate,
        "stop_loss_spin_threshold": stop_loss_spin_threshold,
        "stop_loss_normal_spin_cap": stop_loss_normal_spin_cap,
        "first_hit_spin": first_hit_spin,
        "first_hit_total_spins": first_hit_total_spins,
        "total_hits": total_hits,
        "max_streak": max_streak,
        "total_out_balls": int(total_out_balls),
        "final_balls": int(final_balls),
        "locked_balls": int(locked_balls),
        "final_money": final_money,
        "unused_cash": int(unused_cash),
        "final_remaining_value": final_remaining_value,
        "final_remaining_balance": int(final_remaining_value - budget),
        "net_profit": net_profit,
        "cash_spent": int(cash_spent),
        "exchange_loss": exchange_loss,
        "session_time_limit_minutes": session_time_limit_minutes,
        "cash_input_cutoff_minutes": cash_input_cutoff_minutes,
        "soft_stop_minutes": soft_stop_minutes,
        "cash_budget_exhausted": cash_budget_exhausted_seconds is not None,
        "cash_budget_exhausted_minutes": minutes(cash_budget_exhausted_seconds or 0.0),
        "post_budget_play_minutes": minutes(post_budget_play_seconds),
        "experienced_rush": rush_entries > 0 or lt_entries > 0,
        "rush_entries": rush_entries,
        "lt_entries": lt_entries,
        "upper_entries": upper_entries,
        "hit_events": hit_events,
        "spins_used": spins_used,
        "right_spins": right_spins,
        "normal_balls_fired": int(normal_balls_fired),
        "play_seconds": play_seconds,
        "play_minutes": minutes(play_seconds),
        "normal_play_seconds": normal_play_seconds,
        "normal_play_minutes": minutes(normal_play_seconds),
        "active_launch_seconds": active_launch_seconds,
        "normal_display_seconds": normal_display_seconds,
        "reserve_wait_seconds": reserve_wait_seconds,
        "reserve_wait_minutes": minutes(reserve_wait_seconds),
        "right_play_seconds": right_play_seconds,
        "right_play_minutes": minutes(right_play_seconds),
        "hit_effect_seconds": hit_effect_seconds_total,
        "hit_effect_minutes": minutes(hit_effect_seconds_total),
        "support_event_seconds": support_event_seconds,
        "cashless_play_seconds": cashless_play_seconds,
        "cashless_play_minutes": minutes(cashless_play_seconds),
        "cashless_play_share": cashless_share,
        "time_assumptions": assumption_dict(time_assumptions),
        "strategy": strategy,
        "strategy_label": STRATEGIES[strategy],
        "spins_per_1000y": spins_per_1000y,
        "observed_spins_per_1000y": observed_spins_per_1000y,
        "true_spins_per_1000y": true_spins_per_1000y,
        "border_spins_per_1000y": border_spins_per_1000y,
        "border_spins_per_1000yen": border_spins_per_1000y,
        "spin_rate_quality_stddev": effective_quality_stddev,
        "spin_rate_min": spin_rate_min,
        "spin_rate_max": spin_rate_max,
        "start_probability": start_probability,
        "start_variance": start_variance,
        "lend_rate": lend_rate,
        "exchange_rate": exchange_rate,
        "card_reuse": card_reuse,
        "session_policy": session_policy,
        "session_policy_label": SESSION_POLICIES[session_policy],
        **flags,
    }

def simulate_multiple(
    machine: Machine,
    budget: int,
    lend_rate: float,
    spins_per_1000y: int,
    exchange_rate: float,
    iterations: int,
    strategy: str = "no_rule",
    card_reuse: bool = True,
    stop_loss_spin_threshold: int = 70,
    stop_loss_probe_yen: int = 1000,
    record_events: bool = False,
    session_policy: str = "fixed_spin_cap",
    max_normal_spins: int = None,
    start_variance: bool = True,
    border_spins_per_1000y: float = None,
    spin_rate_quality_stddev: float = 3.0,
    spin_rate_min: float = None,
    spin_rate_max: float = None,
    time_assumptions: TimeAssumptions = None,
    session_time_limit_minutes: float = HARD_SESSION_TIME_LIMIT_MINUTES,
    cash_input_cutoff_minutes: float = LAST_CASH_INPUT_CUTOFF_MINUTES,
    soft_stop_minutes: float = SESSION_TIME_LIMIT_MINUTES,
) -> List[Dict[str, Any]]:
    """반복 시뮬레이션을 수행하고 결과 리스트를 반환"""
    results = []
    for _ in range(iterations):
        res = simulate_single(
            machine,
            budget,
            lend_rate,
            spins_per_1000y,
            exchange_rate,
            strategy=strategy,
            card_reuse=card_reuse,
            stop_loss_spin_threshold=stop_loss_spin_threshold,
            stop_loss_probe_yen=stop_loss_probe_yen,
            record_events=record_events,
            session_policy=session_policy,
            max_normal_spins=max_normal_spins,
            start_variance=start_variance,
            border_spins_per_1000y=border_spins_per_1000y,
            spin_rate_quality_stddev=spin_rate_quality_stddev,
            spin_rate_min=spin_rate_min,
            spin_rate_max=spin_rate_max,
            time_assumptions=time_assumptions,
            session_time_limit_minutes=session_time_limit_minutes,
            cash_input_cutoff_minutes=cash_input_cutoff_minutes,
            soft_stop_minutes=soft_stop_minutes,
        )
        results.append(res)
    return results

def run_matrix_simulation(
    machine: Machine,
    lend_rate: float,
    exchange_rate: float,
    iterations: int,
    budget: int = 10000,
    strategy: str = "no_rule",
    spin_rates: List[int] = None,
    session_policy: str = "fixed_spin_cap",
    start_variance: bool = True,
    border_spins_per_1000y: float = None,
    spin_rate_quality_stddev: float = 3.0,
    time_assumptions: TimeAssumptions = None,
) -> List[Dict[str, Any]]:
    """예산과 회전율에 따른 매트릭스 시뮬레이션을 수행합니다."""
    budgets = [budget]
    spin_cases = (
        border_case_rates(border_spins_per_1000y)
        if spin_rates is None
        else [
            {
                "rotation_basis": "absolute",
                "rotation_label": f"{spins}회",
                "spins_per_1000y": float(spins),
                "border_margin": None,
            }
            for spins in spin_rates
        ]
    )
    matrix_results = []
    
    for budget in budgets:
        for spin_case in spin_cases:
            spins = spin_case["spins_per_1000y"]
            results = simulate_multiple(
                machine,
                budget,
                lend_rate,
                spins,
                exchange_rate,
                iterations,
                strategy=strategy,
                session_policy=session_policy,
                start_variance=start_variance,
                border_spins_per_1000y=border_spins_per_1000y,
                spin_rate_quality_stddev=spin_rate_quality_stddev,
                time_assumptions=time_assumptions,
            )
            matrix_results.append({
                "budget": budget,
                "spins_per_1000y": spins,
                "border_spins_per_1000yen": border_spins_per_1000y,
                "rotation_basis": spin_case["rotation_basis"],
                "rotation_label": spin_case["rotation_label"],
                "border_margin": spin_case["border_margin"],
                "strategy": strategy,
                "session_policy": session_policy,
                "start_variance": start_variance,
                "results": results
            })
    return matrix_results


def run_budget_matrix(
    machine: Machine,
    lend_rate: float,
    exchange_rate: float,
    iterations: int,
    budgets: List[int] = None,
    spins_per_1000y: int = 80,
    strategy: str = "no_rule",
    session_policy: str = "fixed_spin_cap",
    max_normal_spin_multiplier: int | None = None,
    start_variance: bool = True,
    border_spins_per_1000y: float = None,
    spin_rate_quality_stddev: float = 3.0,
    time_assumptions: TimeAssumptions = None,
) -> List[Dict[str, Any]]:
    budgets = budgets or BUDGET_CASES
    session_policy = normalize_session_policy(session_policy)
    matrix_results = []

    for budget in budgets:
        max_normal_spins = None
        if (
            session_policy == "play_until_budget_and_balls_gone"
            and max_normal_spin_multiplier is not None
        ):
            max_normal_spins = int((budget / 1000) * spins_per_1000y * max_normal_spin_multiplier)
        results = simulate_multiple(
            machine,
            budget,
            lend_rate,
            spins_per_1000y,
            exchange_rate,
            iterations,
            strategy=strategy,
            session_policy=session_policy,
            max_normal_spins=max_normal_spins,
            start_variance=start_variance,
            border_spins_per_1000y=border_spins_per_1000y,
            spin_rate_quality_stddev=spin_rate_quality_stddev,
            time_assumptions=time_assumptions,
        )
        matrix_results.append({
            "budget": budget,
            "spins_per_1000y": spins_per_1000y,
            "border_spins_per_1000yen": border_spins_per_1000y,
            "strategy": strategy,
            "session_policy": session_policy,
            "start_variance": start_variance,
            "results": results,
        })
    return matrix_results


def run_strategy_matrix(
    machine: Machine,
    lend_rate: float,
    exchange_rate: float,
    budget: int,
    iterations: int,
    spin_rates: List[int] = None,
    strategies: List[str] = None,
    session_policy: str = "fixed_spin_cap",
    start_variance: bool = True,
    border_spins_per_1000y: float = None,
    spin_rate_quality_stddev: float = 3.0,
    time_assumptions: TimeAssumptions = None,
) -> List[Dict[str, Any]]:
    spin_cases = (
        border_case_rates(border_spins_per_1000y)
        if spin_rates is None
        else [
            {
                "rotation_basis": "absolute",
                "rotation_label": f"{spins}회",
                "spins_per_1000y": float(spins),
                "border_margin": None,
            }
            for spins in spin_rates
        ]
    )
    strategies = strategies or list(STRATEGIES.keys())
    rows = []
    for strategy in strategies:
        for spin_case in spin_cases:
            spins = spin_case["spins_per_1000y"]
            rows.append(
                {
                    "budget": budget,
                    "spins_per_1000y": spins,
                    "border_spins_per_1000yen": border_spins_per_1000y,
                    "rotation_basis": spin_case["rotation_basis"],
                    "rotation_label": spin_case["rotation_label"],
                    "border_margin": spin_case["border_margin"],
                    "strategy": strategy,
                    "strategy_label": STRATEGIES[strategy],
                    "session_policy": session_policy,
                    "start_variance": start_variance,
                    "results": simulate_multiple(
                        machine,
                        budget,
                        lend_rate,
                        spins,
                        exchange_rate,
                        iterations,
                        strategy=strategy,
                        session_policy=session_policy,
                        start_variance=start_variance,
                        border_spins_per_1000y=border_spins_per_1000y,
                        spin_rate_quality_stddev=spin_rate_quality_stddev,
                        time_assumptions=time_assumptions,
                    ),
                }
            )
    return rows
