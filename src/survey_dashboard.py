from __future__ import annotations

import csv
import json
import os
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

import streamlit as st


BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_SPREADSHEET = "https://docs.google.com/spreadsheets/d/136GDfjr_qUIxsWfWqGOr8CZ392IAcAgVOyCH2eBXQdE/edit"
DEFAULT_FOREIGN_SPREADSHEET = ""
DEFAULT_CREDENTIALS = BASE_DIR / "secrets" / "google-service-account.json"
DEFAULT_CSV = BASE_DIR / "data" / "responses" / "제주대학교 교류학생 생활 플랫폼 설문조사.csv"
DEFAULT_FOREIGN_CSV = BASE_DIR / "data" / "responses" / "foreign_student_survey.csv"
DEFAULT_FOREIGN_SUMMARY = BASE_DIR / "data" / "responses" / "foreign_student_survey_summary.json"
REPORT_PDF = BASE_DIR / "output" / "reports" / "student-survey-live-report.pdf"
REPORT_PNG = BASE_DIR / "output" / "reports" / "student-survey-live-report.png"

QUESTION_ALIASES = {
    "stay": ["체류기간", "How long"],
    "pain": ["불편했던 점", "inconvenient"],
    "activity": ["같이 하고 싶은 활동", "activities"],
    "openchat_find": ["오픈채팅에서 가장 많이 찾는", "usually look for in Kakao"],
    "openchat_pain": ["가장 불편한 점", "frustrating", "most frustrating"],
    "taxi_frequency": ["택시팟을 얼마나 자주", "How often did you use taxis"],
    "intent": ["사용하시겠습니까", "how likely", "use it"],
    "comment": ["자유롭게", "anything else", "feedback", "suggestions"],
}

OPTION_ALIASES = {
    "버스 노선": ["버스 노선", "버스 배차", "Bus schedules"],
    "택시비": ["택시비", "Taxi fares"],
    "정보 부족": ["정보 부족", "Lack of information"],
    "교통": ["교통", "Transportation"],
    "같이 이동할 사람 찾기": ["같이 이동할 사람 찾기", "Finding people to travel with"],
    "여행 계획": ["여행 일정", "Planning trips"],
    "맛집": ["맛집", "Food tours / Restaurants", "Finding places to eat", "Restaurant recommendations"],
    "해수욕": ["해수욕", "Beach trips"],
    "여행": ["여행", "Traveling"],
    "드라이브": ["드라이브", "Road trips"],
    "카페": ["카페", "Cafes", "Cafés"],
    "술/나이트라이프": ["술", "Drinking / Nightlife"],
    "운동": ["운동", "Sports"],
    "공연": ["공연", "Concerts"],
    "전시": ["전시회", "전시", "Exhibitions"],
    "공부": ["공부", "Studying together"],
    "택시팟": ["택시팟", "Taxi-sharing"],
    "친구 만들기": ["친구 만들기", "Making friends"],
    "여행팟": ["여행팟", "Travel groups"],
    "공지": ["공지", "Announcements"],
    "시험정보": ["시험정보", "Exam information"],
    "생활정보": ["생활정보", "Student life information"],
    "원하는 글 찾기 어렵다": ["원하는 글을 찾기 어렵다", "원하는 글 찾기 어렵다", "It's hard to find the information I need"],
    "글이 너무 많다": ["글이 너무 많다", "Too many posts"],
    "지난 글 찾기 어렵다": ["지난 글 찾기 어렵다", "Old posts are difficult to find"],
    "채팅이 빨리 올라간다": ["채팅이 너무 빨리 올라간다", "New messages appear too quickly"],
    "모집 종료 글 노출": ["모집이 끝난 글이 계속 있다", "Expired recruitment posts are still visible"],
    "검색 기능 불편": ["검색이 안된다", "The search function is not useful"],
    "정보 정확성 모르겠다": ["정보가 정확한지 모르겠다", "정보가 정확한지 모르겠다", "The search function is not useful"],
    "거의 매일": ["거의 매일", "Almost every day"],
    "주 3~4회": ["주 3~4회", "3-4 times a week", "3–4 times a week"],
    "주 1~2회": ["주 1~2회", "1-2 times a week", "1–2 times a week"],
    "거의 안함": ["거의 안함", "Rarely"],
    "이용 안함": ["이용 안함", "Never"],
}

