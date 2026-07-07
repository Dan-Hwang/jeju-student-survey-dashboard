from __future__ import annotations

import argparse
import csv
import os
import re
import subprocess
from collections import Counter
from pathlib import Path
from typing import Iterable

from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PDF = ROOT / "output" / "reports" / "student-survey-auto-report.pdf"
DEFAULT_PNG = ROOT / "output" / "reports" / "student-survey-auto-report.png"
POPPLER_CANDIDATES = [
    Path(r"C:\Users\Aiffel\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\poppler\Library\bin\pdftoppm.exe"),
    ROOT / "dependencies" / "native" / "poppler" / "Library" / "bin" / "pdftoppm.exe",
]

FONT = Path(r"C:\Windows\Fonts\malgun.ttf")
FONT_BOLD = Path(r"C:\Windows\Fonts\malgunbd.ttf")

PAGE_W = 1280
PAGE_H = 720
MARGIN = 48

NAVY = colors.HexColor("#0F172A")
TEXT = colors.HexColor("#334155")
MUTED = colors.HexColor("#64748B")
LINE = colors.HexColor("#E2E8F0")
BG = colors.HexColor("#F8FAFC")
BLUE = colors.HexColor("#2563EB")
GREEN = colors.HexColor("#059669")
ORANGE = colors.HexColor("#EA580C")
RED = colors.HexColor("#DC2626")
TEAL = colors.HexColor("#0891B2")
PURPLE = colors.HexColor("#7C3AED")
YELLOW = colors.HexColor("#D97706")


QUESTION_ALIASES = {
    "stay": ["체류기간", "How long"],
    "pain": ["불편했던 점", "inconvenient"],
    "activity": ["같이 하고 싶은 활동", "activities"],
    "openchat_find": ["오픈채팅에서 가장 많이 찾는", "usually look for in Kakao"],
    "openchat_pain": ["가장 불편한 점", "frustrating", "most frustrating"],
    "intent": ["사용하시겠습니까", "how likely", "use it"],
}

OPTION_ALIASES = {
    "버스 노선": ["버스 노선", "버스 배차", "Bus schedules"],
    "택시비": ["택시비", "Taxi fares"],
    "정보 부족": ["정보 부족", "Lack of information"],
    "교통": ["교통", "Transportation"],
    "같이 이동할 사람 찾기": ["같이 이동할 사람 찾기", "Finding people to travel with"],
    "맛집": ["맛집", "Food tours / Restaurants", "Finding places to eat", "Restaurant recommendations"],
    "해수욕": ["해수욕", "Beach trips"],
    "여행": ["여행", "Traveling"],
    "드라이브": ["드라이브", "Road trips"],
    "카페": ["카페", "Cafes"],
    "운동": ["운동", "Sports"],
    "공부": ["공부", "Studying together"],
    "택시팟": ["택시팟", "Taxi-sharing"],
    "친구 만들기": ["친구 만들기", "Making friends"],
    "여행팟": ["여행팟", "Travel groups"],
    "공지": ["공지", "Announcements"],
    "생활정보": ["생활정보", "Student life information"],
    "원하는 글 찾기 어렵다": ["원하는 글을 찾기 어렵다", "원하는 글 찾기 어렵다", "It's hard to find the information I need"],
    "글이 너무 많다": ["글이 너무 많다", "Too many posts"],
    "지난 글 찾기 어렵다": ["지난 글 찾기 어렵다", "Old posts are difficult to find"],
    "채팅이 빨리 올라간다": ["채팅이 너무 빨리 올라간다", "New messages appear too quickly"],
    "정보 정확성 모르겠다": ["정보가 정확한지 모르겠다", "정보가 정확한지 모르겠다", "The search function is not useful"],
}

INTENT_GROUPS = {
    "긍정": ["반드시 사용", "사용할 것 같다", "Definitely would use it", "Probably would use it"],
    "중립": ["보통", "Not sure"],
    "부정": ["안 사용할 것 같다", "절대 안 사용", "Probably would not use it", "Definitely would not use it"],
}


def setup_fonts() -> None:
    pdfmetrics.registerFont(TTFont("Malgun", str(FONT)))
    pdfmetrics.registerFont(TTFont("Malgun-Bold", str(FONT_BOLD)))


def draw_text(c, x, y, text, size=16, font="Malgun", color=TEXT):
    c.setFillColor(color)
    c.setFont(font, size)
    c.drawString(x, y, text)


def wrap_text(text, font_name, font_size, max_width):
    lines = []
    for paragraph in text.split("\n"):
        current = ""
        for word in paragraph.split(" "):
            candidate = word if not current else f"{current} {word}"
            if pdfmetrics.stringWidth(candidate, font_name, font_size) <= max_width:
                current = candidate
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
    return lines


