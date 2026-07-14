from __future__ import annotations

from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from src.research_page import build_research_view_model
from src.survey_dashboard import pct


PAGE_WIDTH, PAGE_HEIGHT = A4
MARGIN = 42
CONTENT_WIDTH = PAGE_WIDTH - MARGIN * 2

FONT_FALLBACK = "HYGothic-Medium"
FONT_NAME = "AraPresentationKorean"
FONT_CANDIDATES = [
    Path(__file__).resolve().parents[1] / "assets" / "fonts" / "NotoSansKR-Regular.ttf",
    Path("C:/Windows/Fonts/NotoSansKR-VF.ttf"),
    Path("C:/Windows/Fonts/malgun.ttf"),
    Path("/usr/share/fonts/truetype/nanum/NanumGothic.ttf"),
    Path("/usr/share/opentype/noto/NotoSansCJK-Regular.ttc"),
]

NAVY = colors.HexColor("#10203A")
TEXT = colors.HexColor("#334155")
MUTED = colors.HexColor("#64748B")
TEAL = colors.HexColor("#087F73")
TEAL_SOFT = colors.HexColor("#E9F7F4")
CORAL = colors.HexColor("#F45D48")
CORAL_SOFT = colors.HexColor("#FFF0ED")
BLUE = colors.HexColor("#2563EB")
BACKGROUND = colors.HexColor("#F6F8FB")
WHITE = colors.white
LINE = colors.HexColor("#D8E2EE")
TRACK = colors.HexColor("#E8EEF5")


def register_pdf_font() -> str:
    if FONT_NAME in pdfmetrics.getRegisteredFontNames():
        return FONT_NAME
    for font_path in FONT_CANDIDATES:
        if not font_path.exists():
            continue
        try:
            pdfmetrics.registerFont(TTFont(FONT_NAME, str(font_path)))
            return FONT_NAME
        except Exception:
            continue
    if FONT_FALLBACK not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(UnicodeCIDFont(FONT_FALLBACK))
    return FONT_FALLBACK


def _count(items: list[tuple[str, int]], label: str) -> int:
    return dict(items).get(label, 0)


def _source_label(source: object) -> str:
    labels = {
        "Google Sheets": "Google Sheets",
        "CSV fallback": "저장 CSV",
        "CSV": "CSV",
        "CSV summary": "집계 CSV",
    }
    return labels.get(str(source), "데이터 없음")


def _draw_wrapped(
    pdf: canvas.Canvas,
    text: object,
    x: float,
    y: float,
    max_width: float,
    font: str,
    size: float,
    line_height: float,
    color: colors.Color = TEXT,
    max_lines: int | None = None,
) -> float:
    pdf.setFont(font, size)
    pdf.setFillColor(color)
    lines: list[str] = []
    for paragraph in str(text).splitlines() or [""]:
        current = ""
        for char in paragraph:
            candidate = current + char
            if current and pdfmetrics.stringWidth(candidate, font, size) > max_width:
                lines.append(current)
                current = char
            else:
                current = candidate
        if current or not lines:
            lines.append(current)
    if max_lines is not None and len(lines) > max_lines:
        lines = lines[:max_lines]
        if lines[-1]:
            lines[-1] = lines[-1][:-1] + "…"
    for line in lines:
        pdf.drawString(x, y, line)
        y -= line_height
    return y


def _rounded_panel(
    pdf: canvas.Canvas,
    x: float,
    y: float,
    width: float,
    height: float,
    fill: colors.Color = WHITE,
    stroke: colors.Color = LINE,
) -> None:
    pdf.setFillColor(fill)
    pdf.setStrokeColor(stroke)
    pdf.roundRect(x, y, width, height, 6, stroke=1, fill=1)


def _page_base(pdf: canvas.Canvas, page_number: int, generated_at: str, font: str) -> None:
    pdf.setFillColor(BACKGROUND)
    pdf.rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, stroke=0, fill=1)
    pdf.setStrokeColor(LINE)
    pdf.line(MARGIN, 27, PAGE_WIDTH - MARGIN, 27)
    pdf.setFont(font, 7.5)
    pdf.setFillColor(MUTED)
    pdf.drawString(MARGIN, 15, f"제주대학교 교류학생 생활 플랫폼 수요조사 · {generated_at}")
    pdf.drawRightString(PAGE_WIDTH - MARGIN, 15, f"{page_number} / 4")


