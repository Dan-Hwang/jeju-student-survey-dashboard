from __future__ import annotations

from datetime import datetime
from io import BytesIO
from pathlib import Path
import re
import unicodedata
from typing import Any, Iterable

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from src.survey_dashboard import collect_comments


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
FONT_REGULAR_PATH = ASSETS / "fonts" / "NanumGothic-Regular.ttf"
FONT_BOLD_PATH = ASSETS / "fonts" / "NanumGothic-Bold.ttf"
MEETINGS_PREVIEW = ASSETS / "synapspot-meetings-preview.png"
QUESTION_PREVIEW = ASSETS / "synapspot-question-preview.png"

PAGE_W, PAGE_H = A4
MARGIN = 38
CONTENT_W = PAGE_W - MARGIN * 2

NAVY = colors.HexColor("#13233D")
TEAL = colors.HexColor("#087F72")
CORAL = colors.HexColor("#EC6A5F")
BLUE = colors.HexColor("#2563EB")
MUTED = colors.HexColor("#66768A")
LINE = colors.HexColor("#D8E2E9")
SOFT = colors.HexColor("#F4F7FA")
SOFT_TEAL = colors.HexColor("#EAF6F3")
SOFT_CORAL = colors.HexColor("#FFF1EF")
WHITE = colors.white

FONT_REGULAR = "AraNanumRegular"
FONT_BOLD = "AraNanumBold"
NAME_ASSIGNMENT_PATTERN = re.compile(
    r"(?i)\b(?:name|full\s*name)\s*[:=]\s*[^,;]+|(?:이름|성명)\s*[:=：]\s*[^,;]+"
)
STANDALONE_KOREAN_NAME_PATTERN = re.compile(r"^[가-힣]{2,4}$")


def register_fonts() -> tuple[str, str]:
    if FONT_REGULAR not in pdfmetrics.getRegisteredFontNames():
        missing = [
            str(path)
            for path in (FONT_REGULAR_PATH, FONT_BOLD_PATH)
            if not path.exists()
        ]
        if missing:
            raise FileNotFoundError(
                "Bundled PDF fonts are required: " + ", ".join(missing)
            )
        pdfmetrics.registerFont(TTFont(FONT_REGULAR, str(FONT_REGULAR_PATH)))
        pdfmetrics.registerFont(TTFont(FONT_BOLD, str(FONT_BOLD_PATH)))
    return FONT_REGULAR, FONT_BOLD


def percentage(value: int, total: int) -> str:
    return f"{(value / total * 100):.1f}%" if total else "0.0%"


def source_label(source: str) -> str:
    return "Google Sheets" if source == "Google Sheets" else "저장 데이터"


def get_count(items: Iterable[tuple[str, int]], label: str) -> int:
    return next((int(value) for item, value in items if item == label), 0)


def top_item(items: list[tuple[str, int]]) -> tuple[str, int]:
    return items[0] if items else ("응답 없음", 0)


def sanitize_comment(value: object) -> str:
    text = str(value).replace("\r", " ").replace("\n", " ")
    text = "".join(
        char
        for char in text
        if unicodedata.category(char) not in {"So", "Cs", "Cc"}
    )
    return re.sub(r"\s+", " ", text).strip()


def sanitize_public_comment(value: object) -> str:
    text = sanitize_comment(value)
    if not text:
        return ""
    if NAME_ASSIGNMENT_PATTERN.search(text) or STANDALONE_KOREAN_NAME_PATTERN.fullmatch(text):
        return ""
    public_comments = collect_comments([{"comment": text}], "comment")
    return public_comments[0] if public_comments else ""


def text_lines(
    text: object,
    font_name: str,
    font_size: float,
    max_width: float,
    max_lines: int | None = None,
) -> list[str]:
    paragraphs = str(text).splitlines() or [""]
    lines: list[str] = []
    for paragraph in paragraphs:
        current = ""
        for char in paragraph:
            candidate = current + char
            if current and pdfmetrics.stringWidth(candidate, font_name, font_size) > max_width:
                lines.append(current.rstrip())
                current = char.lstrip()
            else:
                current = candidate
        if current or not paragraph:
            lines.append(current.rstrip())

    if max_lines is not None and len(lines) > max_lines:
        lines = lines[:max_lines]
        last = lines[-1]
        while last and pdfmetrics.stringWidth(last + "...", font_name, font_size) > max_width:
            last = last[:-1]
        lines[-1] = last.rstrip() + "..."
    return lines


