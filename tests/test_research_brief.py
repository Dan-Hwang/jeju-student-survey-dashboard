import unittest

from src.research_brief import build_brief_context, ranked_metrics


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
