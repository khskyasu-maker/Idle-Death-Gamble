from typing import Any


RELIABILITY_SUMMARY = [
    {
        "area": "확률 분모/공식 스펙",
        "confidence": "very_high",
        "note": "DMM/스펙 사이트의 공개 확률과 보더를 그대로 옮긴 영역입니다.",
    },
    {
        "area": "상태 전이 분포",
        "confidence": "high",
        "note": "NORMAL/ST/時短(시단)/確変(확변)/LT/UPPER 계열 전이는 공개 분포와 벤치마크로 검증합니다.",
    },
    {
        "area": "예산/환율/재사용 구슬 회계",
        "confidence": "very_high",
        "note": "고정 레이트, 교환율, 보유구슬 재사용 규칙에 따른 산술 영역입니다.",
    },
    {
        "area": "호기 품질/입상 분포",
        "confidence": "medium",
        "note": "1000円당 회전수와 보더 마진으로 제약하지만, 실제 못 상태는 현장 관찰값에 의존합니다.",
    },
    {
        "area": "체류 시간",
        "confidence": "medium",
        "note": "기종족별 시간 프로파일로 추정하며, 개별 기기의 연출/소화 속도 차이는 오차로 남습니다.",
    },
    {
        "area": "우측 소비 구슬",
        "confidence": "medium_low",
        "note": "right_spend_per_spin은 상태별 평균값이며, 기종별 상구/오버입상/전동 패턴은 세부 반영하지 않습니다.",
    },
    {
        "area": "보류 심볼/특図 제약",
        "confidence": "low",
        "note": "공개 스펙에서 확인 가능한 잔보류 회전수는 반영하지만, 특図1/특図2 보류 큐와 심볼 선택 제약은 명시 큐로 모델링하지 않습니다.",
    },
]


MODEL_LIMITATIONS = [
    "보류 심볼 제약: 일부 기종의 特図1/特図2 보류 우선순위와 심볼 선택 제약은 공개 스펙만으로 확정하기 어렵기 때문에, 현재는 상태별 분포와 잔보류 회전수로 근사합니다.",
    "우측 소비 구슬: right_spend_per_spin은 ST/時短(시단)/確変(확변)/LT 상태별 평균값입니다. 기종별 상구 수, 오버입상, 전동 패턴 차이는 시간·잔류 구슬 오차로 남습니다.",
    "연출 강제 대기 시간: TimeAssumptions는 기종족별 평균 프로파일입니다. 개별 기기의 당첨 고지, 라운드 전후 대기, 특수 모드 연출 시간은 별도 확정값이 있을 때만 반영해야 합니다.",
]


def reliability_summary_rows() -> list[dict[str, str]]:
    return [dict(row) for row in RELIABILITY_SUMMARY]


def reliability_summary_text() -> list[str]:
    return [
        f"{row['area']}: {row['confidence']} - {row['note']}"
        for row in RELIABILITY_SUMMARY
    ]


def public_model_limitations() -> list[str]:
    return list(MODEL_LIMITATIONS)


def machine_modeling_notes(machine: Any) -> list[str]:
    if getattr(machine, "spec_type", "") == "multi-machine budget matrix":
        return [
            "다기종 집계 파일입니다. 실제 모델 신뢰도와 시간 오차는 행별 machine_id의 기종 모델과 TimeAssumptions를 기준으로 해석해야 합니다.",
            "공개 표는 원시 세션이 아니라 보더±0 가정의 집계값이므로 현장 회전수 입력으로 다시 해석해야 합니다.",
        ]

    notes = []
    confidence = getattr(machine, "confidence", "")
    is_estimated = bool(getattr(machine, "is_estimated", False))
    if confidence and confidence != "high":
        notes.append(f"모델 신뢰도 {confidence}: 공개 스펙 일부를 보수적으로 근사한 모델입니다.")
    if is_estimated:
        notes.append("is_estimated=True: 세부 분포나 전이값에 추정이 포함되어 있습니다.")

    distributions = [
        getattr(machine, "normal_hit_dist", []),
        getattr(machine, "st_hit_dist", []),
        getattr(machine, "jitan_hit_dist", []),
        getattr(machine, "kakuben_hit_dist", []),
        getattr(machine, "lt_hit_dist", []),
        getattr(machine, "upper_hit_dist", []),
        getattr(machine, "jinbee_hit_dist", []),
    ]
    has_right_state = any(
        payout.next_state != "NORMAL" or payout.st_spins > 0 or payout.jitan_spins > 0
        for distribution in distributions
        for payout in distribution
    )
    if has_right_state:
        notes.append("우타치/잔보류는 상태별 회전수와 분포로 근사하며, 특図 보류 큐를 별도 시뮬레이션하지 않습니다.")

    if getattr(machine, "right_spend_per_spin", None):
        notes.append("우측 소비는 상태별 평균 구슬 소모값이며, 기기별 오버입상 차이는 포함하지 않습니다.")

    notes.append("체류 시간은 기종족별 평균 시간 프로파일이므로 개별 연출 속도에 따라 흔들릴 수 있습니다.")
    return notes


def concise_machine_modeling_note(machine: Any) -> str:
    notes = machine_modeling_notes(machine)
    return " / ".join(notes)


__all__ = [
    "MODEL_LIMITATIONS",
    "RELIABILITY_SUMMARY",
    "concise_machine_modeling_note",
    "machine_modeling_notes",
    "public_model_limitations",
    "reliability_summary_rows",
    "reliability_summary_text",
]