def draw_text(
    c: canvas.Canvas,
    text: object,
    x: float,
    y: float,
    max_width: float,
    font_name: str,
    font_size: float,
    line_height: float,
    color: colors.Color = NAVY,
    max_lines: int | None = None,
) -> float:
    c.setFont(font_name, font_size)
    c.setFillColor(color)
    for line in text_lines(text, font_name, font_size, max_width, max_lines):
        c.drawString(x, y, line)
        y -= line_height
    return y


def draw_round_rect(
    c: canvas.Canvas,
    x: float,
    y: float,
    width: float,
    height: float,
    fill: colors.Color = WHITE,
    stroke: colors.Color = LINE,
    radius: float = 10,
) -> None:
    c.setFillColor(fill)
    c.setStrokeColor(stroke)
    c.setLineWidth(0.8)
    c.roundRect(x, y, width, height, radius, fill=1, stroke=1)


def draw_kicker(c: canvas.Canvas, text: str, x: float, y: float, font_bold: str) -> None:
    c.setFillColor(TEAL)
    c.setFont(font_bold, 8.5)
    c.drawString(x, y, text)


def draw_page_footer(
    c: canvas.Canvas,
    page_number: int,
    generated_at: str,
    font_regular: str,
    font_bold: str,
) -> None:
    c.setStrokeColor(LINE)
    c.line(MARGIN, 34, PAGE_W - MARGIN, 34)
    c.setFillColor(MUTED)
    c.setFont(font_regular, 7.5)
    c.drawString(MARGIN, 20, f"익명 집계 · 생성 {generated_at}")
    c.setFont(font_bold, 8)
    c.drawRightString(PAGE_W - MARGIN, 20, f"{page_number} / 3")


def draw_metric_card(
    c: canvas.Canvas,
    label: str,
    value: str,
    note: str,
    x: float,
    y: float,
    width: float,
    font_regular: str,
    font_bold: str,
    accent: colors.Color = TEAL,
) -> None:
    height = 66
    draw_round_rect(c, x, y, width, height)
    c.setFillColor(accent)
    c.roundRect(x, y, 4, height, 2, fill=1, stroke=0)
    c.setFont(font_bold, 8)
    c.setFillColor(MUTED)
    c.drawString(x + 12, y + 46, label)
    c.setFont(font_bold, 19)
    c.setFillColor(NAVY)
    c.drawString(x + 12, y + 22, value)
    c.setFont(font_regular, 7.5)
    c.setFillColor(accent)
    c.drawString(x + 12, y + 9, note)


def draw_ranking_rows(
    c: canvas.Canvas,
    items: list[tuple[str, int]],
    total: int,
    x: float,
    y: float,
    width: float,
    font_regular: str,
    font_bold: str,
    accent: colors.Color,
    limit: int = 3,
    row_height: float = 23,
    shared_scale: float | None = None,
) -> float:
    visible = items[:limit]
    if not visible:
        c.setFont(font_regular, 8)
        c.setFillColor(MUTED)
        c.drawString(x, y, "표시할 응답이 없습니다.")
        return y - row_height

    local_scale = max(
        (value / total if total else 0) for _, value in visible
    ) or 1
    scale = shared_scale or local_scale
    label_w = min(86, width * 0.36)
    value_w = 56
    bar_x = x + label_w + 5
    bar_w = max(28, width - label_w - value_w - 12)
    value_x = x + width

    for label, value in visible:
        c.setFont(font_regular, 7.7)
        c.setFillColor(NAVY)
        label_lines = text_lines(label, font_regular, 7.7, label_w, 1)
        c.drawString(x, y, label_lines[0] if label_lines else "-")
        c.setFillColor(colors.HexColor("#E7EDF3"))
        c.roundRect(bar_x, y - 1, bar_w, 6, 3, fill=1, stroke=0)
        c.setFillColor(accent)
        ratio = min(1.0, (value / total if total else 0) / scale) if scale else 0
        c.roundRect(bar_x, y - 1, bar_w * ratio, 6, 3, fill=1, stroke=0)
        c.setFont(font_bold, 7.2)
        c.setFillColor(MUTED)
        c.drawRightString(value_x, y, f"{value}명 · {percentage(value, total)}")
        y -= row_height
    return y