INTENT_GROUPS = {
    "긍정": ["반드시 사용", "사용할 것 같다", "Definitely would use it", "Probably would use it"],
    "중립": ["보통", "Not sure"],
    "부정": ["안 사용할 것 같다", "절대 안 사용", "Probably would not use it", "Definitely would not use it"],
}


def get_secret_value(key: str, default: str = "") -> str:
    try:
        value = st.secrets.get(key, default)
    except Exception:
        value = default
    return str(value) if value else default


def load_credentials_from_secrets() -> Path | None:
    raw_json = get_secret_value("GOOGLE_SERVICE_ACCOUNT_JSON")
    if not raw_json:
        return None
    target = Path(os.getenv("TMP", str(BASE_DIR / "tmp"))) / "ara-guide-google-service-account.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        data: dict[str, Any] = json.loads(raw_json)
    except json.JSONDecodeError:
        return None
    target.write_text(json.dumps(data), encoding="utf-8")
    return target


def get_credentials_path() -> Path:
    credentials_path = Path(os.getenv("GOOGLE_APPLICATION_CREDENTIALS", str(DEFAULT_CREDENTIALS)))
    if not credentials_path.exists():
        credentials_from_secrets = load_credentials_from_secrets()
        if credentials_from_secrets:
            credentials_path = credentials_from_secrets
    return credentials_path


def empty_report_data() -> dict[str, Any]:
    return {
        "n": 0,
        "pain": [],
        "activity": [],
        "openchat_find": [],
        "openchat_pain": [],
        "intent": [("긍정", 0), ("중립", 0), ("부정", 0)],
        "stay_4weeks": 0,
        "comments": [],
    }


def pct(value: int, total: int) -> str:
    if total <= 0:
        return "0.0%"
    return f"{value / total * 100:.1f}%"


def split_multi(value: str) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.replace(";", ",").split(",") if item.strip()]


def canonical_option(value: str) -> str:
    lowered = value.strip().lower()
    for canonical, aliases in OPTION_ALIASES.items():
        if lowered == canonical.lower() or any(lowered == alias.lower() for alias in aliases):
            return canonical
    return value.strip()


def find_column(headers: list[str], key: str) -> str | None:
    aliases = QUESTION_ALIASES[key]
    for header in headers:
        normalized = header.strip()
        if any(alias.lower() in normalized.lower() for alias in aliases):
            return header
    return None


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def quote_sheet_range(title: str) -> str:
    return f"'{title.replace(chr(39), chr(39) + chr(39))}'!A:Z"


def normalize_spreadsheet_id(value: str) -> str:
    match = re.search(r"/spreadsheets/d/([^/]+)", value)
    if match:
        return match.group(1)
    return value.strip()


def resolve_sheet_range(service, spreadsheet_id: str) -> str:
    metadata = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    sheets = metadata.get("sheets", [])
    if not sheets:
        raise RuntimeError("No sheets found in the spreadsheet.")
    return quote_sheet_range(sheets[0]["properties"]["title"])


def load_sheets(spreadsheet_id: str, credentials: Path) -> list[dict[str, str]]:
    from google.oauth2.service_account import Credentials
    from googleapiclient.discovery import build

    scopes = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
    creds = Credentials.from_service_account_file(str(credentials), scopes=scopes)
    service = build("sheets", "v4", credentials=creds)
    result = (
        service.spreadsheets()
        .values()
        .get(spreadsheetId=spreadsheet_id, range=resolve_sheet_range(service, spreadsheet_id))
        .execute()
    )
    values = result.get("values", [])
    if not values:
        return []
    headers = values[0]
    rows = []
    for values_row in values[1:]:
        padded = values_row + [""] * (len(headers) - len(values_row))
        rows.append(dict(zip(headers, padded)))
    return rows


