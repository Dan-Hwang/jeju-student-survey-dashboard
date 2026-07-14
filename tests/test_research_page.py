import unittest

from src.research_page import (
    build_research_view_model,
    product_bridge_html,
    research_story_html,
)


class ResearchPageTest(unittest.TestCase):
    def test_builds_live_summary_without_hard_coded_counts(self) -> None:
        korean = {
            "data": {
                "n": 19,
                "pain": [("버스 노선", 10)],
                "openchat_find": [("택시팟", 9)],
                "intent": [("긍정", 15), ("중립", 3), ("부정", 1)],
            },
            "loaded_at": "2026-07-14 10:00",
            "source": "Google Sheets",
        }
        foreign = {
            "data": {
                "n": 16,
                "pain": [("교통", 11)],
                "openchat_find": [("공지", 9)],
                "intent": [("긍정", 14), ("중립", 1), ("부정", 1)],
            },
            "loaded_at": "2026-07-14 10:01",
            "source": "Google Sheets",
        }

        result = build_research_view_model(korean, foreign)

        self.assertEqual(result["total"], 35)
        self.assertEqual(result["korean_top_pain"], ("버스 노선", 10))
        self.assertEqual(result["foreign_top_find"], ("공지", 9))
        self.assertEqual(result["positive_total"], 29)
        self.assertEqual(result["positive_pct"], "82.9%")

    def test_story_escapes_sheet_labels(self) -> None:
        model = {
            "total": 1,
            "korean_total": 1,
            "foreign_total": 0,
            "korean_top_pain": ("<script>alert(1)</script>", 1),
            "foreign_top_pain": ("-", 0),
            "korean_top_find": ("택시팟", 1),
            "foreign_top_find": ("-", 0),
            "positive_total": 1,
            "positive_pct": "100.0%",
            "loaded_at": "2026-07-14 10:00",
        }

        html = research_story_html(model)

        self.assertNotIn("<script>", html)
        self.assertIn("&lt;script&gt;", html)

    def test_bridge_names_actual_synapspot_flows(self) -> None:
        html = product_bridge_html({})

        self.assertIn("AI 질문", html)
        self.assertIn("파티", html)
        self.assertIn("출처", html)
        self.assertIn("신청", html)


if __name__ == "__main__":
    unittest.main()
