# Survey Research Brief Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild the survey dashboard as a responsive research brief that explains the evidence first, connects it once to two SynapSpot features, and preserves live Sheets data, detailed views, comments, and PDF export.

**Architecture:** Keep `src/survey_dashboard.py` as the only survey loading and aggregation layer. Add a pure `src/research_brief.py` presentation model and HTML generator so counts, group denominators, source state, and fallback behavior can be unit-tested without Streamlit. Let `app.py` orchestrate Streamlit widgets, reuse the existing detailed views and PDF generator, and inject one static CSS file for the approved Jeju research editorial system.

**Tech Stack:** Python 3, Streamlit 1.x, ReportLab 4.x, pypdf, standard-library `dataclasses`, `html`, `base64`, and `unittest`.

## Global Constraints

- Work in `C:\Users\Aiffel\Desktop\workspace\team-projects\ara-guide\.worktrees\survey-dashboard-reset` on `codex/survey-dashboard-reset`.
- Do not modify `C:\Users\Aiffel\Desktop\workspace\team-projects\synapspot`; it is a read-only product reference.
- Keep Google Sheets and CSV fallback parsing in `src/survey_dashboard.py`.
- Use the fixed palette `#13233D`, `#087F72`, `#EC6A5F`, `#FBFCFD`, `#D8E2E9`, `#66768A`, and `#132E50`.
- Keep card and panel radii at 8px or less.
- Do not use viewport-width font sizing, gradients, decorative respondent icons, maps, scenario selector buttons, or hover movement.
- Calculate Korean percentages with the Korean response count and foreign percentages with the foreign response count.
- Show both response count and within-group percentage on ranking charts.
- Show the SynapSpot product bridge once, after the research findings and comparison.
- Keep anonymous comments to five per page.
- Keep the default detailed view as `전체 요약`.
- Treat the dashboard as live only when both survey sources equal `Google Sheets`.
- Preserve unrelated untracked files and never commit service-account credentials.

---

## File Map

- Create `src/research_brief.py`: immutable brief context, group-safe percentages, source state, HTML generators, and image data URI helper.
- Create `assets/research-brief.css`: approved visual tokens, responsive layout, accessible chart styles, and reduced-motion behavior.
- Restore `assets/synapspot-meetings-preview.png`: actual available Meetings screen snapshot from the earlier product-preview commit.
- Restore `assets/synapspot-question-preview.png`: actual available Question screen snapshot from the earlier product-preview commit.
- Modify `app.py`: inject CSS, render the research brief and product bridge, retain detailed views and downloads, and align PDF colors/copy.
- Create `tests/test_research_brief.py`: presentation model, source status, percentages, empty state, HTML, and image fallback tests.
- Create `tests/test_pdf_export.py`: current response totals, three-page PDF structure, and source labels.
- Modify `tests/test_app_copy.py`: research identity, section order, removed presentation controls, and retained detailed workflow assertions.

---

### Task 1: Add the Group-Safe Research Brief Context

**Files:**
- Create: `src/research_brief.py`
- Create: `tests/test_research_brief.py`

**Interfaces:**
- Consumes: survey dictionaries returned by `get_public_survey()` and `get_foreign_survey()`.
- Produces: `build_brief_context(korean_survey, foreign_survey) -> BriefContext`.
- Produces: `ranked_metrics(items, total, limit=3) -> tuple[RankedMetric, ...]`.

- [ ] **Step 1: Write failing tests for totals, live status, and group denominators**

```python
import unittest

from src.research_brief import build_brief_context, ranked_metrics


def survey(total: int, *, source: str, loaded_at: str, pain=None, openchat_find=None, openchat_pain=None):
    return {
        "data": {
            "n": total,
            "pain": pain or [],
            "activity": [],
            "openchat_find": openchat_find or [],
            "openchat_pain": openchat_pain or [],
            "intent": [("긍정", 0), ("중립", 0), ("부정", 0)],
            "comments": [],
        },
        "source": source,
        "loaded_at": loaded_at,
        "error": "",
    }


class ResearchBriefContextTest(unittest.TestCase):
    def test_combines_totals_and_marks_both_sheets_live(self):
        korean = survey(23, source="Google Sheets", loaded_at="2026-07-15 15:00")
        foreign = survey(16, source="Google Sheets", loaded_at="2026-07-15 15:01")

        context = build_brief_context(korean, foreign)

        self.assertEqual(context.total, 39)
        self.assertEqual(context.korean.total, 23)
        self.assertEqual(context.foreign.total, 16)
        self.assertEqual(context.status, "Google Sheets 실시간 집계")
        self.assertTrue(context.is_live)
        self.assertEqual(context.loaded_at, "2026-07-15 15:01")

    def test_uses_each_group_total_for_percentages(self):
        korean = ranked_metrics([("버스 노선", 11)], 23)
        foreign = ranked_metrics([("교통", 11)], 16)

        self.assertEqual(korean[0].percent, "47.8%")
        self.assertEqual(foreign[0].percent, "68.8%")

    def test_any_fallback_source_disables_live_status(self):
        korean = survey(11, source="CSV fallback", loaded_at="2026-07-15 14:00")
        foreign = survey(16, source="Google Sheets", loaded_at="2026-07-15 15:00")

        context = build_brief_context(korean, foreign)

        self.assertFalse(context.is_live)
        self.assertEqual(context.status, "저장 데이터 포함 집계")

    def test_zero_total_returns_zero_percent(self):
        metrics = ranked_metrics([("교통", 0)], 0)
        self.assertEqual(metrics[0].percent, "0%")
```

