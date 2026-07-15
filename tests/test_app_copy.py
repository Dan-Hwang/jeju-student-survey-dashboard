import ast
import unittest
from pathlib import Path

from app import field_counter_html


def call_name(call: ast.Call) -> str:
    parts: list[str] = []
    node = call.func
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
    return ".".join(reversed(parts))


def statement_call_names(statement: ast.stmt) -> set[str]:
    return {
        call_name(node)
        for node in ast.walk(statement)
        if isinstance(node, ast.Call)
    }


def calls_with_text(statement: ast.stmt, name: str, text: str) -> bool:
    return any(
        call_name(node) == name
        and node.args
        and isinstance(node.args[0], ast.Constant)
        and node.args[0].value == text
        for node in ast.walk(statement)
        if isinstance(node, ast.Call)
    )


class AppCopyTest(unittest.TestCase):
    def setUp(self) -> None:
        self.app_text = Path("app.py").read_text(encoding="utf-8")
        app_tree = ast.parse(self.app_text)
        self.dashboard = next(
            node
            for node in app_tree.body
            if isinstance(node, ast.FunctionDef)
            and node.name == "render_survey_dashboard"
        )

    def test_research_brief_has_approved_identity(self) -> None:
        self.assertIn("교류학생의 이동과 정보 탐색", self.app_text)

    def test_dashboard_orchestrates_evidence_first_runtime_flow(self) -> None:
        detail_renderers = {
            "render_korean_view",
            "render_foreign_view",
            "render_compare_view",
            "render_overall_view",
        }
        milestones: list[str] = []

        for statement in self.dashboard.body:
            names = statement_call_names(statement)
            if "render_header" in names:
                milestones.append("render_header")
            if (
                isinstance(statement, ast.If)
                and {
                    "st.button",
                    "st.cache_data.clear",
                    "st.rerun",
                }.issubset(names)
            ):
                milestones.append("refresh")
            if "render_research_findings" in names:
                milestones.append("render_research_findings")
            if "render_product_bridge" in names:
                milestones.append("render_product_bridge")
            if calls_with_text(statement, "st.markdown", "## 상세 조사 결과"):
                milestones.append("detailed_heading")
            if "st.radio" in names:
                milestones.append("detailed_radio")
            if isinstance(statement, ast.If) and detail_renderers.issubset(names):
                milestones.append("selected_detailed_renderer")
            if "render_downloads" in names:
                milestones.append("render_downloads")

        self.assertEqual(
            milestones,
            [
                "render_header",
                "refresh",
                "render_research_findings",
                "render_product_bridge",
                "detailed_heading",
                "detailed_radio",
                "selected_detailed_renderer",
                "render_downloads",
            ],
        )

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
