import re
from typing import Any


JAPANESE_TERM_NOTES = [
    ("初当り確率", "초당첨 확률"),
    ("初当り", "초당첨"),
    ("大当り", "대당첨/아타리"),
    ("転落小当り", "전락 소당첨"),
    ("小当り", "소당첨"),
    ("当り", "당첨"),
    ("世紀末チャージ", "세기말 차지"),
    ("無想転生チャンス", "무상전생 찬스"),
    ("神拳勝舞", "신권승부"),
    ("北斗の拳", "북두의 권"),
    ("確変", "확률 변동"),
    ("時短", "시간 단축"),
    ("電サポ", "전동 서포트"),
    ("残保留", "잔보류"),
    ("右打ち", "우타치"),
    ("ヘソ", "헤소/특도1"),
    ("電チュー", "전츄/특도2"),
    ("特図1", "특도1"),
    ("特図2", "특도2"),
    ("出玉", "출옥"),
    ("払い出し", "지급 출옥"),
    ("賞球", "입상 구슬"),
    ("カウント", "카운트"),
    ("ラウンド", "라운드"),
    ("突入率", "진입률"),
    ("継続率", "계속률"),
    ("引き戻し", "되돌림"),
    ("上位RUSH", "상위 러시"),
    ("ジンベェタイム", "진베에 타임"),
    ("ジンベェ", "진베에"),
    ("GOLDパールRUSH", "골드 펄 러시"),
    ("超強欲PREMIUM BONUS", "초강욕 프리미엄 보너스"),
    ("RUSH", "러시"),
    ("LT", "러키 트리거"),
    ("ST", "스페셜 타임"),
    ("1円", "1엔"),
    ("4円", "4엔"),
    ("玉", "구슬"),
]


STATE_LABELS = {
    "NORMAL": "NORMAL(통상)",
    "ST": "ST(고확 ST/러시)",
    "JITAN": "JITAN/時短(시단)",
    "KAKUBEN": "KAKUBEN/確変(확변)",
    "LT": "LT(러키 트리거)",
    "LT_JITAN": "LT_JITAN/時短(러키 트리거 시단)",
    "UPPER": "UPPER/上位RUSH(상위 러시)",
    "JINBEE": "JINBEE/ジンベェ確変(진베에 확변)",
    "JINBEE_JITAN": "JINBEE_JITAN/ジンベェ時短200(진베에 시단200)",
}


_NOTE_BY_TERM = dict(JAPANESE_TERM_NOTES)
_TERM_PATTERN = re.compile("|".join(re.escape(term) for term, _ in JAPANESE_TERM_NOTES))


def annotate_japanese_terms(value: Any) -> str:
    text = str(value)
    if not text:
        return text

    def replace(match):
        term = match.group(0)
        end = match.end()
        ko_note = _NOTE_BY_TERM[term]
        if text[end:].startswith(f"({ko_note}") or text[end:].startswith(f"（{ko_note}"):
            return term
        return f"{term}({ko_note})"

    return _TERM_PATTERN.sub(replace, text)


def state_label(state: str) -> str:
    return STATE_LABELS.get(state, state)


def state_transition_label(before: str, after: str) -> str:
    return f"{state_label(before)}->{state_label(after)}"