- [ ] **Step 2: Run the new test and verify the expected import failure**

Run:

```powershell
& '..\..\.venv\Scripts\python.exe' -m unittest tests.test_research_brief -v
```

Expected: `ModuleNotFoundError: No module named 'src.research_brief'`.

- [ ] **Step 3: Implement immutable context types and calculations**

Create `src/research_brief.py` with:

```python
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable


@dataclass(frozen=True)
class RankedMetric:
    label: str
    count: int
    percent: str


@dataclass(frozen=True)
class GroupBrief:
    label: str
    total: int
    pain: tuple[RankedMetric, ...]
    openchat_find: tuple[RankedMetric, ...]
    openchat_pain: tuple[RankedMetric, ...]


@dataclass(frozen=True)
class BriefContext:
    total: int
    korean: GroupBrief
    foreign: GroupBrief
    status: str
    source_detail: str
    loaded_at: str
    is_live: bool
    has_data: bool


SOURCE_NAMES = {
    "Google Sheets": "Google Sheets",
    "CSV fallback": "저장 CSV",
    "CSV": "저장 CSV",
    "CSV summary": "저장 집계",
    "empty": "데이터 없음",
}


def percent_text(value: int, total: int) -> str:
    if total <= 0:
        return "0%"
    return f"{value / total * 100:.1f}%"


def ranked_metrics(
    items: Iterable[tuple[str, int]], total: int, limit: int | None = 3
) -> tuple[RankedMetric, ...]:
    selected = list(items)
    if limit is not None:
        selected = selected[:limit]
    return tuple(
        RankedMetric(str(label), int(count), percent_text(int(count), total))
        for label, count in selected
    )


def _group(label: str, survey: dict[str, Any]) -> GroupBrief:
    data = survey["data"]
    total = int(data.get("n", 0))
    return GroupBrief(
        label=label,
        total=total,
        pain=ranked_metrics(data.get("pain", []), total),
        openchat_find=ranked_metrics(data.get("openchat_find", []), total),
        openchat_pain=ranked_metrics(data.get("openchat_pain", []), total),
    )


def build_brief_context(
    korean_survey: dict[str, Any], foreign_survey: dict[str, Any]
) -> BriefContext:
    korean = _group("한국인", korean_survey)
    foreign = _group("외국인", foreign_survey)
    korean_source = str(korean_survey.get("source", "empty"))
    foreign_source = str(foreign_survey.get("source", "empty"))
    is_live = korean_source == "Google Sheets" and foreign_source == "Google Sheets"
    loaded_at = max(
        str(korean_survey.get("loaded_at", "-")),
        str(foreign_survey.get("loaded_at", "-")),
    )
    return BriefContext(
        total=korean.total + foreign.total,
        korean=korean,
        foreign=foreign,
        status="Google Sheets 실시간 집계" if is_live else "저장 데이터 포함 집계",
        source_detail=(
            f"한국인 {SOURCE_NAMES.get(korean_source, korean_source)} · "
            f"외국인 {SOURCE_NAMES.get(foreign_source, foreign_source)}"
        ),
        loaded_at=loaded_at,
        is_live=is_live,
        has_data=(korean.total + foreign.total) > 0,
    )
```

- [ ] **Step 4: Run the context tests**

Run:

```powershell
& '..\..\.venv\Scripts\python.exe' -m unittest tests.test_research_brief -v
```

Expected: four tests pass.

- [ ] **Step 5: Commit the context model**

```powershell
git add src/research_brief.py tests/test_research_brief.py
git commit -m "feat: add survey research brief context"
```

---

### Task 2: Add the Research Brief HTML and Visual System

**Files:**
- Create: `assets/research-brief.css`
- Modify: `src/research_brief.py`
- Modify: `tests/test_research_brief.py`

**Interfaces:**
- Consumes: `BriefContext` from Task 1.
- Produces: `intro_html(context) -> str`.
- Produces: `findings_html(context) -> str`.
- Produces: `comparison_html(context) -> str`.
- Produces: CSS classes prefixed with `research-`.

- [ ] **Step 1: Add failing HTML tests using non-production counts**

Append to `tests/test_research_brief.py`:

```python
from src.research_brief import comparison_html, findings_html, intro_html


class ResearchBriefHtmlTest(unittest.TestCase):
    def setUp(self):
        self.korean = survey(
            4,
            source="Google Sheets",
            loaded_at="2026-07-15 15:00",
            pain=[("버스 노선", 3)],
            openchat_find=[("택시팟", 2)],
            openchat_pain=[("원하는 글 찾기 어렵다", 2)],
        )
        self.foreign = survey(
            3,
            source="Google Sheets",
            loaded_at="2026-07-15 15:01",
            pain=[("교통", 2)],
            openchat_find=[("공지", 2)],
            openchat_pain=[("글이 너무 많다", 1)],
        )
        self.context = build_brief_context(self.korean, self.foreign)

    def test_intro_uses_context_instead_of_hardcoded_production_count(self):
        markup = intro_html(self.context)
        self.assertIn("7명", markup)
        self.assertIn("4명", markup)
        self.assertIn("3명", markup)
        self.assertNotIn("39명", markup)
        self.assertIn('class="research-hero"', markup)

    def test_findings_show_counts_and_group_percentages(self):
        markup = findings_html(self.context)
        self.assertIn("버스 노선", markup)
        self.assertIn("3명", markup)
        self.assertIn("75.0%", markup)
        self.assertIn("교통", markup)
        self.assertIn("66.7%", markup)

    def test_comparison_names_both_groups_and_denominators(self):
        markup = comparison_html(self.context)
        self.assertIn("한국인 · n=4", markup)
        self.assertIn("외국인 · n=3", markup)
```

