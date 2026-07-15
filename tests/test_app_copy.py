import ast
import re
import unittest
from pathlib import Path
from unittest.mock import patch

import app
from app import field_counter_html, intent_chart_html


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
        self.app_tree = ast.parse(self.app_text)
        self.functions = {
            node.name: node
            for node in self.app_tree.body
            if isinstance(node, ast.FunctionDef)
        }
        self.dashboard = self.functions["render_survey_dashboard"]

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
            if "render_conclusion" in names:
                milestones.append("render_conclusion")
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
                "render_conclusion",
                "render_research_findings",
                "render_product_bridge",
                "detailed_heading",
                "detailed_radio",
                "selected_detailed_renderer",
                "render_downloads",
            ],
        )

    def test_embedded_css_uses_complete_visual_contract(self) -> None:
        approved_colors = {
            "#13233D",
            "#087F72",
            "#EC6A5F",
            "#FBFCFD",
            "#D8E2E9",
            "#66768A",
            "#132E50",
        }
        css_functions = [self.functions["apply_page_style"], self.functions["chart_theme"]]
        embedded_css = "\n".join(
            str(node.value)
            for function in css_functions
            for node in ast.walk(function)
            if isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and "<style>" in node.value
        )
        active_css = "\n".join(
            [
                embedded_css,
                Path("assets/research-brief.css").read_text(encoding="utf-8"),
            ]
        )
        literal_colors = {
            match.group(0).upper()
            for match in re.finditer(
                r"#(?:[0-9a-fA-F]{8}|[0-9a-fA-F]{6}|"
                r"[0-9a-fA-F]{4}|[0-9a-fA-F]{3})(?![0-9a-fA-F])",
                active_css,
            )
        }

        self.assertTrue(active_css)
        self.assertLessEqual(literal_colors, approved_colors)
        self.assertNotRegex(
            active_css,
            r"(?i)(?:linear|radial|conic)-gradient\s*\(",
        )
        self.assertNotRegex(active_css, r"(?i)rgba\s*\(")

        for rule in re.finditer(r"(?P<selectors>[^{}]+)\{(?P<body>[^{}]*)\}", active_css):
            selectors = {item.strip() for item in rule.group("selectors").split(",")}
            for radius in re.findall(
                r"border-radius\s*:\s*([^;{}]+)", rule.group("body"), re.IGNORECASE
            ):
                value = radius.strip().lower()
                if value == "50%":
                    self.assertLessEqual(selectors, {".dot"})
                else:
                    match = re.fullmatch(r"([0-9]+(?:\.[0-9]+)?)px", value)
                    self.assertIsNotNone(match, f"unsupported radius {value!r} in {selectors}")
                    self.assertLessEqual(float(match.group(1)), 8)

    def test_rendered_chart_inline_styles_use_approved_colors(self) -> None:
        markup = intent_chart_html(
            [("긍정", 2), ("중립", 1), ("부정", 1)],
            4,
        )
        approved_colors = {
            "#132E50",
            "#13233D",
            "#FBFCFD",
            "#66768A",
            "#EC6A5F",
            "#087F72",
            "#D8E2E9",
        }
        literal_colors = {
            match.group(0).upper()
            for match in re.finditer(r"#[0-9a-fA-F]{6}", markup)
        }

        self.assertLessEqual(literal_colors, approved_colors)

    def test_page_entry_animation_only_runs_when_motion_is_allowed(self) -> None:
        apply_style = self.functions["apply_page_style"]
        stylesheet = "\n".join(
            str(node.value)
            for node in ast.walk(apply_style)
            if isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and "<style>" in node.value
        )
        motion_block = re.search(
            r"@media\s*\(prefers-reduced-motion:\s*no-preference\)\s*\{"
            r"\s*\.main\s+\.block-container\s*>\s*div\s*\{"
            r"[^{}]*\banimation\s*:[^{}]+\}\s*\}",
            stylesheet,
            re.IGNORECASE | re.DOTALL,
        )

        self.assertIsNotNone(motion_block)
        stylesheet_without_motion_block = (
            stylesheet[: motion_block.start()] + stylesheet[motion_block.end() :]
        )
        self.assertNotRegex(
            stylesheet_without_motion_block,
            r"(?is)\.main\s+\.block-container\s*>\s*div\s*\{"
            r"[^{}]*\banimation\s*:",
        )

    def test_intent_chart_uses_three_adjacent_segments_with_complete_labels(self) -> None:
        markup = intent_chart_html(
            [("긍정", 2), ("중립", 1), ("부정", 1)],
            4,
        )

        self.assertIn('class="intent-bar"', markup)
        self.assertEqual(markup.count('class="intent-segment '), 3)
        self.assertNotIn("donut", markup)
        self.assertIn('class="intent-segment positive" style="width:50.0%"', markup)
        self.assertIn('class="intent-segment neutral" style="width:25.0%"', markup)
        self.assertIn('class="intent-segment negative" style="width:25.0%"', markup)
        for expected in ["긍정", "2명 · 50.0%", "중립", "1명 · 25.0%", "부정"]:
            self.assertIn(expected, markup)

    def test_intent_chart_handles_zero_total_without_invalid_widths(self) -> None:
        markup = intent_chart_html(
            [("긍정", 0), ("중립", 0), ("부정", 0)],
            0,
        )

        self.assertEqual(markup.count('style="width:0.0%"'), 3)
        self.assertEqual(markup.count("0명 · 0.0%"), 3)
        self.assertNotRegex(markup, r"(?i)(?:nan|inf)%")
        self.assertNotIn("donut", markup)

    def test_dashboard_renders_product_bridge_exactly_once(self) -> None:
        bridge_calls = [
            node
            for node in ast.walk(self.dashboard)
            if isinstance(node, ast.Call) and call_name(node) == "render_product_bridge"
        ]

        self.assertEqual(len(bridge_calls), 1)

    def test_dashboard_runtime_places_refresh_before_conclusion_and_findings(self) -> None:
        events: list[str] = []
        context = object()
        survey = {"data": {"n": 0}, "source": "empty", "loaded_at": "-"}

        with (
            patch.object(app, "apply_page_style"),
            patch.object(app, "get_public_survey", return_value=survey),
            patch.object(app, "get_foreign_survey", return_value=survey),
            patch.object(
                app,
                "render_header",
                side_effect=lambda *_: events.append("header") or context,
            ),
            patch.object(
                app.st,
                "button",
                side_effect=lambda *_args, **_kwargs: events.append("refresh") or False,
            ),
            patch.object(
                app,
                "render_conclusion",
                side_effect=lambda *_: events.append("conclusion"),
            ),
            patch.object(
                app,
                "render_research_findings",
                side_effect=lambda *_: events.append("findings"),
            ),
            patch.object(app, "render_product_bridge"),
            patch.object(app.st, "radio", return_value="전체 요약"),
            patch.object(app, "render_overall_view"),
            patch.object(app, "render_downloads"),
            patch.object(app.st, "set_page_config"),
            patch.object(app.st, "markdown"),
        ):
            app.render_survey_dashboard()

        self.assertEqual(events, ["header", "refresh", "conclusion", "findings"])

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

    def test_overall_rank_sections_use_each_groups_own_total(self) -> None:
        overall = self.functions["render_overall_view"]
        rank_calls = [
            node
            for node in ast.walk(overall)
            if isinstance(node, ast.Call) and call_name(node) == "render_rank_section"
        ]
        binding_by_title = {
            str(call.args[0].value): (
                (call.args[2].value.id, str(call.args[2].slice.value)),
                call.args[3].id,
            )
            for call in rank_calls
            if len(call.args) == 4
            and isinstance(call.args[0], ast.Constant)
            and isinstance(call.args[2], ast.Subscript)
            and isinstance(call.args[2].value, ast.Name)
            and isinstance(call.args[2].slice, ast.Constant)
            and isinstance(call.args[3], ast.Name)
        }

        self.assertEqual(
            binding_by_title,
            {
                "한국인 핵심 불편": (("korean", "pain"), "korean_total"),
                "한국인 오픈채팅 수요": (
                    ("korean", "openchat_find"),
                    "korean_total",
                ),
                "외국인 핵심 불편": (("foreign", "pain"), "foreign_total"),
                "외국인 오픈채팅 수요": (
                    ("foreign", "openchat_find"),
                    "foreign_total",
                ),
            },
        )
        self.assertFalse(
            any(
                isinstance(node, ast.Call) and call_name(node) == "max"
                for node in ast.walk(overall)
            )
        )

    def test_overall_view_does_not_repeat_research_conclusion(self) -> None:
        overall = self.functions["render_overall_view"]
        copy = {
            str(node.value)
            for node in ast.walk(overall)
            if isinstance(node, ast.Constant) and isinstance(node.value, str)
        }

        self.assertNotIn("### 한눈에 보는 결론", copy)

    def test_detailed_navigation_keeps_four_views_and_overall_default(self) -> None:
        radio = next(
            node
            for node in ast.walk(self.dashboard)
            if isinstance(node, ast.Call) and call_name(node) == "st.radio"
        )
        options = [
            str(item.value)
            for item in radio.args[1].elts
            if isinstance(item, ast.Constant)
        ]
        horizontal = next(
            keyword.value
            for keyword in radio.keywords
            if keyword.arg == "horizontal"
        )
        index_keywords = [
            keyword.value
            for keyword in radio.keywords
            if keyword.arg == "index"
        ]

        self.assertEqual(
            options,
            ["전체 요약", "한국인 설문", "외국인 설문", "비교 요약"],
        )
        self.assertIsInstance(horizontal, ast.Constant)
        self.assertIs(horizontal.value, True)
        self.assertLessEqual(len(index_keywords), 1)
        if index_keywords:
            self.assertIsInstance(index_keywords[0], ast.Constant)
            self.assertEqual(index_keywords[0].value, 0)

        renderer_if = next(
            statement
            for statement in self.dashboard.body
            if isinstance(statement, ast.If)
            and {
                "render_korean_view",
                "render_foreign_view",
                "render_compare_view",
                "render_overall_view",
            }.issubset(statement_call_names(statement))
        )
        final_branch = renderer_if
        while len(final_branch.orelse) == 1 and isinstance(final_branch.orelse[0], ast.If):
            final_branch = final_branch.orelse[0]
        default_calls = {
            name
            for statement in final_branch.orelse
            for name in statement_call_names(statement)
        }
        self.assertIn("render_overall_view", default_calls)

    def test_detailed_navigation_wraps_without_truncating_mobile_labels(self) -> None:
        self.assertIn('div[role="radiogroup"] {', self.app_text)
        self.assertIn("flex-wrap: wrap;", self.app_text)
        self.assertIn('div[role="radiogroup"] label {', self.app_text)
        self.assertIn("min-width: max-content;", self.app_text)

    def test_detailed_renderers_keep_comments_at_five_per_page(self) -> None:
        for renderer_name in ["render_korean_view", "render_foreign_view"]:
            renderer_calls = {
                call_name(node)
                for node in ast.walk(self.functions[renderer_name])
                if isinstance(node, ast.Call)
            }
            self.assertIn("render_comments_section", renderer_calls)

        comments = self.functions["render_comments_section"]
        page_size = next(
            node.value
            for node in ast.walk(comments)
            if isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id == "page_size"
        )
        self.assertIsInstance(page_size, ast.Constant)
        self.assertEqual(page_size.value, 5)
        self.assertTrue(calls_with_text(comments, "st.markdown", "## 익명 자유 의견"))

    def test_downloads_expose_only_the_live_pdf_report(self) -> None:
        downloads = self.functions["render_downloads"]
        buttons = [
            node
            for node in ast.walk(downloads)
            if isinstance(node, ast.Call) and call_name(node) == "st.download_button"
        ]

        self.assertEqual(len(buttons), 1)
        keywords = {keyword.arg: keyword.value for keyword in buttons[0].keywords}
        self.assertIsInstance(keywords["data"], ast.Call)
        self.assertEqual(call_name(keywords["data"]), "build_current_pdf")
        self.assertEqual(keywords["mime"].value, "application/pdf")
        self.assertEqual(
            keywords["file_name"].value,
            "jeju-student-survey-live-report.pdf",
        )
        self.assertNotIn("REPORT_PNG", self.app_text)


if __name__ == "__main__":
    unittest.main()
