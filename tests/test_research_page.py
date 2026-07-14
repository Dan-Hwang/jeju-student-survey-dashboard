import unittest
from pathlib import Path

from src.research_page import (
    build_research_view_model,
    product_bridge_html,
    research_story_html,
)


class ResearchPageTest(unittest.TestCase):
    def story_model(
        self,
        total: int = 3,
        korean_total: int = 2,
        foreign_total: int = 1,
    ) -> dict[str, object]:
        return {
            "total": total,
            "korean_total": korean_total,
            "foreign_total": foreign_total,
            "korean_top_pain": ("버스 노선", korean_total),
            "foreign_top_pain": ("교통", foreign_total),
            "korean_top_find": ("택시팟", korean_total),
            "foreign_top_find": ("공지", foreign_total),
            "korean_positive": korean_total,
            "foreign_positive": foreign_total,
            "positive_total": total,
            "positive_pct": "100.0%" if total else "0.0%",
            "loaded_at": "2026-07-15 10:00",
            "korean_pain": [("버스 노선", korean_total)],
            "korean_find": [("택시팟", korean_total)],
            "foreign_pain": [("교통", foreign_total)],
            "foreign_find": [("공지", foreign_total)],
            "dot_count": min(total, 60),
            "responses_per_dot": max(1, (total + 59) // 60),
        }

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
        self.assertEqual(result["korean_pain"], [("버스 노선", 10)])
        self.assertEqual(result["foreign_find"], [("공지", 9)])
        self.assertEqual(result["dot_count"], 35)
        self.assertEqual(result["responses_per_dot"], 1)

    def test_caps_respondent_dots_for_large_samples(self) -> None:
        korean = {
            "data": {
                "n": 80,
                "pain": [],
                "openchat_find": [],
                "intent": [],
            }
        }
        foreign = {
            "data": {
                "n": 40,
                "pain": [],
                "openchat_find": [],
                "intent": [],
            }
        }

        result = build_research_view_model(korean, foreign)

        self.assertEqual(result["total"], 120)
        self.assertEqual(result["dot_count"], 60)
        self.assertEqual(result["responses_per_dot"], 2)

    def test_story_escapes_sheet_labels(self) -> None:
        model = self.story_model(total=1, korean_total=1, foreign_total=0)
        model["korean_top_pain"] = ("<script>alert(1)</script>", 1)
        model["korean_pain"] = [("<script>alert(1)</script>", 1)]

        html = research_story_html(model)

        self.assertNotIn("<script>", html)
        self.assertIn("&lt;script&gt;", html)

    def test_story_renders_dynamic_respondent_dots(self) -> None:
        model = self.story_model(total=3, korean_total=2, foreign_total=1)

        html = research_story_html(model)

        self.assertEqual(html.count('class="respondent-dot '), 3)
        self.assertIn("한국인 2명", html)
        self.assertIn("외국인 1명", html)
        self.assertNotIn("39명의 응답", html)

    def test_story_bars_expose_values_without_hover(self) -> None:
        model = self.story_model(total=3, korean_total=2, foreign_total=1)

        html = research_story_html(model)

        self.assertIn('class="story-bar-value"', html)
        self.assertIn("2명", html)
        self.assertIn("100.0%", html)
        self.assertIn('tabindex="0"', html)

    def test_story_honors_reduced_motion_and_mobile_layout(self) -> None:
        html = research_story_html(self.story_model())

        self.assertIn("prefers-reduced-motion: reduce", html)
        self.assertIn("@media (max-width: 900px)", html)
        self.assertIn("@media (max-width: 680px)", html)
        self.assertIn("grid-template-columns: 1fr", html)

    def test_story_uses_stable_font_sizes(self) -> None:
        html = research_story_html(self.story_model())

        self.assertNotIn("font-size: clamp", html)

    def test_bridge_names_actual_synapspot_flows(self) -> None:
        html = product_bridge_html({})

        self.assertIn("AI 질문", html)
        self.assertIn("파티", html)
        self.assertIn("출처", html)
        self.assertIn("신청", html)

    def test_product_preview_assets_exist(self) -> None:
        self.assertTrue(Path("assets/synapspot-question-preview.png").is_file())
        self.assertTrue(Path("assets/synapspot-meetings-preview.png").is_file())


if __name__ == "__main__":
    unittest.main()