- [ ] **Step 2: Run the HTML tests and verify missing-function failures**

Run:

```powershell
& '..\..\.venv\Scripts\python.exe' -m unittest tests.test_research_brief.ResearchBriefHtmlTest -v
```

Expected: import failure for `intro_html`, `findings_html`, and `comparison_html`.

- [ ] **Step 3: Implement escaped markup helpers**

Add to `src/research_brief.py`:

```python
from html import escape


def _metric_rows(metrics: tuple[RankedMetric, ...], accent: str) -> str:
    if not metrics:
        return '<p class="research-empty">아직 표시할 응답이 없습니다.</p>'
    rows = []
    for metric in metrics:
        width = min(100.0, float(metric.percent.rstrip("%") or 0))
        rows.append(
            f'''<div class="research-bar-row">
  <span class="research-bar-label">{escape(metric.label)}</span>
  <span class="research-bar-track"><span class="research-bar-fill {accent}" style="width:{width:.1f}%"></span></span>
  <strong>{metric.count}명 <small>{metric.percent}</small></strong>
</div>'''
        )
    return "\n".join(rows)


def intro_html(context: BriefContext) -> str:
    conclusion = (
        '<div class="research-conclusion">이동·동행 모집과 신뢰할 수 있는 '
        "생활정보 탐색이 함께 필요했습니다.</div>"
        if context.has_data
        else '<div class="research-conclusion is-empty">응답을 수집하고 있습니다.</div>'
    )
    return f'''<section class="research-hero">
  <p class="research-kicker">JEJU EXCHANGE STUDENT RESEARCH</p>
  <h1>교류학생의 이동과 정보 탐색은 어디서 막혔을까?</h1>
  <p class="research-lead">학생의 실제 경험을 조사하고, 시냅스팟의 문제 정의로 이어진 근거를 정리했습니다.</p>
  <div class="research-status-grid">
    <div><span>전체 응답</span><strong>{context.total}명</strong></div>
    <div><span>한국인</span><strong>{context.korean.total}명</strong></div>
    <div><span>외국인</span><strong>{context.foreign.total}명</strong></div>
    <div><span>데이터 상태</span><strong class="is-status">{escape(context.status)}</strong></div>
  </div>
  <p class="research-source">{escape(context.source_detail)} · 마지막 갱신 {escape(context.loaded_at)}</p>
</section>
<section class="research-section"> <h2>먼저 볼 결론</h2>{conclusion}</section>'''


def findings_html(context: BriefContext) -> str:
    return f'''<section class="research-section">
  <div class="research-heading"><h2>응답이 가리킨 두 가지 문제</h2><span>복수 응답 · 집단 내 비율</span></div>
  <div class="research-two-column">
    <article class="research-signal korean"><p>PROBLEM 01 · 한국인 이동 경험</p><h3>이동과 동행 모집</h3>{_metric_rows(context.korean.pain, "korean")}{_metric_rows(context.korean.openchat_find, "korean")}</article>
    <article class="research-signal foreign"><p>PROBLEM 02 · 외국인 정보 경험</p><h3>공지와 생활정보 탐색</h3>{_metric_rows(context.foreign.pain, "foreign")}{_metric_rows(context.foreign.openchat_find, "foreign")}</article>
  </div>
</section>'''


def comparison_html(context: BriefContext) -> str:
    korean_top = context.korean.openchat_find[0].label if context.korean.openchat_find else "응답 수집 중"
    foreign_top = context.foreign.openchat_find[0].label if context.foreign.openchat_find else "응답 수집 중"
    return f'''<section class="research-section">
  <div class="research-heading"><h2>한국인과 외국인의 경험은 어떻게 달랐나</h2><span>집단별 분모를 따로 계산</span></div>
  <div class="research-compare">
    <div><span>한국인 · n={context.korean.total}</span><strong>{escape(korean_top)}</strong></div>
    <div><span>외국인 · n={context.foreign.total}</span><strong>{escape(foreign_top)}</strong></div>
  </div>
  <p class="research-interpretation">두 집단 모두 사람과 정보를 제때 찾기 어렵다는 공통 문제를 보였습니다.</p>
</section>'''
```

- [ ] **Step 4: Add the approved CSS tokens and responsive behavior**

Create `assets/research-brief.css`:

