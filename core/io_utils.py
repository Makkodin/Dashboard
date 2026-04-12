from __future__ import annotations

import html
import json
from copy import deepcopy
from datetime import date, datetime
from pathlib import Path
from typing import Any


def esc(v: Any) -> str:
    if v is None:
        return ""
    return html.escape(str(v))


def read_json(path: Path, default: dict) -> dict:
    if not path.exists():
        return deepcopy(default)
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            merged = deepcopy(default)
            merged.update(data)
            return merged
        return deepcopy(default)
    except Exception:
        return deepcopy(default)


def read_json_file(path: Path, default: Any) -> Any:
    if not path.exists():
        return deepcopy(default)
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return deepcopy(default)


def write_json(path: Path, data: Any):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def read_text(path: Path, default: str = "") -> str:
    if not path.exists():
        return default
    try:
        text = path.read_text(encoding="utf-8")
        return text if text.strip() else default
    except Exception:
        return default


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def load_timeline(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def parse_iso_date(value: Any) -> date:
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value).date()
        except Exception:
            return date.today()
    return date.today()


def serialize_date(value: Any) -> str:
    d = parse_iso_date(value)
    return d.isoformat()
