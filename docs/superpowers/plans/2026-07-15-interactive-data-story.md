# Interactive Survey Data Story Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the live survey report into a presentation-ready scrolling data story with animated respondent dots, interactive evidence bars, and a direct visual bridge to Synapspot features.

**Architecture:** Extend the existing `build_research_view_model()` contract with the ranked data already produced by `survey_dashboard.py`, then render the presentation story as accessible server-generated HTML and CSS in `research_page.py`. Keep `app.py` responsible for Streamlit composition, the existing detailed dashboard, data refresh, and PDF download so live data and fallback behavior remain unchanged.

**Tech Stack:** Python 3.14, Streamlit 1.59, server-generated HTML, responsive CSS, `unittest`, Playwright browser verification through the Codex browser runtime.

## Global Constraints

- Do not add a large visualization library or a canvas renderer.
- Do not hard-code the current total of 39 responses or current percentages.
- Render at most 60 respondent dots and disclose aggregation when the total exceeds 60.
- Keep Google Sheets/CSV fallback, detailed views, anonymous-comment pagination, refresh, and PDF download behavior.
- Use coral for movement/companion evidence, teal for information/trust evidence, and navy for primary text.
- Use no infinite animation and honor `prefers-reduced-motion: reduce`.
- Keep Synapspot source code and product functionality unchanged.
- Keep the existing PDF design unchanged.

---

### Task 1: Expand the live research view model

**Files:**
- Modify: `src/research_page.py:17-43`
- Modify: `tests/test_research_page.py:10-42`

**Interfaces:**
- Consumes: `korean_survey: dict[str, Any]`, `foreign_survey: dict[str, Any]` with existing `data.n`, `data.pain`, `data.openchat_find`, and `data.intent` fields.
- Produces: `build_research_view_model(...) -> dict[str, object]` containing the existing summary keys plus `korean_pain`, `korean_find`, `foreign_pain`, `foreign_find`, `dot_count`, and `responses_per_dot`.

- [ ] **Step 1: Write failing tests for ranked data and scalable respondent dots**

Add these assertions to `test_builds_live_summary_without_hard_coded_counts`:

```python
self.assertEqual(result["korean_pain"], [("버스 노선", 10)])
self.assertEqual(result["foreign_find"], [("공지", 9)])
self.assertEqual(result["dot_count"], 35)
self.assertEqual(result["responses_per_dot"], 1)
```

Add a second test using 80 Korean responses and 40 foreign responses:

```python
def test_caps_respondent_dots_for_large_samples(self) -> None:
    korean = {"data": {"n": 80, "pain": [], "openchat_find": [], "intent": []}}
    foreign = {"data": {"n": 40, "pain": [], "openchat_find": [], "intent": []}}

    result = build_research_view_model(korean, foreign)

    self.assertEqual(result["total"], 120)
    self.assertEqual(result["dot_count"], 60)
    self.assertEqual(result["responses_per_dot"], 2)
```

- [ ] **Step 2: Run the focused test and verify it fails**

Run:

```powershell
& 'C:\Users\Aiffel\Desktop\workspace\team-projects\ara-guide\.venv\Scripts\python.exe' -m unittest tests.test_research_page.ResearchPageTest.test_builds_live_summary_without_hard_coded_counts tests.test_research_page.ResearchPageTest.test_caps_respondent_dots_for_large_samples -v
```

Expected: failure because the six new model keys do not exist.

- [ ] **Step 3: Implement the expanded model**

In `build_research_view_model()`, copy ranked lists rather than mutating the parser output and calculate the dot scale:

```python
dot_count = min(total, 60)
responses_per_dot = max(1, (total + 59) // 60)

return {
    "total": total,
    "korean_total": korean_total,
    "foreign_total": foreign_total,
    "korean_top_pain": _top(korean.get("pain", [])),
    "foreign_top_pain": _top(foreign.get("pain", [])),
    "korean_top_find": _top(korean.get("openchat_find", [])),
    "foreign_top_find": _top(foreign.get("openchat_find", [])),
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
```

Use `.get()` for list fields so the empty-data test does not fail before rendering.

- [ ] **Step 4: Run the focused tests and verify they pass**