```css
:root {
  --research-navy: #13233d;
  --research-teal: #087f72;
  --research-coral: #ec6a5f;
  --research-bg: #fbfcfd;
  --research-line: #d8e2e9;
  --research-muted: #66768a;
  --research-bridge: #132e50;
}
.research-hero, .research-section { max-width: 960px; margin: 0 auto; }
.research-hero { padding: 28px 0 24px; border-bottom: 1px solid var(--research-line); }
.research-kicker { margin: 0; color: var(--research-teal); font-size: 12px; font-weight: 800; }
.research-hero h1 { max-width: 760px; margin: 10px 0 0; color: var(--research-navy); font-size: 40px; line-height: 1.2; }
.research-lead, .research-source { color: var(--research-muted); }
.research-lead { max-width: 700px; margin: 10px 0 0; }
.research-status-grid { display: grid; grid-template-columns: 1.4fr 1fr 1fr 1.2fr; margin-top: 22px; border: 1px solid var(--research-line); border-radius: 8px; background: white; }
.research-status-grid > div { padding: 14px 16px; border-right: 1px solid var(--research-line); }
.research-status-grid > div:last-child { border-right: 0; }
.research-status-grid span { display: block; color: var(--research-muted); font-size: 12px; }
.research-status-grid strong { display: block; margin-top: 4px; color: var(--research-navy); font-size: 24px; }
.research-status-grid .is-status { color: var(--research-teal); font-size: 14px; }
.research-source { margin: 9px 0 0; font-size: 12px; }
.research-section { padding: 34px 0; border-bottom: 1px solid var(--research-line); }
.research-section h2 { margin: 0; color: var(--research-navy); font-size: 28px; }
.research-conclusion { margin-top: 16px; padding: 18px 20px; border-left: 4px solid var(--research-coral); background: #fff4f1; color: var(--research-navy); font-size: 18px; font-weight: 700; }
.research-heading { display: flex; align-items: end; justify-content: space-between; gap: 16px; }
.research-heading > span { color: var(--research-muted); font-size: 12px; }
.research-two-column { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 28px; margin-top: 20px; }
.research-signal { padding-top: 14px; border-top: 3px solid var(--research-coral); }
.research-signal.foreign { border-top-color: var(--research-teal); }
.research-signal > p { color: var(--research-muted); font-size: 11px; font-weight: 800; }
.research-signal h3 { color: var(--research-navy); font-size: 20px; }
.research-bar-row { display: grid; grid-template-columns: minmax(100px, .8fr) 1.2fr 92px; gap: 10px; align-items: center; margin: 11px 0; }
.research-bar-track { overflow: hidden; height: 10px; border-radius: 3px; background: #e6edf1; }
.research-bar-fill { display: block; height: 100%; background: var(--research-coral); }
.research-bar-fill.foreign { background: var(--research-teal); }
.research-bar-row strong { text-align: right; font-size: 13px; }
.research-bar-row small { color: var(--research-muted); font-weight: 500; }
.research-compare { display: grid; grid-template-columns: repeat(2, 1fr); gap: 14px; margin-top: 18px; }
.research-compare > div { padding: 16px; border: 1px solid var(--research-line); border-radius: 8px; background: white; }
.research-compare span { color: var(--research-muted); font-size: 12px; }
.research-compare strong { display: block; margin-top: 5px; font-size: 20px; }
.research-interpretation { margin: 14px 0 0; color: var(--research-muted); }
@media (max-width: 640px) {
  .research-hero { padding-top: 16px; }
  .research-hero h1 { font-size: 32px; }
  .research-status-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .research-status-grid > div { border-bottom: 1px solid var(--research-line); }
  .research-status-grid > div:nth-child(2) { border-right: 0; }
  .research-status-grid > div:nth-child(n+3) { border-bottom: 0; }
  .research-section { padding: 26px 0; }
  .research-section h2 { font-size: 23px; }
  .research-two-column, .research-compare { grid-template-columns: 1fr; }
  .research-heading { align-items: start; flex-direction: column; }
  .research-bar-row { grid-template-columns: 82px 1fr 78px; }
}
@media (prefers-reduced-motion: no-preference) {
  .research-bar-fill { animation: research-fill .45s ease-out both; transform-origin: left; }
  @keyframes research-fill { from { transform: scaleX(0); } to { transform: scaleX(1); } }
}
```

- [ ] **Step 5: Run HTML tests and static checks**

Run:

```powershell
& '..\..\.venv\Scripts\python.exe' -m unittest tests.test_research_brief -v
& '..\..\.venv\Scripts\python.exe' -m py_compile src\research_brief.py
```

Expected: all research brief tests pass and compilation exits 0.

- [ ] **Step 6: Commit the HTML and CSS layer**

```powershell
git add assets/research-brief.css src/research_brief.py tests/test_research_brief.py
git commit -m "feat: add research brief visual system"
```

---

### Task 3: Integrate the Evidence-First Page Flow

**Files:**
- Modify: `app.py`
- Modify: `tests/test_app_copy.py`

**Interfaces:**
- Consumes: `build_brief_context`, `intro_html`, `findings_html`, and `comparison_html`.
- Produces: Streamlit order `intro → refresh → findings → comparison → product bridge → detailed views → downloads`.

- [ ] **Step 1: Replace copy-only assertions with section-order assertions**

Update `tests/test_app_copy.py`:

