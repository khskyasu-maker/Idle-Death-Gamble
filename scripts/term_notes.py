import re


JAPANESE_TERM_NOTES = [
    ("新世紀エヴァンゲリオン", "신세기 에반게리온"),
    ("エヴァンゲリオン", "에반게리온"),
    ("未来への咆哮", "미래로의 포효"),
    ("ライトミドル", "라이트 미들 확률대"),
    ("フロアマップ", "층별 배치도"),
    ("機種候補", "기종 후보"),
    ("機種情報", "기종 정보"),
    ("初当り確率", "초당첨 확률"),
    ("初当り", "초당첨"),
    ("大当り", "대당첨/아타리"),
    ("確変", "확률 변동"),
    ("時短", "시간 단축"),
    ("電サポ", "전동 서포트"),
    ("残保留", "잔보류"),
    ("右打ち", "우타치"),
    ("ヘソ", "헤소/특도1"),
    ("電チュー", "전츄/특도2"),
    ("RUSH", "러시"),
    ("ラッシュ", "러시"),
    ("突入率", "진입률"),
    ("継続率", "계속률"),
    ("台数", "설치 대수"),
    ("機種別", "기종별"),
    ("機種名", "기종명"),
    ("機種", "기종"),
    ("遊技料金", "이용 요금"),
    ("低貸", "저가 대여 요금"),
    ("新台", "신규 도입 기종"),
    ("増台", "증설 기종"),
    ("出玉", "출옥"),
    ("払い出し", "지급 출옥"),
    ("賞球", "입상 구슬"),
    ("エヴァ15", "에반게리온 15"),
    ("エヴァ", "에반게리온 계열"),
    ("海物語", "해물어 계열"),
    ("1パチ", "1엔 파칭코"),
    ("1円", "1엔"),
    ("甘デジ", "가벼운 확률대"),
    ("ミドル", "미들 확률대"),
    ("パチンコ", "파칭코"),
    ("ランキング", "순위"),
    ("遊タイム", "유타임(천장 구제 기능)"),
    ("交換率", "교환율(환전 비율)"),
    ("貸出料金", "대여 요금(구슬을 빌리는 가격)"),
]


def term_glossary():
    return [
        {"term": term, "ko_note": ko_note}
        for term, ko_note in JAPANESE_TERM_NOTES
    ]


def annotate_japanese_terms(value):
    if not isinstance(value, str) or not value:
        return value

    note_by_term = dict(JAPANESE_TERM_NOTES)
    pattern = re.compile(
        "|".join(re.escape(term) for term, _ in JAPANESE_TERM_NOTES)
    )

    def replace(match):
        term = match.group(0)
        end = match.end()
        ko_note = note_by_term[term]
        if value[end:].startswith(f"({ko_note}") or value[end:].startswith(f"（{ko_note}"):
            return term
        return f"{term}({ko_note})"

    return pattern.sub(replace, value)