def _page_heading(
    pdf: canvas.Canvas,
    eyebrow: str,
    title: str,
    subtitle: str,
    font: str,
) -> float:
    pdf.setFillColor(TEAL)
    pdf.setFont(font, 8)
    pdf.drawString(MARGIN, 786, eyebrow)
    y = _draw_wrapped(pdf, title, MARGIN, 756, CONTENT_WIDTH, font, 23, 28, NAVY, 2)
    y -= 6
    return _draw_wrapped(pdf, subtitle, MARGIN, y, CONTENT_WIDTH, font, 9.5, 15, MUTED, 3) - 12


def _metric_card(
    pdf: canvas.Canvas,
    x: float,
    y: float,
    width: float,
    label: str,
    value: str,
    note: str,
    font: str,
) -> None:
    _rounded_panel(pdf, x, y, width, 92)
    pdf.setFillColor(TEAL)
    pdf.rect(x, y, 4, 92, stroke=0, fill=1)
    pdf.setFont(font, 8)
    pdf.setFillColor(MUTED)
    pdf.drawString(x + 14, y + 69, label)
    _draw_wrapped(pdf, value, x + 14, y + 45, width - 26, font, 19, 21, NAVY, 2)
    pdf.setFont(font, 7.5)
    pdf.setFillColor(TEAL)
    pdf.drawString(x + 14, y + 12, note)


def _rank_panel(
    pdf: canvas.Canvas,
    x: float,
    y: float,
    width: float,
    height: float,
    title: str,
    items: list[tuple[str, int]],
    total: int,
    font: str,
    accent: colors.Color = TEAL,
) -> None:
    _rounded_panel(pdf, x, y, width, height)
    pdf.setFont(font, 11)
    pdf.setFillColor(NAVY)
    pdf.drawString(x + 18, y + height - 27, title)
    top = items[:5]
    if not top:
        pdf.setFont(font, 8)
        pdf.setFillColor(MUTED)
        pdf.drawString(x + 18, y + height - 52, "표시할 데이터가 없습니다.")
        return
    max_value = max(value for _, value in top) or 1
    row_y = y + height - 57
    for label, value in top:
        pdf.setFont(font, 8)
        pdf.setFillColor(TEXT)
        pdf.drawString(x + 18, row_y, str(label)[:18])
        pdf.setFillColor(TRACK)
        pdf.roundRect(x + 125, row_y - 1, width - 198, 7, 3.5, stroke=0, fill=1)
        pdf.setFillColor(accent)
        pdf.roundRect(
            x + 125,
            row_y - 1,
            max(4, (width - 198) * value / max_value),
            7,
            3.5,
            stroke=0,
            fill=1,
        )
        pdf.setFont(font, 7.2)
        pdf.setFillColor(MUTED)
        pdf.drawRightString(x + width - 18, row_y, f"{value}명 · {pct(value, total)}")
        row_y -= 27


def _insight_panel(
    pdf: canvas.Canvas,
    x: float,
    y: float,
    width: float,
    number: str,
    title: str,
    body: str,
    font: str,
    accent: colors.Color,
    fill: colors.Color,
) -> None:
    _rounded_panel(pdf, x, y, width, 105, fill=fill, stroke=fill)
    pdf.setFont(font, 9)
    pdf.setFillColor(accent)
    pdf.drawString(x + 18, y + 79, number)
    pdf.setFont(font, 15)
    pdf.setFillColor(NAVY)
    pdf.drawString(x + 18, y + 54, title)
    _draw_wrapped(pdf, body, x + 18, y + 31, width - 36, font, 8.2, 13, TEXT, 2)


def _draw_preview(
    pdf: canvas.Canvas,
    image_path: Path | None,
    x: float,
    y: float,
    width: float,
    height: float,
    font: str,
) -> None:
    _rounded_panel(pdf, x, y, width, height, fill=WHITE)
    if image_path is None or not image_path.exists():
        pdf.setFont(font, 9)
        pdf.setFillColor(MUTED)
        pdf.drawCentredString(x + width / 2, y + height / 2, "모바일 화면 준비 중")
        return
    try:
        image = ImageReader(str(image_path))
        image_width, image_height = image.getSize()
        scale = min((width - 12) / image_width, (height - 12) / image_height)
        draw_width = image_width * scale
        draw_height = image_height * scale
        pdf.drawImage(
            image,
            x + (width - draw_width) / 2,
            y + (height - draw_height) / 2,
            width=draw_width,
            height=draw_height,
            preserveAspectRatio=True,
            mask="auto",
        )
    except Exception:
        pdf.setFont(font, 9)
        pdf.setFillColor(MUTED)
        pdf.drawCentredString(x + width / 2, y + height / 2, "미리보기를 표시할 수 없습니다")