```python
    def test_research_brief_has_approved_identity_and_order(self) -> None:
        expected_calls = [
            "intro_html(context)",
            "findings_html(context)",
            "comparison_html(context)",
            "render_product_bridge(context)",
            'st.markdown("## 상세 조사 결과")',
        ]
        positions = [self.app_text.index(call) for call in expected_calls]
        self.assertEqual(positions, sorted(positions))
        self.assertIn("교류학생의 이동과 정보 탐색", self.app_text)

    def test_presentation_gimmicks_are_not_present(self) -> None:
        hidden_terms = [
            "발표 주제 선택",
            "점 1개는 응답 1명",
            "어떤 문제부터 살펴볼까요",
            "WHAT WE FOUND",
            "hover-card",
        ]
        for term in hidden_terms:
            self.assertNotIn(term, self.app_text)
```

- [ ] **Step 2: Run the app-copy tests and verify missing imports/calls**

Run:

```powershell
& '..\..\.venv\Scripts\python.exe' -m unittest tests.test_app_copy -v
```

Expected: the approved section-order test fails because the new functions are not wired into `app.py`.

- [ ] **Step 3: Inject the CSS and replace the current header orchestration**

Add imports and constants to `app.py`:

```python
from src.research_brief import (
    BriefContext,
    build_brief_context,
    comparison_html,
    findings_html,
    intro_html,
)

RESEARCH_CSS_PATH = Path(__file__).parent / "assets" / "research-brief.css"
```

At the end of `apply_page_style()` add:

```python
    st.markdown(
        f"<style>{RESEARCH_CSS_PATH.read_text(encoding='utf-8')}</style>",
        unsafe_allow_html=True,
    )
```

Replace `render_header()` with:

```python
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
```

Add:

```python
def render_research_findings(context: BriefContext) -> None:
    st.markdown(findings_html(context), unsafe_allow_html=True)
    st.markdown(comparison_html(context), unsafe_allow_html=True)
```

- [ ] **Step 4: Reorder the dashboard without changing detailed views**

Update `render_survey_dashboard()` to use this order:

```python
    context = render_header(korean_survey, foreign_survey)
    if st.button("데이터 새로고침", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    render_research_findings(context)
    render_product_bridge(context)
    st.markdown("## 상세 조사 결과")
    selected_view = st.radio(
        "보기 선택",
        ["전체 요약", "한국인 설문", "외국인 설문", "비교 요약"],
        horizontal=True,
        label_visibility="collapsed",
    )
```

Define a temporary bridge before Task 4 so this task remains runnable:

```python
def render_product_bridge(context: BriefContext) -> None:
    if not context.has_data:
        return
    st.markdown(
        '<section class="research-product-bridge"><p>FROM RESEARCH TO PRODUCT</p>'
        '<h2>이 근거가 시냅스팟의 두 기능으로 이어졌습니다.</h2></section>',
        unsafe_allow_html=True,
    )
```

- [ ] **Step 5: Run app tests and compilation**

Run:

```powershell
& '..\..\.venv\Scripts\python.exe' -m unittest tests.test_app_copy tests.test_research_brief -v
& '..\..\.venv\Scripts\python.exe' -m py_compile app.py src\research_brief.py
```

Expected: all selected tests pass and compilation exits 0.

- [ ] **Step 6: Commit the page-flow integration**

```powershell
git add app.py tests/test_app_copy.py
git commit -m "feat: integrate evidence-first survey flow"
```

---

### Task 4: Add the One-Time SynapSpot Product Bridge

**Files:**
- Restore: `assets/synapspot-meetings-preview.png`
- Restore: `assets/synapspot-question-preview.png`
- Modify: `assets/research-brief.css`
- Modify: `src/research_brief.py`
- Modify: `app.py`
- Modify: `tests/test_research_brief.py`

**Interfaces:**
- Produces: `image_data_uri(path: Path) -> str`.
- Produces: `product_bridge_html(context, meetings_path, question_path) -> str`.
- Missing images produce text feature blocks without broken `<img>` tags.

- [ ] **Step 1: Restore the two previously verified real product snapshots**

Run:

```powershell
git restore --source=eb15ebc -- assets/synapspot-meetings-preview.png assets/synapspot-question-preview.png
```

Expected: both PNG files appear as added files in `git status --short`. These are the available real product snapshots, not drawn mockups. Before final deployment, visually compare them with the then-current SynapSpot screens and replace only if the product UI has materially changed.

- [ ] **Step 2: Write failing image and fallback tests**

Append to `tests/test_research_brief.py`:

```python
from pathlib import Path
from tempfile import TemporaryDirectory

from src.research_brief import image_data_uri, product_bridge_html


class ProductBridgeTest(unittest.TestCase):
    def test_png_is_encoded_as_data_uri(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "screen.png"
            path.write_bytes(b"\x89PNG\r\n\x1a\nexample")
            self.assertTrue(image_data_uri(path).startswith("data:image/png;base64,"))

    def test_missing_images_keep_feature_copy_without_broken_image(self):
        korean = survey(4, source="Google Sheets", loaded_at="2026-07-15 15:00")
        foreign = survey(3, source="Google Sheets", loaded_at="2026-07-15 15:01")
        context = build_brief_context(korean, foreign)
        markup = product_bridge_html(context, Path("missing-a.png"), Path("missing-b.png"))

        self.assertIn("이동·동행 파티", markup)
        self.assertIn("근거 있는 정보 탐색", markup)
        self.assertNotIn("<img", markup)
```

