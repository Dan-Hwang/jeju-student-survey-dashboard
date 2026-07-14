# Survey Research Page Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 기존 Google Sheets 자동 집계와 PDF 기능을 유지하면서, 수요조사 결과가 시냅스팟의 AI 질문 및 파티 기능으로 자연스럽게 이어지는 반응형 공개 리서치 페이지를 만든다.

**Architecture:** `src/survey_dashboard.py`는 데이터 수집과 집계를 계속 담당하고, 새 `src/research_page.py`는 집계 객체를 받아 리서치 헤더·핵심 지표·문제 발견·기능 연결 HTML을 만드는 순수 함수만 담당한다. `app.py`는 Streamlit 페이지 구성, 상세 통계, 익명 의견, PDF 다운로드를 조합하며 기존 데이터와 PDF 객체를 그대로 공유한다.

**Tech Stack:** Python 3.12+, Streamlit 1.36+, HTML/CSS, ReportLab, unittest

## Global Constraints

- Google Sheets 실시간 집계, CSV 대체 경로, 익명 의견, PDF 생성 기능을 유지한다.
- `synapspot` 저장소는 읽기 전용 참고 대상으로 사용한다.
- 설문이 기능 효과를 검증한 것처럼 표현하지 않고, 조사 결과와 제품 해석을 구분한다.
- 모바일에서는 핵심 영역을 한 열로 쌓고 데스크톱에서만 비교 영역을 2열로 배치한다.
- 화면과 PDF는 동일한 `korean_survey`, `foreign_survey` 객체를 사용한다.
- 개인 식별 정보와 원본 응답 행은 화면과 PDF에 노출하지 않는다.

---

### Task 1: 리서치 뷰 모델과 순수 HTML 렌더러

**Files:**
- Create: `src/research_page.py`
- Create: `tests/test_research_page.py`

**Interfaces:**
- Consumes: `korean_survey: dict[str, object]`, `foreign_survey: dict[str, object]`, 기존 `pct(value: int, total: int) -> str`
- Produces: `build_research_view_model(korean_survey, foreign_survey) -> dict[str, object]`, `research_story_html(view_model) -> str`, `product_bridge_html(view_model) -> str`

- [ ] **Step 1: 핵심 데이터 계산 테스트 작성**

```python
import unittest

from src.research_page import build_research_view_model


class ResearchPageTest(unittest.TestCase):
    def test_builds_live_summary_without_hard_coded_counts(self) -> None:
        korean = {
            "data": {
                "n": 19,
                "pain": [("버스 노선", 10)],
                "openchat_find": [("택시팟", 9)],
                "intent": [("긍정", 15), ("중립", 3), ("부정", 1)],
            },
            "loaded_at": "2026-07-14 10:00",
            "source": "Google Sheets",
        }
        foreign = {
            "data": {
                "n": 16,
                "pain": [("교통", 11)],
                "openchat_find": [("공지", 9)],
                "intent": [("긍정", 14), ("중립", 1), ("부정", 1)],
            },
            "loaded_at": "2026-07-14 10:01",
            "source": "Google Sheets",
        }

        result = build_research_view_model(korean, foreign)

        self.assertEqual(result["total"], 35)
        self.assertEqual(result["korean_top_pain"], ("버스 노선", 10))
        self.assertEqual(result["foreign_top_find"], ("공지", 9))
        self.assertEqual(result["positive_total"], 29)
```

- [ ] **Step 2: 테스트 실패 확인**

Run: `python -m unittest tests.test_research_page -v`

Expected: `ModuleNotFoundError: No module named 'src.research_page'`

- [ ] **Step 3: 최소 뷰 모델 구현**

```python
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
    return {
        "total": korean_total + foreign_total,
        "korean_total": korean_total,
        "foreign_total": foreign_total,
        "korean_top_pain": _top(korean["pain"]),
        "foreign_top_pain": _top(foreign["pain"]),
        "korean_top_find": _top(korean["openchat_find"]),
        "foreign_top_find": _top(foreign["openchat_find"]),
        "korean_positive": korean_positive,
        "foreign_positive": foreign_positive,
        "positive_total": korean_positive + foreign_positive,
        "positive_pct": pct(korean_positive + foreign_positive, korean_total + foreign_total),
        "loaded_at": str(korean_survey.get("loaded_at", "-")),
    }
```

