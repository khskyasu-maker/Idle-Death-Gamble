import random
from typing import Dict, Any, List
from machines import Machine, Payout  # noqa: F401
from session_accounting import (
    SESSION_POLICIES,
    STRATEGIES,
    apply_strategy_rules,
    current_profit_balls,
    normalize_session_policy,
    normalize_strategy,
)
from session_sampling import (
    HIT_LABELS,  # noqa: F401
    bilingual_hit_label,
    get_payout,
    jitan_denominator,
    sample_payout_balls,
    spins_until_hit,
)
from session_setup import build_session_start
from session_limits import (
    HARD_SESSION_TIME_LIMIT_MINUTES,
    LAST_CASH_INPUT_CUTOFF_MINUTES,
    SESSION_TIME_LIMIT_MINUTES,
)
from session_runtime import (
    cap_spins_before_cash_cutoff,
    cap_spins_by_seconds,
    limit_minutes_to_seconds,
    limit_reached,
    normal_seconds_per_spin,
    remaining_seconds,
)
from time_model import (
    TimeAssumptions,
    assumption_dict,
    gross_launch_balls,
    hit_effect_seconds as hit_effect_time_seconds,
    minutes,
    normal_time_components,
    right_seconds,
    time_assumptions_for_machine,
)
from session_scenarios import BUDGET_CASES, PROFILE_BUDGET_CASES, SPIN_RATE_CASES


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

    session_start = build_session_start(
        budget=budget,
        lend_rate=lend_rate,
        spins_per_1000y=spins_per_1000y,
        strategy=strategy,
        session_policy=session_policy,
        max_normal_spins=max_normal_spins,
        start_variance=start_variance,
        border_spins_per_1000y=border_spins_per_1000y,
        spin_rate_quality_stddev=spin_rate_quality_stddev,
        spin_rate_min=spin_rate_min,
        spin_rate_max=spin_rate_max,
        stop_loss_probe_yen=stop_loss_probe_yen,
        stop_loss_spin_threshold=stop_loss_spin_threshold,
        time_assumptions=time_assumptions,
    )
    true_spins_per_1000y = session_start.true_spins_per_1000y
    effective_quality_stddev = session_start.effective_quality_stddev
    rented_balls_1000 = session_start.rented_balls_1000
    start_probability = session_start.start_probability
    expected_total_spins_possible = session_start.expected_total_spins_possible
    observed_spins_per_1000y = session_start.observed_spins_per_1000y
    total_spins_possible = session_start.total_spins_possible
    stop_loss_probe_budget = session_start.stop_loss_probe_budget
    stop_loss_probe_spins = session_start.stop_loss_probe_spins
    stop_loss_probe_rate = session_start.stop_loss_probe_rate
    normal_spin_cap = session_start.normal_spin_cap
    stop_loss_normal_spin_cap = session_start.stop_loss_normal_spin_cap

    spins_used = 0
    right_spins = 0
    total_out_balls = 0.0
    normal_net_balls_consumed = 0.0
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
    first_hit_cash_spent = None
    first_hit_play_seconds = None
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
    session_time_limit_seconds = limit_minutes_to_seconds(session_time_limit_minutes)
    cash_input_cutoff_seconds = limit_minutes_to_seconds(cash_input_cutoff_minutes, allow_zero=True)
    soft_stop_seconds = limit_minutes_to_seconds(soft_stop_minutes)
    safety_counter = 0

    def elapsed_seconds() -> float:
        return normal_play_seconds + right_play_seconds + hit_effect_seconds_total + support_event_seconds

    def mark_cash_budget_exhausted():
        nonlocal cash_budget_exhausted_seconds
        if cash_budget_exhausted_seconds is None and cash_spent >= budget - spin_cost_yen:
            cash_budget_exhausted_seconds = elapsed_seconds()

    def session_seconds_remaining() -> float | None:
        return remaining_seconds(session_time_limit_seconds, elapsed_seconds())

    def cash_input_allowed() -> bool:
        return not limit_reached(cash_input_cutoff_seconds, elapsed_seconds())

    def soft_stop_reached() -> bool:
        return limit_reached(soft_stop_seconds, elapsed_seconds())

    def soft_stop_seconds_remaining() -> float | None:
        return remaining_seconds(soft_stop_seconds, elapsed_seconds())

    def cap_normal_spins_by_cash_cutoff(spin_count: int) -> tuple[int, bool]:
        if cash_input_cutoff_seconds is None or elapsed_seconds() >= cash_input_cutoff_seconds:
            return spin_count, False
        if cash_spent >= budget:
            return spin_count, False

        planned_ball_cost = spin_cost_balls * spin_count
        needs_new_cash = (not card_reuse) or bank_balls < planned_ball_cost
        if not needs_new_cash:
            return spin_count, False

        capped, limited_by_cutoff = cap_spins_before_cash_cutoff(
            spin_count,
            cash_input_cutoff_seconds,
            elapsed_seconds(),
            normal_seconds_per_spin(spin_cost_balls, time_assumptions),
        )
        if limited_by_cutoff:
            flags["cash_input_cutoff_triggered"] = True
        return capped, limited_by_cutoff

    def cap_normal_spins_by_soft_stop(spin_count: int) -> tuple[int, bool]:
        capped, limited_by_soft_stop = cap_spins_by_seconds(
            spin_count,
            soft_stop_seconds_remaining(),
            normal_seconds_per_spin(spin_cost_balls, time_assumptions),
        )
        if limited_by_soft_stop:
            flags["soft_stop_triggered"] = True
        return capped, limited_by_soft_stop

    def cap_spins_by_time(spin_count: int, seconds_per_spin: float) -> tuple[int, bool]:
        return cap_spins_by_seconds(spin_count, session_seconds_remaining(), seconds_per_spin)

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
        nonlocal bank_balls, cash_spent, normal_net_balls_consumed, normal_balls_fired
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
            normal_net_balls_consumed += ball_cost
        else:
            cash_cost = spin_cost_yen * playable_spins
            cash_spent += cash_cost
            ball_cost = cash_cost / lend_rate
            normal_net_balls_consumed += ball_cost

        time_parts = normal_time_components(playable_spins, ball_cost, time_assumptions)
        normal_balls_fired += time_parts["gross_launched_balls"]
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
        nonlocal cash_spent, normal_net_balls_consumed, normal_balls_fired
        if total_hits > 0 or stop_loss_probe_budget <= 0:
            return
        target_cash_spent = min(float(budget), float(stop_loss_probe_budget))
        if cash_spent < target_cash_spent:
            net_balls = (target_cash_spent - cash_spent) / lend_rate
            normal_net_balls_consumed += net_balls
            normal_balls_fired += gross_launch_balls(net_balls, time_assumptions)
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
                normal_seconds_per_spin(spin_cost_balls, time_assumptions),
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
                elif state in ['JITAN', 'UPPER_JITAN', 'JINBEE_JITAN']:
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
                    if state == 'LT':
                        state = 'LT_JITAN'
                    elif state == 'UPPER':
                        state = 'UPPER_JITAN'
                    else:
                        state = 'JITAN'
                    spins_left = jitan_reserve
                    jitan_reserve = 0
                    continue # 이번 턴은 당첨 추첨 없이 상태 전환만 처리
                else:
                    state = 'NORMAL'
                    streak = 0
                    rush_active = False
                    continue

        elif state in ['JITAN', 'LT_JITAN', 'UPPER_JITAN', 'JINBEE_JITAN']:
            current_prob = jitan_denominator(machine)
            if spins_left > 0:
                wait_to_hit = spins_until_hit(current_prob)
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
                first_hit_cash_spent = int(cash_spent)
                first_hit_play_seconds = elapsed_seconds()
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
            elif state == 'LT_JITAN':
                payout = get_payout(machine.lt_hit_dist)
            elif state == 'KAKUBEN':
                payout = get_payout(machine.kakuben_hit_dist)
            elif state == 'LT':
                payout = get_payout(machine.lt_hit_dist)
            elif state in ['UPPER', 'UPPER_JITAN']:
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
                if state == 'UPPER' and previous_state not in ['UPPER', 'UPPER_JITAN']:
                    upper_entries += 1
                    upper_entry_event = True
                spins_left = payout.st_spins
                jitan_reserve = payout.jitan_spins
            elif state == 'JITAN':
                spins_left = payout.jitan_spins
                jitan_reserve = 0
            elif state == 'LT_JITAN':
                spins_left = payout.jitan_spins or payout.st_spins
                jitan_reserve = 0
            elif state == 'UPPER_JITAN':
                spins_left = payout.jitan_spins or payout.st_spins
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
                if previous_state not in ['LT', 'LT_JITAN']:
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
        "first_hit_cash_spent": first_hit_cash_spent,
        "first_hit_play_minutes": minutes(first_hit_play_seconds or 0.0),
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
        "normal_net_balls_consumed": int(normal_net_balls_consumed),
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
    seed: int | None = None,
) -> List[Dict[str, Any]]:
    """반복 시뮬레이션을 수행하고 결과 리스트를 반환"""
    previous_random_state = None
    if seed is not None:
        previous_random_state = random.getstate()
        random.seed(seed)

    results = []
    try:
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
    finally:
        if previous_random_state is not None:
            random.setstate(previous_random_state)
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
    from session_scenarios import run_matrix_simulation as _run_matrix_simulation

    return _run_matrix_simulation(
        machine,
        lend_rate,
        exchange_rate,
        iterations,
        budget=budget,
        strategy=strategy,
        spin_rates=spin_rates,
        session_policy=session_policy,
        start_variance=start_variance,
        border_spins_per_1000y=border_spins_per_1000y,
        spin_rate_quality_stddev=spin_rate_quality_stddev,
        time_assumptions=time_assumptions,
    )


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
    from session_scenarios import run_budget_matrix as _run_budget_matrix

    return _run_budget_matrix(
        machine,
        lend_rate,
        exchange_rate,
        iterations,
        budgets=budgets,
        spins_per_1000y=spins_per_1000y,
        strategy=strategy,
        session_policy=session_policy,
        max_normal_spin_multiplier=max_normal_spin_multiplier,
        start_variance=start_variance,
        border_spins_per_1000y=border_spins_per_1000y,
        spin_rate_quality_stddev=spin_rate_quality_stddev,
        time_assumptions=time_assumptions,
    )


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
    from session_scenarios import run_strategy_matrix as _run_strategy_matrix

    return _run_strategy_matrix(
        machine,
        lend_rate,
        exchange_rate,
        budget,
        iterations,
        spin_rates=spin_rates,
        strategies=strategies,
        session_policy=session_policy,
        start_variance=start_variance,
        border_spins_per_1000y=border_spins_per_1000y,
        spin_rate_quality_stddev=spin_rate_quality_stddev,
        time_assumptions=time_assumptions,
    )