def count_multi(rows: list[dict[str, str]], column: str | None) -> Counter:
    counter: Counter = Counter()
    if not column:
        return counter
    for row in rows:
        for item in split_multi(row.get(column, "")):
            counter[canonical_option(item)] += 1
    return counter


def count_single(rows: list[dict[str, str]], column: str | None) -> Counter:
    counter: Counter = Counter()
    if not column:
        return counter
    for row in rows:
        value = row.get(column, "").strip()
        if value:
            counter[canonical_option(value)] += 1
    return counter


def collect_comments(rows: list[dict[str, str]], column: str | None) -> list[str]:
    if not column:
        return []
    ignored = {"", "-", "없음", "없습니다", "n/a", "na", "no", "none", "nothing"}
    comments: list[str] = []
    for row in rows:
        value = row.get(column, "").strip()
        normalized = value.lower().replace(".", "").strip()
        if normalized in ignored:
            continue
        comments.append(value)
    return comments


def intent_summary(counter: Counter) -> Counter:
    summary: Counter = Counter({"긍정": 0, "중립": 0, "부정": 0})
    for value, count in counter.items():
        matched = False
        for group, aliases in INTENT_GROUPS.items():
            if value in aliases:
                summary[group] += count
                matched = True
                break
        if not matched:
            summary["중립"] += count
    return summary


def top_items(counter: Counter, wanted: Iterable[str], limit: int | None = None) -> list[tuple[str, int]]:
    items = [(label, counter.get(label, 0)) for label in wanted]
    items = [item for item in items if item[1] > 0]
    items.sort(key=lambda item: item[1], reverse=True)
    return items[:limit] if limit else items


def build_report_data(rows: list[dict[str, str]]) -> dict[str, Any]:
    headers = list(rows[0].keys()) if rows else []
    columns = {key: find_column(headers, key) for key in QUESTION_ALIASES}
    intent = intent_summary(count_single(rows, columns["intent"]))
    stay = count_single(rows, columns["stay"])
    return {
        "n": len(rows),
        "pain": top_items(count_multi(rows, columns["pain"]), ["버스 노선", "택시비", "정보 부족", "교통", "같이 이동할 사람 찾기"], 5),
        "activity": top_items(count_multi(rows, columns["activity"]), ["맛집", "해수욕", "여행", "드라이브", "카페", "운동", "공부"], 7),
        "openchat_find": top_items(count_multi(rows, columns["openchat_find"]), ["택시팟", "친구 만들기", "여행팟", "맛집", "공지", "생활정보"], 6),
        "openchat_pain": top_items(count_multi(rows, columns["openchat_pain"]), ["원하는 글 찾기 어렵다", "글이 너무 많다", "지난 글 찾기 어렵다", "채팅이 빨리 올라간다", "정보 정확성 모르겠다"], 5),
        "intent": [("긍정", intent["긍정"]), ("중립", intent["중립"]), ("부정", intent["부정"])],
        "stay_4weeks": stay.get("4주 이상", 0) + stay.get("More than 4 weeks", 0),
        "comments": collect_comments(rows, columns["comment"]),
    }