def draw_problem_panel(
    c: canvas.Canvas,
    kicker: str,
    title: str,
    summary: str,
    rows: list[tuple[str, int, int]],
    x: float,
    y: float,
    width: float,
    height: float,
    font_regular: str,
    font_bold: str,
    accent: colors.Color,
    fill: colors.Color,
) -> None:
    draw_round_rect(c, x, y, width, height, fill=fill, stroke=fill)
    c.setFont(font_bold, 7.5)
    c.setFillColor(accent)
    c.drawString(x + 14, y + height - 20, kicker)
    c.setFont(font_bold, 15)
    c.setFillColor(NAVY)
    c.drawString(x + 14, y + height - 42, title)
    draw_text(c, summary, x + 14, y + height - 60, width - 28, font_regular, 7.6, 11, MUTED, 2)

    row_y = y + height - 91
    if not rows:
        c.setFont(font_regular, 7.5)
        c.setFillColor(MUTED)
        c.drawString(x + 14, row_y, "관련 응답이 아직 없습니다.")
        return
    for label, value, total in rows[:3]:
        c.setFont(font_regular, 7.5)
        c.setFillColor(NAVY)
        c.drawString(x + 14, row_y, text_lines(label, font_regular, 7.5, width - 92, 1)[0])
        c.setFont(font_bold, 7.5)
        c.setFillColor(accent)
        c.drawRightString(x + width - 14, row_y, f"{value}명 · {percentage(value, total)}")
        row_y -= 19


def draw_contained_image(
    c: canvas.Canvas,
    path: Path,
    x: float,
    y: float,
    width: float,
    height: float,
) -> None:
    image = ImageReader(str(path))
    image_w, image_h = image.getSize()
    scale = min(width / image_w, height / image_h)
    draw_w = image_w * scale
    draw_h = image_h * scale
    c.drawImage(
        image,
        x + (width - draw_w) / 2,
        y + (height - draw_h) / 2,
        draw_w,
        draw_h,
        preserveAspectRatio=True,
        mask="auto",
    )


def draw_product_card(
    c: canvas.Canvas,
    image_path: Path,
    title: str,
    description: str,
    x: float,
    y: float,
    width: float,
    height: float,
    font_regular: str,
    font_bold: str,
) -> None:
    draw_round_rect(c, x, y, width, height, fill=WHITE)
    image_w = 79
    draw_round_rect(c, x + 10, y + 10, image_w, height - 20, fill=SOFT, stroke=SOFT, radius=7)
    draw_contained_image(c, image_path, x + 13, y + 13, image_w - 6, height - 26)
    text_x = x + 101
    c.setFont(font_bold, 8)
    c.setFillColor(CORAL)
    c.drawString(text_x, y + height - 27, "SYNAPSPOT")
    c.setFont(font_bold, 13)
    c.setFillColor(NAVY)
    c.drawString(text_x, y + height - 49, title)
    draw_text(c, description, text_x, y + height - 67, width - 115, font_regular, 7.8, 12, MUTED, 4)


def top_matching(
    items: list[tuple[str, int]], allowed: tuple[str, ...]
) -> tuple[str, int] | None:
    matches = [(label, int(value)) for label, value in items if label in allowed]
    return max(matches, key=lambda item: item[1]) if matches else None


def movement_rows(korean: dict[str, Any], foreign: dict[str, Any]) -> list[tuple[str, int, int]]:
    korean_total = int(korean["n"])
    foreign_total = int(foreign["n"])
    allowed_pain = ("버스 노선", "택시비", "교통", "같이 이동할 사람 찾기", "여행 계획")
    korean_pain = top_matching(korean["pain"], allowed_pain)
    korean_party = top_matching(korean["openchat_find"], ("택시팟", "여행팟"))
    foreign_pain = top_matching(foreign["pain"], allowed_pain)
    candidates = [
        ("한국인", korean_pain, korean_total),
        ("한국인", korean_party, korean_total),
        ("외국인", foreign_pain, foreign_total),
    ]
    return [
        (f"{group} · {item[0]}", int(item[1]), total)
        for group, item, total in candidates
        if item is not None
    ]