- [ ] **Step 4: HTML 안전성과 핵심 카피 테스트 추가**

```python
from src.research_page import product_bridge_html, research_story_html


def test_story_escapes_sheet_labels(self) -> None:
    model = {
        "total": 1,
        "korean_total": 1,
        "foreign_total": 0,
        "korean_top_pain": ("<script>alert(1)</script>", 1),
        "foreign_top_pain": ("-", 0),
        "korean_top_find": ("택시팟", 1),
        "foreign_top_find": ("-", 0),
        "positive_total": 1,
        "positive_pct": "100.0%",
        "loaded_at": "2026-07-14 10:00",
    }
    html = research_story_html(model)
    self.assertNotIn("<script>", html)
    self.assertIn("&lt;script&gt;", html)


def test_bridge_names_actual_synapspot_flows(self) -> None:
    html = product_bridge_html({})
    self.assertIn("AI 질문", html)
    self.assertIn("파티", html)
    self.assertIn("출처", html)
    self.assertIn("신청", html)
```

- [ ] **Step 5: 반응형 HTML 렌더러 구현**

`src/research_page.py`에 아래 구조를 반환하는 함수를 추가한다.

```python
def research_story_html(model: dict[str, object]) -> str:
    korean_pain, korean_pain_count = model["korean_top_pain"]
    foreign_pain, foreign_pain_count = model["foreign_top_pain"]
    return f"""
<section class="research-story">
  <header class="research-hero">
    <p class="eyebrow">JEJU EXCHANGE STUDENT RESEARCH</p>
    <h1>교류학생의 제주 생활,<br>무엇이 가장 불편했을까?</h1>
    <p>한국인·외국인 교류학생의 이동, 동행 모집, 생활정보 탐색 경험을 조사했습니다.</p>
  </header>
  <div class="metric-grid">
    <article><span>전체 응답</span><strong>{int(model['total'])}명</strong></article>
    <article><span>한국인 핵심 불편</span><strong>{escape(str(korean_pain))}</strong><small>{int(korean_pain_count)}명</small></article>
    <article><span>외국인 핵심 불편</span><strong>{escape(str(foreign_pain))}</strong><small>{int(foreign_pain_count)}명</small></article>
    <article><span>서비스 긍정 의향</span><strong>{escape(str(model['positive_pct']))}</strong></article>
  </div>
</section>
"""


def product_bridge_html(model: dict[str, object]) -> str:
    return """
<section class="bridge-section">
  <div class="section-heading"><span>FROM RESEARCH TO PRODUCT</span><h2>조사 결과를 실제 행동으로 연결했습니다</h2></div>
  <div class="bridge-grid">
    <article><span>01</span><h3>이동·동행 수요</h3><p>파티를 찾고 만들고, 신청·승인 후 채팅으로 약속을 조율합니다.</p></article>
    <article><span>02</span><h3>공지·생활정보 탐색</h3><p>AI 질문으로 커뮤니티 근거를 찾고 출처와 신뢰도를 함께 확인합니다.</p></article>
  </div>
</section>
"""
```

CSS는 같은 모듈의 `research_page_css() -> str`에 두고 다음 선택자를 포함한다: `.research-hero`, `.metric-grid`, `.problem-grid`, `.bridge-grid`, `.product-preview`, `@media (max-width: 680px)`. 카드 반경은 `8px`, 모바일 그리드는 `grid-template-columns: 1fr`로 고정한다.

- [ ] **Step 6: 단위 테스트 통과 확인**

Run: `python -m unittest tests.test_research_page -v`

Expected: 3 tests, all `OK`

- [ ] **Step 7: 첫 구현 커밋**

```powershell
git add src/research_page.py tests/test_research_page.py
git commit -m "feat: add survey research story components"
```

### Task 2: Streamlit 공개 리서치 흐름 연결

**Files:**
- Modify: `app.py`
- Modify: `tests/test_app_copy.py`

**Interfaces:**
- Consumes: Task 1의 `build_research_view_model`, `research_page_css`, `research_story_html`, `product_bridge_html`
- Produces: `render_research_intro(korean_survey, foreign_survey) -> None`, 발표용 첫 화면과 기존 상세 통계 흐름

