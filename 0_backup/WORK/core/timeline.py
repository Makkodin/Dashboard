from __future__ import annotations

from datetime import datetime
from typing import Any


_DATE_FORMATS = (
    "%d.%m.%Y",
    "%Y-%m-%d",
    "%d/%m/%Y",
    "%d-%m-%Y",
    "%Y/%m/%d",
)


def normalize_text(v: str) -> str:
    return str(v).strip().lower()


def _parse_timeline_date(value: Any) -> tuple[int, datetime | None]:
    text = str(value).strip()
    if not text or text == "—":
        return 1, None

    for fmt in _DATE_FORMATS:
        try:
            return 0, datetime.strptime(text, fmt)
        except ValueError:
            continue

    try:
        return 0, datetime.fromisoformat(text)
    except Exception:
        return 1, None


def build_timeline_items(timeline_data: dict[str, Any]) -> list[dict[str, str]]:
    raw_items: list[tuple[int, tuple[int, datetime | None], dict[str, str]]] = []

    for index, (stage_name, payload) in enumerate(timeline_data.items()):
        date_text = str(payload.get("Дата", "—"))
        raw_items.append(
            (
                index,
                _parse_timeline_date(date_text),
                {
                    "stage": str(stage_name),
                    "date": date_text,
                    "desc": str(payload.get("Описание", "—")),
                },
            )
        )

    raw_items.sort(key=lambda x: (x[1][0], x[1][1] or datetime.max, x[0]))
    return [item for _, _, item in raw_items]


def get_timeline_item_classes(items: list[dict[str, str]]) -> list[str]:
    classes = ["tl-default"] * len(items)

    surgery_indices = []
    progression_indices = []

    for i, item in enumerate(items):
        stage = normalize_text(item["stage"])
        if "хирург" in stage or "операц" in stage or "резекц" in stage:
            surgery_indices.append(i)
        if "прогресс" in stage:
            progression_indices.append(i)

    if len(surgery_indices) > 1:
        for idx in surgery_indices[:-1]:
            classes[idx] = "tl-surgery-old"

    for idx in progression_indices:
        classes[idx] = "tl-progression"

    if items:
        last_idx = len(items) - 1
        last_stage = normalize_text(items[last_idx]["stage"])
        if "прогресс" not in last_stage:
            classes[last_idx] = "tl-latest"

    return classes
