from session_limits import SESSION_TIME_LIMIT_MINUTES


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
    flags: dict[str, bool],
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


__all__ = [
    "SESSION_POLICIES",
    "STRATEGIES",
    "apply_strategy_rules",
    "current_profit_balls",
    "normalize_session_policy",
    "normalize_strategy",
]
