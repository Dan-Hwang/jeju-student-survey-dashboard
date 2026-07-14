import unittest
from pathlib import Path


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

    def test_app_connects_research_to_synapspot(self) -> None:
        self.assertIn("render_research_intro", self.app_text)
        self.assertIn("product_bridge_html", self.app_text)
        self.assertIn("상세 조사 결과", self.app_text)
        self.assertNotIn("JEJU EXCHANGE SURVEY", self.app_text)

    def test_app_renders_product_preview_with_missing_asset_fallback(self) -> None:
        self.assertIn("render_product_preview", self.app_text)
        self.assertIn("synapspot-question-preview.png", self.app_text)
        self.assertIn("synapspot-meetings-preview.png", self.app_text)
        self.assertIn("미리보기 이미지를 준비 중입니다", self.app_text)


if __name__ == "__main__":
    unittest.main()
