from dataclasses import dataclass
from typing import Any, Dict, List


ABSOLUTE_SPIN_RATE_CASES = [50, 60, 70, 80, 90, 100]
BORDER_MARGIN_CASES = [-10, -5, 0, 5, 10]
LOW_ABSOLUTE_SPIN_WARNING = 70.0


@dataclass(frozen=True)
class RotationEstimate:
    spins_per_1000y: float
    input_basis: str
    source_label: str
    border_margin: float | None = None
    observed_spins: float | None = None
    observed_yen: float | None = None
    observed_balls: float | None = None


def rented_balls_per_1000yen(lend_rate: float) -> float:
    if lend_rate <= 0:
        return 0.0
    return 1000.0 / float(lend_rate)


def spins_from_yen_observation(spins: float, yen: float) -> float:
    if yen <= 0:
        return 0.0
    return float(spins) / float(yen) * 1000.0


def spins_from_ball_unit(spins: float, balls: float, lend_rate: float) -> float:
    if balls <= 0:
        return 0.0
    return float(spins) * (rented_balls_per_1000yen(lend_rate) / float(balls))


def spins_from_border_margin(border_spins_per_1000y: float | None, margin: float) -> float | None:
    if border_spins_per_1000y is None:
        return None
    return max(1.0, float(border_spins_per_1000y) + float(margin))


def estimate_from_absolute_spins(spins_per_1000y: float) -> RotationEstimate:
    spins = float(spins_per_1000y)
    return RotationEstimate(
        spins_per_1000y=spins,
        input_basis="absolute",
        source_label=f"직접입력 {spins:.1f}회/1000엔",
    )


def estimate_from_yen_observation(spins: float, yen: float) -> RotationEstimate:
    normalized = spins_from_yen_observation(spins, yen)
    return RotationEstimate(
        spins_per_1000y=normalized,
        input_basis="cash_observation",
        source_label=f"{float(yen):.0f}엔당 {float(spins):.1f}회",
        observed_spins=float(spins),
        observed_yen=float(yen),
    )


def estimate_from_ball_unit(spins: float, balls: float, lend_rate: float) -> RotationEstimate:
    normalized = spins_from_ball_unit(spins, balls, lend_rate)
    return RotationEstimate(
        spins_per_1000y=normalized,
        input_basis="ball_unit",
        source_label=f"{float(balls):.0f}玉당 {float(spins):.1f}회",
        observed_spins=float(spins),
        observed_balls=float(balls),
    )


def estimate_from_border_margin(border_spins_per_1000y: float | None, margin: float) -> RotationEstimate:
    normalized = spins_from_border_margin(border_spins_per_1000y, margin)
    if normalized is None:
        return estimate_from_absolute_spins(LOW_ABSOLUTE_SPIN_WARNING)
    return RotationEstimate(
        spins_per_1000y=normalized,
        input_basis="border_margin",
        source_label=border_margin_label(float(margin)),
        border_margin=float(margin),
    )


def estimate_summary(estimate: RotationEstimate, border_spins_per_1000y: float | None = None) -> str:
    judgement = rotation_reality_label(estimate.spins_per_1000y, border_spins_per_1000y)
    if border_spins_per_1000y is None:
        return (
            f"{estimate.spins_per_1000y:.1f}회/1000엔 "
            f"({estimate.source_label}, 보더 미확정, {judgement})"
        )
    margin_text = border_delta_text(estimate.spins_per_1000y, border_spins_per_1000y)
    ratio_text = border_ratio_text(estimate.spins_per_1000y, border_spins_per_1000y)
    return (
        f"{estimate.spins_per_1000y:.1f}회/1000엔 "
        f"({estimate.source_label}, 보더+/- {margin_text}, {judgement}, 보더비 {ratio_text})"
    )


def border_margin(spins_per_1000y: float | None, border_spins_per_1000y: float | None) -> float | None:
    if spins_per_1000y is None or border_spins_per_1000y is None:
        return None
    return float(spins_per_1000y) - float(border_spins_per_1000y)


