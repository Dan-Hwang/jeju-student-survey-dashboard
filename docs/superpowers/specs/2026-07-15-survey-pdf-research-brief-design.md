# Survey PDF Research Brief Design

## Goal

Turn the live survey PDF into a presentation-ready research brief that uses the same current Korean and foreign survey aggregates as the web app.

## Scope

- Keep the existing Google Sheets loading, fallback behavior, download button, privacy boundary, and three-page PDF format.
- Replace the fixed-coordinate dashboard copy with a deliberate A4 narrative.
- Bundle an open Korean font so local and Streamlit Cloud rendering match.
- Include the two existing SynapSpot mobile preview images on the first page.

## Page Structure

### Page 1: Research Story

- Title: `교류학생의 이동과 정보 탐색은 어디서 막혔을까?`
- Live totals for all respondents, Korean respondents, and foreign respondents.
- Two evidence panels: movement/companion recruitment and trusted information discovery.
- A short statement explaining that the survey prioritized problems rather than proving product effectiveness.
- SynapSpot movement-party and sourced-information mobile previews.

### Page 2: Group Comparison

- Korean and foreign sample sizes and their top needs.
- Four consistently scaled ranking charts: inconvenience, open-chat demand, desired activities, and open-chat friction.
- Counts and within-group percentages must remain readable without overlapping bars.

### Page 3: Evidence Appendix

- Korean and foreign headline metrics.
- Up to five anonymous comments from each group after removing unsupported symbols.
- Data source, refresh time, multiple-response note, and privacy note.

## Visual Direction

- White A4 background with navy text, teal evidence, and coral product accents.
- Use Nanum Gothic regular and bold fonts embedded in the PDF.
- Use clear section hierarchy, compact cards, horizontal bars, page numbers, and stable margins.
- Avoid decorative filler and reserve space for research evidence and product linkage.

## Data And Privacy

- `build_current_pdf(korean_survey, foreign_survey)` remains the public interface.
- The PDF is generated from the exact survey objects used by the page at download time.
- No names, contact details, source rows, or open-chat messages are included.
- Metadata continues to expose only totals and source labels for automated verification.

## Acceptance Criteria

- The PDF has exactly three pages and current totals match its metadata and visible text.
- Page 1 contains both SynapSpot preview images and the two problem statements.
- Korean text renders with embedded fonts and normal spacing on Windows and Streamlit Cloud.
- Bar values never overlap their bars or labels.
- Empty rankings and comments render a clear empty state.
- Rendered PNG inspection shows no clipping, overlap, broken glyphs, or excessive blank space.
