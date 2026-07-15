from __future__ import annotations

from base64 import b64encode
from dataclasses import dataclass
from html import escape
from io import BytesIO
from pathlib import Path
from typing import Any, Iterable

from PIL import Image


@dataclass(frozen=True)
class RankedMetric:
    label: str
    count: int
    percent: str


@dataclass(frozen=True)
class GroupBrief:
    label: str
    total: int
    pain: tuple[RankedMetric, ...]
    openchat_find: tuple[RankedMetric, ...]
    openchat_pain: tuple[RankedMetric, ...]


@dataclass(frozen=True)
class BriefContext:
    total: int
    korean: GroupBrief
    foreign: GroupBrief
    status: str
    source_detail: str
    loaded_at: str
    is_live: bool
    has_data: bool


SOURCE_NAMES = {
    "Google Sheets": "Google Sheets",
    "CSV fallback": "저장 CSV",
    "CSV": "저장 CSV",
    "CSV summary": "저장 집계",
    "empty": "데이터 없음",
}

MOVEMENT_LABELS = {
    "교통",
    "버스 노선",
    "택시비",
    "같이 이동할 사람 찾기",
    "여행 계획",
    "택시팟",
    "여행팟",
}
INFORMATION_LABELS = {
    "정보 부족",
    "공지",
    "생활정보",
    "시험정보",
    "원하는 글 찾기 어렵다",
    "글이 너무 많다",
    "지난 글 찾기 어렵다",
    "검색 기능 불편",
    "정보 정확성 모르겠다",
    "채팅이 빨리 올라간다",
}


def percent_text(value: int, total: int) -> str:
    if total <= 0:
        return "0%"
    return f"{value / total * 100:.1f}%"


def ranked_metrics(
    items: Iterable[tuple[str, int]], total: int, limit: int | None = 3
) -> tuple[RankedMetric, ...]:
    selected = list(items)
    if limit is not None:
        selected = selected[:limit]
    return tuple(
        RankedMetric(str(label), int(count), percent_text(int(count), total))
        for label, count in selected
    )


def _group(label: str, survey: dict[str, Any]) -> GroupBrief:
    data = survey["data"]
    total = int(data.get("n", 0))
    return GroupBrief(
        label=label,
        total=total,
        pain=ranked_metrics(data.get("pain", []), total),
        openchat_find=ranked_metrics(data.get("openchat_find", []), total),
        openchat_pain=ranked_metrics(data.get("openchat_pain", []), total),
    )


def build_brief_context(
    korean_survey: dict[str, Any], foreign_survey: dict[str, Any]
) -> BriefContext:
    korean = _group("한국인", korean_survey)
    foreign = _group("외국인", foreign_survey)
    korean_source = str(korean_survey.get("source", "empty"))
    foreign_source = str(foreign_survey.get("source", "empty"))
    is_live = korean_source == "Google Sheets" and foreign_source == "Google Sheets"
    total = korean.total + foreign.total
    timestamps = [
        timestamp
        for timestamp in (
            str(korean_survey.get("loaded_at", "-")),
            str(foreign_survey.get("loaded_at", "-")),
        )
        if timestamp not in {"", "-"}
    ]
    if total == 0:
        status = "응답 수집 대기"
    elif korean.total == 0 or foreign.total == 0:
        status = "일부 설문만 집계"
    elif is_live:
        status = "Google Sheets 실시간 집계"
    elif "Google Sheets" in {korean_source, foreign_source}:
        status = "일부 실시간 · 혼합 집계"
    else:
        status = "저장 데이터 기준 집계"
    return BriefContext(
        total=total,
        korean=korean,
        foreign=foreign,
        status=status,
        source_detail=(
            f"한국인 {SOURCE_NAMES.get(korean_source, korean_source)} · "
            f"외국인 {SOURCE_NAMES.get(foreign_source, foreign_source)}"
        ),
        loaded_at=max(timestamps) if timestamps else "-",
        is_live=is_live,
        has_data=total > 0,
    )


def _problem_rows(
    groups: tuple[tuple[GroupBrief, str], ...], labels: set[str]
) -> str:
    selected: list[tuple[str, RankedMetric, str]] = []
    for group, accent in groups:
        seen: set[str] = set()
        for metric in (*group.pain, *group.openchat_find, *group.openchat_pain):
            if metric.label in labels and metric.label not in seen:
                selected.append((group.label, metric, accent))
                seen.add(metric.label)
    if not selected:
        return '<p class="research-empty">아직 표시할 응답이 없습니다.</p>'
    rows = []
    for group_label, metric, accent in selected:
        width = min(100.0, float(metric.percent.rstrip("%") or 0))
        rows.append(
            f'''<div class="research-bar-row">
  <span class="research-bar-label">{escape(group_label)} · {escape(metric.label)}</span>
  <span class="research-bar-track"><span class="research-bar-fill {accent}" style="width:{width:.1f}%"></span></span>
  <strong>{metric.count}명 <small>{metric.percent}</small></strong>
</div>'''
        )
    return "\n".join(rows)


