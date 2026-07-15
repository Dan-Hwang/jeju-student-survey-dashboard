# Final Review Fix Report

Base: `631d10d`
Branch: `codex/survey-dashboard-reset`

## Scope

- `.superpowers/sdd/final-review-fix-report.md`: RED/GREEN and final verification record
- `app.py`: approved embedded visual contract and visible render order
- `assets/research-brief.css`: comparison value styling
- `src/research_brief.py`: source states, problem-specific evidence, complete comparison, split conclusion markup
- `src/survey_dashboard.py`: fallback freshness, PII filtering, foreign information-accuracy signal
- `tests/test_app_copy.py`: embedded/inline CSS and AST/runtime order regressions
- `tests/test_research_brief.py`: source states, mixed-group findings, comparison completeness
- `tests/test_survey_dashboard.py`: fallback mtimes, empty freshness, comment privacy

## RED Evidence

The first attempt with the machine-level Python 3.14 was discarded because it failed during imports (`streamlit` and `PIL` were unavailable). All valid RED/GREEN runs below used the project venv at `C:\Users\Aiffel\Desktop\workspace\team-projects\ara-guide\.venv\Scripts\python.exe`.

1. Visual contract and visible order
   - Focused run failed because embedded CSS contained 22 unapproved colors, `linear-gradient`, `rgba`, and oversized radii.
   - The order assertion lacked `render_conclusion`, and importing `conclusion_html` failed because the split function did not exist.
2. Inline chart colors
   - `test_rendered_chart_inline_styles_use_approved_colors` failed on `#2563EB`, `#F59E0B`, and `#EF4444`.
3. Problem-specific findings and comparison completeness
   - The asymmetric findings test failed because the movement panel had only Korean metrics and the information panel had only foreign metrics.
   - The comparison test failed because top-signal counts and percentages were absent.
4. Source states, freshness, privacy, and signal completeness
   - Mixed, saved, and empty contexts all reported the old saved-data phrase.
   - Korean CSV, foreign CSV, and foreign JSON fallbacks all returned current time instead of backing-file mtimes.
   - Email, Korean/international phone, URL, handle, and explicit contact-label comments all passed through.
   - Foreign `정보 정확성 모르겠다` was dropped from report data.
5. Contact label without punctuation
   - `카톡 jeju2026` remained visible until the explicit-label pattern covered a directly following identifier.

## GREEN Evidence

- Visual/order focused run: 5 tests passed.
- Findings/comparison focused run: 5 tests passed.
- Source/freshness/privacy focused run: 8 tests passed.
- Contact privacy focused run: 2 tests passed.
- Runtime order and empty freshness focused run: 2 tests passed.
- The integration failure in the old escaping assertion was traced to intentional problem-label filtering; the assertion now verifies omission of irrelevant hostile text and escaping of rendered data-derived values.

## Final Verification

- `python -m unittest discover -s tests -v`: 44 tests passed, 0 failures.
- `python -m py_compile app.py src/survey_dashboard.py src/research_brief.py`: exit 0.
- `git diff --check`: exit 0 with Windows LF-to-CRLF conversion warnings only.
- Scoped status audit: only the files listed in this report are included in the commit.

## Concerns

- Unit tests intentionally emit Streamlit `No runtime found` cache warnings outside a Streamlit process; these do not fail tests.
- Verification uses mocked/local loader boundaries and does not contact the production Google Sheets service.
