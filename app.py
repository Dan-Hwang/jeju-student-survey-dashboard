from __future__ import annotations

from pathlib import Path

import streamlit as st

from src.survey_dashboard import REPORT_PDF, REPORT_PNG, get_public_survey, pct


def apply_page_style() -> None:
    st.markdown(
        """
<style>
:root {
    --ara-bg: #f6f8fb;
    --ara-card: #ffffff;
    --ara-text: #172033;
    --ara-muted: #64748b;
    --ara-line: #dbe4ef;
    --ara-blue: #2563eb;
    --ara-teal: #0f766e;
    --ara-mint: #ccfbf1;
    --ara-yellow: #facc15;
}

html, body, [data-testid="stAppViewContainer"], .stApp {
    background: var(--ara-bg);
    color: var(--ara-text);
}

.main .block-container {
    max-width: 760px;
    padding: 1.1rem 1rem 4rem;
}

[data-testid="stHeader"], footer, #MainMenu {
    visibility: hidden;
    height: 0;
}

h1, h2, h3, p {
    letter-spacing: 0;
}

h1 {
    font-size: clamp(2rem, 9vw, 3.35rem) !important;
    line-height: 1.15 !important;
    margin-bottom: 0.65rem !important;
}

h2 {
    font-size: clamp(1.35rem, 6vw, 2rem) !important;
    margin-top: 1.4rem !important;
}

h3 {
    font-size: clamp(1.08rem, 4.5vw, 1.35rem) !important;
}

p, li, .stMarkdown, [data-testid="stCaptionContainer"] {
    color: var(--ara-text);
}

[data-testid="stCaptionContainer"] {
    color: var(--ara-muted) !important;
}

div[data-testid="stVerticalBlockBorderWrapper"] {
    border-color: var(--ara-line);
    border-radius: 18px;
    background: var(--ara-card);
    box-shadow: 0 12px 28px rgba(15, 23, 42, 0.05);
}

div[data-testid="stVerticalBlockBorderWrapper"]:has(h1) {
    border-color: #bfdbfe;
    background:
        linear-gradient(135deg, rgba(37, 99, 235, 0.08), rgba(20, 184, 166, 0.08)),
        #ffffff;
}

div[data-testid="stProgress"] {
    margin: 0.15rem 0 0.7rem;
}

div[data-testid="stProgress"] > div > div {
    background-color: #e7edf4;
}

div[data-testid="stProgress"] > div > div > div {
    background: linear-gradient(90deg, var(--ara-blue), var(--ara-teal));
}

.stButton > button,
div.stDownloadButton > button {
    width: 100%;
    min-height: 2.8rem;
    border-radius: 12px;
    border: 1px solid #cbd5e1;
    background: #ffffff;
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

.main .block-container > div {
    animation: araFadeUp 0.35s ease-out both;
}

@media (max-width: 640px) {
    .main .block-container {
        padding: 0.75rem 0.75rem 3.4rem;
    }

    div[data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 16px;
        box-shadow: 0 8px 20px rgba(15, 23, 42, 0.045);
    }
}
</style>
        """,
        unsafe_allow_html=True,
    )


def source_label(source: str) -> str:
    if source == "Google Sheets":
        return "Google Sheets"
    if source == "CSV fallback":
        return "저장 CSV"
    return "데이터 없음"


def get_count(items: list[tuple[str, int]], label: str, default: int = 0) -> int:
    return dict(items).get(label, default)


def render_header(survey: dict[str, object], total: int) -> None:
    with st.container(border=True):
        st.caption("JEJU EXCHANGE SURVEY")
        st.title("교류학생 생활 플랫폼 수요조사")
        st.write(
            "교류학생의 이동, 동행 모집, 오픈채팅 이용 불편을 한눈에 확인하기 위한 공개 요약 페이지입니다."
        )
        st.caption(
            f"응답 {total}명 · 마지막 갱신 {survey['loaded_at']} · 데이터 소스 {source_label(str(survey['source']))}"
        )
        if survey.get("error"):
            st.warning(f"{survey['error']}로 인해 저장된 CSV 기준 결과를 표시합니다.")
        elif survey.get("source") != "Google Sheets":
            st.warning("Google Sheets 연결 전까지 저장된 CSV 기준 결과를 표시합니다.")


