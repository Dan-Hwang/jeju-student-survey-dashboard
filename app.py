from __future__ import annotations

from datetime import datetime
from html import escape
from io import BytesIO
from pathlib import Path
from typing import Any

import streamlit as st
import streamlit.components.v1 as components
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from src.research_brief import (
    BriefContext,
    build_brief_context,
    comparison_html,
    conclusion_html,
    findings_html,
    intro_html,
    product_bridge_html,
)
from src.survey_dashboard import get_foreign_survey, get_public_survey, pct


RESEARCH_CSS_PATH = Path(__file__).parent / "assets" / "research-brief.css"
MEETINGS_PREVIEW = (
    Path(__file__).parent / "assets" / "synapspot-meetings-preview.png"
)
QUESTION_PREVIEW = (
    Path(__file__).parent / "assets" / "synapspot-question-preview.png"
)


def apply_page_style() -> None:
    st.markdown(
        """
<style>
:root {
    --ara-bg: #fbfcfd;
    --ara-card: #fbfcfd;
    --ara-text: #13233d;
    --ara-muted: #66768a;
    --ara-line: #d8e2e9;
    --ara-blue: #132e50;
    --ara-teal: #087f72;
    --ara-coral: #ec6a5f;
}

html, body, [data-testid="stAppViewContainer"], .stApp {
    background: var(--ara-bg);
    color: var(--ara-text);
}

.main .block-container {
    max-width: 880px;
    padding: 1rem 1rem 4rem;
}

[data-testid="stHeader"], footer, #MainMenu {
    visibility: hidden;
    height: 0;
}

h1, h2, h3, p {
    letter-spacing: 0;
}

h1 {
    font-size: 2.65rem !important;
    line-height: 1.15 !important;
    margin-bottom: 0.65rem !important;
}

h2 {
    font-size: 1.8rem !important;
    margin-top: 1.4rem !important;
}

h3 {
    font-size: 1.3rem !important;
}

p, li, .stMarkdown, [data-testid="stCaptionContainer"] {
    color: var(--ara-text);
}

[data-testid="stCaptionContainer"] {
    color: var(--ara-muted) !important;
}

div[data-testid="stVerticalBlockBorderWrapper"] {
    border-color: var(--ara-line);
    border-radius: 8px;
    background: var(--ara-card);
}

div[data-testid="stVerticalBlockBorderWrapper"]:has(h1) {
    border-color: var(--ara-line);
    background: var(--ara-bg);
}

div[data-testid="stProgress"] {
    margin: 0.15rem 0 0.7rem;
}

div[data-testid="stProgress"] > div > div {
    background-color: var(--ara-line);
}

div[data-testid="stProgress"] > div > div > div {
    background: var(--ara-teal);
}

.stButton > button,
div.stDownloadButton > button {
    width: 100%;
    min-height: 2.8rem;
    border-radius: 8px;
    border: 1px solid var(--ara-line);
    background: var(--ara-bg);
    color: var(--ara-text);
    font-weight: 700;
}

div.stDownloadButton > button:hover {
    border-color: var(--ara-blue);
    color: var(--ara-blue);
}

section[data-testid="stSidebar"] {
    display: none;
}

div[role="radiogroup"] {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
}

div[role="radiogroup"] label {
    min-width: max-content;
}

.field-counter {
    overflow: hidden;
    margin: 1rem 0 0.75rem;
    border: 1px solid var(--ara-line);
    border-radius: 8px;
    background: var(--ara-card);
}

.field-total {
    display: flex;
    align-items: flex-end;
    justify-content: space-between;
    gap: 1rem;
    padding: 1.25rem 1.4rem;
    color: var(--ara-bg);
    background: var(--ara-bridge, #132e50);
}

.field-label {
    margin-bottom: 0.25rem;
    color: var(--ara-line);
    font-size: 0.82rem;
    font-weight: 700;
}

.field-number {
    font-size: 3rem;
    font-weight: 800;
    line-height: 1;
}

.field-live {
    color: var(--ara-bg);
    font-size: 0.82rem;
    font-weight: 700;
    text-align: right;
}

.field-groups {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
}

.field-group {
    padding: 1rem 1.4rem;
}

.field-group + .field-group {
    border-left: 1px solid var(--ara-line);
}

.field-group-label {
    color: var(--ara-muted);
    font-size: 0.82rem;
    font-weight: 700;
}

.field-group-value {
    margin-top: 0.2rem;
    color: var(--ara-text);
    font-size: 1.6rem;
    font-weight: 800;
    line-height: 1.2;
}

.field-status {
    padding: 0.65rem 1.4rem;
    border-top: 1px solid var(--ara-line);
    color: var(--ara-muted);
    font-size: 0.78rem;
}

@keyframes araFadeUp {
    from {
        opacity: 0;
        transform: translateY(10px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

@media (prefers-reduced-motion: no-preference) {
    .main .block-container > div {
        animation: araFadeUp 0.35s ease-out both;
    }
}

@media (max-width: 640px) {
    .main .block-container {
        padding: 0.7rem 0.7rem 3.4rem;
    }

    div[data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 8px;
    }

    h1 {
        font-size: 2rem !important;
    }

    h2 {
        font-size: 1.45rem !important;
    }

    h3 {
        font-size: 1.15rem !important;
    }

    .field-counter {
        margin-top: 0.8rem;
    }

    .field-total {
        padding: 1rem;
    }

    .field-number {
        font-size: 2.5rem;
    }

    .field-live {
        max-width: 9rem;
    }

    .field-group {
        padding: 0.85rem 1rem;
    }

    .field-group-value {
        font-size: 1.45rem;
    }

    .field-status {
        padding: 0.6rem 1rem;
    }
}
</style>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<style>{RESEARCH_CSS_PATH.read_text(encoding='utf-8')}</style>",
        unsafe_allow_html=True,
    )


def source_label(source: str) -> str:
    if source == "Google Sheets":
        return "Google Sheets"
    if source == "CSV fallback":
        return "저장 CSV"
    if source == "CSV":
        return "CSV"
    if source == "CSV summary":
        return "집계 CSV"
    return "데이터 없음"


def get_count(items: list[tuple[str, int]], label: str, default: int = 0) -> int:
    return dict(items).get(label, default)


def render_html(html: str, height: int) -> None:
    components.html(html, height=height, scrolling=False)


def chart_theme() -> str:
    return """
<style>
:root {
    --chart-navy: #13233d;
    --chart-teal: #087f72;
    --chart-coral: #ec6a5f;
    --chart-bg: #fbfcfd;
    --chart-line: #d8e2e9;
    --chart-muted: #66768a;
    --chart-bridge: #132e50;
}
* {
    box-sizing: border-box;
}

body {
    margin: 0;
    padding: 0;
    color: var(--chart-navy);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    background: transparent;
}

.chart-card {
    width: 100%;
    border: 1px solid var(--chart-line);
    border-radius: 8px;
    background: var(--chart-bg);
    padding: clamp(16px, 4vw, 24px);
}

.chart-kicker {
    color: var(--chart-muted);
    font-size: 12px;
    font-weight: 800;
    letter-spacing: 0;
    margin-bottom: 8px;
}

.summary-grid {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 12px;
}

.summary-card {
    min-height: 126px;
    border-radius: 8px;
    padding: 16px;
    background: var(--chart-bg);
    border: 1px solid var(--chart-line);
    position: relative;
    overflow: hidden;
}

.summary-card::before {
    content: "";
    position: absolute;
    left: 0;
    top: 0;
    width: 5px;
    height: 100%;
    background: var(--chart-teal);
}

.summary-label {
    color: var(--chart-muted);
    font-size: 12px;
    font-weight: 800;
}

.summary-value {
    margin-top: 10px;
    color: var(--chart-navy);
    font-size: clamp(23px, 6vw, 33px);
    line-height: 1.1;
    font-weight: 900;
    overflow-wrap: anywhere;
}

.summary-note {
    margin-top: 8px;
    color: var(--chart-teal);
    font-size: 12px;
    font-weight: 800;
}

.bar-list {
    display: grid;
    gap: 14px;
}

.bar-row {
    display: grid;
    grid-template-columns: minmax(108px, 170px) 1fr minmax(86px, auto);
    gap: 12px;
    align-items: center;
}

.bar-label {
    font-size: 15px;
    font-weight: 800;
    overflow-wrap: anywhere;
}

.bar-track {
    height: 16px;
    overflow: hidden;
    border-radius: 3px;
    background: var(--chart-line);
}

.bar-fill {
    height: 100%;
    min-width: 9px;
    border-radius: 3px;
    background: var(--chart-teal);
}

.bar-value {
    color: var(--chart-muted);
    font-size: 13px;
    font-weight: 800;
    text-align: right;
    white-space: nowrap;
}

.intent-layout {
    display: grid;
    gap: 18px;
}

.intent-bar {
    display: flex;
    overflow: hidden;
    width: 100%;
    height: 18px;
    border: 1px solid var(--chart-line);
    border-radius: 3px;
    background: var(--chart-line);
}

.intent-segment {
    display: block;
    height: 100%;
}

.intent-segment.positive, .dot.positive {
    background: var(--chart-teal);
}

.intent-segment.neutral, .dot.neutral {
    background: var(--chart-muted);
}

.intent-segment.negative, .dot.negative {
    background: var(--chart-coral);
}

.legend {
    display: grid;
    gap: 12px;
}

.legend-row {
    display: grid;
    grid-template-columns: 12px 1fr auto;
    gap: 10px;
    align-items: center;
}

.dot {
    width: 12px;
    height: 12px;
    border-radius: 50%;
}

.legend-label {
    font-weight: 800;
}

.legend-value {
    color: var(--chart-muted);
    font-size: 13px;
    font-weight: 800;
    white-space: nowrap;
}

@media (max-width: 620px) {
    .summary-grid {
        grid-template-columns: 1fr 1fr;
    }

    .summary-card {
        min-height: 118px;
        padding: 14px;
    }

    .bar-row {
        grid-template-columns: 1fr;
        gap: 6px;
    }

    .bar-value {
        text-align: left;
    }

}
</style>
"""


def summary_cards_html(data: dict[str, Any], total: int) -> str:
    pain = data["pain"]
    openchat_find = data["openchat_find"]
    top_pain = pain[0] if pain else ("-", 0)
    top_openchat = openchat_find[0] if openchat_find else ("-", 0)
    cards = [
        ("전체 응답", f"{total}명", "실시간 집계 기준"),
        ("4주 이상 체류", f"{int(data['stay_4weeks'])}명", pct(int(data["stay_4weeks"]), total)),
        ("불편 1순위", str(top_pain[0]), f"{top_pain[1]}명"),
        ("오픈채팅 1순위", str(top_openchat[0]), f"{top_openchat[1]}명"),
    ]
    card_markup = "\n".join(
        f"""
<article class="summary-card">
    <div class="summary-label">{escape(label)}</div>
    <div class="summary-value">{escape(value)}</div>
    <div class="summary-note">{escape(note)}</div>
</article>
"""
        for label, value, note in cards
    )
    return f"{chart_theme()}<section class='summary-grid'>{card_markup}</section>"


def simple_cards_html(cards: list[tuple[str, str, str]]) -> str:
    card_markup = "\n".join(
        f"""
<article class="summary-card">
    <div class="summary-label">{escape(label)}</div>
    <div class="summary-value">{escape(value)}</div>
    <div class="summary-note">{escape(note)}</div>
</article>
"""
        for label, value, note in cards
    )
    return f"{chart_theme()}<section class='summary-grid'>{card_markup}</section>"


def bar_chart_html(items: list[tuple[str, int]], total: int) -> str:
    if not items:
        return f"{chart_theme()}<section class='chart-card'>아직 표시할 응답이 없습니다.</section>"

    max_value = max(value for _, value in items) or 1
    rows = []
    for label, value in items:
        width = max(3, round(value / max_value * 100))
        rows.append(
            f"""
<div class="bar-row">
    <div class="bar-label">{escape(label)}</div>
    <div class="bar-track"><div class="bar-fill" style="width:{width}%"></div></div>
    <div class="bar-value">{value}명 · {pct(value, total)}</div>
</div>
"""
        )
    return f"{chart_theme()}<section class='chart-card'><div class='bar-list'>{''.join(rows)}</div></section>"


def intent_chart_html(intent: list[tuple[str, int]], total: int) -> str:
    values = dict(intent)
    positive = values.get("긍정", 0)
    neutral = values.get("중립", 0)
    negative = values.get("부정", 0)
    legend = [
        ("긍정", positive, "positive"),
        ("중립", neutral, "neutral"),
        ("부정", negative, "negative"),
    ]
    segments = []
    for label, value, accent in legend:
        width = max(0.0, min(100.0, value / total * 100)) if total > 0 else 0.0
        segments.append(
            f'<span class="intent-segment {accent}" style="width:{width:.1f}%" '
            f'aria-label="{escape(label)} {value}명 {pct(value, total)}"></span>'
        )
    legend_markup = "\n".join(
        f"""
<div class="legend-row">
    <span class="dot {accent}"></span>
    <span class="legend-label">{escape(label)}</span>
    <span class="legend-value">{value}명 · {pct(value, total)}</span>
</div>
"""
        for label, value, accent in legend
    )
    return f"""
{chart_theme()}
<section class="chart-card">
    <div class="intent-layout">
        <div class="intent-bar">{''.join(segments)}</div>
        <div class="legend">{legend_markup}</div>
    </div>
</section>
"""


def field_counter_html(korean_survey: dict[str, object], foreign_survey: dict[str, object]) -> str:
    korean_total = int(korean_survey["data"]["n"])
    foreign_total = int(foreign_survey["data"]["n"])
    total = korean_total + foreign_total
    is_live = (
        korean_survey.get("source") == "Google Sheets"
        and foreign_survey.get("source") == "Google Sheets"
    )
    status = "Google Sheets 실시간 집계" if is_live else "저장 데이터 기준 집계"
    loaded_at = str(korean_survey.get("loaded_at", "확인 불가"))
    return f"""
<section class="field-counter" aria-label="현장 응답 현황">
    <div class="field-total">
        <div>
            <div class="field-label">총 응답</div>
            <div class="field-number">{total}명</div>
        </div>
        <div class="field-live">{escape(status)}</div>
    </div>
    <div class="field-groups">
        <div class="field-group">
            <div class="field-group-label">한국인</div>
            <div class="field-group-value">{korean_total}명</div>
        </div>
        <div class="field-group">
            <div class="field-group-label">외국인</div>
            <div class="field-group-value">{foreign_total}명</div>
        </div>
    </div>
    <div class="field-status">마지막 갱신 {escape(loaded_at)} · 실시간 집계는 새로고침 시 반영됩니다.</div>
</section>
"""


def render_header(
    korean_survey: dict[str, object], foreign_survey: dict[str, object]
) -> BriefContext:
    context = build_brief_context(korean_survey, foreign_survey)
    st.markdown(intro_html(context), unsafe_allow_html=True)
    if korean_survey.get("error"):
        st.warning(str(korean_survey["error"]))
    if foreign_survey.get("error"):
        st.warning(str(foreign_survey["error"]))
    return context


def render_research_findings(context: BriefContext) -> None:
    st.markdown(findings_html(context), unsafe_allow_html=True)
    st.markdown(comparison_html(context), unsafe_allow_html=True)


def render_conclusion(context: BriefContext) -> None:
    st.markdown(conclusion_html(context), unsafe_allow_html=True)


def render_product_bridge(context: BriefContext) -> None:
    markup = product_bridge_html(context, MEETINGS_PREVIEW, QUESTION_PREVIEW)
    if markup:
        st.markdown(markup, unsafe_allow_html=True)


def render_summary(data: dict[str, object], total: int) -> None:
    pain = data["pain"]
    openchat_find = data["openchat_find"]
    intent = data["intent"]
    positive = get_count(intent, "긍정")
    top_pain = pain[0] if pain else ("-", 0)
    top_openchat = openchat_find[0] if openchat_find else ("-", 0)
    cards = [
        ("한국인 응답", f"{total}명", "집계 기준"),
        ("4주 이상 체류", f"{int(data['stay_4weeks'])}명", pct(int(data["stay_4weeks"]), total)),
        ("불편 1순위", str(top_pain[0]), f"{top_pain[1]}명"),
        ("오픈채팅 1순위", str(top_openchat[0]), f"{top_openchat[1]}명"),
    ]

    st.markdown("## 한국인 설문 요약")
    render_html(simple_cards_html(cards), 290)

    with st.container(border=True):
        st.markdown("### 먼저 볼 점")
        if total:
            st.write(
                f"한국인 응답에서는 **{top_openchat[0]} 탐색**과 **{top_pain[0]} 문제**가 가장 두드러집니다. "
                f"서비스 사용 의향은 긍정 {positive}명({pct(positive, total)})으로, 이동/동행 모집 기능을 먼저 검증할 근거가 됩니다."
            )
        else:
            st.write("아직 표시할 응답이 없습니다.")


def render_foreign_summary(data: dict[str, object], total: int) -> None:
    pain = data["pain"]
    openchat_find = data["openchat_find"]
    intent = data["intent"]
    positive = get_count(intent, "긍정")
    top_pain = pain[0] if pain else ("-", 0)
    top_openchat = openchat_find[0] if openchat_find else ("-", 0)
    top_taxi = data["taxi_frequency"][0] if data["taxi_frequency"] else ("-", 0)
    cards = [
        ("외국인 응답", f"{total}명", "집계 기준"),
        ("불편 1순위", str(top_pain[0]), f"{top_pain[1]}명"),
        ("오픈채팅 1순위", str(top_openchat[0]), f"{top_openchat[1]}명"),
        ("택시 이용", str(top_taxi[0]), f"{top_taxi[1]}명"),
    ]

    st.markdown("## 외국인 설문 요약")
    render_html(simple_cards_html(cards), 290)

    with st.container(border=True):
        st.markdown("### 먼저 볼 점")
        if total:
            st.write(
                f"외국인 응답에서는 **{top_pain[0]}**와 **{top_openchat[0]}** 수요가 두드러집니다. "
                f"서비스 사용 의향은 긍정 {positive}명({pct(positive, total)})입니다."
            )
        else:
            st.write("아직 표시할 응답이 없습니다.")


def render_rank_section(title: str, subtitle: str, items: list[tuple[str, int]], total: int) -> None:
    st.markdown(f"## {title}")
    st.caption(subtitle)
    height = 124 + max(1, len(items)) * 72
    render_html(bar_chart_html(items, total), height)


def render_intent_section(intent: list[tuple[str, int]], total: int) -> None:
    st.markdown("## 서비스 사용 의향")
    render_html(intent_chart_html(intent, total), 340)


def render_comments_section(comments: list[str], key_prefix: str) -> None:
    st.markdown("## 익명 자유 의견")
    with st.container(border=True):
        st.caption("빈 답변과 N/A성 답변은 제외했습니다.")
        if not comments:
            st.write("아직 표시할 자유 의견이 없습니다.")
            return

        page_size = 5
        total_pages = max(1, (len(comments) + page_size - 1) // page_size)
        page_key = f"{key_prefix}_comments_page"
        st.session_state[page_key] = min(st.session_state.get(page_key, 0), total_pages - 1)

        current_page = st.session_state[page_key]
        start = current_page * page_size
        visible_comments = comments[start : start + page_size]

        st.caption(f"{len(comments)}개 중 {start + 1}-{start + len(visible_comments)}개 표시")
        for offset, comment in enumerate(visible_comments, start=1):
            index = start + offset
            st.markdown(f"**의견 {index}**")
            st.write(comment)
            if offset < len(visible_comments):
                st.divider()

        if total_pages > 1:
            previous_col, page_col, next_col = st.columns([1, 1, 1])
            with previous_col:
                if st.button("이전", key=f"{key_prefix}_comments_prev", disabled=current_page == 0, use_container_width=True):
                    st.session_state[page_key] = current_page - 1
                    st.rerun()
            with page_col:
                st.markdown(f"<div style='text-align:center; padding-top:0.45rem;'>{current_page + 1} / {total_pages}</div>", unsafe_allow_html=True)
            with next_col:
                if st.button("다음", key=f"{key_prefix}_comments_next", disabled=current_page >= total_pages - 1, use_container_width=True):
                    st.session_state[page_key] = current_page + 1
                    st.rerun()


PDF_FONT = "HYGothic-Medium"
PDF_TTF_FONT = "AraKorean"
PDF_FONT_CANDIDATES = [
    Path("assets/fonts/NotoSansKR-Regular.ttf"),
    Path("C:/Windows/Fonts/NotoSansKR-VF.ttf"),
    Path("C:/Windows/Fonts/malgun.ttf"),
    Path("/usr/share/fonts/truetype/nanum/NanumGothic.ttf"),
    Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
]
PDF_TEXT = colors.HexColor("#13233D")
PDF_MUTED = colors.HexColor("#66768A")
PDF_LINE = colors.HexColor("#D8E2E9")
PDF_BLUE = colors.HexColor("#EC6A5F")
PDF_TEAL = colors.HexColor("#087F72")


def register_pdf_font() -> str:
    if PDF_TTF_FONT in pdfmetrics.getRegisteredFontNames():
        return PDF_TTF_FONT

    for font_path in PDF_FONT_CANDIDATES:
        if font_path.exists():
            try:
                pdfmetrics.registerFont(TTFont(PDF_TTF_FONT, str(font_path)))
                return PDF_TTF_FONT
            except Exception:
                continue

    if PDF_FONT not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(UnicodeCIDFont(PDF_FONT))
    return PDF_FONT


def draw_wrapped_text(
    c: canvas.Canvas,
    text: str,
    x: float,
    y: float,
    max_width: float,
    line_height: float,
    font_name: str,
    font_size: int,
    color: colors.Color = PDF_TEXT,
) -> float:
    c.setFont(font_name, font_size)
    c.setFillColor(color)
    for paragraph in str(text).splitlines() or [""]:
        current = ""
        for char in paragraph:
            candidate = current + char
            if current and pdfmetrics.stringWidth(candidate, font_name, font_size) > max_width:
                c.drawString(x, y, current)
                y -= line_height
                current = char
            else:
                current = candidate
        if current:
            c.drawString(x, y, current)
            y -= line_height
    return y


def draw_pdf_title(c: canvas.Canvas, title: str, subtitle: str, y: float, font_name: str) -> float:
    c.setFillColor(PDF_TEAL)
    c.setFont(font_name, 9)
    c.drawString(42, y, "JEJU NATIONAL UNIVERSITY EXCHANGE STUDENT SURVEY")
    y -= 28
    y = draw_wrapped_text(c, title, 42, y, 510, 25, font_name, 22)
    y -= 8
    return draw_wrapped_text(c, subtitle, 42, y, 510, 15, font_name, 10, PDF_MUTED) - 18


def draw_pdf_section(c: canvas.Canvas, title: str, y: float, font_name: str) -> float:
    c.setStrokeColor(PDF_LINE)
    c.line(42, y + 12, 553, y + 12)
    c.setFillColor(PDF_TEXT)
    c.setFont(font_name, 16)
    c.drawString(42, y - 8, title)
    return y - 34


def draw_pdf_metric(c: canvas.Canvas, label: str, value: str, note: str, x: float, y: float, font_name: str) -> None:
    c.setStrokeColor(PDF_LINE)
    c.setFillColor(colors.white)
    c.roundRect(x, y - 70, 118, 70, 10, stroke=1, fill=1)
    c.setFillColor(PDF_MUTED)
    c.setFont(font_name, 9)
    c.drawString(x + 12, y - 19, label)
    c.setFillColor(PDF_TEXT)
    c.setFont(font_name, 19)
    c.drawString(x + 12, y - 43, value)
    c.setFillColor(PDF_TEAL)
    c.setFont(font_name, 8)
    c.drawString(x + 12, y - 59, note)


def draw_pdf_rankings(
    c: canvas.Canvas,
    title: str,
    items: list[tuple[str, int]],
    total: int,
    x: float,
    y: float,
    font_name: str,
    limit: int = 5,
) -> float:
    c.setFillColor(PDF_TEXT)
    c.setFont(font_name, 12)
    c.drawString(x, y, title)
    y -= 19
    max_value = max([value for _, value in items[:limit]] + [1])
    for label, value in items[:limit]:
        ratio = value / max_value if max_value else 0
        c.setFillColor(PDF_TEXT)
        c.setFont(font_name, 9)
        c.drawString(x, y, str(label)[:22])
        c.setFillColor(colors.HexColor("#E8EEF5"))
        c.roundRect(x + 118, y - 1, 92, 6, 3, stroke=0, fill=1)
        c.setFillColor(PDF_TEAL)
        c.roundRect(x + 118, y - 1, 92 * ratio, 6, 3, stroke=0, fill=1)
        c.setFillColor(PDF_MUTED)
        c.drawRightString(x + 250, y, f"{value}명 · {pct(value, total)}")
        y -= 18
    return y - 10


def draw_pdf_comments(c: canvas.Canvas, comments: list[str], x: float, y: float, font_name: str, limit: int = 5) -> float:
    c.setFillColor(PDF_TEXT)
    c.setFont(font_name, 12)
    c.drawString(x, y, "익명 자유 의견")
    y -= 18
    if not comments:
        c.setFillColor(PDF_MUTED)
        c.setFont(font_name, 9)
        c.drawString(x, y, "표시할 자유 의견이 없습니다.")
        return y - 18
    for index, comment in enumerate(comments[:limit], start=1):
        y = draw_wrapped_text(c, f"{index}. {comment}", x, y, 495, 13, font_name, 8, PDF_TEXT)
        y -= 4
    if len(comments) > limit:
        c.setFillColor(PDF_MUTED)
        c.setFont(font_name, 8)
        c.drawString(x, y, f"외 {len(comments) - limit}개 의견은 사이트의 익명 자유 의견 페이지에서 확인할 수 있습니다.")
        y -= 14
    return y


def draw_survey_pdf_page(c: canvas.Canvas, title: str, data: dict[str, Any], source: str, loaded_at: str, font_name: str) -> None:
    total = int(data["n"])
    top_pain = data["pain"][0] if data["pain"] else ("-", 0)
    top_openchat = data["openchat_find"][0] if data["openchat_find"] else ("-", 0)
    positive = get_count(data["intent"], "긍정")

    y = draw_pdf_title(c, title, f"응답 {total}명 · 데이터 소스 {source_label(source)} · 마지막 갱신 {loaded_at}", 800, font_name)
    draw_pdf_metric(c, "응답 수", f"{total}명", "현재 집계 기준", 42, y, font_name)
    draw_pdf_metric(c, "불편 1순위", str(top_pain[0]), f"{top_pain[1]}명", 172, y, font_name)
    draw_pdf_metric(c, "오픈채팅 1순위", str(top_openchat[0]), f"{top_openchat[1]}명", 302, y, font_name)
    draw_pdf_metric(c, "사용 의향", f"{positive}명", f"긍정 {pct(positive, total)}", 432, y, font_name)

    y -= 100
    y = draw_pdf_section(c, "주요 응답", y, font_name)
    left_y = draw_pdf_rankings(c, "제주에서 불편했던 점", data["pain"], total, 42, y, font_name)
    right_y = draw_pdf_rankings(c, "오픈채팅에서 찾는 정보", data["openchat_find"], total, 315, y, font_name)
    y = min(left_y, right_y) - 4
    left_y = draw_pdf_rankings(c, "같이 하고 싶은 활동", data["activity"], total, 42, y, font_name)
    right_y = draw_pdf_rankings(c, "오픈채팅에서 불편한 점", data["openchat_pain"], total, 315, y, font_name)
    y = min(left_y, right_y) - 4
    y = draw_pdf_section(c, "익명 의견", y, font_name)
    draw_pdf_comments(c, data.get("comments", []), 42, y, font_name)


def build_current_pdf(korean_survey: dict[str, Any], foreign_survey: dict[str, Any]) -> bytes:
    font_name = register_pdf_font()
    korean = korean_survey["data"]
    foreign = foreign_survey["data"]
    korean_total = int(korean["n"])
    foreign_total = int(foreign["n"])

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    c.setTitle("Jeju Exchange Student Survey Research Brief")
    c.setSubject(
        f"total={korean_total + foreign_total}; korean={korean_total}; foreign={foreign_total}; "
        f"korean_source={korean_survey.get('source', '')}; foreign_source={foreign_survey.get('source', '')}"
    )

    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    korean_top = korean["openchat_find"][0] if korean["openchat_find"] else ("-", 0)
    foreign_top = foreign["openchat_find"][0] if foreign["openchat_find"] else ("-", 0)

    y = draw_pdf_title(c, "제주대학교 교류학생 생활 플랫폼 수요조사", f"생성 시각 {generated_at} · 한국인/외국인 설문 집계 요약", 800, font_name)
    draw_pdf_metric(c, "전체 응답", f"{korean_total + foreign_total}명", "한국인 + 외국인", 42, y, font_name)
    draw_pdf_metric(c, "한국인 응답", f"{korean_total}명", f"주요 수요 {korean_top[0]}", 172, y, font_name)
    draw_pdf_metric(c, "외국인 응답", f"{foreign_total}명", f"주요 수요 {foreign_top[0]}", 302, y, font_name)
    draw_pdf_metric(c, "공통 방향", "이동/동행", "모집과 정보 탐색", 432, y, font_name)
    y -= 105
    y = draw_pdf_section(c, "데이터 기준", y, font_name)
    y = draw_wrapped_text(c, f"한국인 설문: {source_label(str(korean_survey.get('source', '')))} · {korean_survey.get('loaded_at', '-')}", 42, y, 500, 15, font_name, 10)
    y = draw_wrapped_text(c, f"외국인 설문: {source_label(str(foreign_survey.get('source', '')))} · {foreign_survey.get('loaded_at', '-')}", 42, y, 500, 15, font_name, 10)
    y -= 14
    y = draw_pdf_section(c, "한눈에 보는 결론", y, font_name)
    draw_wrapped_text(
        c,
        "이동·동행 모집과 신뢰할 수 있는 생활정보 탐색이 함께 필요했습니다. "
        "PDF는 다운로드 시점의 앱 집계 데이터를 기준으로 생성되며, 개인 식별 정보와 원본 응답 행은 포함하지 않습니다.",
        42,
        y,
        500,
        16,
        font_name,
        10,
    )
    c.showPage()

    draw_survey_pdf_page(
        c,
        "한국인 설문 요약",
        korean,
        str(korean_survey.get("source", "")),
        str(korean_survey.get("loaded_at", "-")),
        font_name,
    )
    c.showPage()

    draw_survey_pdf_page(
        c,
        "외국인 설문 요약",
        foreign,
        str(foreign_survey.get("source", "")),
        str(foreign_survey.get("loaded_at", "-")),
        font_name,
    )
    c.showPage()

    c.save()
    return buffer.getvalue()


def render_downloads(korean_survey: dict[str, Any], foreign_survey: dict[str, Any]) -> None:
    st.markdown("## 공유 자료")
    with st.container(border=True):
        st.write("개별 응답과 원본 대화는 공개하지 않고, 현재 집계 결과와 익명 자유 의견 일부만 표시합니다.")
        st.download_button(
            "현재 데이터로 PDF 내려받기",
            data=build_current_pdf(korean_survey, foreign_survey),
            file_name="jeju-student-survey-live-report.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
        st.caption("PDF는 다운로드 버튼을 누르는 시점의 한국인/외국인 설문 집계를 기준으로 생성됩니다.")


def render_korean_view(survey: dict[str, object]) -> None:
    data = survey["data"]
    total = int(data["n"])
    render_summary(data, total)
    render_rank_section("제주에서 불편했던 점", "한국인 설문 · 복수 응답", data["pain"], total)
    render_rank_section("같이 하고 싶은 활동", "한국인 설문 · 복수 응답", data["activity"], total)
    render_rank_section("오픈채팅에서 찾는 정보", "한국인 설문 · 단일 응답", data["openchat_find"], total)
    render_rank_section("오픈채팅에서 불편한 점", "한국인 설문 · 복수 응답", data["openchat_pain"], total)
    render_intent_section(data["intent"], total)
    render_comments_section(data.get("comments", []), "korean")


def render_foreign_view(survey: dict[str, object]) -> None:
    data = survey["data"]
    total = int(data["n"])
    render_foreign_summary(data, total)
    render_rank_section("제주에서 불편했던 점", "외국인 설문 · 복수 응답", data["pain"], total)
    render_rank_section("택시 이용 빈도", "외국인 설문 · 단일 응답", data["taxi_frequency"], total)
    render_rank_section("같이 하고 싶은 활동", "외국인 설문 · 복수 응답", data["activity"], total)
    render_rank_section("오픈채팅에서 찾는 정보", "외국인 설문 · 복수 응답", data["openchat_find"], total)
    render_rank_section("오픈채팅에서 불편한 점", "외국인 설문 · 복수 응답", data["openchat_pain"], total)
    render_intent_section(data["intent"], total)
    render_comments_section(data.get("comments", []), "foreign")


def render_compare_view(korean_survey: dict[str, object], foreign_survey: dict[str, object]) -> None:
    korean = korean_survey["data"]
    foreign = foreign_survey["data"]
    korean_total = int(korean["n"])
    foreign_total = int(foreign["n"])
    korean_top_pain = korean["pain"][0] if korean["pain"] else ("-", 0)
    foreign_top_pain = foreign["pain"][0] if foreign["pain"] else ("-", 0)
    korean_top_openchat = korean["openchat_find"][0] if korean["openchat_find"] else ("-", 0)
    foreign_top_openchat = foreign["openchat_find"][0] if foreign["openchat_find"] else ("-", 0)
    korean_positive = get_count(korean["intent"], "긍정")
    foreign_positive = get_count(foreign["intent"], "긍정")

    st.markdown("## 비교 요약")
    cards = [
        ("한국인 응답", f"{korean_total}명", f"긍정 {pct(korean_positive, korean_total)}"),
        ("외국인 응답", f"{foreign_total}명", f"긍정 {pct(foreign_positive, foreign_total)}"),
        ("한국인 불편", str(korean_top_pain[0]), f"{korean_top_pain[1]}명"),
        ("외국인 불편", str(foreign_top_pain[0]), f"{foreign_top_pain[1]}명"),
    ]
    render_html(simple_cards_html(cards), 290)

    with st.container(border=True):
        st.markdown("### 공통으로 보이는 방향")
        st.write(
            f"한국인 설문은 **{korean_top_openchat[0]}** 중심, 외국인 설문은 **{foreign_top_openchat[0]}** 중심으로 오픈채팅 수요가 나타납니다. "
            "두 집단 모두 이동과 동행 모집, 그리고 흩어진 정보를 한곳에서 찾는 흐름이 강하므로 "
            "초기 서비스는 실시간 이동/동행 모집과 신뢰 가능한 정보 정리를 함께 보여주는 방향이 적합합니다."
        )

    render_rank_section("한국인 설문: 불편했던 점", "비교용", korean["pain"], korean_total)
    render_rank_section("외국인 설문: 불편했던 점", "비교용", foreign["pain"], foreign_total)
    render_rank_section("한국인 설문: 오픈채팅에서 찾는 것", "비교용", korean["openchat_find"], korean_total)
    render_rank_section("외국인 설문: 오픈채팅에서 찾는 정보", "비교용", foreign["openchat_find"], foreign_total)


def render_overall_view(korean_survey: dict[str, object], foreign_survey: dict[str, object]) -> None:
    korean = korean_survey["data"]
    foreign = foreign_survey["data"]
    korean_total = int(korean["n"])
    foreign_total = int(foreign["n"])
    korean_top_openchat = korean["openchat_find"][0] if korean["openchat_find"] else ("-", 0)
    foreign_top_openchat = foreign["openchat_find"][0] if foreign["openchat_find"] else ("-", 0)

    st.markdown("## 전체 요약")
    cards = [
        ("전체 응답", f"{korean_total + foreign_total}명", "한국인 + 외국인"),
        ("한국인 응답", f"{korean_total}명", f"주요 수요 {korean_top_openchat[0]}"),
        ("외국인 응답", f"{foreign_total}명", f"주요 수요 {foreign_top_openchat[0]}"),
        ("공통 방향", "이동/동행", "정보 탐색과 모집을 함께 해결"),
    ]
    render_html(simple_cards_html(cards), 290)

    st.markdown("### 한국인 응답 상세")
    render_rank_section(
        "한국인 핵심 불편",
        "한국인 응답 기준",
        korean["pain"],
        korean_total,
    )
    render_rank_section(
        "한국인 오픈채팅 수요",
        "한국인 응답 기준",
        korean["openchat_find"],
        korean_total,
    )

    st.markdown("### 외국인 응답 상세")
    render_rank_section(
        "외국인 핵심 불편",
        "외국인 응답 기준",
        foreign["pain"],
        foreign_total,
    )
    render_rank_section(
        "외국인 오픈채팅 수요",
        "외국인 응답 기준",
        foreign["openchat_find"],
        foreign_total,
    )


def render_survey_dashboard() -> None:
    st.set_page_config(
        page_title="교류학생의 이동과 정보 탐색",
        page_icon="📊",
        layout="centered",
    )
    apply_page_style()

    korean_survey = get_public_survey()
    foreign_survey = get_foreign_survey()

    context = render_header(korean_survey, foreign_survey)
    if st.button("데이터 새로고침", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    render_conclusion(context)
    render_research_findings(context)
    render_product_bridge(context)
    st.markdown("## 상세 조사 결과")
    selected_view = st.radio(
        "보기 선택",
        ["전체 요약", "한국인 설문", "외국인 설문", "비교 요약"],
        horizontal=True,
        label_visibility="collapsed",
    )

    if selected_view == "한국인 설문":
        render_korean_view(korean_survey)
    elif selected_view == "외국인 설문":
        render_foreign_view(foreign_survey)
    elif selected_view == "비교 요약":
        render_compare_view(korean_survey, foreign_survey)
    else:
        render_overall_view(korean_survey, foreign_survey)

    render_downloads(korean_survey, foreign_survey)


def main() -> None:
    render_survey_dashboard()


if __name__ == "__main__":
    main()
