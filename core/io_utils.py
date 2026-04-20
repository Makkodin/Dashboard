from __future__ import annotations

import html
import json
from copy import deepcopy
from datetime import date, datetime
from functools import lru_cache
from pathlib import Path
from typing import Any


# Это функция для блока «esc». Она нужна для того, чтобы вынести отдельный шаг логики в самостоятельную и читаемую часть кода.
# Используется в следующих блоках: sections/annotation_blocks.py, sections/biomaterial_block.py.
# На вход: v.
# На выход: str.
def esc(v: Any) -> str:
    if v is None:
        return ""
    return html.escape(str(v))


# Это функция для блока «пути token». Она нужна для того, чтобы вынести отдельный шаг логики в самостоятельную и читаемую часть кода.
# Используется в следующих блоках: core/genetic_profile.py, core/immune_markers.py.
# На вход: path.
# На выход: кортеж[str, int].
def path_token(path: Path) -> tuple[str, int]:
    try:
        return str(path.resolve()), path.stat().st_mtime_ns
    except OSError:
        return str(path.resolve()), -1


# Это функция для блока «dir token». Она нужна для того, чтобы вынести отдельный шаг логики в самостоятельную и читаемую часть кода.
# Используется в следующих блоках: core/immune_status.py, core/paths.py.
# На вход: path.
# На выход: кортеж[str, int].
def dir_token(path: Path) -> tuple[str, int]:
    return path_token(path)


@lru_cache(maxsize=1024)
# Это функция для чтения данных, связанных с блоком «чтения JSON-данных raw». 
# Используется в следующих блоках: core/io_utils.py.
# На вход: path_str, mtime_ns.
# На выход: Any.
def _read_json_raw(path_str: str, mtime_ns: int) -> Any:
    if mtime_ns < 0:
        raise FileNotFoundError(path_str)
    with open(path_str, "r", encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=1024)
# Это функция для чтения данных, связанных с блоком «чтения текста raw». 
# Используется в следующих блоках: core/io_utils.py.
# На вход: path_str, mtime_ns.
# На выход: str.
def _read_text_raw(path_str: str, mtime_ns: int) -> str:
    if mtime_ns < 0:
        raise FileNotFoundError(path_str)
    return Path(path_str).read_text(encoding="utf-8")


# Это функция для блока «clear file caches». Она нужна для того, чтобы вынести отдельный шаг логики в самостоятельную и читаемую часть кода.
# Используется в следующих блоках: core/io_utils.py.
# На вход: функция не ожидает обязательных входных параметров.
# На выход: None.
def clear_file_caches() -> None:
    _read_json_raw.cache_clear()
    _read_text_raw.cache_clear()


# Это функция для чтения данных, связанных с блоком «чтения JSON-данных». 
# Используется в следующих блоках: core/genetic_profile.py, core/immune_markers.py.
# На вход: path, default.
# На выход: словарь.
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


# Это функция для чтения данных, связанных с блоком «чтения JSON-данных file». 
# Используется в следующих блоках: core/immune_markers.py, core/immune_signatures.py.
# На вход: path, default.
# На выход: Any.
def read_json_file(path: Path, default: Any) -> Any:
    path_str, mtime_ns = path_token(path)
    if mtime_ns < 0:
        return deepcopy(default)
    try:
        return _read_json_raw(path_str, mtime_ns)
    except Exception:
        return deepcopy(default)


# Это функция для блока «write JSON-данных». Она нужна для того, чтобы вынести отдельный шаг логики в самостоятельную и читаемую часть кода.
# Используется в следующих блоках: core/state.py, core/timeline.py.
# На вход: path, data.
# На выход: результат дальнейшего шага обработки.
def write_json(path: Path, data: Any):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    clear_file_caches()


# Это функция для чтения данных, связанных с блоком «чтения текста». 
# Используется в следующих блоках: app.py, sections/annotation_blocks.py, core/genetic_profile.py.
# На вход: path, default.
# На выход: str.
def read_text(path: Path, default: str = "") -> str:
    path_str, mtime_ns = path_token(path)
    if mtime_ns < 0:
        return default
    try:
        text = _read_text_raw(path_str, mtime_ns)
        return text if text.strip() else default
    except Exception:
        return default


# Это функция для блока «write текста». Она нужна для того, чтобы вынести отдельный шаг логики в самостоятельную и читаемую часть кода.
# Используется в следующих блоках: core/io_utils.py.
# На вход: path, text.
# На выход: None.
def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    clear_file_caches()


# Это функция для загрузки данных, связанных с блоком «загрузки таймлайна». 
# Используется в следующих блоках: core/timeline.py.
# На вход: path.
# На выход: словарь[str, Any].
def load_timeline(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


# Это функция для блока «parse iso date». Она нужна для того, чтобы вынести отдельный шаг логики в самостоятельную и читаемую часть кода.
# Используется в следующих блоках: sections/meta_block.py, sections/treatment_block.py.
# На вход: value.
# На выход: date.
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


# Это функция для блока «serialize date». Она нужна для того, чтобы вынести отдельный шаг логики в самостоятельную и читаемую часть кода.
# Используется в следующих блоках: core/state.py.
# На вход: value.
# На выход: str.
def serialize_date(value: Any) -> str:
    d = parse_iso_date(value)
    return d.isoformat()