Run the command from Step 2.

Expected: both tests pass.

- [ ] **Step 5: Commit the model contract**

```powershell
git add src/research_page.py tests/test_research_page.py
git commit -m "feat: expand live research story model"
```

---

### Task 2: Build the respondent visualization and interactive evidence bars

**Files:**
- Modify: `src/research_page.py:45-325`
- Modify: `tests/test_research_page.py`

**Interfaces:**
- Consumes: the expanded research model from Task 1.
- Produces: `_respondent_dots_html(model) -> str`, `_story_bars_html(items, total, tone) -> str`, and an updated `research_story_html(model) -> str`.

- [ ] **Step 1: Write failing HTML contract tests**

Add a reusable model helper in `ResearchPageTest` and these tests:

```python
def story_model(
    self,
    total: int = 3,
    korean_total: int = 2,
    foreign_total: int = 1,
) -> dict[str, object]:
    return {
        "total": total,
        "korean_total": korean_total,
        "foreign_total": foreign_total,
        "korean_top_pain": ("버스 노선", korean_total),
        "foreign_top_pain": ("교통", foreign_total),
        "korean_top_find": ("택시팟", korean_total),
        "foreign_top_find": ("공지", foreign_total),
        "korean_positive": korean_total,
        "foreign_positive": foreign_total,
        "positive_total": total,
        "positive_pct": "100.0%" if total else "0.0%",
        "loaded_at": "2026-07-15 10:00",
        "korean_pain": [("버스 노선", korean_total)],
        "korean_find": [("택시팟", korean_total)],
        "foreign_pain": [("교통", foreign_total)],
        "foreign_find": [("공지", foreign_total)],
        "dot_count": min(total, 60),
        "responses_per_dot": max(1, (total + 59) // 60),
    }

def test_story_renders_dynamic_respondent_dots(self) -> None:
    model = self.story_model(total=3, korean_total=2, foreign_total=1)

    html = research_story_html(model)

    self.assertEqual(html.count('class="respondent-dot '), 3)
    self.assertIn("한국인 2명", html)
    self.assertIn("외국인 1명", html)
    self.assertNotIn("39명의 응답", html)

def test_story_bars_expose_values_without_hover(self) -> None:
    model = self.story_model(total=3, korean_total=2, foreign_total=1)

    html = research_story_html(model)

    self.assertIn('class="story-bar-value"', html)
    self.assertIn("2명", html)
    self.assertIn("100.0%", html)
    self.assertIn('tabindex="0"', html)

def test_story_honors_reduced_motion_and_mobile_layout(self) -> None:
    html = research_story_html(self.story_model())

    self.assertIn("prefers-reduced-motion: reduce", html)
    self.assertIn("@media (max-width: 680px)", html)
    self.assertIn("grid-template-columns: 1fr", html)
```

- [ ] **Step 2: Run the new HTML contract tests and verify they fail**

Run:

```powershell
& 'C:\Users\Aiffel\Desktop\workspace\team-projects\ara-guide\.venv\Scripts\python.exe' -m unittest tests.test_research_page -v
```

Expected: failures for missing respondent-dot, story-bar-value, keyboard focus, and reduced-motion markup.

- [ ] **Step 3: Add server-generated respondent dots**

Add `_respondent_dots_html(model)` to `src/research_page.py`:

```python
def _respondent_dots_html(model: dict[str, object]) -> str:
    total = int(model["total"])
    dot_count = int(model["dot_count"])
    korean_total = int(model["korean_total"])
    korean_dots = round(dot_count * korean_total / total) if total else 0
    dots = []
    for index in range(dot_count):
        group = "korean" if index < korean_dots else "foreign"
        dots.append(
            f'<span class="respondent-dot {group}" style="--dot-index:{index}" aria-hidden="true"></span>'
        )
    scale = int(model["responses_per_dot"])
    scale_note = f"점 1개는 약 {scale}명의 응답" if scale > 1 else "점 1개는 응답 1명"
    return (
        '<div class="respondent-visual" role="img" '
        f'aria-label="전체 {total}명, 한국인 {korean_total}명, 외국인 {int(model["foreign_total"])}명">'
        f'<div class="respondent-dots">{"".join(dots)}</div>'
        f'<p class="dot-scale">{scale_note}</p></div>'
    )
```

