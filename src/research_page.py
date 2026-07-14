from __future__ import annotations

from html import escape
from typing import Any

from src.survey_dashboard import pct


def _top(items: list[tuple[str, int]]) -> tuple[str, int]:
    return items[0] if items else ("-", 0)


def _count(items: list[tuple[str, int]], label: str) -> int:
    return dict(items).get(label, 0)


def build_research_view_model(
    korean_survey: dict[str, Any], foreign_survey: dict[str, Any]
) -> dict[str, object]:
    korean = korean_survey["data"]
    foreign = foreign_survey["data"]
    korean_total = int(korean["n"])
    foreign_total = int(foreign["n"])
    korean_positive = _count(korean["intent"], "긍정")
    foreign_positive = _count(foreign["intent"], "긍정")
    positive_total = korean_positive + foreign_positive
    total = korean_total + foreign_total
    dot_count = min(total, 60)
    responses_per_dot = max(1, (total + 59) // 60)

    return {
        "total": total,
        "korean_total": korean_total,
        "foreign_total": foreign_total,
        "korean_top_pain": _top(korean["pain"]),
        "foreign_top_pain": _top(foreign["pain"]),
        "korean_top_find": _top(korean["openchat_find"]),
        "foreign_top_find": _top(foreign["openchat_find"]),
        "korean_positive": korean_positive,
        "foreign_positive": foreign_positive,
        "positive_total": positive_total,
        "positive_pct": pct(positive_total, total),
        "loaded_at": str(korean_survey.get("loaded_at", "-")),
        "korean_pain": list(korean.get("pain", [])),
        "korean_find": list(korean.get("openchat_find", [])),
        "foreign_pain": list(foreign.get("pain", [])),
        "foreign_find": list(foreign.get("openchat_find", [])),
        "dot_count": dot_count,
        "responses_per_dot": responses_per_dot,
    }


def research_page_css() -> str:
    return """
<style>
* { box-sizing: border-box; }
body {
  margin: 0;
  color: #12213a;
  font-family: "Noto Sans KR", "Pretendard", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  background: transparent;
}
.research-page { width: 100%; }
.research-hero {
  padding: 44px 36px 34px;
  border: 1px solid #dbe3ec;
  border-radius: 8px;
  background: #ffffff;
  position: relative;
  overflow: hidden;
}
.research-hero::before {
  content: "";
  position: absolute;
  inset: 0 auto 0 0;
  width: 6px;
  background: #087f73;
}
.eyebrow {
  margin: 0 0 14px;
  color: #087f73;
  font-size: 12px;
  font-weight: 800;
}
.research-hero h1 {
  max-width: 760px;
  margin: 0;
  color: #10203a;
  font-size: 42px;
  line-height: 1.22;
  font-weight: 850;
}
.hero-copy {
  max-width: 690px;
  margin: 18px 0 0;
  color: #526176;
  font-size: 16px;
  line-height: 1.75;
}
.hero-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 18px;
  margin-top: 24px;
  color: #6b7789;
  font-size: 12px;
  font-weight: 700;
}
.metric-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
  margin-top: 14px;
}
.metric-card {
  min-height: 132px;
  padding: 20px;
  border: 1px solid #dbe3ec;
  border-radius: 8px;
  background: #ffffff;
}
.metric-card span {
  display: block;
  color: #65738a;
  font-size: 12px;
  font-weight: 800;
}
.metric-card strong {
  display: block;
  margin-top: 14px;
  color: #10203a;
  font-size: 27px;
  line-height: 1.18;
  font-weight: 850;
  overflow-wrap: anywhere;
}
.metric-card small {
  display: block;
  margin-top: 8px;
  color: #087f73;
  font-size: 12px;
  font-weight: 800;
}
.story-heading { margin: 54px 0 18px; }
.story-heading span {
  color: #087f73;
  font-size: 11px;
  font-weight: 850;
}
.story-heading h2 {
  margin: 7px 0 0;
  font-size: 29px;
  line-height: 1.35;
}
.problem-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  border-top: 1px solid #cad5e2;
  border-bottom: 1px solid #cad5e2;
}
.problem-panel { padding: 26px 28px 28px 0; }
.problem-panel + .problem-panel {
  padding-left: 28px;
  border-left: 1px solid #cad5e2;
}
.problem-index {
  color: #e76547;
  font-size: 12px;
  font-weight: 900;
}
.problem-panel h3 {
  margin: 10px 0 8px;
  font-size: 22px;
  line-height: 1.35;
}
.problem-panel p {
  margin: 0;
  color: #526176;
  font-size: 14px;
  line-height: 1.65;
}
.evidence-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 18px;
}
.evidence {
  padding: 7px 9px;
  border-radius: 4px;
  background: #edf7f5;
  color: #075f58;
  font-size: 12px;
  font-weight: 800;
}
.bridge-section { padding-top: 14px; }
.bridge-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}
.bridge-card {
  min-height: 240px;
  padding: 26px;
  border: 1px solid #d7e0e9;
  border-radius: 8px;
  background: #ffffff;
}
.bridge-card .number {
  color: #e76547;
  font-size: 12px;
  font-weight: 900;
}
.bridge-card h3 {
  margin: 16px 0 10px;
  font-size: 24px;
  line-height: 1.35;
}
.bridge-card p {
  margin: 0;
  color: #526176;
  font-size: 14px;
  line-height: 1.7;
}
.feature-list {
  display: flex;
  flex-wrap: wrap;
  gap: 7px;
  margin-top: 22px;
}
.feature-list span {
  padding: 7px 9px;
  border: 1px solid #d3dee8;
  border-radius: 4px;
  color: #34455d;
  font-size: 12px;
  font-weight: 750;
}
.bridge-note {
  margin: 14px 0 0;
  color: #7b8798;
  font-size: 11px;
  line-height: 1.6;
}
@media (max-width: 680px) {
  .research-hero { padding: 30px 22px 26px; }
  .research-hero h1 { font-size: 30px; }
  .hero-copy { font-size: 14px; }
  .metric-grid { grid-template-columns: 1fr 1fr; }
  .metric-card { min-height: 116px; padding: 16px; }
  .metric-card strong { font-size: 22px; }
  .story-heading { margin-top: 40px; }
  .story-heading h2 { font-size: 24px; }
  .problem-grid, .bridge-grid { grid-template-columns: 1fr; }
  .problem-panel { padding: 22px 0; }
  .problem-panel + .problem-panel {
    padding-left: 0;
    border-left: 0;
    border-top: 1px solid #cad5e2;
  }
  .bridge-card { min-height: 0; padding: 22px; }
}
</style>
"""


def _evidence(label: object, count: object, total: int) -> str:
    return (
        f'<span class="evidence">{escape(str(label))} '
        f'{int(count)}명 · {escape(pct(int(count), total))}</span>'
    )


def research_story_html(model: dict[str, object]) -> str:
    korean_pain, korean_pain_count = model["korean_top_pain"]
    foreign_pain, foreign_pain_count = model["foreign_top_pain"]
    korean_find, korean_find_count = model["korean_top_find"]
    foreign_find, foreign_find_count = model["foreign_top_find"]
    korean_total = int(model["korean_total"])
    foreign_total = int(model["foreign_total"])

    return f"""
{research_page_css()}
<main class="research-page">
  <header class="research-hero">
    <p class="eyebrow">JEJU EXCHANGE STUDENT RESEARCH</p>
    <h1>교류학생의 제주 생활,<br>무엇이 가장 불편했을까?</h1>
    <p class="hero-copy">한국인·외국인 교류학생의 이동, 동행 모집, 생활정보 탐색 경험을 조사했습니다. 실제 응답에서 반복된 문제를 서비스 기능과 연결해 살펴봅니다.</p>
    <div class="hero-meta">
      <span>한국인 {korean_total}명</span>
      <span>외국인 {foreign_total}명</span>
      <span>마지막 집계 {escape(str(model['loaded_at']))}</span>
    </div>
  </header>

  <section class="metric-grid" aria-label="핵심 조사 결과">
    <article class="metric-card"><span>전체 응답</span><strong>{int(model['total'])}명</strong><small>실시간 집계</small></article>
    <article class="metric-card"><span>한국인 핵심 불편</span><strong>{escape(str(korean_pain))}</strong><small>{int(korean_pain_count)}명 · {escape(pct(int(korean_pain_count), korean_total))}</small></article>
    <article class="metric-card"><span>외국인 핵심 불편</span><strong>{escape(str(foreign_pain))}</strong><small>{int(foreign_pain_count)}명 · {escape(pct(int(foreign_pain_count), foreign_total))}</small></article>
    <article class="metric-card"><span>서비스 긍정 의향</span><strong>{escape(str(model['positive_pct']))}</strong><small>{int(model['positive_total'])}명</small></article>
  </section>

  <section aria-labelledby="problem-title">
    <div class="story-heading"><span>WHAT WE FOUND</span><h2 id="problem-title">응답은 두 가지 문제로 모였습니다</h2></div>
    <div class="problem-grid">
      <article class="problem-panel">
        <span class="problem-index">01</span>
        <h3>이동과 동행 모집</h3>
        <p>택시비와 버스 이용의 부담뿐 아니라, 같은 시간과 목적지를 가진 사람을 빠르게 찾는 과정이 반복되는 문제로 나타났습니다.</p>
        <div class="evidence-row">{_evidence(korean_find, korean_find_count, korean_total)}{_evidence(korean_pain, korean_pain_count, korean_total)}</div>
      </article>
      <article class="problem-panel">
        <span class="problem-index">02</span>
        <h3>공지와 생활정보 탐색</h3>
        <p>외국인 학생에게는 교통 문제와 함께 공지·생활정보를 한곳에서 찾고, 그 정보가 믿을 만한지 확인하는 과정이 중요했습니다.</p>
        <div class="evidence-row">{_evidence(foreign_find, foreign_find_count, foreign_total)}{_evidence(foreign_pain, foreign_pain_count, foreign_total)}</div>
      </article>
    </div>
  </section>
</main>
"""


def product_bridge_html(model: dict[str, object]) -> str:
    return f"""
{research_page_css()}
<section class="bridge-section">
  <div class="story-heading"><span>FROM RESEARCH TO PRODUCT</span><h2>조사 결과를 실제 행동으로 연결했습니다</h2></div>
  <div class="bridge-grid">
    <article class="bridge-card">
      <span class="number">01 · MOVE TOGETHER</span>
      <h3>이동·동행 파티</h3>
      <p>오픈채팅에서 흘러가던 모집을 구조화해 파티를 찾고 만들고, 신청 이후의 상태까지 한 흐름에서 관리합니다.</p>
      <div class="feature-list"><span>조건별 탐색</span><span>파티 생성</span><span>신청·승인</span><span>참가자 채팅</span></div>
    </article>
    <article class="bridge-card">
      <span class="number">02 · TRUST THE ANSWER</span>
      <h3>근거 있는 AI 질문</h3>
      <p>공지와 생활정보를 자연어로 묻고, 커뮤니티 근거를 검색한 답변과 함께 출처·신뢰도를 확인합니다.</p>
      <div class="feature-list"><span>AI 질문</span><span>근거 검색</span><span>출처 표시</span><span>신뢰도 안내</span></div>
    </article>
  </div>
  <p class="bridge-note">위 연결은 조사 결과를 바탕으로 정한 제품 방향이며, 설문 자체가 기능 효과를 검증했다는 의미는 아닙니다.</p>
</section>
"""
