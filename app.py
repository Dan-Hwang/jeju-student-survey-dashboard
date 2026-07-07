from __future__ import annotations

from html import escape
from pathlib import Path
from typing import Any

import streamlit as st

from src.survey_dashboard import REPORT_PDF, REPORT_PNG, get_public_survey, pct

BASE_DIR = Path(__file__).resolve().parent


def apply_page_style() -> None:
    st.markdown(
        """
        <style>
        :root {
            --bg: #070a12;
            --panel: rgba(12, 20, 35, 0.78);
            --panel-strong: rgba(14, 27, 47, 0.9);
            --line: rgba(93, 242, 255, 0.22);
            --line-hot: rgba(255, 71, 196, 0.38);
            --cyan: #5df2ff;
            --mint: #72f6bf;
            --pink: #ff47c4;
            --amber: #ffd166;
            --text: #eef7ff;
            --muted: #a9b7c9;
            --dim: #6f7d90;
        }

        html, body, [data-testid="stAppViewContainer"], .stApp {
            background:
                radial-gradient(circle at 12% 8%, rgba(93, 242, 255, 0.18), transparent 28rem),
                radial-gradient(circle at 88% 14%, rgba(255, 71, 196, 0.16), transparent 24rem),
                linear-gradient(135deg, #05070d 0%, #08111f 48%, #060711 100%);
            color: var(--text);
        }

        .main .block-container {
            max-width: 1100px;
            padding: clamp(1.1rem, 4vw, 3.2rem) clamp(1rem, 3vw, 2.2rem) 4rem;
        }

        [data-testid="stHeader"], footer, #MainMenu {
            visibility: hidden;
            height: 0;
        }

        h1, h2, h3, p {
            letter-spacing: 0;
        }

        .cyber-shell {
            position: relative;
            overflow: hidden;
        }

        .cyber-shell::before {
            content: "";
            position: fixed;
            inset: 0;
            pointer-events: none;
            background: linear-gradient(rgba(255,255,255,0.035) 1px, transparent 1px);
            background-size: 100% 4px;
            mix-blend-mode: screen;
            opacity: 0.16;
            animation: scan 7s linear infinite;
            z-index: 0;
        }

        .hero {
            position: relative;
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: clamp(1.15rem, 5vw, 2.2rem);
            background:
                linear-gradient(135deg, rgba(93, 242, 255, 0.12), transparent 38%),
                linear-gradient(160deg, rgba(255, 71, 196, 0.08), transparent 52%),
                var(--panel);
            box-shadow: 0 0 30px rgba(93, 242, 255, 0.08), inset 0 0 0 1px rgba(255,255,255,0.04);
            animation: rise 0.55s ease-out both;
        }

        .hero::after {
            content: "";
            position: absolute;
            inset: 0;
            border-radius: 8px;
            pointer-events: none;
            background: linear-gradient(90deg, transparent, rgba(93, 242, 255, 0.16), transparent);
            transform: translateX(-120%);
            animation: sweep 5.5s ease-in-out infinite;
        }

        .kicker {
            display: inline-flex;
            align-items: center;
            gap: 0.55rem;
            color: var(--cyan);
            font-size: 0.78rem;
            font-weight: 800;
            text-transform: uppercase;
            margin-bottom: 0.9rem;
        }

        .kicker::before {
            content: "";
            width: 0.52rem;
            height: 0.52rem;
            background: var(--pink);
            box-shadow: 0 0 12px var(--pink);
        }

        .hero-title {
            color: var(--text);
            font-size: clamp(1.9rem, 7.2vw, 4.2rem);
            line-height: 1.08;
            font-weight: 900;
            margin: 0;
            max-width: 880px;
        }

        .hero-title span {
            color: transparent;
            -webkit-text-stroke: 1px rgba(93, 242, 255, 0.62);
            text-shadow: 0 0 18px rgba(93, 242, 255, 0.22);
        }

        .hero-copy {
            color: var(--muted);
            font-size: clamp(0.95rem, 2.6vw, 1.08rem);
            line-height: 1.7;
            max-width: 760px;
            margin: 1.1rem 0 0;
        }

        .meta-strip {
            display: flex;
            flex-wrap: wrap;
            gap: 0.6rem;
            margin-top: 1.25rem;
        }

        .meta-chip {
            border: 1px solid rgba(93, 242, 255, 0.24);
            border-radius: 999px;
            color: var(--muted);
            background: rgba(4, 12, 24, 0.6);
            padding: 0.42rem 0.72rem;
            font-size: 0.84rem;
        }

        .meta-chip strong {
            color: var(--cyan);
            font-weight: 800;
        }

        .warning {
            margin-top: 1rem;
            border: 1px solid rgba(255, 209, 102, 0.34);
            border-radius: 8px;
            color: #ffe4a3;
            background: rgba(255, 209, 102, 0.08);
            padding: 0.78rem 0.9rem;
            font-size: 0.9rem;
        }

        .metric-grid {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 0.9rem;
            margin: 1rem 0 1.3rem;
        }

        .metric-card, .panel, .intent-card {
            border: 1px solid var(--line);
            border-radius: 8px;
            background: var(--panel);
            box-shadow: 0 0 24px rgba(93, 242, 255, 0.07);
        }

        .metric-card {
            position: relative;
            min-height: 120px;
            padding: 1rem;
            overflow: hidden;
            animation: rise 0.6s ease-out both;
        }

        .metric-card::before {
            content: "";
            position: absolute;
            left: 0;
            top: 0;
            width: 3px;
            height: 100%;
            background: linear-gradient(var(--cyan), var(--pink));
            box-shadow: 0 0 14px var(--cyan);
        }

        .metric-label {
            color: var(--muted);
            font-size: 0.8rem;
            font-weight: 700;
        }

        .metric-value {
            color: var(--text);
            font-size: clamp(1.7rem, 4vw, 2.5rem);
            line-height: 1.1;
            font-weight: 900;
            margin-top: 0.45rem;
        }

        .metric-note {
            color: var(--mint);
            font-size: 0.82rem;
            margin-top: 0.5rem;
        }

        .brief {
            border: 1px solid rgba(114, 246, 191, 0.28);
            border-radius: 8px;
            background:
                linear-gradient(90deg, rgba(114, 246, 191, 0.12), transparent),
                rgba(7, 18, 26, 0.72);
            color: #dffdf2;
            padding: 1rem 1.05rem;
            margin: 1rem 0 1.35rem;
            line-height: 1.7;
        }

        .brief strong {
            color: var(--mint);
        }

        .section-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 1rem;
            margin-top: 1rem;
        }

        .panel {
            padding: clamp(1rem, 3vw, 1.25rem);
            animation: rise 0.7s ease-out both;
        }

        .panel-title {
            display: flex;
            justify-content: space-between;
            align-items: baseline;
            gap: 0.8rem;
            color: var(--text);
            font-size: clamp(1.12rem, 3.5vw, 1.45rem);
            line-height: 1.25;
            font-weight: 900;
            margin-bottom: 1rem;
        }

        .panel-title small {
            color: var(--dim);
            font-size: 0.78rem;
            font-weight: 700;
            white-space: nowrap;
        }

        .bar-row {
            display: grid;
            grid-template-columns: minmax(92px, 150px) 1fr minmax(82px, auto);
            gap: 0.7rem;
            align-items: center;
            color: var(--muted);
            font-size: 0.94rem;
            margin: 0.72rem 0;
        }

        .bar-label {
            color: var(--text);
            overflow-wrap: anywhere;
        }

        .bar-track {
            height: 0.62rem;
            border-radius: 999px;
            background: rgba(157, 183, 205, 0.14);
            overflow: hidden;
        }

        .bar-fill {
            height: 100%;
            min-width: 0.55rem;
            border-radius: 999px;
            background: linear-gradient(90deg, var(--cyan), var(--mint));
            box-shadow: 0 0 14px rgba(93, 242, 255, 0.4);
            transform-origin: left center;
            animation: barIn 0.9s cubic-bezier(.2,.8,.2,1) both;
        }

        .bar-value {
            color: var(--muted);
            text-align: right;
            white-space: nowrap;
        }

        .intent-grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 0.9rem;
            margin: 0.9rem 0 1rem;
        }

        .intent-card {
            padding: 1rem;
        }

        .intent-card .metric-value {
            font-size: clamp(1.75rem, 5vw, 2.7rem);
        }

        .intent-line {
            height: 0.72rem;
            border-radius: 999px;
            background: rgba(157, 183, 205, 0.14);
            overflow: hidden;
            margin-top: 0.75rem;
        }

        .intent-line > div {
            height: 100%;
            border-radius: 999px;
            background: linear-gradient(90deg, var(--pink), var(--cyan), var(--mint));
            box-shadow: 0 0 18px rgba(93, 242, 255, 0.45);
            animation: barIn 0.95s ease-out both;
        }

        .download-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 0.85rem;
            margin-top: 0.8rem;
        }

        div.stDownloadButton > button,
        div.stButton > button {
            width: 100%;
            border-radius: 8px;
            border: 1px solid rgba(93, 242, 255, 0.4);
            background: rgba(8, 22, 38, 0.92);
            color: var(--text);
            min-height: 3rem;
            font-weight: 800;
            box-shadow: 0 0 16px rgba(93, 242, 255, 0.12);
        }

        div.stDownloadButton > button:hover,
        div.stButton > button:hover {
            border-color: var(--pink);
            color: var(--cyan);
            box-shadow: 0 0 22px rgba(255, 71, 196, 0.2);
        }

        .download-note {
            color: var(--dim);
            font-size: 0.86rem;
            line-height: 1.6;
            margin-top: 0.75rem;
        }

        .spacer {
            height: 1.2rem;
        }

        @keyframes scan {
            0% { transform: translateY(0); }
            100% { transform: translateY(24px); }
        }

        @keyframes sweep {
            0%, 58% { transform: translateX(-120%); }
            82%, 100% { transform: translateX(120%); }
        }

        @keyframes rise {
            from { opacity: 0; transform: translateY(14px); }
            to { opacity: 1; transform: translateY(0); }
        }

        @keyframes barIn {
            from { transform: scaleX(0); opacity: 0.45; }
            to { transform: scaleX(1); opacity: 1; }
        }

        @media (prefers-reduced-motion: reduce) {
            *, *::before, *::after {
                animation: none !important;
                transition: none !important;
            }
        }

        @media (max-width: 760px) {
            .main .block-container {
                padding-left: 0.9rem;
                padding-right: 0.9rem;
            }

            .metric-grid,
            .section-grid,
            .intent-grid,
            .download-grid {
                grid-template-columns: 1fr;
            }

            .metric-card {
                min-height: 104px;
            }

            .bar-row {
                grid-template-columns: 1fr;
                gap: 0.34rem;
                margin: 0.9rem 0;
            }

            .bar-value {
                text-align: left;
                font-size: 0.86rem;
            }

            .panel-title {
                display: block;
            }

            .panel-title small {
                display: block;
                margin-top: 0.25rem;
            }

            .meta-strip {
                display: grid;
                grid-template-columns: 1fr;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def metric_card(label: str, value: str, note: str) -> str:
    return f"""
    <article class="metric-card">
        <div class="metric-label">{escape(label)}</div>
        <div class="metric-value">{escape(value)}</div>
        <div class="metric-note">{escape(note)}</div>
    </article>
    """


def bar_rows(items: list[tuple[str, int]], total: int) -> str:
    if not items:
        return '<div class="download-note">아직 표시할 응답이 없습니다.</div>'
    max_value = max(value for _, value in items) or 1
    rows = []
    for label, value in items:
        width = max(5, round(value / max_value * 100))
        rows.append(
            f"""
            <div class="bar-row">
                <div class="bar-label">{escape(label)}</div>
                <div class="bar-track"><div class="bar-fill" style="width:{width}%"></div></div>
                <div class="bar-value">{value}명 · {pct(value, total)}</div>
            </div>
            """
        )
    return "\n".join(rows)


def panel(title: str, subtitle: str, items: list[tuple[str, int]], total: int) -> str:
    return f"""
    <section class="panel">
        <div class="panel-title">
            <span>{escape(title)}</span>
            <small>{escape(subtitle)}</small>
        </div>
        {bar_rows(items, total)}
    </section>
    """


def render_download_button(path: Path, label: str, file_name: str, mime: str) -> None:
    if path.exists():
        st.download_button(
            label,
            path.read_bytes(),
            file_name=file_name,
            mime=mime,
            use_container_width=True,
        )
    else:
        st.button(f"{label} 준비 중", disabled=True, use_container_width=True)


def render_downloads() -> None:
    st.markdown(
        """
        <section class="panel">
            <div class="panel-title">
                <span>공유 자료</span>
                <small>집계본만 제공</small>
            </div>
        """,
        unsafe_allow_html=True,
    )
    left, right = st.columns(2)
    with left:
        render_download_button(REPORT_PDF, "PDF 내려받기", "jeju-student-survey-report.pdf", "application/pdf")
    with right:
        render_download_button(REPORT_PNG, "PNG 내려받기", "jeju-student-survey-report.png", "image/png")
    st.markdown(
        '<div class="download-note">개별 응답과 원본 대화는 공개하지 않고, 집계 결과만 표시합니다.</div></section>',
        unsafe_allow_html=True,
    )


def render_survey_dashboard() -> None:
    survey = get_public_survey()
    data = survey["data"]
    total = data["n"]
    intent = dict(data["intent"])
    positive = intent.get("긍정", 0)
    neutral = intent.get("중립", 0)
    negative = intent.get("부정", 0)
    top_pain = data["pain"][0] if data["pain"] else ("응답 없음", 0)
    top_openchat = data["openchat_find"][0] if data["openchat_find"] else ("응답 없음", 0)
    positive_width = round(positive / total * 100) if total else 0

    warning = ""
    if survey.get("error"):
        warning = f'<div class="warning">{escape(survey["error"])}로 인해 저장된 CSV 기준 결과를 표시합니다.</div>'

    st.markdown(
        f"""
        <main class="cyber-shell">
            <section class="hero">
                <div class="kicker">Jeju Exchange Survey // Live Report</div>
                <h1 class="hero-title">교류학생 생활 플랫폼 <span>수요조사</span></h1>
                <p class="hero-copy">
                    이동, 동행 모집, 오픈채팅 이용 불편을 한 화면에서 확인합니다.
                    표본 수가 작은 중간 결과이므로 방향성 판단용으로 해석합니다.
                </p>
                <div class="meta-strip">
                    <div class="meta-chip">응답 <strong>{total}명</strong></div>
                    <div class="meta-chip">갱신 <strong>{escape(survey["loaded_at"])}</strong></div>
                    <div class="meta-chip">데이터 <strong>{escape(survey["source"])}</strong></div>
                </div>
                {warning}
            </section>

            <section class="metric-grid">
                {metric_card("응답 수", f"{total}명", "현재 집계 기준")}
                {metric_card("4주 이상 체류", f"{data['stay_4weeks']}명", pct(data["stay_4weeks"], total))}
                {metric_card("불편 1순위", top_pain[0], f"{top_pain[1]}명")}
                {metric_card("오픈채팅 1순위", top_openchat[0], f"{top_openchat[1]}명")}
            </section>

            <section class="brief">
                주요 신호는 <strong>{escape(top_openchat[0])}</strong> 탐색과
                <strong>{escape(top_pain[0])}</strong> 불편입니다.
                서비스 사용 의향은 긍정 {positive}명({pct(positive, total)})으로,
                실시간 동행/이동 모집을 먼저 검증할 근거가 됩니다.
            </section>

            <section class="section-grid">
                {panel("제주에서 불편했던 점", "복수 응답", data["pain"], total)}
                {panel("같이 하고 싶은 활동", "복수 응답", data["activity"], total)}
                {panel("오픈채팅에서 많이 찾는 것", "단일 응답", data["openchat_find"], total)}
                {panel("오픈채팅에서 불편한 점", "복수 응답", data["openchat_pain"], total)}
            </section>

            <section class="panel">
                <div class="panel-title">
                    <span>서비스 사용 의향</span>
                    <small>긍정 / 중립 / 부정</small>
                </div>
                <div class="intent-grid">
                    {metric_card("긍정", f"{positive}명", pct(positive, total))}
                    {metric_card("중립", f"{neutral}명", pct(neutral, total))}
                    {metric_card("부정", f"{negative}명", pct(negative, total))}
                </div>
                <div class="intent-line"><div style="width:{positive_width}%"></div></div>
                <div class="download-note">긍정 응답 {pct(positive, total)}</div>
            </section>
        </main>
        <div class="spacer"></div>
        """,
        unsafe_allow_html=True,
    )
    render_downloads()


def main() -> None:
    st.set_page_config(page_title="제주대 교류학생 생활 플랫폼", page_icon="AG", layout="wide")
    apply_page_style()
    render_survey_dashboard()


if __name__ == "__main__":
    main()