def _cover_page(
    pdf: canvas.Canvas,
    model: dict[str, object],
    korean_survey: dict[str, Any],
    foreign_survey: dict[str, Any],
    generated_at: str,
    font: str,
) -> None:
    _page_base(pdf, 1, generated_at, font)
    _rounded_panel(pdf, MARGIN, 555, CONTENT_WIDTH, 235)
    pdf.setFillColor(TEAL)
    pdf.rect(MARGIN, 555, 5, 235, stroke=0, fill=1)
    pdf.setFont(font, 8)
    pdf.setFillColor(TEAL)
    pdf.drawString(MARGIN + 24, 754, "JEJU EXCHANGE STUDENT RESEARCH")
    y = _draw_wrapped(
        pdf,
        "교류학생의 제주 생활,\n무엇이 가장 불편했을까?",
        MARGIN + 24,
        714,
        CONTENT_WIDTH - 48,
        font,
        26,
        32,
        NAVY,
    )
    y -= 5
    _draw_wrapped(
        pdf,
        "한국인·외국인 교류학생의 이동, 동행 모집, 생활정보 탐색 경험에서 반복된 문제를 제품 기능과 연결했습니다.",
        MARGIN + 24,
        y,
        CONTENT_WIDTH - 48,
        font,
        9.5,
        16,
        TEXT,
        3,
    )
    pdf.setFont(font, 7.5)
    pdf.setFillColor(MUTED)
    pdf.drawString(
        MARGIN + 24,
        575,
        f"한국인 {model['korean_total']}명 · 외국인 {model['foreign_total']}명 · 생성 {generated_at}",
    )

    gap = 10
    card_width = (CONTENT_WIDTH - gap * 3) / 4
    card_y = 438
    cards = [
        ("전체 응답", f"{model['total']}명", "실시간 집계"),
        ("한국인 핵심 불편", str(model["korean_top_pain"][0]), f"{model['korean_top_pain'][1]}명"),
        ("외국인 핵심 불편", str(model["foreign_top_pain"][0]), f"{model['foreign_top_pain'][1]}명"),
        ("서비스 긍정 의향", str(model["positive_pct"]), f"{model['positive_total']}명"),
    ]
    for index, (label, value, note) in enumerate(cards):
        _metric_card(pdf, MARGIN + index * (card_width + gap), card_y, card_width, label, value, note, font)

    pdf.setFont(font, 8)
    pdf.setFillColor(TEAL)
    pdf.drawString(MARGIN, 400, "WHAT WE FOUND")
    pdf.setFont(font, 19)
    pdf.setFillColor(NAVY)
    pdf.drawString(MARGIN, 369, "응답은 두 가지 문제로 모였습니다")
    panel_gap = 12
    panel_width = (CONTENT_WIDTH - panel_gap) / 2
    _insight_panel(
        pdf,
        MARGIN,
        222,
        panel_width,
        "01",
        "이동과 동행 모집",
        "택시와 버스의 부담을 넘어, 같은 시간과 목적지를 가진 사람을 빠르게 찾는 문제가 반복됐습니다.",
        font,
        CORAL,
        CORAL_SOFT,
    )
    _insight_panel(
        pdf,
        MARGIN + panel_width + panel_gap,
        222,
        panel_width,
        "02",
        "공지와 생활정보 탐색",
        "외국인 학생은 교통 문제와 함께 공지·생활정보를 한곳에서 찾고 신뢰도를 확인해야 했습니다.",
        font,
        TEAL,
        TEAL_SOFT,
    )
    pdf.setFont(font, 7.5)
    pdf.setFillColor(MUTED)
    pdf.drawString(
        MARGIN,
        194,
        f"데이터 기준 · 한국인 {_source_label(korean_survey.get('source'))} · 외국인 {_source_label(foreign_survey.get('source'))}",
    )


def _problem_page(
    pdf: canvas.Canvas,
    page_number: int,
    eyebrow: str,
    title: str,
    subtitle: str,
    insight_title: str,
    insight_body: str,
    data: dict[str, Any],
    generated_at: str,
    font: str,
    accent: colors.Color,
    accent_soft: colors.Color,
) -> None:
    _page_base(pdf, page_number, generated_at, font)
    y = _page_heading(pdf, eyebrow, title, subtitle, font)
    _insight_panel(
        pdf,
        MARGIN,
        y - 102,
        CONTENT_WIDTH,
        f"0{page_number - 1}",
        insight_title,
        insight_body,
        font,
        accent,
        accent_soft,
    )
    total = int(data["n"])
    panel_y = y - 342
    _rank_panel(
        pdf,
        MARGIN,
        panel_y,
        CONTENT_WIDTH,
        210,
        "제주에서 불편했던 점",
        data["pain"],
        total,
        font,
        accent,
    )
    _rank_panel(
        pdf,
        MARGIN,
        panel_y - 228,
        CONTENT_WIDTH,
        210,
        "오픈채팅에서 많이 찾은 것",
        data["openchat_find"],
        total,
        font,
        accent,
    )


