import unittest
from io import BytesIO
from pathlib import Path

from pypdf import PdfReader

from src.presentation_pdf import build_presentation_pdf


def survey_fixture(
    total: int,
    pain: list[tuple[str, int]],
    openchat_find: list[tuple[str, int]],
) -> dict[str, object]:
    return {
        "data": {
            "n": total,
            "pain": pain,
            "activity": [("여행", max(1, total // 2)), ("맛집", max(1, total // 3))],
            "openchat_find": openchat_find,
            "openchat_pain": [("원하는 글 찾기 어렵다", max(1, total // 3))],
            "intent": [("긍정", total - 2), ("중립", 1), ("부정", 1)],
            "stay_4weeks": max(0, total - 3),
            "comments": [],
            "taxi_frequency": [("주 1~2회", max(1, total // 3))],
        },
        "source": "Google Sheets",
        "loaded_at": "2026-07-15 10:00",
        "error": "",
    }


class PresentationPdfTest(unittest.TestCase):
    def setUp(self) -> None:
        self.korean = survey_fixture(
            23,
            [("버스 노선", 11), ("택시비", 8), ("정보 부족", 6)],
            [("택시팟", 10), ("여행팟", 6), ("친구 만들기", 4)],
        )
        self.foreign = survey_fixture(
            16,
            [("교통", 11), ("정보 부족", 7), ("식사", 5)],
            [("공지", 9), ("생활정보", 7), ("친구 만들기", 5)],
        )

    def build(self, question_preview: Path | None = None, meetings_preview: Path | None = None) -> bytes:
        return build_presentation_pdf(
            self.korean,
            self.foreign,
            question_preview=question_preview,
            meetings_preview=meetings_preview,
            public_url="https://example.streamlit.app/",
        )

    def test_builds_four_page_presentation_report(self) -> None:
        reader = PdfReader(BytesIO(self.build()))

        self.assertEqual(len(reader.pages), 4)
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        self.assertIn("39명", text)
        self.assertIn("이동과 동행 모집", text)
        self.assertIn("공지와 생활정보 탐색", text)
        self.assertIn("이동/동행 파티", text)
        self.assertIn("근거 있는 AI 질문", text)

    def test_missing_preview_images_do_not_break_pdf(self) -> None:
        pdf = self.build(Path("missing-question.png"), Path("missing-meetings.png"))

        self.assertGreater(len(pdf), 1_000)
        self.assertEqual(len(PdfReader(BytesIO(pdf)).pages), 4)


if __name__ == "__main__":
    unittest.main()