- [ ] **Step 4: Add accessible interactive story bars**

Add `_story_bars_html(items, total, tone)`:

```python
def _story_bars_html(items: list[tuple[str, int]], total: int, tone: str) -> str:
    rows = []
    for index, (label, count) in enumerate(items[:5]):
        width = count / total * 100 if total else 0
        rows.append(
            f'<div class="story-bar-row {tone}" tabindex="0" style="--bar-index:{index}">'
            f'<div class="story-bar-head"><span>{escape(str(label))}</span>'
            f'<strong class="story-bar-value">{int(count)}명 · {escape(pct(int(count), total))}</strong></div>'
            f'<div class="story-bar-track"><span style="--bar-width:{width:.1f}%"></span></div></div>'
        )
    return "".join(rows) or '<p class="empty-story">아직 집계된 응답이 없습니다.</p>'
```

- [ ] **Step 5: Replace the card-heavy story with seven scrolling sections**

Update `research_story_html()` so it renders:

```python
return f"""
{research_page_css()}
<main class="research-page">
  <header class="story-hero">
    <div class="hero-copy-block">
      <p class="eyebrow">JEJU EXCHANGE STUDENT RESEARCH</p>
      <h1><em>{total}명</em>의 응답이<br>두 가지 문제를 가리켰습니다</h1>
      <p class="hero-copy">한국인과 외국인 교류학생이 제주에서 이동하고, 사람을 만나고, 생활정보를 찾으며 겪은 경험을 조사했습니다.</p>
      <div class="hero-meta"><span>한국인 {korean_total}명</span><span>외국인 {foreign_total}명</span><span>마지막 집계 {escape(str(model['loaded_at']))}</span></div>
    </div>
    {_respondent_dots_html(model)}
  </header>
  <section class="story-problems" aria-labelledby="problem-title">
    <p class="section-kicker">WHAT WE FOUND</p>
    <h2 id="problem-title">응답은 두 갈래의 불편으로 모였습니다</h2>
    <div class="problem-paths">
      <article class="problem-path movement"><span>01</span><h3>이동과 동행 모집</h3><p>같은 시간과 목적지의 사람을 빠르게 찾는 과정이 반복됐습니다.</p></article>
      <article class="problem-path information"><span>02</span><h3>공지와 생활정보 탐색</h3><p>흩어진 정보를 찾고 최신성과 신뢰도를 확인해야 했습니다.</p></article>
    </div>
  </section>
  <section class="evidence-scene movement-scene">
    <div class="scene-copy"><span>PROBLEM 01</span><h2>이동 비용보다 더 오래 걸린 것은<br>함께 갈 사람을 찾는 일이었습니다</h2><p>한국인 교류학생 응답에서 확인한 이동과 모집 관련 상위 결과입니다.</p></div>
    <div class="scene-charts"><article><h3>제주에서 불편했던 점</h3>{_story_bars_html(list(model['korean_pain']), korean_total, 'movement')}</article><article><h3>오픈채팅에서 찾은 것</h3>{_story_bars_html(list(model['korean_find']), korean_total, 'movement')}</article></div>
  </section>
  <section class="evidence-scene information-scene">
    <div class="scene-copy"><span>PROBLEM 02</span><h2>정보를 찾은 뒤에도<br>믿어도 되는지 확인해야 했습니다</h2><p>외국인 교류학생 응답에서 확인한 생활정보 탐색 관련 상위 결과입니다.</p></div>
    <div class="scene-charts"><article><h3>제주에서 불편했던 점</h3>{_story_bars_html(list(model['foreign_pain']), foreign_total, 'information')}</article><article><h3>오픈채팅에서 찾은 것</h3>{_story_bars_html(list(model['foreign_find']), foreign_total, 'information')}</article></div>
  </section>
</main>
"""
```

Use the live total in the headline: `<em>{total}명</em>의 응답이<br>두 가지 문제를 가리켰습니다`. Include the existing evidence statement that the survey informs product direction but does not prove feature effectiveness.

