import math
import random


DEFAULT_SPIN_RATE_STDDEV = 3.0
DEFAULT_SPIN_RATE_MARGIN = 12.0


def clamp(value: float, lower: float, upper: float) -> float:
    if lower > upper:
        lower, upper = upper, lower
    return max(lower, min(upper, value))


def rented_balls_per_1000yen(lend_rate: float) -> float:
    if lend_rate <= 0:
        return 0.0
    return 1000.0 / lend_rate


def start_probability_from_rate(lend_rate: float, spins_per_1000y: float) -> float:
    balls = rented_balls_per_1000yen(lend_rate)
    if balls <= 0 or spins_per_1000y <= 0:
        return 0.0
    return max(0.0, min(1.0, spins_per_1000y / balls))


def sample_binomial(trials: int, probability: float) -> int:
    """Sample Binomial(trials, probability) with stdlib-only approximations."""
    trials = int(trials)
    probability = max(0.0, min(1.0, probability))
    if trials <= 0 or probability <= 0.0:
        return 0
    if probability >= 1.0:
        return trials

    mean = trials * probability
    variance = trials * probability * (1.0 - probability)
    if trials < 200 or mean < 20:
        return sum(1 for _ in range(trials) if random.random() < probability)

    sampled = int(round(random.gauss(mean, math.sqrt(variance))))
    return max(0, min(trials, sampled))


def sample_start_spins(ball_count: float, start_probability: float) -> int:
    return sample_binomial(int(ball_count), start_probability)


def observed_rate_per_1000yen(spins: int, budget: int) -> float:
    if budget <= 0:
        return 0.0
    return spins / (budget / 1000.0)


def default_spin_rate_bounds(
    reference_spins_per_1000y: float,
    border_spins_per_1000y: float = None,
    margin: float = DEFAULT_SPIN_RATE_MARGIN,
) -> tuple[float, float]:
    """Return conservative lower/upper bounds for one table's hidden rotation quality."""
    reference = max(1.0, float(reference_spins_per_1000y or 1.0))
    anchors = [reference]
    if border_spins_per_1000y is not None and border_spins_per_1000y > 0:
        anchors.append(float(border_spins_per_1000y))
    lower = max(1.0, min(anchors) - margin)
    upper = max(anchors) + margin
    return lower, upper


def sample_truncated_normal(mean: float, stddev: float, lower: float, upper: float) -> float:
    """Sample a normal distribution while keeping impossible rotation values out."""
    mean = float(mean)
    stddev = max(0.0, float(stddev or 0.0))
    if stddev <= 0.0:
        return clamp(mean, lower, upper)

    for _ in range(40):
        sampled = random.gauss(mean, stddev)
        if lower <= sampled <= upper:
            return sampled
    return clamp(random.gauss(mean, stddev), lower, upper)


def sample_session_spin_rate(
    reference_spins_per_1000y: float,
    border_spins_per_1000y: float = None,
    quality_stddev: float = DEFAULT_SPIN_RATE_STDDEV,
    min_spins_per_1000y: float = None,
    max_spins_per_1000y: float = None,
) -> float:
    """Sample the hidden table quality before per-ball start-entry variance.

    The reference value is the player's field estimate or scenario input. The
    sampled value represents table-level physical conditions such as 釘(못),
    風車(풍차), ステージ(스테이지), ワープ(와프), and 네카세.
    """
    reference = max(1.0, float(reference_spins_per_1000y or 1.0))
    lower, upper = default_spin_rate_bounds(reference, border_spins_per_1000y)
    if min_spins_per_1000y is not None:
        lower = max(1.0, float(min_spins_per_1000y))
    if max_spins_per_1000y is not None:
        upper = max(lower, float(max_spins_per_1000y))
    return sample_truncated_normal(reference, quality_stddev, lower, upper)


def estimate_rate_from_observed_spins(observed_spins: int, observed_yen: int) -> float:
    """Convert a field note such as 200円で14回転 into spins per 1000 yen."""
    if observed_yen <= 0:
        return 0.0
    return (float(observed_spins) / float(observed_yen)) * 1000.0