- [ ] **Step 1: 새 정보 구조에 대한 실패 테스트 작성**

```python
def test_app_connects_research_to_synapspot(self) -> None:
    self.assertIn("render_research_intro", self.app_text)
    self.assertIn("product_bridge_html", self.app_text)
    self.assertIn("상세 조사 결과", self.app_text)
    self.assertNotIn("JEJU EXCHANGE SURVEY", self.app_text)
```

- [ ] **Step 2: 테스트 실패 확인**

Run: `python -m unittest tests.test_app_copy.AppCopyTest.test_app_connects_research_to_synapspot -v`

Expected: FAIL because `render_research_intro` is absent.

- [ ] **Step 3: 리서치 인트로 렌더링 연결**

`app.py`에서 새 모듈을 가져온다.

```python
from src.research_page import (
    build_research_view_model,
    product_bridge_html,
    research_page_css,
    research_story_html,
)
```

`render_research_intro`를 추가한다.

```python
def render_research_intro(korean_survey: dict[str, object], foreign_survey: dict[str, object]) -> None:
    model = build_research_view_model(korean_survey, foreign_survey)
    st.markdown(research_page_css(), unsafe_allow_html=True)
    render_html(research_story_html(model), 650)
    render_html(product_bridge_html(model), 720)
```

`render_survey_dashboard()`의 순서를 다음으로 변경한다.

```python
render_research_intro(korean_survey, foreign_survey)
render_data_status(korean_survey, foreign_survey)
st.markdown("## 상세 조사 결과")
selected_view = st.radio(...)
...
render_downloads(korean_survey, foreign_survey)
```

기존 `render_header()`는 데이터 오류 및 소스 안내만 담당하는 `render_data_status()`로 축소한다. 데이터 오류가 없으면 갱신 시각과 데이터 소스를 한 줄로 표시한다.

- [ ] **Step 4: 상세 통계의 시각 우선순위 조정**

`apply_page_style()`에서 다음을 반영한다.

```css
.main .block-container {
    max-width: 1120px;
    padding: 1.25rem 1rem 4rem;
}

div[data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: 8px;
    box-shadow: 0 8px 24px rgba(15, 23, 42, 0.05);
}

@media (max-width: 680px) {
    .main .block-container { padding: 0.75rem 0.75rem 3.5rem; }
}
```

상세 통계의 기존 차트는 유지하되 카드 반경을 `8px`로 통일하고, 제목 크기는 첫 리서치 헤더보다 작게 유지한다.

- [ ] **Step 5: 전체 테스트와 문법 검사**

Run: `python -m py_compile app.py src/research_page.py src/survey_dashboard.py`

Expected: exit code 0.

Run: `python -m unittest discover -s tests -v`

Expected: all tests `OK`.

- [ ] **Step 6: Streamlit 연결 커밋**

```powershell
git add app.py tests/test_app_copy.py
git commit -m "feat: reshape survey dashboard as research story"
```

### Task 3: 실제 시냅스팟 기능 미리보기

**Files:**
- Create: `assets/synapspot-question-preview.png`
- Create: `assets/synapspot-meetings-preview.png`
- Modify: `src/research_page.py`
- Modify: `app.py`
- Modify: `tests/test_research_page.py`

**Interfaces:**
- Consumes: synapspot의 실제 `QuestionScreen`과 `MeetingsScreen`, Task 1 뷰 모델
- Produces: `render_product_preview() -> None`, 이미지 누락 시에도 동작하는 미리보기 영역

- [ ] **Step 1: 이미지 자산 계약 테스트 작성**

```python
from pathlib import Path


def test_product_preview_assets_exist(self) -> None:
    self.assertTrue(Path("assets/synapspot-question-preview.png").is_file())
    self.assertTrue(Path("assets/synapspot-meetings-preview.png").is_file())
```

- [ ] **Step 2: synapspot 로컬 화면 실행**

Run from `C:\Users\Aiffel\Desktop\workspace\team-projects\synapspot`:

```powershell
npm --workspace apps/web run dev
```

Expected: Next.js web server starts on `http://127.0.0.1:3000` without changing the synapspot worktree.