- [ ] **Step 6: Replace the flat CSS with responsive editorial styling and bounded motion**

In `research_page_css()`:

- Use a full-width white hero with an asymmetric two-column layout on desktop.
- Use coral `#f05d4e`, teal `#008f83`, navy `#10213d`, and pale blue-gray `#f2f6fa`.
- Animate dots with `animation-delay: calc(var(--dot-index) * 22ms)`.
- Animate bars from `scaleX(0)` to `scaleX(1)` with `transform-origin: left`.
- On `.story-bar-row:hover` and `.story-bar-row:focus-visible`, strengthen the active row and reduce sibling opacity only within the same chart.
- Add `@media (prefers-reduced-motion: reduce)` that removes animation and transition.
- Under 680px, switch every scene to one column and place bar values below long labels.

- [ ] **Step 7: Run HTML tests and the full suite**

```powershell
& 'C:\Users\Aiffel\Desktop\workspace\team-projects\ara-guide\.venv\Scripts\python.exe' -m unittest tests.test_research_page -v
& 'C:\Users\Aiffel\Desktop\workspace\team-projects\ara-guide\.venv\Scripts\python.exe' -m unittest discover -s tests -v
```

Expected: all tests pass.

- [ ] **Step 8: Commit the interactive story**

```powershell
git add src/research_page.py tests/test_research_page.py
git commit -m "feat: add interactive survey data story"
```

---

### Task 3: Integrate the product transition and detailed-data boundary

**Files:**
- Modify: `src/research_page.py`
- Modify: `app.py:478-776`
- Modify: `tests/test_app_copy.py`

**Interfaces:**
- Consumes: `research_story_html(model)` and `product_bridge_html(model)` from Task 2.
- Produces: a single Streamlit flow in which the data story appears before product previews and the detailed dashboard begins under a clearly labeled secondary section.

- [ ] **Step 1: Write failing flow tests**

Add these assertions to `tests/test_app_copy.py`:

```python
def test_presentation_story_precedes_detailed_dashboard(self) -> None:
    story_index = self.app_text.index("render_research_intro")
    preview_index = self.app_text.index("render_product_preview")
    detail_index = self.app_text.index("전체 데이터 살펴보기")
    self.assertLess(story_index, preview_index)
    self.assertLess(preview_index, detail_index)

def test_page_style_supports_full_width_presentation(self) -> None:
    self.assertIn("max-width: 1180px", self.app_text)
    self.assertIn("scroll-margin-top", self.app_text)
```

- [ ] **Step 2: Run the flow tests and verify they fail**

```powershell
& 'C:\Users\Aiffel\Desktop\workspace\team-projects\ara-guide\.venv\Scripts\python.exe' -m unittest tests.test_app_copy -v
```

Expected: failure because the new boundary copy and 1180px presentation width are absent.

- [ ] **Step 3: Update the Streamlit composition**

In `app.py`:

- Increase `.main .block-container` max width from `1120px` to `1180px`.
- Keep `render_research_intro()` and `render_product_preview()` before data status.
- Replace `## 상세 조사 결과` with `## 전체 데이터 살펴보기`.
- Add the caption `발표 흐름에서 다룬 근거와 전체 응답 항목을 직접 비교할 수 있습니다.`.
- Add `scroll-margin-top: 24px` to headings so anchored headings do not touch the viewport edge.
- Retain the radio control and every existing view renderer without changing data behavior.

- [ ] **Step 4: Refine the product bridge and preview treatment**

Update `product_bridge_html()` to use two colored paths rather than two uniform cards. Keep the exact feature claims already grounded in the Synapspot screens. In `render_product_preview()`, retain the missing-asset fallback and place each feature heading before its matching image using this order:

```python
previews = [
    (MEETINGS_PREVIEW, "이동·동행 파티", "모임을 찾고 만들고 신청 상태를 관리합니다."),
    (QUESTION_PREVIEW, "근거 있는 AI 질문", "답변과 함께 출처와 신뢰도를 확인합니다."),
]
columns = st.columns(2)
for column, (image_path, title, description) in zip(columns, previews):
    with column:
        st.markdown(f"### {title}")
        st.caption(description)
        if image_path.exists():
            st.image(str(image_path), width="stretch")
        else:
            st.info("미리보기 이미지를 준비 중입니다.")
```