def intro_html(context: BriefContext) -> str:
    return f'''<section class="research-hero">
  <p class="research-kicker">JEJU EXCHANGE STUDENT RESEARCH</p>
  <h1>교류학생의 이동과 정보 탐색은 어디서 막혔을까?</h1>
  <p class="research-lead">학생의 실제 경험을 조사하고, 시냅스팟의 문제 정의로 이어진 근거를 정리했습니다.</p>
  <div class="research-status-grid">
    <div><span>전체 응답</span><strong>{context.total}명</strong></div>
    <div><span>한국인</span><strong>{context.korean.total}명</strong></div>
    <div><span>외국인</span><strong>{context.foreign.total}명</strong></div>
    <div><span>데이터 상태</span><strong class="is-status">{escape(context.status)}</strong></div>
  </div>
  <p class="research-source">{escape(context.source_detail)} · 마지막 갱신 {escape(context.loaded_at)}</p>
</section>'''


def conclusion_html(context: BriefContext) -> str:
    conclusion = (
        '<div class="research-conclusion">이동·동행 모집과 신뢰할 수 있는 '
        "생활정보 탐색이 함께 필요했습니다.</div>"
        if context.has_data
        else '<div class="research-conclusion is-empty">응답을 수집하고 있습니다.</div>'
    )
    return f'''<section class="research-section"><h2>먼저 볼 결론</h2>{conclusion}</section>'''


def findings_html(context: BriefContext) -> str:
    groups = ((context.korean, "korean"), (context.foreign, "foreign"))
    return f'''<section class="research-section">
  <div class="research-heading"><h2>응답이 가리킨 두 가지 문제</h2><span>복수 응답 · 집단 내 비율</span></div>
  <div class="research-two-column">
    <article class="research-signal korean"><p>PROBLEM 01 · 두 집단의 이동 경험</p><h3>이동과 동행 모집</h3>{_problem_rows(groups, MOVEMENT_LABELS)}</article>
    <article class="research-signal foreign"><p>PROBLEM 02 · 두 집단의 정보 경험</p><h3>공지와 생활정보 탐색</h3>{_problem_rows(groups, INFORMATION_LABELS)}</article>
  </div>
</section>'''


def comparison_html(context: BriefContext) -> str:
    def top_markup(group: GroupBrief) -> str:
        if not group.openchat_find:
            return "<strong>응답 수집 중</strong>"
        metric = group.openchat_find[0]
        return (
            f"<strong>{escape(metric.label)}</strong>"
            f"<small>{metric.count}명 · {metric.percent}</small>"
        )

    return f'''<section class="research-section">
  <div class="research-heading"><h2>한국인과 외국인의 경험은 어떻게 달랐나</h2><span>집단별 분모를 따로 계산</span></div>
  <div class="research-compare">
    <div><span>한국인 · n={context.korean.total}</span>{top_markup(context.korean)}</div>
    <div><span>외국인 · n={context.foreign.total}</span>{top_markup(context.foreign)}</div>
  </div>
  <p class="research-interpretation">두 집단 모두 사람과 정보를 제때 찾기 어렵다는 공통 문제를 보였습니다.</p>
</section>'''


def image_data_uri(path: Path) -> str:
    if not path.is_file() or path.suffix.lower() != ".png":
        return ""
    try:
        image_bytes = path.read_bytes()
        with Image.open(BytesIO(image_bytes)) as image:
            if image.format != "PNG":
                return ""
            image.verify()
        with Image.open(BytesIO(image_bytes)) as image:
            image.load()
    except (OSError, SyntaxError, ValueError, Image.DecompressionBombError):
        return ""
    encoded = b64encode(image_bytes).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def _feature(title: str, description: str, image_uri: str, alt: str) -> str:
    image = f'<img src="{image_uri}" alt="{escape(alt)}">' if image_uri else ""
    return f'''<article class="research-product-feature">
  {image}
  <div><h3>{escape(title)}</h3><p>{escape(description)}</p></div>
</article>'''


def product_bridge_html(
    context: BriefContext, meetings_path: Path, question_path: Path
) -> str:
    if not context.has_data:
        return ""
    meetings = _feature(
        "이동·동행 파티",
        "시간, 목적지, 인원을 기준으로 함께 이동할 사람을 찾습니다.",
        image_data_uri(meetings_path),
        "시냅스팟 이동·동행 파티 모바일 화면",
    )
    question = _feature(
        "근거 있는 정보 탐색",
        "공지와 생활정보를 질문하고 답변의 출처를 확인합니다.",
        image_data_uri(question_path),
        "시냅스팟 근거 있는 정보 탐색 모바일 화면",
    )
    return f'''<section class="research-product-bridge">
  <p class="research-kicker">FROM RESEARCH TO PRODUCT</p>
  <h2>이 근거가 시냅스팟의 두 기능으로 이어졌습니다.</h2>
  <p>설문이 기능의 효과를 입증한 것이 아니라, 구현할 문제의 우선순위를 정하는 근거로 사용됐습니다.</p>
  <div class="research-product-grid">{meetings}{question}</div>
</section>'''
