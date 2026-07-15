import re
import unittest
from base64 import b64decode
from pathlib import Path
from tempfile import TemporaryDirectory

from src.research_brief import (
    build_brief_context,
    comparison_html,
    findings_html,
    image_data_uri,
    intro_html,
    product_bridge_html,
    ranked_metrics,
)


VALID_TINY_PNG = b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk"
    "+A8AAQUBAScY42YAAAAASUVORK5CYII="
)


def survey(total: int, *, source: str, loaded_at: str, pain=None, openchat_find=None, openchat_pain=None):
    return {
        "data": {
            "n": total,
            "pain": pain or [],
            "activity": [],
            "openchat_find": openchat_find or [],
            "openchat_pain": openchat_pain or [],
            "intent": [("긍정", 0), ("중립", 0), ("부정", 0)],
            "comments": [],
        },
        "source": source,
        "loaded_at": loaded_at,
        "error": "",
    }


class ResearchBriefContextTest(unittest.TestCase):
    def test_combines_totals_and_marks_both_sheets_live(self):
        korean = survey(23, source="Google Sheets", loaded_at="2026-07-15 15:00")
        foreign = survey(16, source="Google Sheets", loaded_at="2026-07-15 15:01")

        context = build_brief_context(korean, foreign)

        self.assertEqual(context.total, 39)
        self.assertEqual(context.korean.total, 23)
        self.assertEqual(context.foreign.total, 16)
        self.assertEqual(context.status, "Google Sheets 실시간 집계")
        self.assertTrue(context.is_live)
        self.assertEqual(context.loaded_at, "2026-07-15 15:01")

    def test_uses_each_group_total_for_percentages(self):
        korean = ranked_metrics([("버스 노선", 11)], 23)
        foreign = ranked_metrics([("교통", 11)], 16)

        self.assertEqual(korean[0].percent, "47.8%")
        self.assertEqual(foreign[0].percent, "68.8%")

    def test_any_fallback_source_disables_live_status(self):
        korean = survey(11, source="CSV fallback", loaded_at="2026-07-15 14:00")
        foreign = survey(16, source="Google Sheets", loaded_at="2026-07-15 15:00")

        context = build_brief_context(korean, foreign)

        self.assertFalse(context.is_live)
        self.assertEqual(context.status, "저장 데이터 포함 집계")

    def test_zero_total_returns_zero_percent(self):
        metrics = ranked_metrics([("교통", 0)], 0)
        self.assertEqual(metrics[0].percent, "0%")


class ResearchBriefHtmlTest(unittest.TestCase):
    def setUp(self):
        self.korean = survey(
            4,
            source="Google Sheets",
            loaded_at="2026-07-15 15:00",
            pain=[("버스 노선", 3)],
            openchat_find=[("택시팟", 2)],
            openchat_pain=[("원하는 글 찾기 어렵다", 2)],
        )
        self.foreign = survey(
            3,
            source="Google Sheets",
            loaded_at="2026-07-15 15:01",
            pain=[("교통", 2)],
            openchat_find=[("공지", 2)],
            openchat_pain=[("글이 너무 많다", 1)],
        )
        self.context = build_brief_context(self.korean, self.foreign)

    def test_intro_uses_context_instead_of_hardcoded_production_count(self):
        markup = intro_html(self.context)
        self.assertIn("7명", markup)
        self.assertIn("4명", markup)
        self.assertIn("3명", markup)
        self.assertNotIn("39명", markup)
        self.assertIn('class="research-hero"', markup)

    def test_findings_show_counts_and_group_percentages(self):
        markup = findings_html(self.context)
        self.assertIn("버스 노선", markup)
        self.assertIn("3명", markup)
        self.assertIn("75.0%", markup)
        self.assertIn("교통", markup)
        self.assertIn("66.7%", markup)

    def test_comparison_names_both_groups_and_denominators(self):
        markup = comparison_html(self.context)
        self.assertIn("한국인 · n=4", markup)
        self.assertIn("외국인 · n=3", markup)

    def test_data_derived_labels_are_html_escaped(self):
        korean = survey(
            1,
            source="<b>source</b>",
            loaded_at="<time>",
            pain=[("<script>alert(1)</script>", 1)],
            openchat_find=[("<strong>택시팟</strong>", 1)],
        )
        context = build_brief_context(korean, self.foreign)

        markup = intro_html(context) + findings_html(context) + comparison_html(context)

        self.assertNotIn("<script>", markup)
        self.assertNotIn("<strong>택시팟</strong>", markup)
        self.assertNotIn("<b>source</b>", markup)
        self.assertNotIn("<time>", markup)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", markup)
        self.assertIn("&lt;strong&gt;택시팟&lt;/strong&gt;", markup)
        self.assertIn("&lt;b&gt;source&lt;/b&gt;", markup)
        self.assertIn("&lt;time&gt;", markup)


