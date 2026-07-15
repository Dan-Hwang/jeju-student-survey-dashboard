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


def subject_fields(reader: PdfReader) -> dict[str, str]:
    subject = reader.metadata.subject or ""
    return dict(
        field.strip().split("=", 1)
        for field in subject.split(";")
        if field.strip()
    )


class PdfExportTest(unittest.TestCase):
    def test_each_pdf_metadata_exactly_tracks_its_current_surveys(self) -> None:
        first_pdf = build_current_pdf(
            report(7, "sentinel-alpha", "SENTINEL-KOREAN-ALPHA"),
            report(13, "sentinel-beta", "SENTINEL-FOREIGN-ALPHA"),
        )
        second_pdf = build_current_pdf(
            report(41, "sentinel-gamma", "SENTINEL-KOREAN-BETA"),
            report(6, "sentinel-delta", "SENTINEL-FOREIGN-BETA"),
        )

        first_reader = PdfReader(BytesIO(first_pdf))
        second_reader = PdfReader(BytesIO(second_pdf))

        self.assertEqual(len(first_reader.pages), 3)
        self.assertEqual(
            subject_fields(first_reader),
            {
                "total": "20",
                "korean": "7",
                "foreign": "13",
                "korean_source": "SENTINEL-KOREAN-ALPHA",
                "foreign_source": "SENTINEL-FOREIGN-ALPHA",
            },
        )
        self.assertEqual(len(second_reader.pages), 3)
        self.assertEqual(
            subject_fields(second_reader),
            {
                "total": "47",
                "korean": "41",
                "foreign": "6",
                "korean_source": "SENTINEL-KOREAN-BETA",
                "foreign_source": "SENTINEL-FOREIGN-BETA",
            },
        )


if __name__ == "__main__":
    unittest.main()