def _product_page(
    pdf: canvas.Canvas,
    model: dict[str, object],
    question_preview: Path | None,
    meetings_preview: Path | None,
    public_url: str,
    generated_at: str,
    font: str,
) -> None:
    _page_base(pdf, 4, generated_at, font)
    y = _page_heading(
        pdf,
        "FROM RESEARCH TO PRODUCT",
        "조사 결과를 실제 행동으로 연결했습니다",
        "수요조사에서 확인한 두 문제와 직접 연결되는 시냅스팟의 실제 모바일 화면입니다.",
        font,
    )
    gap = 14
    column_width = (CONTENT_WIDTH - gap) / 2
    feature_y = y - 94
    _insight_panel(
        pdf,
        MARGIN,
        feature_y,
        column_width,
        "01 · MOVE TOGETHER",
        "이동·동행 파티",
        "조건별 탐색, 파티 생성, 신청·승인, 참가자 채팅을 한 흐름에서 관리합니다.",
        font,
        CORAL,
        CORAL_SOFT,
    )
    _insight_panel(
        pdf,
        MARGIN + column_width + gap,
        feature_y,
        column_width,
        "02 · TRUST THE ANSWER",
        "근거 있는 AI 질문",
        "공지와 생활정보를 묻고 출처·신뢰도를 함께 확인합니다.",
        font,
        TEAL,
        TEAL_SOFT,
    )
    preview_y = 160
    preview_height = feature_y - preview_y - 18
    _draw_preview(pdf, meetings_preview, MARGIN, preview_y, column_width, preview_height, font)
    _draw_preview(
        pdf,
        question_preview,
        MARGIN + column_width + gap,
        preview_y,
        column_width,
        preview_height,
        font,
    )
    _rounded_panel(pdf, MARGIN, 63, CONTENT_WIDTH, 73, fill=WHITE)
    pdf.setFont(font, 8)
    pdf.setFillColor(NAVY)
    pdf.drawString(MARGIN + 16, 112, "조사에서 제품으로")
    _draw_wrapped(
        pdf,
        f"전체 {model['total']}명의 응답은 제품 방향을 정한 근거이며 기능 효과를 입증한 결과는 아닙니다.",
        MARGIN + 16,
        94,
        CONTENT_WIDTH - 32,
        font,
        7.5,
        11,
        TEXT,
        2,
    )
    pdf.setFont(font, 7)
    pdf.setFillColor(TEAL)
    pdf.drawString(MARGIN + 16, 72, public_url)


def build_presentation_pdf(
    korean_survey: dict[str, Any],
    foreign_survey: dict[str, Any],
    *,
    question_preview: Path | None = None,
    meetings_preview: Path | None = None,
    public_url: str = "",
) -> bytes:
    font = register_pdf_font()
    model = build_research_view_model(korean_survey, foreign_survey)
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    pdf.setTitle("제주대학교 교류학생 생활 플랫폼 수요조사")
    pdf.setAuthor("Synapspot")

    _cover_page(pdf, model, korean_survey, foreign_survey, generated_at, font)
    pdf.showPage()
    _problem_page(
        pdf,
        2,
        "PROBLEM 01 · MOVE TOGETHER",
        "이동과 동행 모집",
        "한국인 교류학생 응답에서 이동 비용과 동행 탐색 문제가 어떻게 나타났는지 살펴봅니다.",
        "같은 시간과 목적지를 가진 사람 찾기",
        "오픈채팅의 빠른 대화 흐름 대신 모집 조건과 상태가 보이는 구조가 필요합니다.",
        korean_survey["data"],
        generated_at,
        font,
        CORAL,
        CORAL_SOFT,
    )
    pdf.showPage()
    _problem_page(
        pdf,
        3,
        "PROBLEM 02 · TRUST THE INFORMATION",
        "공지와 생활정보 탐색",
        "외국인 교류학생 응답에서 교통과 공지·생활정보 탐색 문제가 어떻게 나타났는지 살펴봅니다.",
        "한곳에서 찾고 믿을 만한지 확인하기",
        "흩어진 정보를 검색하고 출처와 최신성을 함께 확인할 수 있는 흐름이 필요합니다.",
        foreign_survey["data"],
        generated_at,
        font,
        TEAL,
        TEAL_SOFT,
    )
    pdf.showPage()
    _product_page(
        pdf,
        model,
        question_preview,
        meetings_preview,
        public_url,
        generated_at,
        font,
    )
    pdf.showPage()
    pdf.save()
    return buffer.getvalue()