- [ ] **Step 3: Run product-bridge tests and verify missing functions**

Run:

```powershell
& '..\..\.venv\Scripts\python.exe' -m unittest tests.test_research_brief.ProductBridgeTest -v
```

Expected: import failure for `image_data_uri` and `product_bridge_html`.

- [ ] **Step 4: Implement safe image embedding and bridge markup**

Add to `src/research_brief.py`:

```python
from base64 import b64encode
from pathlib import Path


def image_data_uri(path: Path) -> str:
    if not path.exists() or path.suffix.lower() != ".png":
        return ""
    encoded = b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def _feature(title: str, description: str, image_uri: str, alt: str) -> str:
    image = f'<img src="{image_uri}" alt="{escape(alt)}">' if image_uri else ""
    return f'''<article class="research-product-feature">{image}<div><h3>{escape(title)}</h3><p>{escape(description)}</p></div></article>'''


def product_bridge_html(
    context: BriefContext, meetings_path: Path, question_path: Path
) -> str:
    if not context.has_data:
        return ""
    meetings = _feature(
        "이동·동행 파티",
        "시간, 목적지, 인원을 기준으로 함께 이동할 사람을 찾습니다.",
        image_data_uri(meetings_path),
        "시냅스팟 이동·동행 파티 모바일 화면",
    )
    question = _feature(
        "근거 있는 정보 탐색",
        "공지와 생활정보를 질문하고 답변의 출처를 확인합니다.",
        image_data_uri(question_path),
        "시냅스팟 근거 있는 정보 탐색 모바일 화면",
    )
    return f'''<section class="research-product-bridge">
  <p class="research-kicker">FROM RESEARCH TO PRODUCT</p>
  <h2>이 근거가 시냅스팟의 두 기능으로 이어졌습니다.</h2>
  <p>설문이 기능의 효과를 입증한 것이 아니라, 구현할 문제의 우선순위를 정하는 근거로 사용됐습니다.</p>
  <div class="research-product-grid">{meetings}{question}</div>
</section>'''
```

- [ ] **Step 5: Style the bridge and replace the temporary renderer**

Append to `assets/research-brief.css`:

```css
.research-product-bridge { max-width: 960px; margin: 0 auto; padding: 34px 28px; border-radius: 8px; background: var(--research-bridge); color: white; }
.research-product-bridge h2 { max-width: 680px; margin: 8px 0; color: white; font-size: 28px; }
.research-product-bridge > p:not(.research-kicker) { color: #c9d6e6; }
.research-product-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 18px; margin-top: 20px; }
.research-product-feature { overflow: hidden; border: 1px solid #3a5778; border-radius: 8px; background: #19395f; }
.research-product-feature img { display: block; width: 100%; aspect-ratio: 9 / 16; object-fit: cover; object-position: top; }
.research-product-feature > div { padding: 14px; }
.research-product-feature h3 { margin: 0; color: white; font-size: 18px; }
.research-product-feature p { margin: 6px 0 0; color: #c9d6e6; }
@media (max-width: 640px) {
  .research-product-bridge { padding: 26px 16px; }
  .research-product-grid { grid-template-columns: 1fr; }
}
```

In `app.py` import `product_bridge_html`, define paths, and replace the temporary renderer:

```python
MEETINGS_PREVIEW = Path(__file__).parent / "assets" / "synapspot-meetings-preview.png"
QUESTION_PREVIEW = Path(__file__).parent / "assets" / "synapspot-question-preview.png"


def render_product_bridge(context: BriefContext) -> None:
    markup = product_bridge_html(context, MEETINGS_PREVIEW, QUESTION_PREVIEW)
    if markup:
        st.markdown(markup, unsafe_allow_html=True)
```

- [ ] **Step 6: Run tests and inspect both restored images**

Run:

```powershell
& '..\..\.venv\Scripts\python.exe' -m unittest tests.test_research_brief -v
```

Expected: all research brief tests pass. Then inspect both PNG files with the image viewer and confirm they show the Meetings and Question screens rather than blank or error states.

- [ ] **Step 7: Commit the product bridge**

```powershell
git add assets/research-brief.css assets/synapspot-meetings-preview.png assets/synapspot-question-preview.png src/research_brief.py app.py tests/test_research_brief.py
git commit -m "feat: connect survey evidence to SynapSpot"
```

---

### Task 5: Correct and Preserve Detailed Survey Views

**Files:**
- Modify: `app.py`
- Modify: `tests/test_app_copy.py`
- Modify: `tests/test_research_brief.py`

**Interfaces:**
- Keeps: `render_korean_view`, `render_foreign_view`, `render_compare_view`, `render_comments_section`, and four detailed view labels.
- Changes: `render_overall_view` must never use `max(korean_total, foreign_total)` as a shared percentage denominator.

- [ ] **Step 1: Add regression assertions for detailed navigation and denominator safety**

Append to `tests/test_app_copy.py`:

```python
    def test_detailed_views_and_comment_paging_remain_available(self) -> None:
        for label in ["전체 요약", "한국인 설문", "외국인 설문", "비교 요약", "익명 자유 의견"]:
            self.assertIn(label, self.app_text)
        self.assertIn("page_size = 5", self.app_text)

    def test_overall_view_does_not_share_the_larger_group_denominator(self) -> None:
        self.assertNotIn("max(korean_total, foreign_total)", self.app_text)
```