def round_rect(c, x, y, w, h, fill=colors.white, stroke=LINE, radius=16):
    c.setFillColor(fill)
    c.setStrokeColor(stroke)
    c.roundRect(x, y, w, h, radius, stroke=1, fill=1)


def pct(value, total):
    if total <= 0:
        return "0.0%"
    return f"{value / total * 100:.1f}%"


def split_multi(value: str) -> list[str]:
    if not value:
        return []
    parts: list[str] = []
    for chunk in value.replace(";", ",").split(","):
        item = chunk.strip()
        if item:
            parts.append(item)
    return parts


def canonical_option(value: str) -> str:
    lowered = value.strip().lower()
    for canonical, aliases in OPTION_ALIASES.items():
        if lowered == canonical.lower():
            return canonical
        if any(lowered == alias.lower() for alias in aliases):
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


def quote_sheet_range(title: str) -> str:
    escaped = title.replace("'", "''")
    return f"'{escaped}'!A:Z"


def resolve_sheet_range(service, spreadsheet_id: str, range_name: str | None) -> str:
    if range_name:
        return range_name
    metadata = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    sheets = metadata.get("sheets", [])
    if not sheets:
        raise SystemExit("No sheets found in the spreadsheet.")
    title = sheets[0]["properties"]["title"]
    return quote_sheet_range(title)


