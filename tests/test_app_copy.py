import unittest
from pathlib import Path


class AppCopyTest(unittest.TestCase):
    def setUp(self) -> None:
        self.app_text = Path("app.py").read_text(encoding="utf-8")

    def test_app_presents_single_product_flow(self) -> None:
        self.assertIn("제주대학교 교류학생 생활 플랫폼 수요조사", self.app_text)
        self.assertIn("render_survey_dashboard()", self.app_text)
        self.assertNotIn("st.tabs(", self.app_text)
        self.assertNotIn("st.sidebar.radio", self.app_text)

    def test_internal_experiment_copy_is_not_visible_in_app(self) -> None:
        hidden_terms = ["생활도우미", "예시 질문", "공식 출처", "개발자 실험실", "개발 메모", "모집글 분류", "confidence", "mock"]
        for term in hidden_terms:
            self.assertNotIn(term, self.app_text)


if __name__ == "__main__":
    unittest.main()