def information_rows(korean: dict[str, Any], foreign: dict[str, Any]) -> list[tuple[str, int, int]]:
    korean_total = int(korean["n"])
    foreign_total = int(foreign["n"])
    friction_labels = (
        "원하는 글 찾기 어렵다",
        "글이 너무 많다",
        "검색 기능 불편",
        "지난 글 찾기 어렵다",
        "채팅이 빨리 올라간다",
        "모집 종료 글 노출",
        "정보 정확성 모르겠다",
    )
    korean_pain = top_matching(korean["openchat_pain"], friction_labels)
    foreign_find = top_matching(foreign["openchat_find"], ("공지", "생활정보", "시험정보"))
    foreign_pain = top_matching(foreign["openchat_pain"], friction_labels)
    candidates = [
        ("한국인", korean_pain, korean_total),
        ("외국인", foreign_find, foreign_total),
        ("외국인", foreign_pain, foreign_total),
    ]
    return [
        (f"{group} · {item[0]}", int(item[1]), total)
        for group, item, total in candidates
        if item is not None
    ]


def draw_research_story_page(
    c: canvas.Canvas,
    korean: dict[str, Any],
    foreign: dict[str, Any],
    generated_at: str,
    font_regular: str,
    font_bold: str,
) -> None:
    korean_total = int(korean["n"])
    foreign_total = int(foreign["n"])
    total = korean_total + foreign_total

    draw_kicker(c, "JEJU EXCHANGE STUDENT RESEARCH BRIEF", MARGIN, 806, font_bold)
    draw_text(
        c,
        "교류학생의 이동과 정보 탐색은 어디서 막혔을까?",
        MARGIN,
        778,
        CONTENT_W,
        font_bold,
        24,
        31,
        NAVY,
        2,
    )
    c.setFont(font_regular, 8.8)
    c.setFillColor(MUTED)
    c.drawString(MARGIN, 716, "학생의 실제 경험을 조사하고, 시냅스팟의 문제 정의로 이어진 근거를 정리했습니다.")

    gap = 10
    card_w = (CONTENT_W - gap * 2) / 3
    draw_metric_card(c, "전체 응답", f"{total}명", "한국인 + 외국인", MARGIN, 632, card_w, font_regular, font_bold)
    draw_metric_card(c, "한국인 응답", f"{korean_total}명", "현재 집계 기준", MARGIN + card_w + gap, 632, card_w, font_regular, font_bold, BLUE)
    draw_metric_card(c, "외국인 응답", f"{foreign_total}명", "현재 집계 기준", MARGIN + (card_w + gap) * 2, 632, card_w, font_regular, font_bold, CORAL)

    if total == 0:
        draw_round_rect(c, MARGIN, 410, CONTENT_W, 180, fill=SOFT, stroke=SOFT, radius=8)
        c.setFont(font_bold, 8)
        c.setFillColor(TEAL)
        c.drawString(MARGIN + 20, 556, "WAITING FOR RESPONSES")
        c.setFont(font_bold, 18)
        c.setFillColor(NAVY)
        c.drawString(MARGIN + 20, 522, "아직 표시할 설문 응답이 없습니다.")
        draw_text(
            c,
            "응답이 집계되면 이동·동행과 정보 탐색의 근거, 집단 비교, 익명 의견을 이 보고서에 표시합니다.",
            MARGIN + 20,
            491,
            CONTENT_W - 40,
            font_regular,
            9,
            15,
            MUTED,
            3,
        )
        draw_page_footer(c, 1, generated_at, font_regular, font_bold)
        return

    draw_round_rect(c, MARGIN, 564, CONTENT_W, 48, fill=NAVY, stroke=NAVY, radius=8)
    c.setFont(font_bold, 8)
    c.setFillColor(colors.HexColor("#68D7C8"))
    c.drawString(MARGIN + 14, 592, "먼저 볼 결론")
    c.setFont(font_bold, 11.5)
    c.setFillColor(WHITE)
    c.drawString(MARGIN + 14, 575, "이동·동행 모집과 신뢰할 수 있는 생활정보 탐색이 함께 필요했습니다.")

    c.setFont(font_bold, 14)
    c.setFillColor(NAVY)
    c.drawString(MARGIN, 536, "응답이 가리킨 두 가지 문제")
    panel_gap = 12
    panel_w = (CONTENT_W - panel_gap) / 2
    draw_problem_panel(
        c,
        "PROBLEM 01",
        "이동과 동행 모집",
        "교통비와 이동 제약뿐 아니라 같은 목적지로 갈 사람을 제때 찾는 문제가 함께 나타났습니다.",
        movement_rows(korean, foreign),
        MARGIN,
        361,
        panel_w,
        156,
        font_regular,
        font_bold,
        TEAL,
        SOFT_TEAL,
    )
    draw_problem_panel(
        c,
        "PROBLEM 02",
        "공지와 생활정보 탐색",
        "빠르게 흘러가는 오픈채팅에서 필요한 정보와 모집 상태를 다시 확인하기 어려웠습니다.",
        information_rows(korean, foreign),
        MARGIN + panel_w + panel_gap,
        361,
        panel_w,
        156,
        font_regular,
        font_bold,
        CORAL,
        SOFT_CORAL,
    )

    c.setFont(font_bold, 8)
    c.setFillColor(CORAL)
    c.drawString(MARGIN, 337, "FROM RESEARCH TO PRODUCT")
    c.setFont(font_bold, 14)
    c.setFillColor(NAVY)
    c.drawString(MARGIN, 316, "이 근거가 시냅스팟의 두 기능으로 이어졌습니다.")
    c.setFont(font_regular, 7.8)
    c.setFillColor(MUTED)
    c.drawRightString(PAGE_W - MARGIN, 317, "설문은 효과 입증이 아닌 문제 우선순위의 근거입니다.")

    product_y = 65
    product_h = 232
    draw_product_card(
        c,
        MEETINGS_PREVIEW,
        "이동·동행 파티",
        "시간, 목적지, 인원을 기준으로 함께 이동할 사람을 찾습니다.",
        MARGIN,
        product_y,
        panel_w,
        product_h,
        font_regular,
        font_bold,
    )
    draw_product_card(
        c,
        QUESTION_PREVIEW,
        "근거 있는 정보 탐색",
        "공지와 생활정보를 질문하고 답변의 출처를 확인합니다.",
        MARGIN + panel_w + panel_gap,
        product_y,
        panel_w,
        product_h,
        font_regular,
        font_bold,
    )
    draw_page_footer(c, 1, generated_at, font_regular, font_bold)