- [ ] **Step 2: Run the app-copy tests and verify the denominator assertion fails**

Run:

```powershell
& '..\..\.venv\Scripts\python.exe' -m unittest tests.test_app_copy.AppCopyTest.test_overall_view_does_not_share_the_larger_group_denominator -v
```

Expected: FAIL because the current overall view passes `max(korean_total, foreign_total)` to both comparison charts.

- [ ] **Step 3: Replace shared-denominator comparison charts**

In `render_overall_view()`, remove the two `render_rank_section()` calls that combine Korean and foreign values with one denominator. Keep the compact whole-sample summary, then render group-specific sections:

```python
    st.markdown("### 한국인 응답 상세")
    render_rank_section("한국인 핵심 불편", "한국인 응답 기준", korean["pain"], korean_total)
    render_rank_section("한국인 오픈채팅 수요", "한국인 응답 기준", korean["openchat_find"], korean_total)

    st.markdown("### 외국인 응답 상세")
    render_rank_section("외국인 핵심 불편", "외국인 응답 기준", foreign["pain"], foreign_total)
    render_rank_section("외국인 오픈채팅 수요", "외국인 응답 기준", foreign["openchat_find"], foreign_total)
```

Remove the repeated `한눈에 보는 결론` card from `render_overall_view()` because the research brief already provides the interpretation above the product bridge.

- [ ] **Step 4: Keep detailed tabs usable on mobile**

Add a CSS rule in `apply_page_style()` or `assets/research-brief.css` that allows the horizontal radio container to wrap without truncating labels:

```css
div[role="radiogroup"] { display: flex; flex-wrap: wrap; gap: 6px; }
div[role="radiogroup"] label { min-width: max-content; }
```

- [ ] **Step 5: Run detailed-view tests and the full test suite**

Run:

```powershell
& '..\..\.venv\Scripts\python.exe' -m unittest discover -s tests -v
```

Expected: all tests pass, including the no-shared-denominator regression.

- [ ] **Step 6: Commit detailed-view corrections**

```powershell
git add app.py assets/research-brief.css tests/test_app_copy.py tests/test_research_brief.py
git commit -m "fix: preserve group-safe survey details"
```

---

### Task 6: Align PDF Export and Fallback Status

**Files:**
- Modify: `app.py`
- Create: `tests/test_pdf_export.py`

**Interfaces:**
- Keeps: `build_current_pdf(korean_survey, foreign_survey) -> bytes`.
- Produces: a three-page PDF with total, Korean, and foreign data generated from the same survey objects rendered on screen.

- [ ] **Step 1: Add a failing PDF regression test**

Create `tests/test_pdf_export.py`:

```python
import unittest
from io import BytesIO

from pypdf import PdfReader

from app import build_current_pdf


def report(total: int, label: str):
    return {
        "data": {
            "n": total,
            "pain": [(label, total)],
            "activity": [],
            "openchat_find": [(label, total)],
            "openchat_pain": [],
            "intent": [("긍정", total), ("중립", 0), ("부정", 0)],
            "comments": [],
        },
        "source": "Google Sheets",
        "loaded_at": "2026-07-15 15:00",
    }


class PdfExportTest(unittest.TestCase):
    def test_pdf_contains_current_group_totals_and_three_pages(self):
        pdf = build_current_pdf(report(23, "택시팟"), report(16, "공지"))
        reader = PdfReader(BytesIO(pdf))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)

        self.assertEqual(len(reader.pages), 3)
        self.assertIn("39명", text)
        self.assertIn("23명", text)
        self.assertIn("16명", text)
        self.assertIn("한국인", text)
        self.assertIn("외국인", text)
```

- [ ] **Step 2: Run the PDF test and record the actual failure if font extraction differs**

Run:

```powershell
& '..\..\.venv\Scripts\python.exe' -m unittest tests.test_pdf_export -v
```

Expected: three pages are generated. If Korean extraction fails because the host falls back to a CID font, change the test to assert ASCII PDF metadata added in Step 3 rather than weakening the response-total assertion.

- [ ] **Step 3: Add stable metadata and align PDF colors/copy**

In `build_current_pdf()` set metadata before drawing pages:

```python
    c.setTitle("Jeju Exchange Student Survey Research Brief")
    c.setSubject(
        f"total={korean_total + foreign_total}; korean={korean_total}; foreign={foreign_total}; "
        f"korean_source={korean_survey.get('source', '')}; foreign_source={foreign_survey.get('source', '')}"
    )
```

Move `korean_total` and `foreign_total` calculation above this metadata call. Update PDF colors:

```python
PDF_TEXT = colors.HexColor("#13233D")
PDF_MUTED = colors.HexColor("#66768A")
PDF_LINE = colors.HexColor("#D8E2E9")
PDF_BLUE = colors.HexColor("#EC6A5F")
PDF_TEAL = colors.HexColor("#087F72")
```

Update the cover conclusion to the approved wording while keeping the source lines:

```python
"이동·동행 모집과 신뢰할 수 있는 생활정보 탐색이 함께 필요했습니다. "
"PDF는 다운로드 시점의 앱 집계 데이터를 기준으로 생성되며, 개인 식별 정보와 원본 응답 행은 포함하지 않습니다."
```

