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


def build_focus_view_model(model: dict[str, object], focus: str) -> dict[str, object]:
    if focus == "이동·동행":
        return {
            "focus": focus,
            "kicker": "PROBLEM 01",
            "title": "이동 비용보다 더 오래 걸린 것은 함께 갈 사람을 찾는 일이었습니다",
            "description": "한국인 교류학생 응답에서 확인한 이동과 모집 관련 상위 결과입니다.",
            "interpretation": "이동 자체뿐 아니라 같은 시간과 목적지의 동행을 찾는 과정이 반복됐습니다.",
            "tone": "movement",
            "total": int(model["korean_total"]),
            "pain_items": list(model["korean_pain"]),
            "find_items": list(model["korean_find"]),
            "product_asset": "meetings",
            "product_title": "이동·동행 파티",
            "product_description": "모임을 찾고 만들고 신청 상태를 관리합니다.",
            "problems": [],
        }

    if focus == "정보 탐색":
        return {
            "focus": focus,
            "kicker": "PROBLEM 02",
            "title": "정보를 찾은 뒤에도 믿어도 되는지 확인해야 했습니다",
            "description": "외국인 교류학생 응답에서 확인한 생활정보 탐색 관련 상위 결과입니다.",
            "interpretation": "정보의 위치뿐 아니라 최신성과 신뢰도를 다시 확인하는 과정이 필요했습니다.",
            "tone": "information",
            "total": int(model["foreign_total"]),
            "pain_items": list(model["foreign_pain"]),
            "find_items": list(model["foreign_find"]),
            "product_asset": "question",
            "product_title": "근거 있는 AI 질문",
            "product_description": "답변과 함께 출처와 신뢰도를 확인합니다.",
            "problems": [],
        }

    return {
        "focus": "전체 응답",
        "kicker": "WHAT WE FOUND",
        "title": "응답은 두 갈래의 불편으로 모였습니다",
        "description": "두 집단의 상위 응답을 제품 방향과 연결해 살펴봅니다.",
        "interpretation": "이동·동행 모집과 신뢰할 수 있는 생활정보 탐색이 함께 필요했습니다.",
        "tone": "overview",
        "total": int(model["total"]),
        "pain_items": [],
        "find_items": [],
        "product_asset": None,
        "product_title": "두 문제를 하나의 흐름으로",
        "product_description": "파티 모집과 근거 있는 정보 탐색을 함께 연결합니다.",
        "problems": [
            {
                "number": "01",
                "tone": "movement",
                "title": "이동과 동행 모집",
                "description": "같은 시간과 목적지의 사람을 빠르게 찾는 과정이 반복됐습니다.",
            },
            {
                "number": "02",
                "tone": "information",
                "title": "공지와 생활정보 탐색",
                "description": "흩어진 정보의 위치와 최신성, 신뢰도를 다시 확인해야 했습니다.",
            },
        ],
    }


