from __future__ import annotations

from copy import deepcopy
import csv
from functools import lru_cache
import re
from typing import Any

from core.io_utils import path_token, read_json, read_json_file
from core.paths import defaults_immune_signatures_path, immune_signature_scores_path, immune_signatures_path


FALLBACK = {"groups": [], "legend_min": -5.0, "legend_max": 5.0}
TONE_DEFAULTS = {
    "red": {"icon": "↑", "text": "#EF4444"},
    "blue": {"icon": "↓", "text": "#2563EB"},
    "neutral": {"icon": "•", "text": "#4B5563"},
    "green": {"icon": "↑", "text": "#16A34A"},
}


def _normalize_sample_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", str(value).lower())


def _sample_base_key(value: str) -> str:
    base = re.sub(r"(?:[_\-\s]?(?:19|20)\d{2})$", "", str(value).strip(), flags=re.IGNORECASE)
    return _normalize_sample_key(base)


def _sample_year(value: str) -> int:
    match = re.search(r"(?:19|20)\d{2}$", str(value).strip())
    return int(match.group(0)) if match else -1


def _to_float(value: Any, fallback: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return fallback


@lru_cache(maxsize=128)
def _sample_scores_cached(sample: str, path_str: str, mtime_ns: int) -> tuple[tuple[str, float], ...]:
    if mtime_ns < 0:
        return tuple()

    target = _normalize_sample_key(sample)
    target_base = _sample_base_key(sample)
    best_rank: tuple[int, int] | None = None
    best_row: dict[str, Any] | None = None

    try:
        with open(path_str, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f, delimiter="	")
            name_col = (reader.fieldnames or [""])[0]
            for row in reader:
                raw_name = str(row.get(name_col, "")).strip()
                if not raw_name:
                    continue

                normalized = _normalize_sample_key(raw_name)
                base_key = _sample_base_key(raw_name)
                year = _sample_year(raw_name)

                score = -1
                if normalized == target:
                    score = 4
                elif base_key and base_key == target_base:
                    score = 3
                elif normalized.startswith(target):
                    score = 2
                elif target.startswith(normalized):
                    score = 1

                if score < 0:
                    continue

                rank = (score, year)
                if best_rank is None or rank > best_rank:
                    best_rank = rank
                    best_row = row

        if best_row is not None:
            return tuple((k, _to_float(v)) for k, v in best_row.items() if k != name_col)
    except Exception:
        return tuple()
    return tuple()


def _sample_scores(sample: str) -> dict[str, float]:
    path_str, mtime_ns = path_token(immune_signature_scores_path())
    return dict(_sample_scores_cached(sample, path_str, mtime_ns))


def load_immune_signatures(sample: str) -> dict[str, Any]:
    defaults = read_json_file(defaults_immune_signatures_path(), FALLBACK)
    if not isinstance(defaults, dict):
        defaults = deepcopy(FALLBACK)
    stored = read_json(immune_signatures_path(sample), defaults)
    result = deepcopy(defaults)
    if isinstance(stored, dict):
        result.update(stored)

    score_map = _sample_scores(sample)
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
            value = item.get("value")
            if col and col in score_map:
                value = score_map[col]
            items.append({
                "label": str(item.get("label", "")).strip(),
                "column": col,
                "value": round(max(-5.0, min(5.0, _to_float(value, 0.0))), 2),
            })
        merged["items"] = items
        groups.append(merged)

    return {
        "groups": groups,
        "legend_min": _to_float(result.get("legend_min"), -5.0),
        "legend_max": _to_float(result.get("legend_max"), 5.0),
    }
