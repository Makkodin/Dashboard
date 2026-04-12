from __future__ import annotations

import html
import json
from copy import deepcopy
from datetime import date, datetime
from functools import lru_cache
from pathlib import Path
from typing import Any


def esc(v: Any) -> str:
    if v is None:
        return ""
    return html.escape(str(v))


def path_token(path: Path) -> tuple[str, int]:
    try:
        return str(path.resolve()), path.stat().st_mtime_ns
    except OSError:
        return str(path.resolve()), -1


def dir_token(path: Path) -> tuple[str, int]:
    return path_token(path)


@lru_cache(maxsize=1024)
def _read_json_raw(path_str: str, mtime_ns: int) -> Any:
    if mtime_ns < 0:
        raise FileNotFoundError(path_str)
    with open(path_str, "r", encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=1024)
def _read_text_raw(path_str: str, mtime_ns: int) -> str:
    if mtime_ns < 0:
        raise FileNotFoundError(path_str)
    return Path(path_str).read_text(encoding="utf-8")


def clear_file_caches() -> None:
    _read_json_raw.cache_clear()
    _read_text_raw.cache_clear()


def read_json(path: Path, default: dict) -> dict:
    path_str, mtime_ns = path_token(path)
    if mtime_ns < 0:
        return deepcopy(default)
    try:
        data = _read_json_raw(path_str, mtime_ns)
        if isinstance(data, dict):
            merged = deepcopy(default)
            merged.update(data)
            return merged
        return deepcopy(default)
    except Exception:
        return deepcopy(default)


def read_json_file(path: Path, default: Any) -> Any:
    path_str, mtime_ns = path_token(path)
    if mtime_ns < 0:
        return deepcopy(default)
    try:
        return _read_json_raw(path_str, mtime_ns)
    except Exception:
        return deepcopy(default)


def write_json(path: Path, data: Any):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    clear_file_caches()


def read_text(path: Path, default: str = "") -> str:
    path_str, mtime_ns = path_token(path)
    if mtime_ns < 0:
        return default
    try:
        text = _read_text_raw(path_str, mtime_ns)
        return text if text.strip() else default
    except Exception:
        return default


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    clear_file_caches()


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