def research_page_css() -> str:
    return """
<style>
* { box-sizing: border-box; }
:root {
  --story-navy: #10213d;
  --story-ink: #15233b;
  --story-muted: #65738a;
  --story-paper: #ffffff;
  --story-wash: #f2f6fa;
  --story-line: #d8e2ec;
  --story-coral: #f05d4e;
  --story-coral-soft: #fff0ec;
  --story-teal: #008f83;
  --story-teal-soft: #e6f7f4;
  --story-blue: #3d7cf4;
}
body {
  margin: 0;
  color: var(--story-ink);
  font-family: "Noto Sans KR", "Pretendard", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  background: transparent;
}
.research-page {
  display: grid;
  gap: 72px;
  width: 100%;
}
.story-hero {
  min-height: 560px;
  display: grid;
  grid-template-columns: minmax(0, 1.08fr) minmax(340px, .92fr);
  gap: 48px;
  align-items: center;
  padding: clamp(38px, 7vw, 76px);
  border-radius: 8px;
  background: var(--story-navy);
  position: relative;
  overflow: hidden;
}
.story-hero::after {
  content: "";
  position: absolute;
  right: -84px;
  bottom: -114px;
  width: 290px;
  height: 290px;
  border: 1px solid rgba(255,255,255,.13);
  border-radius: 50%;
  pointer-events: none;
}
.hero-copy-block {
  position: relative;
  z-index: 1;
}
.eyebrow {
  margin: 0 0 20px;
  color: #72e0d5;
  font-size: 11px;
  font-weight: 900;
}
.story-hero h1 {
  max-width: 650px;
  margin: 0;
  color: #ffffff;
  font-size: 64px;
  line-height: 1.12;
  font-weight: 900;
  word-break: keep-all;
}
.story-hero h1 em {
  color: #ff796b;
  font-style: normal;
}
.hero-copy {
  max-width: 590px;
  margin: 24px 0 0;
  color: #c8d5e8;
  font-size: 15px;
  line-height: 1.8;
  word-break: keep-all;
}
.hero-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 30px;
}
.hero-meta span {
  padding: 8px 10px;
  border: 1px solid rgba(255,255,255,.17);
  border-radius: 4px;
  color: #eef5ff;
  font-size: 12px;
  font-weight: 800;
}
.respondent-visual {
  position: relative;
  z-index: 1;
  min-width: 0;
  padding: 28px;
  border: 1px solid rgba(255,255,255,.17);
  border-radius: 8px;
  background: rgba(255,255,255,.07);
}
.respondent-dots {
  display: grid;
  grid-template-columns: repeat(8, minmax(20px, 1fr));
  gap: clamp(8px, 1.2vw, 12px);
  align-items: center;
  justify-items: center;
}
.respondent-dot {
  width: clamp(13px, 1.7vw, 19px);
  aspect-ratio: 1;
  border-radius: 50%;
  opacity: 0;
  transform: translateY(12px) scale(.65);
  animation: dotArrive .48s cubic-bezier(.2,.8,.2,1) forwards;
  animation-delay: calc(var(--dot-index) * 22ms + 120ms);
}
.respondent-dot.korean {
  background: var(--story-coral);
  box-shadow: 0 0 0 5px rgba(240,93,78,.11);
}
.respondent-dot.foreign {
  background: #39c9bd;
  box-shadow: 0 0 0 5px rgba(57,201,189,.11);
}
.dot-scale {
  margin: 24px 0 0;
  color: #aebed3;
  font-size: 12px;
  font-weight: 800;
  text-align: center;
}
@keyframes dotArrive {
  to { opacity: 1; transform: translateY(0) scale(1); }
}
.story-problems {
  padding: 0 clamp(4px, 3vw, 28px);
}
.section-kicker,
.scene-copy > span,
.bridge-kicker {
  margin: 0 0 10px;
  color: var(--story-teal);
  font-size: 11px;
  font-weight: 900;
}
.story-problems > h2 {
  max-width: 720px;
  margin: 0;
  color: var(--story-navy);
  font-size: 48px;
  line-height: 1.2;
  font-weight: 900;
  word-break: keep-all;
}
.problem-paths {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0;
  margin-top: 34px;
  border-top: 1px solid var(--story-line);
  border-bottom: 1px solid var(--story-line);
}
.problem-path {
  min-height: 260px;
  padding: 34px 38px 34px 0;
  position: relative;
}
.problem-path + .problem-path {
  padding-left: 38px;
  border-left: 1px solid var(--story-line);
}
.problem-path::after {
  content: "";
  position: absolute;
  left: 0;
  right: 38px;
  bottom: -2px;
  height: 4px;
  transform: scaleX(.18);
  transform-origin: left;
  transition: transform .45s ease;
}
.problem-path:hover::after { transform: scaleX(1); }
.problem-path.movement::after { background: var(--story-coral); }
.problem-path.information::after { background: var(--story-teal); }
.problem-path > span {
  color: var(--story-muted);
  font-size: 12px;
  font-weight: 900;
}
.problem-path h3 {
  margin: 34px 0 12px;
  color: var(--story-navy);
  font-size: 35px;
  line-height: 1.25;
}
.problem-path p {
  max-width: 410px;
  margin: 0;
  color: var(--story-muted);
  font-size: 14px;
  line-height: 1.75;
  word-break: keep-all;
}
.evidence-scene {
  display: grid;
  grid-template-columns: minmax(260px, .72fr) minmax(0, 1.28fr);
  gap: clamp(34px, 6vw, 82px);
  align-items: start;
  padding: clamp(46px, 7vw, 78px);
  border-radius: 8px;
  overflow: hidden;
}
.movement-scene { background: var(--story-coral-soft); }
.information-scene { background: var(--story-teal-soft); }
.movement-scene .scene-copy > span { color: var(--story-coral); }
.scene-copy {
  position: sticky;
  top: 30px;
}
.scene-copy h2 {
  margin: 0;
  color: var(--story-navy);
  font-size: 44px;
  line-height: 1.22;
  font-weight: 900;
  word-break: keep-all;
}
.scene-copy p {
  margin: 20px 0 0;
  color: #526176;
  font-size: 14px;
  line-height: 1.75;
  word-break: keep-all;
}
.scene-charts {
  display: grid;
  gap: 38px;
  min-width: 0;
}
.scene-charts article + article {
  padding-top: 32px;
  border-top: 1px solid rgba(16,33,61,.14);
}
.scene-charts h3 {
  margin: 0 0 20px;
  color: var(--story-navy);
  font-size: 17px;
  font-weight: 900;
}
.story-bar-list {
  display: grid;
  gap: 16px;
}
.story-bar-row {
  outline: none;
  transition: opacity .2s ease, transform .2s ease;
}
.story-bar-list:has(.story-bar-row:hover) .story-bar-row:not(:hover),
.story-bar-list:has(.story-bar-row:focus-visible) .story-bar-row:not(:focus-visible) {
  opacity: .42;
}
.story-bar-row:hover,
.story-bar-row:focus-visible {
  transform: translateX(4px);
}
.story-bar-row:focus-visible {
  box-shadow: 0 0 0 3px rgba(61,124,244,.32);
  border-radius: 4px;
}
.story-bar-head {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: baseline;
  margin-bottom: 8px;
}
.story-bar-head > span {
  min-width: 0;
  color: var(--story-ink);
  font-size: 14px;
  font-weight: 800;
  overflow-wrap: anywhere;
}
.story-bar-value {
  flex: 0 0 auto;
  color: #46566e;
  font-size: 12px;
  font-weight: 900;
}
.story-bar-track {
  height: 12px;
  border-radius: 3px;
  background: rgba(16,33,61,.09);
  overflow: hidden;
}
.story-bar-track span {
  display: block;
  width: var(--bar-width);
  height: 100%;
  border-radius: inherit;
  transform: scaleX(0);
  transform-origin: left;
  animation: barGrow .7s cubic-bezier(.2,.8,.2,1) forwards;
  animation-delay: calc(var(--bar-index) * 75ms + 180ms);
}
.story-bar-row.movement .story-bar-track span { background: var(--story-coral); }
.story-bar-row.information .story-bar-track span { background: var(--story-teal); }
@keyframes barGrow { to { transform: scaleX(1); } }
.empty-story {
  margin: 0;
  color: var(--story-muted);
  font-size: 12px;
  line-height: 1.6;
}
.bridge-section { padding: 10px 0 0; }
.story-heading { margin: 0 0 24px; }
.story-heading span {
  color: var(--story-teal);
  font-size: 11px;
  font-weight: 900;
}
.story-heading h2 {
  max-width: 760px;
  margin: 8px 0 0;
  color: var(--story-navy);
  font-size: 44px;
  line-height: 1.25;
  font-weight: 900;
}
.bridge-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0;
  border-top: 1px solid var(--story-line);
  border-bottom: 1px solid var(--story-line);
}
.bridge-card {
  min-height: 250px;
  padding: 34px 38px 36px 0;
  border: 0;
  border-radius: 0;
  background: transparent;
}
.bridge-card + .bridge-card {
  padding-left: 38px;
  border-left: 1px solid var(--story-line);
}
.bridge-card .number {
  color: var(--story-coral);
  font-size: 12px;
  font-weight: 900;
}
.bridge-card + .bridge-card .number { color: var(--story-teal); }
.bridge-card h3 {
  margin: 26px 0 10px;
  color: var(--story-navy);
  font-size: 28px;
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
  border: 1px solid var(--story-line);
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
@media (max-width: 900px) {
  .story-hero {
    min-height: 0;
    grid-template-columns: 1fr;
  }
  .respondent-visual {
    width: min(100%, 560px);
  }
  .evidence-scene {
    grid-template-columns: 1fr;
  }
  .scene-copy { position: static; }
  .story-hero h1 { font-size: 52px; }
  .story-problems > h2 { font-size: 40px; }
  .problem-path h3 { font-size: 31px; }
  .scene-copy h2,
  .story-heading h2 { font-size: 38px; }
}
@media (max-width: 680px) {
  .research-page { gap: 48px; }
  .story-hero {
    min-height: 0;
    grid-template-columns: 1fr;
    gap: 34px;
    padding: 34px 22px 30px;
  }
  .story-hero h1 { font-size: 38px; }
  .hero-copy { font-size: 14px; }
  .hero-meta { margin-top: 22px; }
  .respondent-visual { padding: 22px 16px; }
  .respondent-dots {
    grid-template-columns: repeat(8, minmax(16px, 1fr));
    gap: 9px 6px;
  }
  .respondent-dot { width: 13px; }
  .story-problems { padding: 0 4px; }
  .story-problems > h2 { font-size: 31px; }
  .problem-paths, .bridge-grid { grid-template-columns: 1fr; }
  .problem-path { min-height: 0; padding: 26px 0 30px; }
  .problem-path + .problem-path {
    padding-left: 0;
    border-left: 0;
    border-top: 1px solid var(--story-line);
  }
  .problem-path::after { right: 0; }
  .problem-path h3 { margin-top: 22px; }
  .evidence-scene {
    grid-template-columns: 1fr;
    gap: 34px;
    padding: 38px 20px 42px;
  }
  .scene-copy { position: static; }
  .scene-copy h2 { font-size: 31px; }
  .problem-path h3 { font-size: 28px; }
  .story-heading h2 { font-size: 31px; }
  .story-bar-head {
    display: grid;
    grid-template-columns: 1fr;
    gap: 4px;
  }
  .story-bar-value { white-space: normal; }
  .bridge-card { min-height: 0; padding: 28px 0 30px; }
  .bridge-card + .bridge-card {
    padding-left: 0;
    border-left: 0;
    border-top: 1px solid var(--story-line);
  }
}
@media (prefers-reduced-motion: reduce) {
  .respondent-dot,
  .story-bar-track span {
    animation: none !important;
    opacity: 1;
    transform: none;
  }
  .problem-path::after,
  .story-bar-row { transition: none; }
}
</style>
"""