- [ ] **Step 3: 모바일 화면 캡처**

브라우저 뷰포트를 `390x844`로 두고 질문 화면과 파티 화면을 각각 캡처한다. 캡처에는 브라우저 UI, 개인정보, 관리 코드, 환경변수, API 키를 포함하지 않는다. 결과를 다음 경로에 저장한다.

```text
assets/synapspot-question-preview.png
assets/synapspot-meetings-preview.png
```

- [ ] **Step 4: 미리보기 렌더링 구현**

`app.py`에 아래 함수를 추가한다.

```python
def render_product_preview() -> None:
    st.markdown("## 시냅스팟에서는 이렇게 해결합니다")
    left, right = st.columns(2)
    with left:
        st.image("assets/synapspot-question-preview.png", use_container_width=True)
        st.markdown("**근거 있는 AI 질문**")
        st.caption("답변과 함께 출처·신뢰도를 확인합니다.")
    with right:
        st.image("assets/synapspot-meetings-preview.png", use_container_width=True)
        st.markdown("**이동·동행 파티**")
        st.caption("모임을 찾고 만들고 신청 상태를 관리합니다.")
```

두 파일 중 하나라도 없으면 `st.image()` 대신 기능 설명 박스를 표시하도록 `Path.exists()` 분기를 둔다.

- [ ] **Step 5: 이미지와 미리보기 테스트**

Run: `python -m unittest tests.test_research_page -v`

Expected: all tests `OK`.

- [ ] **Step 6: 미리보기 커밋**

```powershell
git add assets/synapspot-question-preview.png assets/synapspot-meetings-preview.png src/research_page.py app.py tests/test_research_page.py
git commit -m "feat: add synapspot product preview"
```

### Task 4: 반응형·데이터·PDF 최종 검증

**Files:**
- Modify: `app.py` only if verification exposes a layout defect
- Modify: `src/research_page.py` only if verification exposes a layout defect

**Interfaces:**
- Consumes: 완성된 Streamlit 앱과 현재 설문 데이터
- Produces: 모바일·데스크톱·PDF가 동일한 최신 데이터 기준으로 동작하는 검증 결과

- [ ] **Step 1: 로컬 Streamlit 실행**

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501
```

Expected: `http://127.0.0.1:8501`에서 앱이 열리고 Python 예외가 없다.

- [ ] **Step 2: 데스크톱 화면 검증**

브라우저 뷰포트 `1440x1000`에서 다음을 확인한다.

- 리서치 목적, 전체 응답, 두 핵심 문제가 첫 화면에 보인다.
- 문제와 기능 연결이 2열로 보인다.
- 한국인·외국인 상세 탭과 PDF 다운로드가 동작한다.
- 원본 응답 행과 개인 식별 정보가 보이지 않는다.

- [ ] **Step 3: 모바일 화면 검증**

브라우저 뷰포트 `390x844`에서 다음을 확인한다.

- 가로 스크롤이 없다.
- 핵심 카드, 기능 연결, 시냅스팟 미리보기가 한 열로 쌓인다.
- 긴 항목명이 카드와 막대그래프 밖으로 넘치지 않는다.
- 익명 자유 의견 페이지 이동 버튼을 누를 수 있다.

- [ ] **Step 4: 최신 데이터와 PDF 일치 검증**

```powershell
.\.venv\Scripts\python.exe -c "from app import build_current_pdf; from src.survey_dashboard import get_public_survey,get_foreign_survey; k=get_public_survey(); f=get_foreign_survey(); b=build_current_pdf(k,f); print(k['data']['n'], f['data']['n'], len(b))"
```

Expected: 한국인·외국인 현재 응답 수가 출력되고 PDF byte length가 0보다 크다. 화면의 응답 수와 출력된 두 수가 일치한다.

- [ ] **Step 5: 전체 회귀 검사**

Run: `python -m py_compile app.py src/research_page.py src/survey_dashboard.py`

Expected: exit code 0.

Run: `python -m unittest discover -s tests -v`

Expected: all tests `OK`.

- [ ] **Step 6: 검증 중 수정이 있었다면 커밋**

```powershell
git add app.py src/research_page.py
git commit -m "fix: polish responsive survey research layout"
```

