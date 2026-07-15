from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable


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
    loaded_at = max(
        str(korean_survey.get("loaded_at", "-")),
        str(foreign_survey.get("loaded_at", "-")),
    )
    return BriefContext(
        total=korean.total + foreign.total,
        korean=korean,
        foreign=foreign,
        status="Google Sheets 실시간 집계" if is_live else "저장 데이터 포함 집계",
        source_detail=(
            f"한국인 {SOURCE_NAMES.get(korean_source, korean_source)} · "
            f"외국인 {SOURCE_NAMES.get(foreign_source, foreign_source)}"
        ),
        loaded_at=loaded_at,
        is_live=is_live,
        has_data=(korean.total + foreign.total) > 0,
    )