def shared_percentage_scale(
    korean_items: list[tuple[str, int]],
    foreign_items: list[tuple[str, int]],
    korean_total: int,
    foreign_total: int,
    limit: int = 3,
) -> float:
    ratios = [
        value / korean_total
        for _, value in korean_items[:limit]
        if korean_total
    ]
    ratios.extend(
        value / foreign_total
        for _, value in foreign_items[:limit]
        if foreign_total
    )
    return max(ratios, default=1.0) or 1.0


def draw_comparison_panel(
    c: canvas.Canvas,
    title: str,
    korean_items: list[tuple[str, int]],
    foreign_items: list[tuple[str, int]],
    korean_total: int,
    foreign_total: int,
    x: float,
    y: float,
    width: float,
    height: float,
    font_regular: str,
    font_bold: str,
) -> None:
    draw_round_rect(c, x, y, width, height, fill=WHITE)
    c.setFont(font_bold, 12)
    c.setFillColor(NAVY)
    c.drawString(x + 14, y + height - 24, title)
    row_y = y + height - 50
    shared_scale = shared_percentage_scale(
        korean_items,
        foreign_items,
        korean_total,
        foreign_total,
    )
    c.setFont(font_bold, 7.5)
    c.setFillColor(BLUE)
    c.drawString(x + 14, row_y, f"한국인 · n={korean_total}")
    row_y = draw_ranking_rows(c, korean_items, korean_total, x + 14, row_y - 20, width - 28, font_regular, font_bold, BLUE, shared_scale=shared_scale)
    c.setFont(font_bold, 7.5)
    c.setFillColor(CORAL)
    c.drawString(x + 14, row_y - 1, f"외국인 · n={foreign_total}")
    draw_ranking_rows(c, foreign_items, foreign_total, x + 14, row_y - 21, width - 28, font_regular, font_bold, CORAL, shared_scale=shared_scale)


