import unittest
from io import BytesIO

from pypdf import PdfReader

from app import build_current_pdf
from src.pdf_report import information_rows, movement_rows, shared_percentage_scale


def report(
    total: int,
    label: str,
    source: str,
    comments: list[str] | None = None,
) -> dict[str, object]:
    return {
        "data": {
            "n": total,
            "pain": [(label, total)],
            "activity": [],
            "openchat_find": [(label, total)],
            "openchat_pain": [],
            "intent": [("긍정", total), ("중립", 0), ("부정", 0)],
            "comments": comments or [],
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


def has_embedded_font(reader: PdfReader) -> bool:
    for page in reader.pages:
        resources = page.get("/Resources", {})
        fonts = resources.get("/Font", {})
        for font_ref in fonts.values():
            font = font_ref.get_object()
            candidates = [font]
            candidates.extend(
                descendant.get_object()
                for descendant in font.get("/DescendantFonts", [])
            )
            for candidate in candidates:
                descriptor_ref = candidate.get("/FontDescriptor")
                if not descriptor_ref:
                    continue
                descriptor = descriptor_ref.get_object()
                if any(key in descriptor for key in ("/FontFile", "/FontFile2", "/FontFile3")):
                    return True
    return False


def embedded_font_names(reader: PdfReader) -> set[str]:
    names: set[str] = set()
    for page in reader.pages:
        resources = page.get("/Resources", {})
        fonts = resources.get("/Font", {})
        for font_ref in fonts.values():
            font = font_ref.get_object()
            names.add(str(font.get("/BaseFont", "")))
            for descendant in font.get("/DescendantFonts", []):
                names.add(str(descendant.get_object().get("/BaseFont", "")))
    return names


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

    def test_pdf_presents_the_research_story_and_product_bridge(self) -> None:
        reader = PdfReader(
            BytesIO(
                build_current_pdf(
                    report(23, "버스 노선", "Google Sheets"),
                    report(17, "교통", "Google Sheets"),
                )
            )
        )

        text = "\n".join(page.extract_text() or "" for page in reader.pages)

        self.assertEqual(
            reader.metadata.title,
            "교류학생의 이동과 정보 탐색은 어디서 막혔을까?",
        )
        self.assertIn("PROBLEM 01", text)
        self.assertIn("PROBLEM 02", text)
        self.assertIn("FROM RESEARCH TO PRODUCT", text)
        self.assertIn("이동과 동행 모집", text)
        self.assertIn("공지와 생활정보 탐색", text)
        self.assertIn("이동·동행 파티", text)
        self.assertIn("근거 있는 정보 탐색", text)
        self.assertIn("40명", text)

    def test_pdf_embeds_fonts_and_two_product_previews_on_page_one(self) -> None:
        reader = PdfReader(
            BytesIO(
                build_current_pdf(
                    report(23, "택시팟", "Google Sheets"),
                    report(17, "맛집", "Google Sheets"),
                )
            )
        )

        self.assertTrue(has_embedded_font(reader))
        self.assertTrue(
            any("NanumGothic" in name for name in embedded_font_names(reader))
        )
        self.assertGreaterEqual(len(reader.pages[0].images), 2)

    def test_pdf_drops_identifier_shaped_comments_at_export_boundary(self) -> None:
        reader = PdfReader(
            BytesIO(
                build_current_pdf(
                    report(
                        23,
                        "택시팟",
                        "Google Sheets",
                        [
                            "student@example.com",
                            "010-1234-5678",
                            "Name: Hong Gildong",
                            "The bus information was useful",
                        ],
                    ),
                    report(17, "공지", "Google Sheets"),
                )
            )
        )

        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        self.assertNotIn("student@example.com", text)
        self.assertNotIn("010-1234-5678", text)
        self.assertNotIn("Hong Gildong", text)
        self.assertIn("The bus information was useful", text)

    def test_empty_pdf_uses_waiting_state_without_product_claims(self) -> None:
        reader = PdfReader(
            BytesIO(
                build_current_pdf(
                    report(0, "응답 없음", "empty"),
                    report(0, "응답 없음", "empty"),
                )
            )
        )

        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        self.assertIn("WAITING FOR RESPONSES", text)
        self.assertNotIn("FROM RESEARCH TO PRODUCT", text)
        self.assertEqual(len(reader.pages[0].images), 0)

    def test_group_comparison_uses_one_percentage_scale(self) -> None:
        scale = shared_percentage_scale(
            [("한국인", 5)],
            [("외국인", 9)],
            11,
            16,
        )

        self.assertAlmostEqual(scale, 9 / 16)
        self.assertLess((5 / 11) / scale, 1.0)

    def test_problem_rows_do_not_fall_back_to_unrelated_categories(self) -> None:
        korean = report(10, "맛집", "Google Sheets")["data"]
        foreign = report(10, "맛집", "Google Sheets")["data"]
        korean["pain"] = [("정보 부족", 6)]
        foreign["pain"] = [("정보 부족", 7)]
        korean["openchat_find"] = [("맛집", 8)]
        foreign["openchat_find"] = [("맛집", 9)]
        korean["openchat_pain"] = []
        foreign["openchat_pain"] = []

        self.assertEqual(movement_rows(korean, foreign), [])
        self.assertTrue(
            all("맛집" not in label for label, _, _ in information_rows(korean, foreign))
        )


if __name__ == "__main__":
    unittest.main()