class ProductBridgeTest(unittest.TestCase):
    def setUp(self):
        korean = survey(4, source="Google Sheets", loaded_at="2026-07-15 15:00")
        foreign = survey(3, source="Google Sheets", loaded_at="2026-07-15 15:01")
        self.context = build_brief_context(korean, foreign)

    def test_png_is_encoded_as_data_uri(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "screen.png"
            path.write_bytes(VALID_TINY_PNG)

            uri = image_data_uri(path)

        self.assertTrue(uri.startswith("data:image/png;base64,"))
        self.assertEqual(b64decode(uri.partition(",")[2]), VALID_TINY_PNG)

    def test_non_png_path_is_not_embedded(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "screen.jpg"
            path.write_bytes(b"not-a-png")

            self.assertEqual(image_data_uri(path), "")

    def test_missing_images_keep_feature_copy_without_broken_image(self):
        markup = product_bridge_html(
            self.context, Path("missing-a.png"), Path("missing-b.png")
        )

        self.assertIn("이동·동행 파티", markup)
        self.assertIn("근거 있는 정보 탐색", markup)
        self.assertNotIn("<img", markup)

    def test_corrupt_png_keeps_feature_copy_without_broken_image(self):
        with TemporaryDirectory() as directory:
            corrupt = Path(directory) / "corrupt.png"
            corrupt.write_bytes(VALID_TINY_PNG[:20])

            markup = product_bridge_html(
                self.context, corrupt, Path(directory) / "missing.png"
            )
            uri = image_data_uri(corrupt)

        self.assertEqual(uri, "")
        self.assertIn("이동·동행 파티", markup)
        self.assertIn("근거 있는 정보 탐색", markup)
        self.assertNotIn("<img", markup)

    def test_bridge_is_rendered_once_with_restrained_research_claim(self):
        with TemporaryDirectory() as directory:
            meetings = Path(directory) / "meetings.png"
            question = Path(directory) / "question.png"
            meetings.write_bytes(VALID_TINY_PNG)
            question.write_bytes(VALID_TINY_PNG)

            markup = product_bridge_html(self.context, meetings, question)

        self.assertEqual(markup.count('class="research-product-bridge"'), 1)
        self.assertEqual(markup.count("<img"), 2)
        self.assertIn("문제의 우선순위를 정하는 근거", markup)
        self.assertIn("기능의 효과를 입증한 것이 아니라", markup)

    def test_no_data_omits_product_bridge(self):
        korean = survey(0, source="CSV", loaded_at="2026-07-15 15:00")
        foreign = survey(0, source="CSV", loaded_at="2026-07-15 15:01")
        context = build_brief_context(korean, foreign)

        self.assertEqual(
            product_bridge_html(context, Path("missing-a.png"), Path("missing-b.png")),
            "",
        )


class ResearchBriefCssTest(unittest.TestCase):
    def test_korean_heading_wrap_is_targeted_and_overflow_safe(self):
        stylesheet = (
            Path(__file__).resolve().parents[1] / "assets" / "research-brief.css"
        ).read_text(encoding="utf-8")
        rules = [
            (match.group("selectors").strip(), match.group("body"))
            for match in re.finditer(
                r"(?P<selectors>[^{}]+)\{(?P<body>[^{}]*)\}",
                stylesheet,
            )
            if re.search(r"\b(?:word-break|overflow-wrap)\s*:", match.group("body"))
        ]

        self.assertEqual(len(rules), 1)
        selectors, declarations = rules[0]
        self.assertEqual(
            {selector.strip() for selector in selectors.split(",")},
            {
                ".research-hero h1",
                ".research-section h2",
                ".research-product-bridge h2",
            },
        )
        self.assertRegex(declarations, r"\bword-break\s*:\s*keep-all\s*;")
        self.assertRegex(declarations, r"\boverflow-wrap\s*:\s*anywhere\s*;")

    def test_stylesheet_uses_only_the_approved_palette(self):
        stylesheet = (
            Path(__file__).resolve().parents[1] / "assets" / "research-brief.css"
        ).read_text(encoding="utf-8")
        approved_colors = {
            "#13233D",
            "#087F72",
            "#EC6A5F",
            "#FBFCFD",
            "#D8E2E9",
            "#66768A",
            "#132E50",
        }
        approved_tokens = {
            "navy",
            "teal",
            "coral",
            "bg",
            "line",
            "muted",
            "bridge",
        }

        literal_colors = {
            match.group(0).upper()
            for match in re.finditer(
                r"#(?:[0-9a-fA-F]{8}|[0-9a-fA-F]{6}|"
                r"[0-9a-fA-F]{4}|[0-9a-fA-F]{3})(?![0-9a-fA-F])",
                stylesheet,
            )
        }
        self.assertEqual(literal_colors, approved_colors)

        declaration_pattern = re.compile(
            r"(?P<property>background(?:-color)?|color|"
            r"border(?:-(?:top|right|bottom|left))?(?:-color)?|"
            r"(?:box|text)-shadow|outline(?:-color)?|fill|stroke|"
            r"(?:accent|caret)-color|column-rule(?:-color)?|"
            r"text-decoration(?:-color)?)"
            r"\s*:\s*(?P<value>[^;{}]+)",
            re.IGNORECASE,
        )
        token_pattern = re.compile(
            r"var\(--research-(?:" + "|".join(sorted(approved_tokens)) + r")\)"
        )
        allowed_non_color_words = {"inset", "none", "px", "solid"}

        for declaration in declaration_pattern.finditer(stylesheet):
            value = declaration.group("value").strip()
            if value == "0":
                continue
            self.assertRegex(value, token_pattern)
            value_without_tokens = token_pattern.sub("", value)
            remaining_words = set(re.findall(r"[A-Za-z]+", value_without_tokens))
            self.assertLessEqual(remaining_words, allowed_non_color_words)

    def test_stylesheet_limits_radii_and_omits_hover_selectors(self):
        stylesheet = (
            Path(__file__).resolve().parents[1] / "assets" / "research-brief.css"
        ).read_text(encoding="utf-8")
        radii = [
            float(value)
            for value in re.findall(
                r"border-radius\s*:\s*([0-9]+(?:\.[0-9]+)?)px",
                stylesheet,
                flags=re.IGNORECASE,
            )
        ]

        self.assertTrue(radii)
        self.assertLessEqual(max(radii), 8)
        self.assertNotRegex(stylesheet, r"(?i):hover\b")
