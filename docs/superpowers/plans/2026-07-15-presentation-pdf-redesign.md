# Presentation PDF Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the legacy survey PDF with a four-page presentation report that mirrors the public research page and uses the current Korean and foreign survey data.

**Architecture:** Move PDF rendering out of `app.py` into a focused `src/presentation_pdf.py` module. The module consumes the same survey dictionaries as the Streamlit page, renders fixed A4 pages with ReportLab, and embeds the existing Synapspot preview assets when available.

**Tech Stack:** Python 3.14, ReportLab, pypdf, unittest, Poppler or bundled PDF rendering tools

## Global Constraints

- Generate exactly four A4 pages.
- Use current survey objects without hard-coded response counts.
- Match the web page's navy, teal, coral, white, and light-gray visual language.
- Include source labels, generated timestamp, and page numbers.
- Continue generating a usable PDF when a preview image is unavailable.
- Do not change Google Form, Google Sheets, or Synapspot application code.

---

### Task 1: Presentation PDF contract and tests

**Files:**
- Create: `tests/test_presentation_pdf.py`
- Create: `src/presentation_pdf.py`

**Interfaces:**
- Consumes: Korean and foreign survey dictionaries with `data`, `source`, and `loaded_at` fields.
- Produces: `build_presentation_pdf(korean_survey, foreign_survey, question_preview, meetings_preview, public_url) -> bytes`.

- [ ] **Step 1: Write failing tests**

Add tests that create minimal survey fixtures and assert that the generated document has four pages and contains `이동과 동행 모집`, `공지와 생활정보 탐색`, `이동·동행 파티`, and `근거 있는 AI 질문`.

- [ ] **Step 2: Verify the tests fail**

Run: `python -m unittest tests.test_presentation_pdf -v`

Expected: import failure because `src.presentation_pdf` does not exist.

- [ ] **Step 3: Implement the PDF module**

Create page helpers for the shared header/footer, metric cards, ranking bars, explanatory panels, and preview images. Implement four pages following the approved design document.

- [ ] **Step 4: Verify tests pass**

Run: `python -m unittest tests.test_presentation_pdf -v`

Expected: all presentation PDF tests pass.

- [ ] **Step 5: Commit**

```powershell
git add src/presentation_pdf.py tests/test_presentation_pdf.py
git commit -m "feat: add presentation survey pdf"
```

### Task 2: Streamlit download integration

**Files:**
- Modify: `app.py`
- Modify: `tests/test_app_copy.py`

**Interfaces:**
- Consumes: `build_presentation_pdf()` from Task 1.
- Produces: the existing Streamlit download button backed by the redesigned PDF bytes.

- [ ] **Step 1: Write a failing integration test**

Assert that `app.py` imports `build_presentation_pdf`, passes both preview assets and the public research URL, and no longer defines the legacy `draw_pdf_*` helpers.

- [ ] **Step 2: Verify the test fails**

Run: `python -m unittest tests.test_app_copy -v`

Expected: failure because `app.py` still uses `build_current_pdf()` and legacy drawing helpers.

- [ ] **Step 3: Replace the legacy integration**

Import the new builder, remove the legacy PDF drawing block, and make the download button call the new builder with the live survey objects and existing preview image paths.

- [ ] **Step 4: Verify all tests pass**

Run: `python -m unittest discover -s tests -v`

Expected: all tests pass.

- [ ] **Step 5: Commit**

```powershell
git add app.py tests/test_app_copy.py
git commit -m "refactor: use presentation pdf download"
```

### Task 3: Render and visually verify the final PDF

**Files:**
- Create temporarily: `tmp/pdfs/presentation-report.pdf`
- Create temporarily: `tmp/pdfs/presentation-report-*.png`

**Interfaces:**
- Consumes: the completed `build_presentation_pdf()` integration.
- Produces: visual evidence that all four pages are legible and aligned.

- [ ] **Step 1: Generate a PDF from the current survey loaders**

Run a Python verification command that calls `get_public_survey()`, `get_foreign_survey()`, and `build_presentation_pdf()` and writes the result under `tmp/pdfs/`.

- [ ] **Step 2: Verify PDF structure**

Use `pypdf` to assert four pages and non-empty extracted text on every page.

- [ ] **Step 3: Render all pages to PNG**

Use the available Poppler or bundled PDF renderer to generate one PNG per page under `tmp/pdfs/`.

- [ ] **Step 4: Inspect all page images**

Confirm that headings, cards, bars, screenshots, footer metadata, and page numbers have no clipping or overlap.

- [ ] **Step 5: Run final verification and commit fixes**

Run `python -m py_compile app.py src/presentation_pdf.py`, the full unittest suite, and `git diff --check`. Commit any visual corrections before deployment.

### Task 4: Publish the preview update

**Files:**
- No additional source files unless verification finds a defect.

**Interfaces:**
- Consumes: committed feature branch.
- Produces: updated public Streamlit preview download behavior.

- [ ] **Step 1: Push the feature branch**

Run: `git push origin codex/survey-research-redesign`

- [ ] **Step 2: Verify the public preview rebuilds**

Open `https://jeju-student-survey-research-preview.streamlit.app/` and confirm the app loads with 39 total responses.

- [ ] **Step 3: Download and inspect the deployed PDF**

Confirm the downloaded document has the same four-page presentation layout and current Korean/foreign response counts.