def render_metric(label: str, value: str, note: str) -> None:
    with st.container(border=True):
        st.caption(label)
        st.markdown(f"## {value}")
        st.caption(note)


def render_summary(data: dict[str, object], total: int) -> None:
    pain = data["pain"]
    openchat_find = data["openchat_find"]
    intent = data["intent"]
    positive = get_count(intent, "긍정")
    top_pain = pain[0] if pain else ("-", 0)
    top_openchat = openchat_find[0] if openchat_find else ("-", 0)

    st.markdown("## 핵심 요약")
    render_metric("전체 응답", f"{total}명", "집계된 설문 응답 수")
    render_metric("4주 이상 체류", f"{data['stay_4weeks']}명", pct(int(data["stay_4weeks"]), total))
    render_metric("불편 1순위", str(top_pain[0]), f"{top_pain[1]}명")
    render_metric("오픈채팅 1순위", str(top_openchat[0]), f"{top_openchat[1]}명")

    with st.container(border=True):
        st.markdown("### 지금 가장 먼저 볼 점")
        if total:
            st.write(
                f"현재 응답에서는 **{top_openchat[0]} 탐색**과 **{top_pain[0]} 문제**가 가장 두드러집니다. "
                f"서비스 사용 의향은 긍정 {positive}명({pct(positive, total)})으로, 이동/동행 모집 기능을 먼저 검증할 근거가 됩니다."
            )
        else:
            st.write("아직 표시할 응답이 없습니다.")


def render_rank_section(title: str, subtitle: str, items: list[tuple[str, int]], total: int) -> None:
    st.markdown(f"## {title}")
    with st.container(border=True):
        st.caption(subtitle)
        if not items:
            st.info("아직 표시할 응답이 없습니다.")
            return

        max_value = max(value for _, value in items) or 1
        for label, value in items:
            st.markdown(f"**{label}**")
            st.progress(value / max_value)
            st.caption(f"{value}명 · {pct(value, total)}")


def render_intent_section(intent: list[tuple[str, int]], total: int) -> None:
    st.markdown("## 서비스 사용 의향")
    positive = get_count(intent, "긍정")
    with st.container(border=True):
        for label, value in intent:
            st.markdown(f"**{label}**")
            st.progress(value / total if total else 0)
            st.caption(f"{value}명 · {pct(value, total)}")

        st.divider()
        st.markdown(f"**긍정 응답 {pct(positive, total)}**")
        st.progress(positive / total if total else 0)


def render_download_button(path: Path, label: str, file_name: str, mime: str) -> None:
    if path.exists():
        st.download_button(
            label,
            data=path.read_bytes(),
            file_name=file_name,
            mime=mime,
            use_container_width=True,
        )
    else:
        st.button(f"{label} 준비 중", disabled=True, use_container_width=True)


def render_downloads() -> None:
    st.markdown("## 공유 자료")
    with st.container(border=True):
        st.write("개별 응답과 원본 대화는 공개하지 않고, 집계 결과만 표시합니다.")
        col_pdf, col_png = st.columns(2)
        with col_pdf:
            render_download_button(REPORT_PDF, "PDF 내려받기", "jeju-student-survey-report.pdf", "application/pdf")
        with col_png:
            render_download_button(REPORT_PNG, "PNG 내려받기", "jeju-student-survey-report.png", "image/png")


def render_survey_dashboard() -> None:
    st.set_page_config(
        page_title="제주대학교 교류학생 생활 플랫폼 수요조사",
        page_icon="📊",
        layout="centered",
    )
    apply_page_style()

    survey = get_public_survey()
    data = survey["data"]
    total = int(data["n"])

    render_header(survey, total)
    render_summary(data, total)
    render_rank_section("제주에서 불편했던 점", "복수 응답", data["pain"], total)
    render_rank_section("같이 하고 싶은 활동", "복수 응답", data["activity"], total)
    render_rank_section("오픈채팅에서 많이 찾는 것", "단일 응답", data["openchat_find"], total)
    render_rank_section("오픈채팅에서 불편한 점", "복수 응답", data["openchat_pain"], total)
    render_intent_section(data["intent"], total)
    render_downloads()


def main() -> None:
    render_survey_dashboard()


if __name__ == "__main__":
    main()
