import re
import unittest
from base64 import b64decode
from pathlib import Path
from tempfile import TemporaryDirectory

from src.research_brief import (
    build_brief_context,
    comparison_html,
    conclusion_html,
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

    def test_mixed_sources_have_partial_status(self):
        korean = survey(11, source="CSV fallback", loaded_at="2026-07-15 14:00")
        foreign = survey(16, source="Google Sheets", loaded_at="2026-07-15 15:00")

        context = build_brief_context(korean, foreign)

        self.assertFalse(context.is_live)
        self.assertEqual(context.status, "일부 실시간 · 혼합 집계")

    def test_saved_sources_have_fallback_status(self):
        korean = survey(11, source="CSV fallback", loaded_at="2026-07-15 14:00")
        foreign = survey(8, source="CSV summary", loaded_at="2026-07-14 12:00")

        context = build_brief_context(korean, foreign)

        self.assertEqual(context.status, "저장 데이터 기준 집계")
        self.assertEqual(context.loaded_at, "2026-07-15 14:00")

    def test_both_empty_sources_show_waiting_state_and_no_timestamp(self):
        korean = survey(0, source="empty", loaded_at="-")
        foreign = survey(0, source="empty", loaded_at="-")

        context = build_brief_context(korean, foreign)

        self.assertEqual(context.status, "응답 수집 대기")
        self.assertEqual(context.loaded_at, "-")
        self.assertNotIn("저장 데이터", context.status)

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
        self.assertNotIn("먼저 볼 결론", markup)

    def test_conclusion_is_separate_from_header_for_refresh_order(self):
        markup = conclusion_html(self.context)

        self.assertIn("먼저 볼 결론", markup)
        self.assertIn("이동·동행 모집", markup)

    def test_findings_show_counts_and_group_percentages(self):
        markup = findings_html(self.context)
        self.assertIn("버스 노선", markup)
        self.assertIn("3명", markup)
        self.assertIn("75.0%", markup)
        self.assertIn("교통", markup)
        self.assertIn("66.7%", markup)

    def test_findings_group_metrics_by_problem_across_both_populations(self):
        korean = survey(
            10,
            source="Google Sheets",
            loaded_at="2026-07-15 15:00",
            pain=[("버스 노선", 9), ("정보 부족", 1)],
            openchat_find=[("택시팟", 8), ("공지", 2)],
            openchat_pain=[("원하는 글 찾기 어렵다", 3)],
        )
        foreign = survey(
            4,
            source="Google Sheets",
            loaded_at="2026-07-15 15:01",
            pain=[("정보 부족", 4), ("교통", 2)],
            openchat_find=[("생활정보", 3), ("여행팟", 1)],
            openchat_pain=[("검색 기능 불편", 2)],
        )

        markup = findings_html(build_brief_context(korean, foreign))
        movement = markup.split("이동과 동행 모집", 1)[1].split("공지와 생활정보 탐색", 1)[0]
        information = markup.split("공지와 생활정보 탐색", 1)[1]

        for expected in ["한국인", "외국인", "버스 노선", "교통", "택시팟", "여행팟"]:
            self.assertIn(expected, movement)
        for excluded in ["정보 부족", "공지", "생활정보", "검색 기능 불편"]:
            self.assertNotIn(excluded, movement)
        for expected in [
            "한국인",
            "외국인",
            "정보 부족",
            "공지",
            "생활정보",
            "원하는 글 찾기 어렵다",
            "검색 기능 불편",
        ]:
            self.assertIn(expected, information)
        for excluded in ["버스 노선", "교통", "택시팟", "여행팟"]:
            self.assertNotIn(excluded, information)
        self.assertIn("9명 <small>90.0%</small>", movement)
        self.assertIn("2명 <small>50.0%</small>", movement)
        self.assertIn("4명 <small>100.0%</small>", information)

    def test_comparison_shows_top_signal_count_and_group_percentage(self):
        markup = comparison_html(self.context)

        self.assertIn("한국인 · n=4", markup)
        self.assertIn("택시팟", markup)
        self.assertIn("2명 · 50.0%", markup)
        self.assertIn("외국인 · n=3", markup)
        self.assertIn("공지", markup)
        self.assertIn("2명 · 66.7%", markup)

    def test_comparison_handles_empty_groups_without_inventing_a_signal(self):
        empty = survey(0, source="empty", loaded_at="-")

        markup = comparison_html(build_brief_context(empty, empty))

        self.assertEqual(markup.count("응답 수집 중"), 2)
        self.assertNotRegex(markup, r"[1-9][0-9]*명")

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
        self.assertNotIn("alert(1)", markup)
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