If CID extraction was the only failure, assert metadata instead:

```python
        subject = reader.metadata.subject or ""
        self.assertIn("total=39", subject)
        self.assertIn("korean=23", subject)
        self.assertIn("foreign=16", subject)
```

- [ ] **Step 4: Run PDF and full regression tests**

Run:

```powershell
& '..\..\.venv\Scripts\python.exe' -m unittest tests.test_pdf_export -v
& '..\..\.venv\Scripts\python.exe' -m unittest discover -s tests -v
```

Expected: PDF test and all existing tests pass.

- [ ] **Step 5: Commit PDF alignment**

```powershell
git add app.py tests/test_pdf_export.py
git commit -m "fix: align live PDF with research brief"
```

---

### Task 7: Verify Responsive Behavior and Publish the Approved Build

**Files:**
- Modify only if verification finds a defect: `app.py`, `assets/research-brief.css`, or tests that reproduce the defect.

**Interfaces:**
- Verifies: local Streamlit UI, Google Sheets/CSV source copy, product images, PDF, and public deployment branch.
- Publishes: tested commits from `codex/survey-dashboard-reset` to `codex/survey-research-redesign` after visual approval.

- [ ] **Step 1: Run fresh automated verification**

Run:

```powershell
& '..\..\.venv\Scripts\python.exe' -m unittest discover -s tests -v
& '..\..\.venv\Scripts\python.exe' -m py_compile app.py src\survey_dashboard.py src\research_brief.py
git diff --check
```

Expected: all tests pass, compilation exits 0, and `git diff --check` prints nothing.

- [ ] **Step 2: Start the local dashboard on an unused port**

Run:

```powershell
& '..\..\.venv\Scripts\python.exe' -m streamlit run app.py --server.address 127.0.0.1 --server.port 8512
```

Expected: Streamlit reports `http://127.0.0.1:8512`. Keep the session running until browser verification finishes.

- [ ] **Step 3: Verify desktop 1440x900**

Open `http://127.0.0.1:8512` with the browser verification tool at 1440x900 and confirm:

- the title identifies a student research brief;
- total, Korean, foreign, and source status appear without hardcoded counts;
- findings precede the product bridge;
- only one product bridge appears;
- both real product images render;
- detailed tabs, comments, refresh, and PDF remain available;
- no HTML source text is displayed as visible content.

Expected: no horizontal overflow and no overlapping text or controls.

- [ ] **Step 4: Verify mobile 390x844**

Set the browser viewport to 390x844, reload, and confirm:

- the first viewport contains the title, response counts, source state, and refresh button;
- the status grid becomes two columns;
- findings, comparison, product features, and detailed results become one column;
- tab labels wrap without clipping;
- chart labels, counts, and percentages remain visible;
- `document.documentElement.scrollWidth` equals `window.innerWidth`.

Expected: no horizontal scrolling, clipped text, or button overlap.

- [ ] **Step 5: Verify fallback and empty states without changing secrets**

Run unit tests from Tasks 1 and 4, then inspect the local CSV fallback banner. Confirm it says `저장 데이터 포함 집계`, not `Google Sheets 실시간 집계`. Do not remove or overwrite Streamlit Cloud secrets.

- [ ] **Step 6: Request final visual approval before public deployment**

Share the local URL and desktop/mobile screenshots with the user. Do not merge or push to the public deployment branch until the user approves this rendered build.

- [ ] **Step 7: Push the implementation branch after approval**

Run:

```powershell
git push origin codex/survey-dashboard-reset
```

Expected: the remote branch advances to the final tested commit.

- [ ] **Step 8: Merge into the Streamlit deployment branch**

From `C:\Users\Aiffel\Desktop\workspace\team-projects\ara-guide\.worktrees\survey-research-redesign` run:

```powershell
git status --short --branch
git merge --no-ff codex/survey-dashboard-reset -m "merge: publish survey research brief"
git push origin codex/survey-research-redesign
```

Expected: the worktree has no tracked changes before the merge, the merge succeeds without force-pushing, and Streamlit begins rebuilding the existing public URL.

- [ ] **Step 9: Verify the public deployment**

Open `https://jeju-student-survey-research-preview.streamlit.app/` at desktop and 390x844. Confirm the public app reads Google Sheets, displays the latest total with separate Korean and foreign counts, and matches the approved local layout. If Streamlit does not rebuild automatically, request action-time approval before using `Reboot` in Streamlit Community Cloud.

Expected: public DOM contains `Google Sheets 실시간 집계`, current group counts, the research title, and one `FROM RESEARCH TO PRODUCT` bridge.

---

## Final Review Checklist

- [ ] Every count in the research brief comes from `BriefContext`.
- [ ] Korean and foreign percentages use separate denominators.
- [ ] Live status requires two Google Sheets sources.
- [ ] Research findings appear before the SynapSpot bridge.
- [ ] The SynapSpot bridge appears once and uses real product snapshots.
- [ ] Detailed views, five-comment pagination, refresh, and PDF remain available.
- [ ] PDF metadata and pages use the same survey objects as the screen.
- [ ] Automated tests, Python compilation, desktop verification, and mobile verification pass.
- [ ] No unrelated untracked files or credentials are staged.
- [ ] Public deployment occurs only after local visual approval.