def load_sheets(spreadsheet_id: str, range_name: str | None, credentials: Path) -> list[dict[str, str]]:
    try:
        from google.oauth2.service_account import Credentials
        from googleapiclient.discovery import build
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "Google Sheets dependencies are missing. Run: pip install google-api-python-client google-auth"
        ) from exc

    scopes = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
    creds = Credentials.from_service_account_file(str(credentials), scopes=scopes)
    service = build("sheets", "v4", credentials=creds)
    resolved_range = resolve_sheet_range(service, spreadsheet_id, range_name)
    result = (
        service.spreadsheets()
        .values()
        .get(spreadsheetId=spreadsheet_id, range=resolved_range)
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


def normalize_spreadsheet_id(value: str) -> str:
    match = re.search(r"/spreadsheets/d/([^/]+)", value)
    if match:
        return match.group(1)
    return value.strip()


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


def build_report_data(rows: list[dict[str, str]]) -> dict:
    headers = list(rows[0].keys()) if rows else []
    columns = {key: find_column(headers, key) for key in QUESTION_ALIASES}

    pain = count_multi(rows, columns["pain"])
    activity = count_multi(rows, columns["activity"])
    openchat_find = count_multi(rows, columns["openchat_find"])
    openchat_pain = count_multi(rows, columns["openchat_pain"])
    intent_raw = count_single(rows, columns["intent"])
    intent = intent_summary(intent_raw)
    stay = count_single(rows, columns["stay"])

    return {
        "n": len(rows),
        "columns": columns,
        "pain": top_items(pain, ["버스 노선", "택시비", "정보 부족", "교통", "같이 이동할 사람 찾기"], 5),
        "activity": top_items(activity, ["맛집", "해수욕", "여행", "드라이브", "카페", "운동", "공부"], 7),
        "openchat_find": top_items(openchat_find, ["택시팟", "친구 만들기", "여행팟", "맛집", "공지", "생활정보"], 6),
        "openchat_pain": top_items(openchat_pain, ["원하는 글 찾기 어렵다", "글이 너무 많다", "지난 글 찾기 어렵다", "채팅이 빨리 올라간다", "정보 정확성 모르겠다"], 5),
        "intent": [("긍정", intent["긍정"]), ("중립", intent["중립"]), ("부정", intent["부정"])],
        "stay_4weeks": stay.get("4주 이상", 0) + stay.get("More than 4 weeks", 0),
    }


def metric_card(c, x, y, w, h, label, value, note, accent):
    round_rect(c, x, y, w, h)
    c.setFillColor(accent)
    c.roundRect(x + 18, y + h - 16, 52, 6, 3, stroke=0, fill=1)
    draw_text(c, x + 18, y + h - 38, label, 14, "Malgun-Bold", MUTED)
    draw_text(c, x + 18, y + 34, value, 30, "Malgun-Bold", NAVY)
    draw_text(c, x + 18, y + 14, note, 12, "Malgun", MUTED)


def hbar_chart(c, x, y, w, h, title, subtitle, data, total, max_value=None, color=BLUE, label_w=190):
    round_rect(c, x, y, w, h)
    draw_text(c, x + 20, y + h - 34, title, 18, "Malgun-Bold", NAVY)
    draw_text(c, x + 20, y + h - 56, subtitle, 12, "Malgun", MUTED)
    if not data:
        draw_text(c, x + 20, y + h - 100, "응답 데이터 없음", 13, "Malgun", MUTED)
        return
    max_value = max_value or max(v for _, v in data) or 1
    value_w = 94
    bar_x = x + 20 + label_w
    bar_w = max(56, w - 40 - label_w - value_w)
    top = y + h - 86
    row_h = min(31, (h - 108) / len(data))
    for i, (label, value) in enumerate(data):
        yy = top - i * row_h
        draw_text(c, x + 20, yy + 3, label, 11.5, "Malgun", TEXT)
        c.setFillColor(colors.HexColor("#EEF2FF"))
        c.roundRect(bar_x, yy, bar_w, 11, 5.5, stroke=0, fill=1)
        c.setFillColor(color)
        c.roundRect(bar_x, yy, bar_w * (value / max_value), 11, 5.5, stroke=0, fill=1)
        draw_text(c, bar_x + bar_w + 10, yy - 1, f"{value}명 ({pct(value, total)})", 10.5, "Malgun-Bold", TEXT)


def stacked_intent_chart(c, x, y, w, h, title, subtitle, data, total):
    round_rect(c, x, y, w, h)
    draw_text(c, x + 20, y + h - 34, title, 18, "Malgun-Bold", NAVY)
    draw_text(c, x + 20, y + h - 56, subtitle, 12, "Malgun", MUTED)

    colors_by_label = {"긍정": GREEN, "중립": YELLOW, "부정": RED}
    bar_x = x + 22
    bar_y = y + h - 104
    bar_w = w - 44
    current_x = bar_x
    for label, value in data:
        segment_w = bar_w * value / max(total, 1)
        c.setFillColor(colors_by_label[label])
        c.roundRect(current_x, bar_y, segment_w, 22, 10, stroke=0, fill=1)
        current_x += segment_w

    draw_text(c, x + 22, y + h - 134, f"전체 {total}명", 12, "Malgun-Bold", MUTED)
    row_y = y + h - 166
    for label, value in data:
        c.setFillColor(colors_by_label[label])
        c.circle(x + 27, row_y + 4, 5, stroke=0, fill=1)
        draw_text(c, x + 42, row_y, label, 12, "Malgun-Bold", TEXT)
        draw_text(c, x + 132, row_y, f"{value}명 ({pct(value, total)})", 12, "Malgun", TEXT)
        row_y -= 28


def insight_box(c, x, y, w, h, data):
    round_rect(c, x, y, w, h)
    draw_text(c, x + 20, y + h - 34, "해석", 18, "Malgun-Bold", NAVY)
    pain_top = data["pain"][0] if data["pain"] else ("불편 항목", 0)
    open_top = data["openchat_find"][0] if data["openchat_find"] else ("오픈채팅 항목", 0)
    find_top = data["openchat_pain"][0] if data["openchat_pain"] else ("탐색 불편", 0)
    positive = dict(data["intent"]).get("긍정", 0)
    insights = [
        f"불편 1순위: {pain_top[0]} {pain_top[1]}명",
        f"오픈채팅: {open_top[0]} {open_top[1]}명, {find_top[0]} {find_top[1]}명",
        f"사용 의향: 긍정 {positive}명",
    ]
    y0 = y + h - 68
    for item in insights:
        c.setFillColor(GREEN)
        c.circle(x + 25, y0 + 4, 4, stroke=0, fill=1)
        c.setFillColor(TEXT)
        c.setFont("Malgun", 10.5)
        for line in wrap_text(item, "Malgun", 10.5, w - 58):
            c.drawString(x + 38, y0, line)
            y0 -= 16
        y0 -= 8

    c.setFillColor(colors.HexColor("#EFF6FF"))
    c.roundRect(x + 20, y + 16, w - 40, 58, 12, stroke=0, fill=1)
    draw_text(c, x + 38, y + 50, "팀 결정 포인트", 11.5, "Malgun-Bold", BLUE)
    c.setFillColor(NAVY)
    c.setFont("Malgun", 10.5)
    ty = y + 31
    for line in wrap_text("실시간 동행 모집 중심, 교통/생활정보는 보조 기능", "Malgun", 10.5, w - 76):
        c.drawString(x + 38, ty, line)
        ty -= 15


def draw_report(c, data, report_date):
    total = data["n"]
    c.setFillColor(BG)
    c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)

    draw_text(c, MARGIN, PAGE_H - 58, "제주대 교류학생 생활 플랫폼 수요조사 중간 결과", 26, "Malgun-Bold", NAVY)
    draw_text(c, MARGIN, PAGE_H - 84, f"이동/동행 수요와 오픈채팅 불편을 중심으로 | 응답 {total}명 | {report_date}", 13, "Malgun", MUTED)
    draw_text(c, PAGE_W - 245, PAGE_H - 58, "표본 수가 작아 방향성 확인용", 12, "Malgun-Bold", ORANGE)

    positive = dict(data["intent"]).get("긍정", 0)
    taxi = dict(data["openchat_find"]).get("택시팟", 0)
    stay_4weeks = data["stay_4weeks"]
    card_y = PAGE_H - 188
    metric_card(c, MARGIN, card_y, 210, 100, "응답 수", f"{total}명", "현재 연결된 응답", BLUE)
    metric_card(c, MARGIN + 228, card_y, 250, 100, "서비스 긍정 의향", f"{positive}명 / {pct(positive, total)}", "반드시+사용할 것 같다", GREEN)
    metric_card(c, MARGIN + 496, card_y, 250, 100, "오픈채팅 택시팟 탐색", f"{taxi}명 / {pct(taxi, total)}", "가장 많이 찾는 항목", ORANGE)
    metric_card(c, MARGIN + 764, card_y, 250, 100, "4주 이상 체류", f"{stay_4weeks}명 / {pct(stay_4weeks, total)}", "장기 체류 응답자 중심", TEAL)

    hbar_chart(c, MARGIN, 310, 575, 230, "Q3. 제주에서 가장 불편했던 점", "복수응답, 상위 불편 항목", data["pain"], total, color=BLUE)
    hbar_chart(c, 648, 310, 270, 230, "Q6. 오픈채팅에서 찾는 것", "주요 사용 목적", data["openchat_find"], total, color=ORANGE, label_w=90)
    stacked_intent_chart(c, 938, 310, 294, 230, "Q8. 서비스 사용 의향", "긍정/중립/부정 재분류", data["intent"], total)
    hbar_chart(c, MARGIN, 66, 575, 218, "Q5. 같이 하고 싶은 활동", "동행/모임 콘텐츠 후보", data["activity"], total, color=PURPLE)
    hbar_chart(c, 648, 66, 330, 218, "Q7. 오픈채팅 불편", "정보 탐색 과정의 마찰", data["openchat_pain"], total, color=TEAL, label_w=132)
    insight_box(c, 998, 66, 234, 218, data)