def border_ratio(spins_per_1000y: float | None, border_spins_per_1000y: float | None) -> float | None:
    if spins_per_1000y is None or border_spins_per_1000y is None or border_spins_per_1000y <= 0:
        return None
    return float(spins_per_1000y) / float(border_spins_per_1000y)


def signed_number(value: float) -> str:
    sign = "+" if value >= 0 else ""
    return f"{sign}{value:.1f}"


def border_margin_label(margin: float | None) -> str:
    if margin is None:
        return "보더 미확정"
    if abs(margin) < 0.05:
        return "보더±0"
    return f"보더{signed_number(margin)}"


def border_judgement_from_margin(margin: float | None) -> str:
    if margin is None:
        return "보더 미확정"
    if margin <= -10:
        return "나쁨"
    if margin < -5:
        return "불리"
    if margin < 0:
        return "보더 근처이나 부족"
    if margin < 5:
        return "보더 근처"
    if margin < 10:
        return "좋음"
    return "매우 좋음"


def border_label(spins_per_1000y: float | None, border_spins_per_1000y: float | None) -> str:
    if border_spins_per_1000y is None:
        return "보더 미확정"
    margin = border_margin(spins_per_1000y, border_spins_per_1000y) or 0.0
    judgement = border_judgement_from_margin(margin)
    return f"보더 {border_spins_per_1000y:.1f}회/1000엔, {signed_number(margin)}회 ({judgement})"


def border_delta_text(spins_per_1000y: float | None, border_spins_per_1000y: float | None) -> str:
    margin = border_margin(spins_per_1000y, border_spins_per_1000y)
    if margin is None:
        return "N/A"
    return signed_number(margin)


def border_ratio_text(spins_per_1000y: float | None, border_spins_per_1000y: float | None) -> str:
    ratio = border_ratio(spins_per_1000y, border_spins_per_1000y)
    if ratio is None:
        return "N/A"
    return f"{ratio:.2f}x"


def rotation_reality_label(spins_per_1000y: float | None, border_spins_per_1000y: float | None) -> str:
    margin = border_margin(spins_per_1000y, border_spins_per_1000y)
    if margin is not None:
        return border_judgement_from_margin(margin)
    if spins_per_1000y is None:
        return "회전 미확정"
    spins = float(spins_per_1000y)
    if spins < 50:
        return "위험"
    if spins < 60:
        return "나쁨"
    if spins < 70:
        return "타협"
    if spins < 80:
        return "합격선"
    if spins < 90:
        return "우수"
    return "매우 우수"


def border_adjustment(spins_per_1000y: float | None, border_spins_per_1000y: float | None) -> float:
    if spins_per_1000y is None:
        return 0.0
    margin = border_margin(spins_per_1000y, border_spins_per_1000y)
    if margin is None:
        if float(spins_per_1000y) < LOW_ABSOLUTE_SPIN_WARNING:
            return -35.0
        return 0.0
    return max(-30.0, min(12.0, margin * 0.9))


def border_case_rates(
    border_spins_per_1000y: float | None,
    margins: List[int] | None = None,
    fallback_rates: List[int] | None = None,
) -> List[Dict[str, Any]]:
    if border_spins_per_1000y is None:
        rates = fallback_rates or ABSOLUTE_SPIN_RATE_CASES
        return [
            {
                "rotation_basis": "absolute",
                "rotation_label": f"{rate}회",
                "spins_per_1000y": float(rate),
                "border_margin": None,
            }
            for rate in rates
        ]

    rows = []
    for margin in margins or BORDER_MARGIN_CASES:
        spins = spins_from_border_margin(border_spins_per_1000y, margin)
        rows.append(
            {
                "rotation_basis": "border_margin",
                "rotation_label": border_margin_label(float(margin)),
                "spins_per_1000y": float(spins),
                "border_margin": float(margin),
            }
        )
    return rows
