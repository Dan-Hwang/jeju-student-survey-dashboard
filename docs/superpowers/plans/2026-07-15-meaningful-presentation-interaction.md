# Meaningful Presentation Interaction Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace decorative hover motion with a persistent presentation focus control that changes the evidence, interpretation, and Synapspot product preview.

**Architecture:** Keep survey loading and detailed dashboards unchanged. Add a pure focus-model builder in `src/research_page.py`, then let `app.py` own the native Streamlit segmented control and render the selected evidence and product preview from that model.

**Tech Stack:** Python 3, Streamlit 1.59, server-rendered HTML/CSS, unittest, Playwright with local Chrome

## Global Constraints

- Preserve Google Sheets synchronization, CSV fallback, detailed views, comments, refresh, and PDF download.
- Use `st.segmented_control` with `presentation_focus` session-state key.
- The three allowed labels are `전체 응답`, `이동·동행`, and `정보 탐색`; invalid values fall back to `전체 응답`.
- Remove decorative bar translation and sibling fading.
- Keep values visible without hover and honor `prefers-reduced-motion: reduce`.
- Verify at 390px and 1440px without horizontal overflow.

---

### Task 1: Build the presentation focus model

**Files:**
- Modify: `src/research_page.py`
- Test: `tests/test_research_page.py`

**Interfaces:**
- Consumes: `build_research_view_model(korean_survey, foreign_survey) -> dict[str, object]`
- Produces: `build_focus_view_model(model: dict[str, object], focus: str) -> dict[str, object]`

- [ ] **Step 1: Write failing selection-model tests**

Add tests asserting that `전체 응답` returns both problem summaries, `이동·동행` returns Korean pain/find data and meetings product metadata, `정보 탐색` returns foreign pain/find data and question product metadata, and an unknown label falls back to `전체 응답`.

```python
movement = build_focus_view_model(model, "이동·동행")
self.assertEqual(movement["focus"], "이동·동행")
self.assertEqual(movement["pain_items"], model["korean_pain"])
self.assertEqual(movement["product_asset"], "meetings")

information = build_focus_view_model(model, "정보 탐색")
self.assertEqual(information["find_items"], model["foreign_find"])
self.assertEqual(information["product_asset"], "question")

fallback = build_focus_view_model(model, "unknown")
self.assertEqual(fallback["focus"], "전체 응답")
```

- [ ] **Step 2: Run the focused tests and verify failure**

Run:

```powershell
& '..\..\.venv\Scripts\python.exe' -m unittest tests.test_research_page.ResearchPageTest.test_builds_movement_focus_model tests.test_research_page.ResearchPageTest.test_builds_information_focus_model tests.test_research_page.ResearchPageTest.test_invalid_focus_falls_back_to_overview -v
```

Expected: import or attribute failure because `build_focus_view_model` does not exist.

- [ ] **Step 3: Implement the pure focus model**

Return a dictionary with stable keys:

```python
{
    "focus": "이동·동행",
    "kicker": "PROBLEM 01",
    "title": "이동 비용보다 더 오래 걸린 것은 함께 갈 사람을 찾는 일이었습니다",
    "description": "한국인 교류학생 응답에서 확인한 이동과 모집 관련 상위 결과입니다.",
    "interpretation": "이동 자체뿐 아니라 같은 시간과 목적지의 동행을 찾는 과정이 반복됐습니다.",
    "tone": "movement",
    "total": model["korean_total"],
    "pain_items": model["korean_pain"],
    "find_items": model["korean_find"],
    "product_asset": "meetings",
    "product_title": "이동·동행 파티",
    "product_description": "모임을 찾고 만들고 신청 상태를 관리합니다.",
}
```

The information model uses foreign data and `product_asset="question"`. The overview model contains both problem summaries and no ranked lists or single product asset.

- [ ] **Step 4: Run all research-page tests**

Run:

```powershell
& '..\..\.venv\Scripts\python.exe' -m unittest tests.test_research_page -v
```

Expected: all research-page tests pass.

- [ ] **Step 5: Commit the focus model**

```powershell
git add src/research_page.py tests/test_research_page.py
git commit -m "feat: add presentation focus model"
```

### Task 2: Render persistent, meaningful selection

**Files:**
- Modify: `app.py`
- Modify: `src/research_page.py`
- Test: `tests/test_app_copy.py`
- Test: `tests/test_research_page.py`

