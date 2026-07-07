from __future__ import annotations

from pathlib import Path
from typing import Any

import streamlit as st

from src.survey_dashboard import REPORT_PDF, REPORT_PNG, get_public_survey, pct

BASE_DIR = Path(__file__).resolve().parent


def apply_page_style() -> None:
    st.markdown(
        """
        <style>
        .main .block-container {
            max-width: 940px;
            padding-top: 3rem;
            padding-bottom: 4rem;
        }
        [data-testid="stHeader"] {
            background: rgba(255, 255, 255, 0);
        }
        .eyebrow {
            color: #25636a;
            font-size: 0.92rem;
            font-weight: 700;
            margin-bottom: 0.35rem;
        }
        .empty-state {
            color: #6b7280;
            background: #fafafa;
            border: 1px dashed #d1d5db;
            border-radius: 8px;
            padding: 1rem;
            margin-top: 1rem;
        }
        div.stButton > button {
            border-radius: 8px;
            border-color: #cbd5e1;
            min-height: 2.5rem;
        }
        div.stButton > button[kind="primary"] {
            background: #2f6f73;
            border-color: #2f6f73;
        }
        .survey-hero {
            border-bottom: 1px solid #d8e0e5;
            padding-bottom: 1.35rem;
            margin-bottom: 1.4rem;
        }
        .survey-meta {
            color: #64748b;
            font-size: 0.94rem;
            line-height: 1.55;
            margin-top: 0.2rem;
        }
        .insight-strip {
            border-left: 4px solid #2f6f73;
            background: #f6faf8;
            color: #24333a;
            padding: 0.9rem 1rem;
            border-radius: 8px;
            margin: 1rem 0 1.25rem;
        }
        .mini-label {
            color: #334155;
            font-weight: 700;
            margin: 0.35rem 0 0.25rem;
        }
        .bar-row {
            display: grid;
            grid-template-columns: minmax(108px, 170px) 1fr minmax(82px, auto);
            gap: 0.75rem;
            align-items: center;
            margin: 0.62rem 0;
            color: #334155;
            font-size: 0.93rem;
        }
        .bar-track {
            height: 0.62rem;
            background: #e8eef1;
            border-radius: 999px;
            overflow: hidden;
        }
        .bar-fill {
            height: 100%;
            background: #2f6f73;
            border-radius: 999px;
        }
        .download-note {
            color: #64748b;
            font-size: 0.9rem;
            margin-top: 0.2rem;
        }
        .source-warning {
            color: #92400e;
            background: #fffbeb;
            border: 1px solid #fde68a;
            border-radius: 8px;
            padding: 0.7rem 0.85rem;
            margin: 0.9rem 0 0;
            font-size: 0.9rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_bar_list(title: str, items: list[tuple[str, int]], total: int) -> None:
    st.markdown(f"#### {title}")
    if not items:
        st.markdown(
            '<div class="empty-state">아직 표시할 응답이 없습니다.</div>',
            unsafe_allow_html=True,
        )
        return
    max_value = max(value for _, value in items) or 1
    for label, value in items:
        width = max(4, round(value / max_value * 100))
        st.markdown(
            f"""
            <div class="bar-row">
                <div>{label}</div>
                <div class="bar-track"><div class="bar-fill" style="width:{width}%"></div></div>
                <div>{value}명 · {pct(value, total)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_intent(data: dict[str, Any]) -> None:
    total = data["n"]
    intent = dict(data["intent"])
    positive = intent.get("긍정", 0)
    neutral = intent.get("중립", 0)
    negative = intent.get("부정", 0)
    st.markdown("#### 서비스 사용 의향")
    cols = st.columns(3)
    cols[0].metric("긍정", f"{positive}명", pct(positive, total))
    cols[1].metric("중립", f"{neutral}명", pct(neutral, total))
    cols[2].metric("부정", f"{negative}명", pct(negative, total))
    st.progress(positive / total if total else 0, text=f"긍정 응답 {pct(positive, total)}")


def render_downloads() -> None:
    st.markdown("#### 공유 자료")
    cols = st.columns(2)
    if REPORT_PDF.exists():
        cols[0].download_button(
            "PDF 내려받기",
            REPORT_PDF.read_bytes(),
            file_name="jeju-student-survey-report.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
    else:
        cols[0].button("PDF 준비 중", disabled=True, use_container_width=True)
    if REPORT_PNG.exists():
        cols[1].download_button(
            "PNG 내려받기",
            REPORT_PNG.read_bytes(),
            file_name="jeju-student-survey-report.png",
            mime="image/png",
            use_container_width=True,
        )
    else:
        cols[1].button("PNG 준비 중", disabled=True, use_container_width=True)
    st.markdown(
        '<div class="download-note">개별 응답과 원본 대화는 공개하지 않고, 집계 결과만 표시합니다.</div>',
        unsafe_allow_html=True,
    )


def render_survey_dashboard() -> None:
    survey = get_public_survey()
    data = survey["data"]
    total = data["n"]
    positive = dict(data["intent"]).get("긍정", 0)
    top_pain = data["pain"][0] if data["pain"] else ("응답 없음", 0)
    top_openchat = data["openchat_find"][0] if data["openchat_find"] else ("응답 없음", 0)

    st.markdown('<div class="survey-hero">', unsafe_allow_html=True)
    st.markdown('<div class="eyebrow">JEJU NATIONAL UNIVERSITY EXCHANGE STUDENT SURVEY</div>', unsafe_allow_html=True)
    st.title("제주대학교 교류학생 생활 플랫폼 수요조사")
    st.markdown(
        f"""
        <div class="survey-meta">
        교류학생의 이동, 동행 모집, 오픈채팅 이용 불편을 확인하기 위한 공개 요약 페이지입니다.<br>
        응답 {total}명 · 마지막 갱신 {survey["loaded_at"]} · 데이터 소스 {survey["source"]}
        </div>
        """,
        unsafe_allow_html=True,
    )
    if survey.get("error"):
        st.markdown(
            f'<div class="source-warning">{survey["error"]}로 인해 저장된 CSV 기준 결과를 표시합니다.</div>',
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)

    metric_cols = st.columns(4)
    metric_cols[0].metric("응답 수", f"{total}명")
    metric_cols[1].metric("4주 이상 체류", f"{data['stay_4weeks']}명", pct(data["stay_4weeks"], total))
    metric_cols[2].metric("불편 1순위", top_pain[0], f"{top_pain[1]}명")
    metric_cols[3].metric("오픈채팅 1순위", top_openchat[0], f"{top_openchat[1]}명")

    st.markdown(
        f"""
        <div class="insight-strip">
        현재 응답에서는 <strong>{top_openchat[0]}</strong> 탐색과 <strong>{top_pain[0]}</strong> 문제가 가장 두드러집니다.
        서비스 사용 의향은 긍정 {positive}명({pct(positive, total)})으로, 실시간 동행/이동 모집을 우선 검증할 근거가 됩니다.
        </div>
        """,
        unsafe_allow_html=True,
    )

    left, right = st.columns(2)
    with left:
        render_bar_list("제주에서 불편했던 점", data["pain"], total)
        render_bar_list("오픈채팅에서 많이 찾는 것", data["openchat_find"], total)
    with right:
        render_bar_list("같이 하고 싶은 활동", data["activity"], total)
        render_bar_list("오픈채팅에서 불편한 점", data["openchat_pain"], total)

    render_intent(data)
    render_downloads()


def main() -> None:
    st.set_page_config(page_title="제주대 교류학생 생활 플랫폼", page_icon="AG", layout="wide")
    apply_page_style()
    render_survey_dashboard()


if __name__ == "__main__":
    main()