def draw_comparison_page(
    c: canvas.Canvas,
    korean: dict[str, Any],
    foreign: dict[str, Any],
    generated_at: str,
    font_regular: str,
    font_bold: str,
) -> None:
    korean_total = int(korean["n"])
    foreign_total = int(foreign["n"])
    draw_kicker(c, "GROUP COMPARISON", MARGIN, 806, font_bold)
    c.setFont(font_bold, 23)
    c.setFillColor(NAVY)
    c.drawString(MARGIN, 772, "한국인과 외국인의 경험은 어떻게 달랐나")
    c.setFont(font_regular, 8.5)
    c.setFillColor(MUTED)
    c.drawString(MARGIN, 748, "막대 길이는 각 집단의 상위 응답 안에서 비교하고, 수치는 집단별 분모로 계산했습니다.")

    panel_gap = 12
    panel_w = (CONTENT_W - panel_gap) / 2
    panel_h = 300
    top_y = 421
    bottom_y = 88
    draw_comparison_panel(c, "제주에서 불편했던 점", korean["pain"], foreign["pain"], korean_total, foreign_total, MARGIN, top_y, panel_w, panel_h, font_regular, font_bold)
    draw_comparison_panel(c, "오픈채팅에서 찾는 정보", korean["openchat_find"], foreign["openchat_find"], korean_total, foreign_total, MARGIN + panel_w + panel_gap, top_y, panel_w, panel_h, font_regular, font_bold)
    draw_comparison_panel(c, "같이 하고 싶은 활동", korean["activity"], foreign["activity"], korean_total, foreign_total, MARGIN, bottom_y, panel_w, panel_h, font_regular, font_bold)
    draw_comparison_panel(c, "오픈채팅에서 불편한 점", korean["openchat_pain"], foreign["openchat_pain"], korean_total, foreign_total, MARGIN + panel_w + panel_gap, bottom_y, panel_w, panel_h, font_regular, font_bold)
    draw_page_footer(c, 2, generated_at, font_regular, font_bold)


def draw_comment_panel(
    c: canvas.Canvas,
    title: str,
    comments: list[str],
    x: float,
    y: float,
    width: float,
    height: float,
    font_regular: str,
    font_bold: str,
    accent: colors.Color,
) -> None:
    draw_round_rect(c, x, y, width, height)
    c.setFillColor(accent)
    c.roundRect(x, y, 4, height, 2, fill=1, stroke=0)
    c.setFont(font_bold, 12)
    c.setFillColor(NAVY)
    c.drawString(x + 15, y + height - 25, title)
    c.setFont(font_regular, 7.5)
    c.setFillColor(MUTED)
    c.drawString(x + 15, y + height - 42, "최대 5개의 익명 자유 의견")

    clean = [sanitize_public_comment(comment) for comment in comments]
    clean = [comment for comment in clean if comment]
    cursor = y + height - 69
    if not clean:
        c.setFont(font_regular, 8)
        c.setFillColor(MUTED)
        c.drawString(x + 15, cursor, "표시할 자유 의견이 없습니다.")
        return

    for index, comment in enumerate(clean[:5], start=1):
        c.setFillColor(accent)
        c.circle(x + 18, cursor + 2, 2.2, fill=1, stroke=0)
        cursor = draw_text(c, comment, x + 27, cursor + 5, width - 43, font_regular, 7.7, 11, NAVY, 2)
        cursor -= 10


