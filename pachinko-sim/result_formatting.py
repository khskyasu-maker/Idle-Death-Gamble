import unicodedata
from typing import Any, List


def format_ci(low: float, high: float, suffix: str = "%") -> str:
    if suffix == "%":
        return f"{low:.1f}~{high:.1f}%"
    return f"{int(low)}~{int(high)}{suffix}"


def display_width(value: Any) -> int:
    text = str(value)
    width = 0
    for char in text:
        if unicodedata.combining(char):
            continue
        width += 2 if unicodedata.east_asian_width(char) in {"F", "W"} else 1
    return width


def clean_cell(value: Any) -> str:
    return str(value).replace("\n", " ").replace("|", "/")


def pad_cell(value: Any, width: int) -> str:
    text = clean_cell(value)
    return text + (" " * max(0, width - display_width(text)))


def build_ascii_table(headers: List[str], rows: List[List[Any]]) -> str:
    table_rows = [[clean_cell(cell) for cell in row] for row in rows]
    widths = []
    for col_index, header in enumerate(headers):
        column_values = [row[col_index] for row in table_rows]
        widths.append(max(display_width(header), *(display_width(value) for value in column_values)))

    border = "+" + "+".join("-" * (width + 2) for width in widths) + "+"
    header_line = "| " + " | ".join(pad_cell(header, width) for header, width in zip(headers, widths)) + " |"
    body_lines = [
        "| " + " | ".join(pad_cell(cell, width) for cell, width in zip(row, widths)) + " |"
        for row in table_rows
    ]
    return "\n".join([border, header_line, border, *body_lines, border])


def build_ascii_bar(value: int, max_value: int, width: int = 32) -> str:
    if max_value <= 0:
        return ""
    filled = int(round((value / max_value) * width))
    return "#" * max(0, min(width, filled))


def yen(value: int, signed: bool = False) -> str:
    number = int(value)
    if signed:
        return f"{number:+,}yen"
    return f"{number:,}yen"


def pct(value: float) -> str:
    return f"{value:.1f}%"


def spins_text(value: float) -> str:
    if value is None:
        return "-"
    if abs(float(value) - int(float(value))) < 0.05:
        return f"{int(round(float(value)))}회"
    return f"{float(value):.1f}회"


def lend_rate_text(value: float) -> str:
    text = f"{float(value):.3f}".rstrip("0").rstrip(".")
    return f"{text}엔/발"


def minutes_text(value: float) -> str:
    if value is None:
        return "-"
    minutes_value = max(0.0, float(value))
    if minutes_value < 60:
        return f"{minutes_value:.1f}분"
    hours = int(minutes_value // 60)
    minutes_remainder = int(round(minutes_value % 60))
    if minutes_remainder >= 60:
        hours += 1
        minutes_remainder = 0
    return f"{hours}시간 {minutes_remainder}분"
