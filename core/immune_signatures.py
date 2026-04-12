from __future__ import annotations

from copy import deepcopy
import csv
import re
from typing import Any

from core.io_utils import read_json, read_json_file
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


def _to_float(value: Any, fallback: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return fallback


def _sample_scores(sample: str) -> dict[str, float]:
    path = immune_signature_scores_path()
    if not path.exists():
        return {}
    target = _normalize_sample_key(sample)
    try:
        with open(path, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f, delimiter="	")
            name_col = (reader.fieldnames or [""])[0]
            for row in reader:
                raw_name = str(row.get(name_col, ""))
                normalized = _normalize_sample_key(raw_name)
                if normalized == target or normalized.startswith(target):
                    return {k: _to_float(v) for k, v in row.items() if k != name_col}
    except Exception:
        return {}
    return {}


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
