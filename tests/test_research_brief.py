import unittest

from src.research_brief import build_brief_context, ranked_metrics
from src.research_brief import comparison_html, findings_html, intro_html


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
