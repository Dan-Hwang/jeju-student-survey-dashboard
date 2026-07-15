# Survey PDF Research Brief Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the live survey PDF's rigid dashboard export with a polished three-page research brief while preserving current-data generation.

**Architecture:** Move PDF drawing into `src/pdf_report.py` and keep `app.py` as the Streamlit composition layer. The PDF module consumes the existing Korean and foreign survey dictionaries, embeds bundled fonts, draws the narrative pages, and returns bytes through the unchanged `build_current_pdf` interface.

**Tech Stack:** Python, ReportLab, Pillow, pypdf, unittest, Poppler

## Global Constraints

- Keep exactly one PDF download button and the existing filename.
- Keep the PDF at three A4 pages.
- Use the same current survey objects as the web page.
- Do not expose individual response rows or identifying information.
- Preserve unrelated Streamlit behavior and styling.

---

### Task 1: Lock The PDF Story With Tests

**Files:**
- Modify: `tests/test_pdf_export.py`

**Interfaces:**
- Consumes: `app.build_current_pdf(korean_survey, foreign_survey) -> bytes`
- Produces: regression tests for page count, metadata, narrative text, embedded fonts, and product images

- [ ] Add a failing test that extracts page text and requires the research title, both problem headings, and both SynapSpot feature names.
- [ ] Add a failing test that requires at least two images on page 1 and embedded TrueType font resources.
- [ ] Run `python -m unittest tests.test_pdf_export -v` and confirm the new assertions fail against the old layout.

### Task 2: Build The Research Brief Generator

**Files:**
- Create: `src/pdf_report.py`
- Modify: `app.py`
- Create: `assets/fonts/NanumGothic-Regular.ttf`
- Create: `assets/fonts/NanumGothic-Bold.ttf`

**Interfaces:**
- Consumes: the existing survey dictionaries and the two preview image paths
- Produces: `build_current_pdf(korean_survey: dict[str, Any], foreign_survey: dict[str, Any]) -> bytes`

- [ ] Bundle Nanum Gothic regular and bold font files and register both faces.
- [ ] Implement reusable title, card, ranking, comment, footer, and image drawing helpers with fixed safe content bounds.
- [ ] Implement page 1 as the research story and product bridge.
- [ ] Implement page 2 as group comparison charts with counts in a dedicated right column.
- [ ] Implement page 3 as the evidence appendix with sanitized anonymous comments and methodology.
- [ ] Import and re-export `build_current_pdf` from `app.py`, removing the old PDF drawing implementation.
- [ ] Run `python -m unittest tests.test_pdf_export -v` and confirm the tests pass.

### Task 3: Verify Rendering And Deployment

**Files:**
- Modify only if verification exposes a defect: `src/pdf_report.py`

**Interfaces:**
- Consumes: current local survey aggregate objects
- Produces: a visually verified PDF and deployed download behavior

- [ ] Run the complete test suite with `python -m unittest discover -s tests -v`.
- [ ] Generate a PDF from current survey data and use `pdfinfo` to verify three A4 pages.
- [ ] Render all pages with `pdftoppm -png -r 150` and inspect every page for clipping, overlap, and broken glyphs.
- [ ] Commit the scoped changes, push `codex/survey-research-redesign`, reboot Streamlit Cloud, and verify the live download metadata matches the visible totals.