def build_foreign_report_data(rows: list[dict[str, str]]) -> dict[str, Any]:
    headers = list(rows[0].keys()) if rows else []
    columns = {key: find_column(headers, key) for key in QUESTION_ALIASES}
    intent = intent_summary(count_single(rows, columns["intent"]))
    return {
        "n": len(rows),
        "pain": top_items(
            count_multi(rows, columns["pain"]),
            ["교통", "버스 노선", "택시비", "같이 이동할 사람 찾기", "여행 계획", "정보 부족"],
            6,
        ),
        "taxi_frequency": top_items(
            count_single(rows, columns["taxi_frequency"]),
            ["거의 매일", "주 3~4회", "주 1~2회", "거의 안함", "이용 안함"],
            5,
        ),
        "activity": top_items(
            count_multi(rows, columns["activity"]),
            ["해수욕", "맛집", "카페", "드라이브", "술/나이트라이프", "운동", "공연", "전시", "여행", "공부"],
            10,
        ),
        "openchat_find": top_items(
            count_multi(rows, columns["openchat_find"]),
            ["택시팟", "여행팟", "맛집", "공지", "시험정보", "생활정보", "친구 만들기"],
            7,
        ),
        "openchat_pain": top_items(
            count_multi(rows, columns["openchat_pain"]),
            ["글이 너무 많다", "원하는 글 찾기 어렵다", "검색 기능 불편", "지난 글 찾기 어렵다", "채팅이 빨리 올라간다", "모집 종료 글 노출"],
            6,
        ),
        "intent": [("긍정", intent["긍정"]), ("중립", intent["중립"]), ("부정", intent["부정"])],
        "comments": collect_comments(rows, columns["comment"]),
    }


@st.cache_data(ttl=300, show_spinner=False)
def get_public_survey() -> dict[str, Any]:
    spreadsheet = get_secret_value("ARA_SURVEY_SPREADSHEET", os.getenv("ARA_SURVEY_SPREADSHEET", DEFAULT_SPREADSHEET))
    credentials_path = get_credentials_path()

    source = "Google Sheets"
    error = ""
    rows: list[dict[str, str]] = []
    if credentials_path.exists():
        try:
            rows = load_sheets(normalize_spreadsheet_id(spreadsheet), credentials_path)
        except Exception as exc:
            error = f"Google Sheets 연결 실패: {type(exc).__name__}"
            rows = []

    if not rows and DEFAULT_CSV.exists():
        rows = load_csv(DEFAULT_CSV)
        source = "CSV fallback"
    elif not rows:
        source = "empty"

    data = build_report_data(rows) if rows else empty_report_data()
    return {
        "data": data,
        "rows": len(rows),
        "source": source,
        "error": error,
        "loaded_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }


@st.cache_data(ttl=300, show_spinner=False)
def get_foreign_survey() -> dict[str, Any]:
    spreadsheet = get_secret_value(
        "ARA_FOREIGN_SURVEY_SPREADSHEET",
        os.getenv("ARA_FOREIGN_SURVEY_SPREADSHEET", DEFAULT_FOREIGN_SPREADSHEET),
    )
    credentials_path = get_credentials_path()

    source = "empty"
    error = ""
    rows: list[dict[str, str]] = []
    if spreadsheet and credentials_path.exists():
        try:
            rows = load_sheets(normalize_spreadsheet_id(spreadsheet), credentials_path)
            source = "Google Sheets"
        except Exception as exc:
            error = f"외국인 설문 Google Sheets 연결 실패: {type(exc).__name__}"
            rows = []

    if rows:
        data = build_foreign_report_data(rows)
    elif DEFAULT_FOREIGN_CSV.exists():
        rows = load_csv(DEFAULT_FOREIGN_CSV)
        data = build_foreign_report_data(rows)
        source = "CSV"
    elif DEFAULT_FOREIGN_SUMMARY.exists():
        data = load_json(DEFAULT_FOREIGN_SUMMARY)
        source = "CSV summary"
    else:
        data = {
        "n": 0,
        "pain": [],
        "taxi_frequency": [],
        "activity": [],
        "openchat_find": [],
        "openchat_pain": [],
        "intent": [("긍정", 0), ("중립", 0), ("부정", 0)],
        "comments": [],
        }
        if not error:
            error = "외국인 설문 집계 파일을 찾을 수 없습니다."
    return {
        "data": data,
        "rows": int(data["n"]),
        "source": source,
        "error": error,
        "loaded_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }
