from __future__ import annotations

import re
from copy import deepcopy
from datetime import datetime
from typing import Any
from uuid import uuid4

from core.io_utils import load_timeline, read_json_file, write_json
from core.paths import timeline_edit_path, timeline_path

_DATE_FORMATS = (
    "%d.%m.%Y",
    "%Y-%m-%d",
    "%d/%m/%Y",
    "%d-%m-%Y",
    "%Y/%m/%d",
    "%b %Y",
    "%B %Y",
)

RU_MONTHS = {
    "январь": 1,
    "января": 1,
    "февраль": 2,
    "февраля": 2,
    "март": 3,
    "марта": 3,
    "апрель": 4,
    "апреля": 4,
    "май": 5,
    "мая": 5,
    "июнь": 6,
    "июня": 6,
    "июль": 7,
    "июля": 7,
    "август": 8,
    "августа": 8,
    "сентябрь": 9,
    "сентября": 9,
    "октябрь": 10,
    "октября": 10,
    "ноябрь": 11,
    "ноября": 11,
    "декабрь": 12,
    "декабря": 12,
}

TIMELINE_ICON_OPTIONS = [
    ("surgery", "✂️"),
    ("progression", "⚠️"),
    ("immunotherapy", "🛡️"),
    ("treatment", "✚"),
]

TIMELINE_ICON_BG_PRESETS = [
    ("#CBD5E1", "⚪ Серая"),
    ("#BFDBFE", "🔵 Синяя"),
    ("#BBF7D0", "🟢 Зелёная"),
    ("#FDE68A", "🟡 Жёлтая"),
    ("#FCA5A5", "🔴 Красная"),
    ("#E9D5FF", "🟣 Фиолетовая"),
]

DEFAULT_NEW_ITEM = {
    "id": "",
    "stage": "Новый этап",
    "date": "",
    "desc": "",
    "icon": "treatment",
    "icon_bg": "#BFDBFE",
}


def normalize_text(v: str) -> str:
    return str(v).strip().lower()


def _parse_russian_month_date(value: str) -> datetime | None:
    text = normalize_text(value)
    match = re.fullmatch(r"([а-яё]+)\s+(\d{4})", text)
    if not match:
        return None
    month_name, year = match.groups()
    month = RU_MONTHS.get(month_name)
    if month is None:
        return None
    return datetime(int(year), month, 1)


def _parse_timeline_date(value: Any) -> tuple[int, datetime | None]:
    text = str(value).strip()
    if not text or text == "—":
        return 1, None

    ru_dt = _parse_russian_month_date(text)
    if ru_dt is not None:
        return 0, ru_dt

    for fmt in _DATE_FORMATS:
        try:
            return 0, datetime.strptime(text, fmt)
        except Exception:
            continue
    try:
        return 0, datetime.fromisoformat(text)
    except Exception:
        return 1, None


def _infer_icon(stage_name: str) -> str:
    s = normalize_text(stage_name)
    if "прогресс" in s:
        return "progression"
    if "хирург" in s or "операц" in s or "резекц" in s:
        return "surgery"
    if "+ ит" in s or "иммунотерап" in s or "anti-pd1" in s or "анти-pd1" in s:
        return "immunotherapy"
    return "treatment"


def _default_bg_for_icon(icon: str) -> str:
    return {
        "surgery": "#CBD5E1",
        "progression": "#FCA5A5",
        "immunotherapy": "#BBF7D0",
        "treatment": "#BFDBFE",
    }.get(icon, "#BFDBFE")


def _ensure_item_id(raw: dict[str, Any]) -> str:
    value = str(raw.get("id", "")).strip()
    return value or uuid4().hex


def _coerce_item(raw: Any) -> dict[str, str]:
    if not isinstance(raw, dict):
        item = deepcopy(DEFAULT_NEW_ITEM)
        item["id"] = uuid4().hex
        return item

    icon = str(raw.get("icon", "")).strip().lower() or ""
    if icon not in {k for k, _ in TIMELINE_ICON_OPTIONS}:
        icon = _infer_icon(str(raw.get("stage", "")))
    icon_bg = str(raw.get("icon_bg", "")).strip() or _default_bg_for_icon(icon)
    return {
        "id": _ensure_item_id(raw),
        "stage": str(raw.get("stage", "")).strip() or "Новый этап",
        "date": str(raw.get("date", "")).strip(),
        "desc": str(raw.get("desc", "")).strip(),
        "icon": icon,
        "icon_bg": icon_bg,
    }


def build_timeline_items(timeline_data: dict[str, Any]) -> list[dict[str, str]]:
    raw_items: list[tuple[int, tuple[int, datetime | None], dict[str, str]]] = []
    for index, (stage_name, payload) in enumerate(timeline_data.items()):
        payload = payload if isinstance(payload, dict) else {}
        icon = _infer_icon(str(stage_name))
        item = {
            "id": uuid4().hex,
            "stage": str(stage_name),
            "date": str(payload.get("Дата", "—")),
            "desc": str(payload.get("Описание", "—")),
            "icon": icon,
            "icon_bg": _default_bg_for_icon(icon),
        }
        raw_items.append((index, _parse_timeline_date(item["date"]), item))
    raw_items.sort(key=lambda x: (x[1][0], x[1][1] or datetime.max, x[0]))
    return [item for _, _, item in raw_items]


def load_treatment_items(sample: str) -> list[dict[str, str]]:
    edit_path = timeline_edit_path(sample)

    if edit_path.exists():
        edit_payload = read_json_file(edit_path, {"items": []})
        items_raw = []

        if isinstance(edit_payload, dict):
            items_raw = edit_payload.get("items", [])
        elif isinstance(edit_payload, list):
            items_raw = edit_payload

        if isinstance(items_raw, list):
            return [_coerce_item(item) for item in items_raw]

    timeline_data = load_timeline(timeline_path(sample))
    return build_timeline_items(timeline_data)


def save_treatment_items(sample: str, items: list[dict[str, Any]]) -> None:
    payload = {"items": [_coerce_item(item) for item in items]}
    write_json(timeline_edit_path(sample), payload)


def add_empty_treatment_item(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = deepcopy(items)
    item = deepcopy(DEFAULT_NEW_ITEM)
    item["id"] = uuid4().hex
    out.append(item)
    return out


def get_timeline_item_classes(items: list[dict[str, str]]) -> list[str]:
    classes = ["tl-default"] * len(items)
    surgery_indices = []
    progression_indices = []
    for i, item in enumerate(items):
        icon = item.get("icon") or _infer_icon(item.get("stage", ""))
        if icon == "surgery":
            surgery_indices.append(i)
        if icon == "progression":
            progression_indices.append(i)
    if len(surgery_indices) > 1:
        for idx in surgery_indices[:-1]:
            classes[idx] = "tl-surgery-old"
    for idx in progression_indices:
        classes[idx] = "tl-progression"
    if items:
        last_idx = len(items) - 1
        if classes[last_idx] != "tl-progression":
            classes[last_idx] = "tl-latest"
    return classes
