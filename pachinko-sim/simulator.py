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


SPIN_RATE_CASES = ABSOLUTE_SPIN_RATE_CASES
BUDGET_CASES = [10000, 20000, 30000, 40000, 50000]
PROFILE_BUDGET_CASES = [1000, 10000, 20000, 30000, 40000, 50000]

SESSION_POLICIES = {
    "fixed_spin_cap": "예산 고정 회전수",
    "play_until_budget_and_balls_gone": "현금+보유구슬 소진",
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
) -> Dict[str, Any]:
    """단일 시뮬레이션: 현금 투입, 보유 구슬, 우타치 소모, 전략을 함께 반영합니다."""

    strategy = normalize_strategy(strategy)
    session_policy = normalize_session_policy(session_policy)

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
    }

    effective_spins_per_1000y = max(1.0, observed_spins_per_1000y)
    spin_cost_balls = rented_balls_1000 / effective_spins_per_1000y
    spin_cost_yen = 1000.0 / effective_spins_per_1000y
    safety_counter = 0

    def pay_normal_spins(spin_count: int) -> int:
        nonlocal bank_balls, cash_spent, normal_balls_fired
        if spin_count <= 0:
            return 0

        if card_reuse:
            remaining_cash_balls = max(0.0, (budget - cash_spent) / lend_rate)
            max_affordable = int((bank_balls + remaining_cash_balls) / spin_cost_balls)
        else:
            max_affordable = int((budget - cash_spent) / spin_cost_yen)

        playable_spins = max(0, min(spin_count, max_affordable))
        if playable_spins <= 0:
            return 0

        if card_reuse:
            ball_cost = spin_cost_balls * playable_spins
            reusable_balls = min(bank_balls, ball_cost)
            bank_balls -= reusable_balls
            cash_spent += (ball_cost - reusable_balls) * lend_rate
            normal_balls_fired += ball_cost
        else:
            cash_spent += spin_cost_yen * playable_spins
            normal_balls_fired += (spin_cost_yen * playable_spins) / lend_rate

        if cash_spent > budget and cash_spent - budget < 0.000001:
            cash_spent = float(budget)
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

    while True:
        safety_counter += 1
        if safety_counter > 100000:
            flags["safety_stopped"] = True
            break

        current_prob = machine.normal_prob

        if state == 'NORMAL':
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

            played_spins = pay_normal_spins(spins_to_take)
            spins_used += played_spins
            if played_spins < spins_to_take:
                break

            if played_spins < next_normal_event:
                if stop_loss_normal_spin_cap is not None and spins_used >= stop_loss_normal_spin_cap:
                    flags["stop_loss_triggered"] = True
                    settle_stop_loss_probe_cost()
                elif normal_spin_cap is not None and spins_used >= normal_spin_cap:
                    flags["normal_spin_cap_triggered"] = True
                break

            if support_event:
                payout = get_payout(machine.normal_support_dist)
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
                    right_spins_to_take = wait_to_hit
                    right_spins += right_spins_to_take
                    bank_balls = max(
                        0.0,
                        bank_balls - (machine.right_spend_per_spin.get(state, 0.0) * right_spins_to_take),
                    )
                else:
                    right_spins_to_take = wait_to_fall
                    right_spins += right_spins_to_take
                    bank_balls = max(
                        0.0,
                        bank_balls - (machine.right_spend_per_spin.get(state, 0.0) * right_spins_to_take),
                    )

                    reserve_spins = machine.fall_reserve_spins.get(state, 0)
                    if reserve_spins <= 0:
                        state = 'NORMAL'
                        streak = 0
                        rush_active = False
                        continue

                    wait_to_reserve_hit = spins_until_hit(machine.high_prob)
                    reserve_spins_to_take = min(wait_to_reserve_hit, reserve_spins)
                    right_spins += reserve_spins_to_take
                    bank_balls = max(
                        0.0,
                        bank_balls - (machine.right_spend_per_spin.get(state, 0.0) * reserve_spins_to_take),
                    )
                    if reserve_spins_to_take < wait_to_reserve_hit:
                        state = 'NORMAL'
                        streak = 0
                        rush_active = False
                        continue
            elif spins_left > 0:
                wait_to_hit = spins_until_hit(machine.high_prob)
                right_spins_to_take = min(wait_to_hit, spins_left)
                spins_left -= right_spins_to_take
                right_spins += right_spins_to_take
                bank_balls = max(
                    0.0,
                    bank_balls - (machine.right_spend_per_spin.get(state, 0.0) * right_spins_to_take),
                )
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
                right_spins += right_spins_to_take
                bank_balls = max(
                    0.0,
                    bank_balls - (machine.right_spend_per_spin.get(state, 0.0) * right_spins_to_take),
                )
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
            right_spins += wait_to_hit
            bank_balls = max(
                0.0,
                bank_balls - (machine.right_spend_per_spin.get(state, 0.0) * wait_to_hit),
            )

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
    net_profit = int(final_money - cash_spent)
    exchange_loss = int(final_balls * lend_rate - final_money)
    
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
        "net_profit": net_profit,
        "cash_spent": int(cash_spent),
        "exchange_loss": exchange_loss,
        "experienced_rush": rush_entries > 0 or lt_entries > 0,
        "rush_entries": rush_entries,
        "lt_entries": lt_entries,
        "upper_entries": upper_entries,
        "hit_events": hit_events,
        "spins_used": spins_used,
        "right_spins": right_spins,
        "normal_balls_fired": int(normal_balls_fired),
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
    max_normal_spin_multiplier: int = 2,
    start_variance: bool = True,
    border_spins_per_1000y: float = None,
    spin_rate_quality_stddev: float = 3.0,
) -> List[Dict[str, Any]]:
    budgets = budgets or BUDGET_CASES
    session_policy = normalize_session_policy(session_policy)
    matrix_results = []

    for budget in budgets:
        max_normal_spins = None
        if session_policy == "play_until_budget_and_balls_gone":
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
                    ),
                }
            )
    return rows