def draw_evidence_page(
    c: canvas.Canvas,
    korean_survey: dict[str, Any],
    foreign_survey: dict[str, Any],
    generated_at: str,
    font_regular: str,
    font_bold: str,
) -> None:
    korean = korean_survey["data"]
    foreign = foreign_survey["data"]
    korean_total = int(korean["n"])
    foreign_total = int(foreign["n"])
    korean_positive = get_count(korean["intent"], "긍정")
    foreign_positive = get_count(foreign["intent"], "긍정")

    draw_kicker(c, "EVIDENCE APPENDIX", MARGIN, 806, font_bold)
    c.setFont(font_bold, 23)
    c.setFillColor(NAVY)
    c.drawString(MARGIN, 772, "상세 근거와 익명 자유 의견")
    c.setFont(font_regular, 8.5)
    c.setFillColor(MUTED)
    c.drawString(MARGIN, 748, "개별 응답 행은 공개하지 않고, 집계 결과와 식별 정보가 없는 의견만 표시합니다.")

    gap = 10
    card_w = (CONTENT_W - gap * 3) / 4
    korean_top = top_item(korean["openchat_find"])
    foreign_top = top_item(foreign["openchat_find"])
    cards = [
        ("한국인 주요 수요", str(korean_top[0]), f"{korean_top[1]}명", BLUE),
        ("한국인 사용 의향", f"{korean_positive}명", f"긍정 {percentage(korean_positive, korean_total)}", BLUE),
        ("외국인 주요 수요", str(foreign_top[0]), f"{foreign_top[1]}명", CORAL),
        ("외국인 사용 의향", f"{foreign_positive}명", f"긍정 {percentage(foreign_positive, foreign_total)}", CORAL),
    ]
    for index, (label, value, note, accent) in enumerate(cards):
        draw_metric_card(c, label, value, note, MARGIN + index * (card_w + gap), 655, card_w, font_regular, font_bold, accent)

    panel_gap = 12
    panel_w = (CONTENT_W - panel_gap) / 2
    draw_comment_panel(c, "한국인 익명 의견", korean.get("comments", []), MARGIN, 310, panel_w, 320, font_regular, font_bold, BLUE)
    draw_comment_panel(c, "외국인 익명 의견", foreign.get("comments", []), MARGIN + panel_w + panel_gap, 310, panel_w, 320, font_regular, font_bold, CORAL)

    draw_round_rect(c, MARGIN, 76, CONTENT_W, 205, fill=SOFT, stroke=SOFT, radius=8)
    c.setFont(font_bold, 12)
    c.setFillColor(NAVY)
    c.drawString(MARGIN + 15, 255, "집계 기준")
    methodology = [
        f"한국인 설문 · {source_label(str(korean_survey.get('source', '')))} · {korean_survey.get('loaded_at', '-')}",
        f"외국인 설문 · {source_label(str(foreign_survey.get('source', '')))} · {foreign_survey.get('loaded_at', '-')}",
        "복수 응답 문항의 비율은 각 집단 응답자 수를 분모로 계산했습니다.",
        "PDF는 다운로드 시점의 앱 집계 데이터를 사용하며 이름, 연락처, 원본 응답 행은 포함하지 않습니다.",
    ]
    cursor = 232
    for item in methodology:
        c.setFillColor(TEAL)
        c.circle(MARGIN + 19, cursor + 2, 2.1, fill=1, stroke=0)
        cursor = draw_text(c, item, MARGIN + 29, cursor + 5, CONTENT_W - 46, font_regular, 8.2, 13, NAVY, 2) - 8

    c.setFont(font_bold, 8)
    c.setFillColor(MUTED)
    c.drawString(MARGIN + 15, 125, "해석 원칙")
    draw_text(c, "이 설문은 제품 효과를 입증하지 않습니다. 교류학생이 반복해서 겪은 문제를 찾고 구현 우선순위를 정하는 탐색 조사입니다.", MARGIN + 15, 109, CONTENT_W - 30, font_regular, 8, 12, MUTED, 2)
    draw_page_footer(c, 3, generated_at, font_regular, font_bold)


def build_current_pdf(
    korean_survey: dict[str, Any], foreign_survey: dict[str, Any]
) -> bytes:
    font_regular, font_bold = register_fonts()
    korean = korean_survey["data"]
    foreign = foreign_survey["data"]
    korean_total = int(korean["n"])
    foreign_total = int(foreign["n"])
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4, pageCompression=1)
    c.setTitle("교류학생의 이동과 정보 탐색은 어디서 막혔을까?")
    c.setAuthor("Anonymous aggregated survey")
    c.setKeywords("PROBLEM 01; PROBLEM 02; FROM RESEARCH TO PRODUCT")
    c.setSubject(
        f"total={korean_total + foreign_total}; korean={korean_total}; foreign={foreign_total}; "
        f"korean_source={korean_survey.get('source', '')}; foreign_source={foreign_survey.get('source', '')}"
    )

    draw_research_story_page(c, korean, foreign, generated_at, font_regular, font_bold)
    c.showPage()
    draw_comparison_page(c, korean, foreign, generated_at, font_regular, font_bold)
    c.showPage()
    draw_evidence_page(c, korean_survey, foreign_survey, generated_at, font_regular, font_bold)
    c.showPage()
    c.save()
    return buffer.getvalue()
