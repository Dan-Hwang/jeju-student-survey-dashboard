import unittest
from pathlib import Path

from app import field_counter_html


class AppCopyTest(unittest.TestCase):
    def setUp(self) -> None:
        self.app_text = Path("app.py").read_text(encoding="utf-8")

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