- [ ] **Step 5: Run app tests and the full suite**

```powershell
& 'C:\Users\Aiffel\Desktop\workspace\team-projects\ara-guide\.venv\Scripts\python.exe' -m py_compile app.py src\research_page.py
& 'C:\Users\Aiffel\Desktop\workspace\team-projects\ara-guide\.venv\Scripts\python.exe' -m unittest discover -s tests -v
```

Expected: compilation succeeds and all tests pass.

- [ ] **Step 6: Commit the integrated presentation flow**

```powershell
git add app.py src/research_page.py tests/test_app_copy.py
git commit -m "feat: integrate presentation survey flow"
```

---

### Task 4: Verify responsive rendering and deploy the preview branch

**Files:**
- Modify only if verification exposes a defect: `app.py`, `src/research_page.py`, related test file

**Interfaces:**
- Consumes: the completed Streamlit page and live Google Sheets secrets already configured for the preview app.
- Produces: verified screenshots at 390px and 1440px plus an updated public preview at `https://jeju-student-survey-research-preview.streamlit.app/`.

- [ ] **Step 1: Run final static and unit verification**

```powershell
& 'C:\Users\Aiffel\Desktop\workspace\team-projects\ara-guide\.venv\Scripts\python.exe' -m py_compile app.py src\research_page.py src\survey_dashboard.py src\presentation_pdf.py
& 'C:\Users\Aiffel\Desktop\workspace\team-projects\ara-guide\.venv\Scripts\python.exe' -m unittest discover -s tests -v
git diff --check
git status --short
```

Expected: no compilation error, all tests pass, no diff-check error, and no generated artifacts are untracked.

- [ ] **Step 2: Start the local Streamlit server**

```powershell
& 'C:\Users\Aiffel\Desktop\workspace\team-projects\ara-guide\.venv\Scripts\python.exe' -m streamlit run app.py --server.headless true --server.port 8511
```

Expected: Streamlit reports `Local URL: http://localhost:8511`.

- [ ] **Step 3: Verify desktop rendering at 1440px**

Use the browser viewport capability at 1440x1000, open `http://localhost:8511`, and verify:

- the hero shows the live total and respondent dots;
- Korean and foreign groups are distinguishable;
- the movement and information evidence scenes each have visible labels, bars, counts, and percentages;
- product screenshots appear after the research-to-product bridge;
- no HTML source is printed as text and no elements overlap.

- [ ] **Step 4: Verify mobile rendering at 390px**

Set the browser viewport to 390x844 and verify:

- there is no horizontal scroll;
- dots stay inside the hero;
- each evidence scene is one column;
- long labels wrap without covering counts;
- product previews stack vertically;
- the detailed-view radio control and PDF button remain usable.

- [ ] **Step 5: Verify reduced motion and console health**

Emulate reduced motion if the browser capability supports it. Otherwise inspect the rendered CSS for the media query. Read browser console logs and confirm there are no page errors from the new story.

- [ ] **Step 6: Fix any visual defect with a regression test**

For each observed defect, add the narrowest HTML/CSS contract assertion to `tests/test_research_page.py` or `tests/test_app_copy.py`, confirm it fails, patch the implementation, and rerun the full suite.

- [ ] **Step 7: Push and reboot the Streamlit preview app**

```powershell
git push origin codex/survey-research-redesign
```

Reboot the Streamlit preview app from its Manage app panel so it checks out the new branch commit.

- [ ] **Step 8: Verify the public preview**

At the public URL, confirm:

- total response count equals Korean plus foreign responses;
- both data-source labels say `Google Sheets`;
- animated story, detailed views, refresh, comment pagination, and PDF download are present;
- a freshly downloaded PDF still has 4 pages and the same live totals shown on the site.

- [ ] **Step 9: Commit any verification fixes and leave the branch clean**

```powershell
git add app.py src/research_page.py tests
git commit -m "fix: polish responsive survey story"
git push origin codex/survey-research-redesign
git status --short
```

Skip the fix commit when verification required no code change. The final status must be clean and the preview branch must match its remote commit.