**Interfaces:**
- Consumes: `build_focus_view_model(model, focus)` from Task 1
- Produces: `focus_panel_html(focus_model: dict[str, object]) -> str` and `render_product_preview(focus_model: dict[str, object]) -> None`

- [ ] **Step 1: Write failing composition and hover-removal tests**

```python
self.assertIn("st.segmented_control", self.app_text)
self.assertIn('key="presentation_focus"', self.app_text)
self.assertIn("build_focus_view_model", self.app_text)
self.assertNotIn("translateX(4px)", research_story_html(self.story_model()))
self.assertNotIn(":has(.story-bar-row:hover)", research_story_html(self.story_model()))
```

Also assert that movement panel HTML includes `data-focus="이동·동행"`, movement evidence, and the meetings product title; the information panel contains the corresponding foreign evidence and AI question title.

- [ ] **Step 2: Run focused tests and verify failure**

Run:

```powershell
& '..\..\.venv\Scripts\python.exe' -m unittest tests.test_app_copy.AppCopyTest.test_presentation_uses_persistent_focus_control tests.test_research_page.ResearchPageTest.test_focus_panel_removes_decorative_hover tests.test_research_page.ResearchPageTest.test_focus_panel_changes_content -v
```

Expected: failures because the segmented control and focus panel do not exist and hover CSS remains.

- [ ] **Step 3: Implement native selection and dynamic panel**

In `render_research_intro()`:

```python
model = build_research_view_model(korean_survey, foreign_survey)
st.html(research_hero_html(model))
focus = st.segmented_control(
    "발표 주제 선택",
    ["전체 응답", "이동·동행", "정보 탐색"],
    default="전체 응답",
    key="presentation_focus",
    width="stretch",
)
focus_model = build_focus_view_model(model, str(focus or "전체 응답"))
st.html(focus_panel_html(focus_model))
return focus_model
```

Update `render_product_preview()` to accept the focus model. Overview shows both previews; movement shows meetings only; information shows question only. Keep `st.image(..., width="stretch")` and missing-asset fallback.

Split the former all-in-one story HTML so the hero is always visible and only the selected evidence panel is rendered. Remove `translateX(4px)` and `:has()` sibling fading; retain visible labels, counts, percentages, focus outline, and one-time bar fill.

- [ ] **Step 4: Run focused and full unit tests**

Run:

```powershell
& '..\..\.venv\Scripts\python.exe' -m unittest tests.test_app_copy tests.test_research_page -v
& '..\..\.venv\Scripts\python.exe' -m unittest discover -s tests -v
```

Expected: all tests pass.

- [ ] **Step 5: Commit the interactive presentation flow**

```powershell
git add app.py src/research_page.py tests/test_app_copy.py tests/test_research_page.py
git commit -m "feat: add meaningful presentation interaction"
```

### Task 3: Verify behavior in a real browser

**Files:**
- Modify only if verification exposes a defect: `app.py`, `src/research_page.py`, related tests

**Interfaces:**
- Consumes: local Streamlit app at `http://127.0.0.1:8511`
- Produces: evidence that click state changes and persists at desktop and mobile widths

- [ ] **Step 1: Start Streamlit locally**

```powershell
& '..\..\.venv\Scripts\python.exe' -m streamlit run app.py --server.headless true --server.port 8511
```

Expected: local app responds on port 8511.

- [ ] **Step 2: Verify desktop click state with Playwright**

At 1440x1000, assert the default overview is visible, click `이동·동행`, confirm movement evidence and `이동·동행 파티` are visible, move the mouse away, and confirm the same selection remains. Click `정보 탐색` and confirm the evidence and `근거 있는 AI 질문` replace the movement content.

- [ ] **Step 3: Verify mobile layout with Playwright**

At 390x844, repeat both selections and assert `document.documentElement.scrollWidth <= 390`, the selected control remains visible, and the product image stays within its container.

- [ ] **Step 4: Run final verification**

```powershell
& '..\..\.venv\Scripts\python.exe' -m unittest discover -s tests -v
& '..\..\.venv\Scripts\python.exe' -m py_compile app.py src\research_page.py src\survey_dashboard.py src\presentation_pdf.py
git diff --check
git status --short
```

Expected: tests and compilation exit 0, diff check is clean, and the worktree has no uncommitted changes after the final commit.

- [ ] **Step 5: Push the feature branch and refresh the public preview**

```powershell
git push origin codex/survey-research-redesign
```

Expected: the public preview deploys the new branch commit and shows the same three persistent states.
