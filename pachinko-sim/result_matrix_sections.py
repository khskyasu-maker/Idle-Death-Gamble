from typing import Any

from result_output_helpers import print_ascii_table
from session_limits import (
    HARD_SESSION_TIME_LIMIT_HOURS,
    SESSION_TIME_LIMIT_HOURS,
)


MATRIX_SUMMARY_HEADERS = [
    "입력회전",
    "가능회전",
    "평균시간",
    "보더+/-",
    "판정/보더비",
    "플러스",
    "평균",
    "중앙",
    "하위10",
    "상위10",
    "실익조건",
    "주의",
]
MATRIX_RISK_HEADERS = [
    "회전",
    "당첨",
    "0회",
    "이론0회",
    "RUSH",
    "LT",
    "상위RUSH",
    "회수50/80/100",
    "최대당/연",
    "상위10당/연",
]

BUDGET_MONEY_HEADERS = [
    "예산",
    "가능회전",
    "평균회전",
    "판정/보더비",
    "플러스",
    "평균",
    "중앙",
    "하위10",
    "상위10",
    "실익조건",
    "평균현금",
]
BUDGET_RISK_HEADERS = [
    "예산",
    "당첨",
    "0회",
    "이론0회",
    "RUSH",
    "LT",
    "상위RUSH",
    "회수50/80/100",
    "최대당/연",
]
BUDGET_TIME_HEADERS = [
    "예산",
    "평균시간",
    "P50/P90",
    "현금없는",
    "무현금비율",
    "소진후",
    "통상",
    "우타치",
    "당첨연출",
    "보류대기",
    "현금속도",
]
BUDGET_STAY_HEADERS = [
    "예산",
    "1h+",
    "2h+",
    "3h+",
    "4h+",
    "6h+",
    "8h+",
    f"{SESSION_TIME_LIMIT_HOURS}h+",
    f"{SESSION_TIME_LIMIT_HOURS}h정리",
    f"{HARD_SESSION_TIME_LIMIT_HOURS}h하드",
    "현금마감",
]
BUDGET_REMAINING_HEADERS = [
    "예산",
    "예산소진",
    "미사용현금",
    "교환가능",
    "최종잔류",
    "P10/P50/P90",
    "잔류손익",
    "완전소진",
]
BUDGET_STATS_HEADERS = [
    "예산",
    "평균SE",
    "평균95CI",
    "중앙95CI",
    "하위10 95CI",
    "CVaR10",
    "상위10 95CI",
]

PROFILE_FEEL_HEADERS = [
    "예산",
    "가능회전",
    "이론당첨",
    "시뮬당첨",
    "평균초당첨",
    "초당첨P50/P90",
    "총체감P50/P90",
    "평균아타리",
    "초당첨후",
    "평균연속",
    "평균우타치",
    "RUSH",
    "LT",
    "상위RUSH",
    "실익조건",
    "중앙",
    "하위10",
]
PROFILE_TIME_HEADERS = BUDGET_TIME_HEADERS
PROFILE_STAY_HEADERS = [
    "예산",
    "1h+",
    "2h+",
    "3h+",
    "4h+",
    "6h+",
    "8h+",
    f"{SESSION_TIME_LIMIT_HOURS}h+",
    "최종잔류",
]
PROFILE_BENCHMARK_HEADERS = ["지표", "공개/일본값", "모델값", "차이", "판정", "출처"]

STRATEGY_CORE_HEADERS = [
    "전략",
    "회전",
    "점수",
    "플러스",
    "평균시간",
    "평균",
    "중앙",
    "하위10",
    "0회",
    "RUSH",
    "LT",
    "상위RUSH",
]
STRATEGY_CONDITION_HEADERS = [
    "전략",
    "회전",
    "보더+/-",
    "판정/보더비",
    "주의",
    "최대당/연",
    "회수50",
    "회수80",
    "회수100",
    "실익조건",
    "익절",
    "손절",
]
STRATEGY_TOP_HEADERS = ["순위", "전략", "회전", "점수", "플러스", "평균", "하위10", "보더+/-", "주의"]


def print_matrix_tables(rows: dict[str, list[list[Any]]]):
    print_ascii_table("ASCII 조건 수익표", MATRIX_SUMMARY_HEADERS, rows["summary"])
    print_ascii_table("ASCII 조건 체감표", MATRIX_RISK_HEADERS, rows["risk"])


def print_budget_tables(tables: dict[str, list[list[Any]]]):
    print_ascii_table("ASCII 예산 손익표", BUDGET_MONEY_HEADERS, tables["money"])
    print_ascii_table("ASCII 예산 체감표", BUDGET_RISK_HEADERS, tables["risk"])
    print_ascii_table("ASCII 예산 체류 시간표", BUDGET_TIME_HEADERS, tables["time"])
    print_ascii_table("ASCII 체류 도달률표", BUDGET_STAY_HEADERS, tables["stay"])
    print_ascii_table("ASCII 최종 잔류액표", BUDGET_REMAINING_HEADERS, tables["remaining"])
    print_ascii_table("ASCII 통계 신뢰도", BUDGET_STATS_HEADERS, tables["stats"])


def print_profile_tables(tables: dict[str, list[list[Any]]], benchmark_table_rows: list[list[Any]]):
    print_ascii_table("ASCII 예산별 아타리/연속 주요 지표", PROFILE_FEEL_HEADERS, tables["feel"])
    print_ascii_table("ASCII 예산별 체류 시간", PROFILE_TIME_HEADERS, tables["time"])
    print_ascii_table("ASCII 예산별 체류 도달률", PROFILE_STAY_HEADERS, tables["stay"])
    print_ascii_table("ASCII 공개 일본 스펙값 대비 위화감 체크", PROFILE_BENCHMARK_HEADERS, benchmark_table_rows)


def print_strategy_tables(tables: dict[str, list[list[Any]]]):
    print_ascii_table("ASCII 전략 핵심 비교", STRATEGY_CORE_HEADERS, tables["core"])
    print_ascii_table("ASCII 전략 조건/발동", STRATEGY_CONDITION_HEADERS, tables["condition"])
    print_ascii_table("ASCII 조건 비교 상위 5개", STRATEGY_TOP_HEADERS, tables["top"])
