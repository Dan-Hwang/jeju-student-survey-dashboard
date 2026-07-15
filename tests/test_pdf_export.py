import unittest
from io import BytesIO

from pypdf import PdfReader

from app import build_current_pdf


def report(total: int, label: str, source: str) -> dict[str, object]:
    return {
        "data": {
            "n": total,
            "pain": [(label, total)],
            "activity": [],
            "openchat_find": [(label, total)],
            "openchat_pain": [],
            "intent": [("긍정", total), ("중립", 0), ("부정", 0)],
            "comments": [],
        },
        "source": source,
        "loaded_at": "2026-07-15 15:00",
    }


class PdfExportTest(unittest.TestCase):
    def test_pdf_metadata_tracks_current_group_totals_sources_and_three_pages(self) -> None:
        pdf = build_current_pdf(
            report(23, "생활정보", "Korean Fixture Sheet"),
            report(16, "교통", "Foreign Fixture CSV"),
        )

        reader = PdfReader(BytesIO(pdf))
        subject = reader.metadata.subject or ""

        self.assertEqual(len(reader.pages), 3)
        self.assertIn("total=39", subject)
        self.assertIn("korean=23", subject)
        self.assertIn("foreign=16", subject)
        self.assertIn("korean_source=Korean Fixture Sheet", subject)
        self.assertIn("foreign_source=Foreign Fixture CSV", subject)


if __name__ == "__main__":
    unittest.main()
