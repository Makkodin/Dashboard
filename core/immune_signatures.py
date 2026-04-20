from __future__ import annotations

from copy import deepcopy
import csv
from functools import lru_cache
import re
from typing import Any

from core.io_utils import path_token, read_json, read_json_file
from core.paths import defaults_immune_signatures_path, immune_signature_scores_path, immune_signatures_path


FALLBACK = {"groups": [], "legend_min": -5.0, "legend_max": 5.0, "missing_message": ""}
TONE_DEFAULTS = {
    "red": {"icon": "↑", "text": "#EF4444"},
    "blue": {"icon": "↓", "text": "#2563EB"},
    "neutral": {"icon": "•", "text": "#4B5563"},
    "green": {"icon": "↑", "text": "#16A34A"},
}


# Это функция для блока «нормализации образца ключевых». Она нужна для того, чтобы вынести отдельный шаг логики в самостоятельную и читаемую часть кода.
# Используется в следующих блоках: core/immune_signatures.py, core/immune_status.py.
# На вход: value.
# На выход: str.
def _normalize_sample_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", str(value).lower())


# Это функция для блока «to float». Она нужна для того, чтобы вынести отдельный шаг логики в самостоятельную и читаемую часть кода.
# Используется в следующих блоках: core/immune_signatures.py.
# На вход: value, fallback.
# На выход: float.
def _to_float(value: Any, fallback: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return fallback


@lru_cache(maxsize=128)
# Это функция для блока «образца scores cached». Она нужна для того, чтобы вынести отдельный шаг логики в самостоятельную и читаемую часть кода.
# Используется в следующих блоках: core/immune_signatures.py.
# На вход: sample, path_str, mtime_ns.
# На выход: кортеж[кортеж[str, float], ...]  или  None.
def _sample_scores_cached(sample: str, path_str: str, mtime_ns: int) -> tuple[tuple[str, float], ...] | None:
    if mtime_ns < 0:
        return None
    target = _normalize_sample_key(sample)
    try:
        with open(path_str, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f, delimiter="	")
            name_col = (reader.fieldnames or [""])[0]
            best_row: tuple[tuple[str, float], ...] | None = None
            best_rank = 99
            for row in reader:
                raw_name = str(row.get(name_col, "")).strip()
                if not raw_name:
                    continue
                normalized = _normalize_sample_key(raw_name)
                rank = None
                if normalized == target:
                    rank = 0
                elif normalized.startswith(target):
                    rank = 1
                elif target.startswith(normalized):
                    rank = 2
                if rank is None:
                    continue
                payload = tuple((k, _to_float(v)) for k, v in row.items() if k != name_col)
                if rank < best_rank:
                    best_row = payload
                    best_rank = rank
                    if rank == 0:
                        break
            return best_row
    except Exception:
        return None
    return None


# Это функция для блока «образца scores». Она нужна для того, чтобы вынести отдельный шаг логики в самостоятельную и читаемую часть кода.
# Используется в следующих блоках: core/immune_signatures.py.
# На вход: sample.
# На выход: словарь[str, float]  или  None.
def _sample_scores(sample: str) -> dict[str, float] | None:
    path_str, mtime_ns = path_token(immune_signature_scores_path())
    payload = _sample_scores_cached(sample, path_str, mtime_ns)
    if payload is None:
        return None
    return dict(payload)


# Это функция для загрузки данных, связанных с блоком «загрузки иммунного профиля иммунных сигнатур». 
# Используется в следующих блоках: sections/immune_signatures_block.py.
# На вход: sample.
# На выход: словарь[str, Any].
def load_immune_signatures(sample: str) -> dict[str, Any]:
    defaults = read_json_file(defaults_immune_signatures_path(), FALLBACK)
    if not isinstance(defaults, dict):
        defaults = deepcopy(FALLBACK)
    stored = read_json(immune_signatures_path(sample), defaults)
    result = deepcopy(defaults)
    if isinstance(stored, dict):
        result.update(stored)

    score_map = _sample_scores(sample)
    if score_map is None:
        return {
            "groups": [],
            "legend_min": _to_float(result.get("legend_min"), -5.0),
            "legend_max": _to_float(result.get("legend_max"), 5.0),
            "missing_message": "Иммунные сигнатуры отсутствуют",
        }

    groups = []
    for group in result.get("groups", []):
        if not isinstance(group, dict):
            continue
        merged = deepcopy(group)
        tone = str(merged.get("summary_tone", "neutral")).strip().lower()
        if tone not in TONE_DEFAULTS:
            tone = "neutral"
        merged["summary_tone"] = tone
        merged["summary_icon"] = str(merged.get("summary_icon") or TONE_DEFAULTS[tone]["icon"])
        items = []
        for item in merged.get("items", []):
            if not isinstance(item, dict):
                continue
            col = str(item.get("column", "")).strip()
            if not col:
                continue
            if col not in score_map:
                continue
            items.append({
                "label": str(item.get("label", "")).strip(),
                "column": col,
                "value": round(max(-5.0, min(5.0, _to_float(score_map[col], 0.0))), 2),
            })
        merged["items"] = items
        groups.append(merged)

    return {
        "groups": groups,
        "legend_min": _to_float(result.get("legend_min"), -5.0),
        "legend_max": _to_float(result.get("legend_max"), 5.0),
        "missing_message": "" if groups else "Иммунные сигнатуры отсутствуют",
    }
