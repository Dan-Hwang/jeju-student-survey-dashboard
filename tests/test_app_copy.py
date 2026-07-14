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
        self.assertIn("전체 데이터 살펴보기", self.app_text)
        self.assertNotIn("JEJU EXCHANGE SURVEY", self.app_text)

    def test_app_renders_product_preview_with_missing_asset_fallback(self) -> None:
        self.assertIn("render_product_preview", self.app_text)
        self.assertIn("synapspot-question-preview.png", self.app_text)
        self.assertIn("synapspot-meetings-preview.png", self.app_text)
        self.assertIn("미리보기 이미지를 준비 중입니다", self.app_text)

    def test_research_story_uses_intrinsic_height_html(self) -> None:
        self.assertIn("st.html(research_story_html", self.app_text)
        self.assertIn("st.html(product_bridge_html", self.app_text)

    def test_dynamic_openchat_summary_avoids_broken_particles(self) -> None:
        self.assertIn("수요가 많이 나타났어요", self.app_text)
        self.assertNotIn("을 많이 찾고 있어요", self.app_text)

    def test_app_avoids_deprecated_streamlit_rendering_apis(self) -> None:
        self.assertNotIn("streamlit.components.v1", self.app_text)
        self.assertNotIn("use_container_width", self.app_text)

    def test_download_uses_presentation_pdf_renderer(self) -> None:
        self.assertIn("from src.presentation_pdf import build_presentation_pdf", self.app_text)
        self.assertIn("question_preview=QUESTION_PREVIEW", self.app_text)
        self.assertIn("meetings_preview=MEETINGS_PREVIEW", self.app_text)
        self.assertIn("jeju-student-survey-research-preview.streamlit.app", self.app_text)
        self.assertNotIn("def build_current_pdf", self.app_text)
        self.assertNotIn("def draw_pdf_metric", self.app_text)

    def test_presentation_story_precedes_detailed_dashboard(self) -> None:
        story_index = self.app_text.index("render_research_intro")
        preview_index = self.app_text.index("render_product_preview")
        detail_index = self.app_text.index("전체 데이터 살펴보기")

        self.assertLess(story_index, preview_index)
        self.assertLess(preview_index, detail_index)

    def test_page_style_supports_full_width_presentation(self) -> None:
        self.assertIn("max-width: 1180px", self.app_text)
        self.assertIn("scroll-margin-top", self.app_text)


if __name__ == "__main__":
    unittest.main()
