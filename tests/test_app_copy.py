import unittest
from pathlib import Path

from app import field_counter_html


class AppCopyTest(unittest.TestCase):
    def setUp(self) -> None:
        self.app_text = Path("app.py").read_text(encoding="utf-8")

    def test_app_presents_single_product_flow(self) -> None:
        self.assertIn("교류학생 생활 플랫폼", self.app_text)
        self.assertIn("수요조사", self.app_text)
        self.assertIn("render_survey_dashboard()", self.app_text)
        self.assertNotIn("st.tabs(", self.app_text)
        self.assertNotIn("st.sidebar.radio", self.app_text)

    def test_internal_experiment_copy_is_not_visible_in_app(self) -> None:
        hidden_terms = ["생활도우미", "예시 질문", "공식 출처", "개발자 실험실", "개발 메모", "모집글 분류", "confidence", "mock"]
        for term in hidden_terms:
            self.assertNotIn(term, self.app_text)

    def test_mobile_field_counter_prioritizes_live_response_counts(self) -> None:
        self.assertIn("def field_counter_html", self.app_text)
        self.assertIn('class="field-counter"', self.app_text)
        self.assertIn('class="field-total"', self.app_text)
        self.assertIn('class="field-groups"', self.app_text)
        self.assertIn("korean_total + foreign_total", self.app_text)
        self.assertIn("총 응답", self.app_text)
        self.assertIn("한국인", self.app_text)
        self.assertIn("외국인", self.app_text)
        self.assertIn("실시간 집계", self.app_text)

    def test_field_counter_combines_live_korean_and_foreign_counts(self) -> None:
        korean = {"data": {"n": 23}, "source": "Google Sheets", "loaded_at": "2026-07-15 15:00"}
        foreign = {"data": {"n": 16}, "source": "Google Sheets", "loaded_at": "2026-07-15 15:00"}

        markup = field_counter_html(korean, foreign)

        self.assertIn("39명", markup)
        self.assertIn("23명", markup)
        self.assertIn("16명", markup)
        self.assertIn("Google Sheets 실시간 집계", markup)


if __name__ == "__main__":
    unittest.main()