def write_pdf(data, output: Path, report_date: str):
    setup_fonts()
    output.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(output), pagesize=(PAGE_W, PAGE_H))
    c.setTitle("제주대 교류학생 생활 플랫폼 수요조사 중간 결과")
    draw_report(c, data, report_date)
    c.save()


def render_png(pdf_path: Path, png_path: Path):
    poppler = next((path for path in POPPLER_CANDIDATES if path.exists()), None)
    if not poppler:
        return
    prefix = png_path.with_suffix("")
    subprocess.run([str(poppler), "-png", "-singlefile", "-r", "144", str(pdf_path), str(prefix)], check=True)


def parse_args():
    parser = argparse.ArgumentParser(description="Build a survey summary report from CSV or Google Sheets.")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--csv", type=Path, help="Downloaded Google Forms responses CSV.")
    source.add_argument("--sheets-id", help="Google Sheets spreadsheet ID linked to Google Forms responses.")
    parser.add_argument("--range", default=os.getenv("ARA_SURVEY_SHEETS_RANGE"), help="Google Sheets range. If omitted, the first sheet tab is used.")
    parser.add_argument("--credentials", type=Path, default=os.getenv("GOOGLE_APPLICATION_CREDENTIALS"), help="Service account credentials JSON.")
    parser.add_argument("--date", default="2026-07-07", help="Report date label.")
    parser.add_argument("--pdf", type=Path, default=DEFAULT_PDF)
    parser.add_argument("--png", type=Path, default=DEFAULT_PNG)
    return parser.parse_args()


def main():
    args = parse_args()
    if args.csv:
        rows = load_csv(args.csv)
    else:
        if not args.credentials:
            raise SystemExit("--credentials is required with --sheets-id")
        rows = load_sheets(normalize_spreadsheet_id(args.sheets_id), args.range, args.credentials)
    if not rows:
        raise SystemExit("No response rows found.")
    data = build_report_data(rows)
    write_pdf(data, args.pdf, args.date)
    render_png(args.pdf, args.png)
    print(args.pdf)
    print(args.png)


if __name__ == "__main__":
    main()
