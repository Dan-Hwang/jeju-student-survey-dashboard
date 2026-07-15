import json
import os
import unittest
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from src import survey_dashboard
from src.survey_dashboard import build_foreign_report_data, collect_comments


class SurveyFreshnessTest(unittest.TestCase):
    def tearDown(self) -> None:
        survey_dashboard.get_public_survey.clear()
        survey_dashboard.get_foreign_survey.clear()

    def test_public_csv_fallback_uses_file_modification_time(self) -> None:
        with TemporaryDirectory() as directory:
            csv_path = Path(directory) / "korean.csv"
            csv_path.write_text("자유롭게\n좋은 서비스입니다\n", encoding="utf-8")
            modified_at = 1_700_000_000
            os.utime(csv_path, (modified_at, modified_at))
            missing_credentials = Path(directory) / "missing.json"

            survey_dashboard.get_public_survey.clear()
            with (
                patch.object(survey_dashboard, "DEFAULT_CSV", csv_path),
                patch.object(
                    survey_dashboard,
                    "get_credentials_path",
                    return_value=missing_credentials,
                ),
            ):
                result = survey_dashboard.get_public_survey()

        self.assertEqual(result["source"], "CSV fallback")
        self.assertEqual(
            result["loaded_at"],
            datetime.fromtimestamp(modified_at).strftime("%Y-%m-%d %H:%M"),
        )

    def test_missing_backing_data_uses_explicit_empty_timestamp(self) -> None:
        with TemporaryDirectory() as directory:
            missing = Path(directory) / "missing"

            survey_dashboard.get_public_survey.clear()
            survey_dashboard.get_foreign_survey.clear()
            with (
                patch.object(survey_dashboard, "DEFAULT_CSV", missing),
                patch.object(survey_dashboard, "DEFAULT_FOREIGN_CSV", missing),
                patch.object(survey_dashboard, "DEFAULT_FOREIGN_SUMMARY", missing),
                patch.object(
                    survey_dashboard,
                    "get_credentials_path",
                    return_value=missing,
                ),
                patch.object(survey_dashboard, "get_secret_value", return_value=""),
            ):
                korean = survey_dashboard.get_public_survey()
                foreign = survey_dashboard.get_foreign_survey()

        self.assertEqual((korean["source"], korean["loaded_at"]), ("empty", "-"))
        self.assertEqual((foreign["source"], foreign["loaded_at"]), ("empty", "-"))

    def test_foreign_csv_and_json_fallbacks_use_backing_file_mtime(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            csv_path = root / "foreign.csv"
            csv_path.write_text("anything else\nHelpful dashboard\n", encoding="utf-8")
            json_path = root / "foreign.json"
            json_path.write_text(
                json.dumps(
                    {
                        "n": 1,
                        "pain": [],
                        "taxi_frequency": [],
                        "activity": [],
                        "openchat_find": [],
                        "openchat_pain": [],
                        "intent": [["긍정", 0], ["중립", 0], ["부정", 0]],
                        "comments": [],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            missing = root / "missing"

            for fallback_path, csv_candidate, json_candidate, expected_source in [
                (csv_path, csv_path, json_path, "CSV"),
                (json_path, missing, json_path, "CSV summary"),
            ]:
                with self.subTest(source=expected_source):
                    modified_at = 1_700_000_000 + len(expected_source) * 60
                    os.utime(fallback_path, (modified_at, modified_at))
                    survey_dashboard.get_foreign_survey.clear()
                    with (
                        patch.object(survey_dashboard, "DEFAULT_FOREIGN_CSV", csv_candidate),
                        patch.object(survey_dashboard, "DEFAULT_FOREIGN_SUMMARY", json_candidate),
                        patch.object(
                            survey_dashboard,
                            "get_credentials_path",
                            return_value=missing,
                        ),
                        patch.object(survey_dashboard, "get_secret_value", return_value=""),
                    ):
                        result = survey_dashboard.get_foreign_survey()

                    self.assertEqual(result["source"], expected_source)
                    self.assertEqual(
                        result["loaded_at"],
                        datetime.fromtimestamp(modified_at).strftime("%Y-%m-%d %H:%M"),
                    )


class PublicCommentPrivacyTest(unittest.TestCase):
    def test_collect_comments_excludes_pii_and_preserves_ordinary_feedback(self) -> None:
        comments = [
            "메일은 student@example.com 입니다",
            "전화 010-1234-5678",
            "Call me at +1 415 555 2671",
            "https://example.com/profile 에 남겼어요",
            "인스타 @jeju_friend",
            "카톡 ID: jeju2026",
            "카톡 jeju2026",
            "연락처: 비밀계정",
            "버스 노선 정보가 더 정확하면 좋겠어요",
            "It would be easier to find old announcements.",
        ]
        rows = [{"comment": value} for value in comments]

        result = collect_comments(rows, "comment")

        self.assertEqual(
            result,
            [
                "버스 노선 정보가 더 정확하면 좋겠어요",
                "It would be easier to find old announcements.",
            ],
        )
        for private_value in comments[:8]:
            self.assertNotIn(private_value, result)

    def test_foreign_information_accuracy_signal_reaches_report_data(self) -> None:
        rows = [
            {
                "most frustrating": "정보가 정확한지 모르겠다",
                "anything else": "Normal feedback",
            }
        ]

        data = build_foreign_report_data(rows)

        self.assertEqual(data["openchat_pain"], [("정보 정확성 모르겠다", 1)])


if __name__ == "__main__":
    unittest.main()
