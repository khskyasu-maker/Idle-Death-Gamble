import math
import statistics
from typing import Any, Dict, List


PROFIT_CONDITION_MIN_SAMPLES = 30
PROFIT_CONDITION_TARGET_RATE = 50.0
PROFIT_CONDITION_THRESHOLDS = [1, 2, 3, 5, 7, 10, 15, 20]


def _pct(value: float) -> str:
    return f"{value:.1f}%"


def wilson_interval(successes: int, total: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson score interval for a binomial proportion, returned as percentages."""
    if total <= 0:
        return 0.0, 0.0
    p = successes / total
    denominator = 1 + (z * z / total)
    centre = p + (z * z / (2 * total))
    margin = z * math.sqrt((p * (1 - p) / total) + (z * z / (4 * total * total)))
    low = max(0.0, (centre - margin) / denominator)
    high = min(1.0, (centre + margin) / denominator)
    return low * 100.0, high * 100.0


def profit_condition_judgement(sample_count: int, ci_low: float, ci_high: float) -> str:
    if sample_count < PROFIT_CONDITION_MIN_SAMPLES:
        return "표본적음"
    if ci_low > PROFIT_CONDITION_TARGET_RATE:
        return "플러스우세"
    if ci_high < PROFIT_CONDITION_TARGET_RATE:
        return "플러스열세"
    return "경계"


def profit_condition_label(kind: str, threshold: int) -> str:
    if kind == "hits":
        return f"大当り(대당첨) {threshold}회+"
    return f"최대연속 {threshold}연+"


def profit_condition_short_label(kind: str, threshold: int) -> str:
    if kind == "hits":
        return f"{threshold}당+"
    return f"{threshold}연+"


def profit_condition_thresholds(max_value: int, include_one: bool) -> List[int]:
    if max_value <= 0:
        return []
    thresholds = [
        t for t in PROFIT_CONDITION_THRESHOLDS
        if t <= max_value and (include_one or t > 1)
    ]
    if include_one and 1 not in thresholds:
        thresholds.insert(0, 1)
    if max_value not in thresholds and (include_one or max_value > 1):
        thresholds.append(max_value)
    return sorted(set(thresholds))


def calculate_profit_condition_rows(results: List[Dict[str, Any]], iterations: int) -> List[Dict[str, Any]]:
    """Conditioned profit rates for actual useful outcomes, not just first-hit exposure."""
    if not results or iterations <= 0:
        return []

    definitions = [
        ("hits", "total_hits", True),
        ("streak", "max_streak", False),
    ]
    rows = []

    for kind, field, include_one in definitions:
        max_value = max(int(r.get(field, 0) or 0) for r in results)
        for threshold in profit_condition_thresholds(max_value, include_one):
            sample = [r for r in results if int(r.get(field, 0) or 0) >= threshold]
            sample_count = len(sample)
            if sample_count <= 0:
                continue

            positives = [r for r in sample if r["net_profit"] > 0]
            positive_count = len(positives)
            positive_rate = (positive_count / sample_count) * 100.0
            ci_low, ci_high = wilson_interval(positive_count, sample_count)
            profits = [r["net_profit"] for r in sample]
            rows.append(
                {
                    "kind": kind,
                    "threshold": threshold,
                    "label": profit_condition_label(kind, threshold),
                    "short_label": profit_condition_short_label(kind, threshold),
                    "sample_count": sample_count,
                    "occurrence_rate": (sample_count / iterations) * 100.0,
                    "positive_count": positive_count,
                    "positive_rate": positive_rate,
                    "positive_rate_ci_low": ci_low,
                    "positive_rate_ci_high": ci_high,
                    "avg_profit": int(statistics.mean(profits)),
                    "median_profit": int(statistics.median(profits)),
                    "judgement": profit_condition_judgement(sample_count, ci_low, ci_high),
                }
            )

    return rows


def best_profit_condition(rows: List[Dict[str, Any]], kind: str = None) -> Dict[str, Any]:
    candidates = [
        row for row in rows
        if (kind is None or row["kind"] == kind)
        and row["sample_count"] >= PROFIT_CONDITION_MIN_SAMPLES
        and row["positive_rate_ci_low"] > PROFIT_CONDITION_TARGET_RATE
    ]
    if not candidates:
        return {}
    return sorted(candidates, key=lambda row: (row["threshold"], -row["occurrence_rate"]))[0]


def profit_condition_summary_from_rows(rows: List[Dict[str, Any]]) -> str:
    parts = []
    for kind in ["hits", "streak"]:
        row = best_profit_condition(rows, kind)
        if row:
            parts.append(
                f"{row['short_label']} {_pct(row['positive_rate'])}"
                f"(발생 {_pct(row['occurrence_rate'])})"
            )
    return " / ".join(parts) if parts else "통계적으로 우세한 플러스 조건 없음"


T_CRITICAL_95 = {
    1: 12.706,
    2: 4.303,
    3: 3.182,
    4: 2.776,
    5: 2.571,
    6: 2.447,
    7: 2.365,
    8: 2.306,
    9: 2.262,
    10: 2.228,
    11: 2.201,
    12: 2.179,
    13: 2.160,
    14: 2.145,
    15: 2.131,
    16: 2.120,
    17: 2.110,
    18: 2.101,
    19: 2.093,
    20: 2.086,
    21: 2.080,
    22: 2.074,
    23: 2.069,
    24: 2.064,
    25: 2.060,
    26: 2.056,
    27: 2.052,
    28: 2.048,
    29: 2.045,
    30: 2.042,
}


def mean_critical_value(sample_size: int) -> float:
    """95% two-sided critical value for mean Monte Carlo uncertainty."""
    if sample_size < 2:
        return 0.0
    degrees_of_freedom = sample_size - 1
    if degrees_of_freedom <= 30:
        return T_CRITICAL_95[degrees_of_freedom]
    if degrees_of_freedom <= 40:
        return 2.021
    if degrees_of_freedom <= 60:
        return 2.000
    if degrees_of_freedom <= 120:
        return 1.980
    return 1.960


def mean_interval(values: List[int], critical_value: float = None) -> tuple[int, int]:
    if not values:
        return 0, 0
    if len(values) < 2:
        value = int(values[0])
        return value, value
    mean = statistics.mean(values)
    stderr = statistics.stdev(values) / math.sqrt(len(values))
    critical = mean_critical_value(len(values)) if critical_value is None else critical_value
    return int(mean - (critical * stderr)), int(mean + (critical * stderr))


def standard_error(values: List[int]) -> float:
    if len(values) < 2:
        return 0.0
    return statistics.stdev(values) / math.sqrt(len(values))


def quantile_interval(values: List[int], percentile: float, z: float = 1.96) -> tuple[int, int]:
    """Approximate non-parametric CI for a quantile using binomial rank bounds."""
    if not values:
        return 0, 0
    sorted_values = sorted(values)
    n = len(sorted_values)
    if n == 1:
        value = int(sorted_values[0])
        return value, value

    p = max(0.0, min(1.0, percentile))
    centre_rank = p * (n - 1)
    rank_stderr = math.sqrt(max(0.0, n * p * (1.0 - p)))
    low_index = max(0, int(math.floor(centre_rank - (z * rank_stderr))))
    high_index = min(n - 1, int(math.ceil(centre_rank + (z * rank_stderr))))
    return int(sorted_values[low_index]), int(sorted_values[high_index])


def tail_mean(values: List[int], percentile: float, lower: bool = True) -> int:
    if not values:
        return 0
    sorted_values = sorted(values)
    count = max(1, int(math.ceil(len(sorted_values) * percentile)))
    tail_values = sorted_values[:count] if lower else sorted_values[-count:]
    return int(statistics.mean(tail_values))


def percentile_value(values: List[int], percentile: float) -> int:
    if not values:
        return 0
    sorted_values = sorted(values)
    index = min(len(sorted_values) - 1, max(0, int(len(sorted_values) * percentile)))
    return int(sorted_values[index])


def percentile_float(values: List[float], percentile: float) -> float:
    if not values:
        return 0.0
    sorted_values = sorted(values)
    index = min(len(sorted_values) - 1, max(0, int(len(sorted_values) * percentile)))
    return float(sorted_values[index])