def _respondent_dots_html(model: dict[str, object]) -> str:
    total = int(model["total"])
    if total <= 0:
        return '<p class="empty-story">아직 집계된 응답이 없습니다.</p>'

    dot_count = int(model["dot_count"])
    korean_total = int(model["korean_total"])
    korean_dots = round(dot_count * korean_total / total)
    dots = []
    for index in range(dot_count):
        group = "korean" if index < korean_dots else "foreign"
        dots.append(
            f'<span class="respondent-dot {group}" '
            f'style="--dot-index:{index}" aria-hidden="true"></span>'
        )

    scale = int(model["responses_per_dot"])
    scale_note = f"점 1개는 약 {scale}명의 응답" if scale > 1 else "점 1개는 응답 1명"
    foreign_total = int(model["foreign_total"])
    return (
        '<div class="respondent-visual" role="img" '
        f'aria-label="전체 {total}명, 한국인 {korean_total}명, 외국인 {foreign_total}명">'
        f'<div class="respondent-dots">{"".join(dots)}</div>'
        f'<p class="dot-scale">{scale_note}</p></div>'
    )


def _story_bars_html(items: list[tuple[str, int]], total: int, tone: str) -> str:
    rows = []
    for index, (label, count) in enumerate(items[:5]):
        width = count / total * 100 if total else 0
        rows.append(
            f'<div class="story-bar-row {escape(tone)}" tabindex="0" '
            f'style="--bar-index:{index}">'
            f'<div class="story-bar-head"><span>{escape(str(label))}</span>'
            f'<strong class="story-bar-value">{int(count)}명 · '
            f'{escape(pct(int(count), total))}</strong></div>'
            f'<div class="story-bar-track"><span style="--bar-width:{width:.1f}%"></span>'
            f'</div></div>'
        )
    if not rows:
        return '<p class="empty-story">아직 집계된 응답이 없습니다.</p>'
    return f'<div class="story-bar-list">{"".join(rows)}</div>'


def _evidence(label: object, count: object, total: int) -> str:
    return (
        f'<span class="evidence">{escape(str(label))} '
        f'{int(count)}명 · {escape(pct(int(count), total))}</span>'
    )


def research_story_html(model: dict[str, object]) -> str:
    total = int(model["total"])
    korean_total = int(model["korean_total"])
    foreign_total = int(model["foreign_total"])

    return f"""
{research_page_css()}
<main class="research-page">
  <header class="story-hero">
    <div class="hero-copy-block">
      <p class="eyebrow">JEJU EXCHANGE STUDENT RESEARCH</p>
      <h1><em>{total}명</em>의 응답이<br>두 가지 문제를 가리켰습니다</h1>
      <p class="hero-copy">한국인과 외국인 교류학생이 제주에서 이동하고, 사람을 만나고, 생활정보를 찾으며 겪은 경험을 조사했습니다.</p>
      <div class="hero-meta">
        <span>한국인 {korean_total}명</span>
        <span>외국인 {foreign_total}명</span>
        <span>마지막 집계 {escape(str(model['loaded_at']))}</span>
      </div>
    </div>
    {_respondent_dots_html(model)}
  </header>

  <section class="story-problems" aria-labelledby="problem-title">
    <p class="section-kicker">WHAT WE FOUND</p>
    <h2 id="problem-title">응답은 두 갈래의 불편으로 모였습니다</h2>
    <div class="problem-paths">
      <article class="problem-path movement">
        <span>01</span>
        <h3>이동과 동행 모집</h3>
        <p>택시비와 버스 이용의 부담을 넘어, 같은 시간과 목적지의 사람을 빠르게 찾는 과정이 반복됐습니다.</p>
      </article>
      <article class="problem-path information">
        <span>02</span>
        <h3>공지와 생활정보 탐색</h3>
        <p>흩어진 생활정보를 한곳에서 찾고, 그 정보가 최신인지 믿을 만한지 다시 확인해야 했습니다.</p>
      </article>
    </div>
  </section>

  <section class="evidence-scene movement-scene" aria-labelledby="movement-title">
    <div class="scene-copy">
      <span>PROBLEM 01</span>
      <h2 id="movement-title">이동 비용보다 더 오래 걸린 것은<br>함께 갈 사람을 찾는 일이었습니다</h2>
      <p>한국인 교류학생 응답에서 확인한 이동과 모집 관련 상위 결과입니다.</p>
    </div>
    <div class="scene-charts">
      <article>
        <h3>제주에서 불편했던 점</h3>
        {_story_bars_html(list(model['korean_pain']), korean_total, 'movement')}
      </article>
      <article>
        <h3>오픈채팅에서 찾은 것</h3>
        {_story_bars_html(list(model['korean_find']), korean_total, 'movement')}
      </article>
    </div>
  </section>

  <section class="evidence-scene information-scene" aria-labelledby="information-title">
    <div class="scene-copy">
      <span>PROBLEM 02</span>
      <h2 id="information-title">정보를 찾은 뒤에도<br>믿어도 되는지 확인해야 했습니다</h2>
      <p>외국인 교류학생 응답에서 확인한 생활정보 탐색 관련 상위 결과입니다.</p>
    </div>
    <div class="scene-charts">
      <article>
        <h3>제주에서 불편했던 점</h3>
        {_story_bars_html(list(model['foreign_pain']), foreign_total, 'information')}
      </article>
      <article>
        <h3>오픈채팅에서 찾은 것</h3>
        {_story_bars_html(list(model['foreign_find']), foreign_total, 'information')}
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
