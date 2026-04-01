from __future__ import annotations

from copy import deepcopy
from typing import Any

from core.io_utils import read_json
from core.paths import immune_signatures_path


DEFAULT_IMMUNE_SIGNATURES = {
    "groups": [
        {
            "key": "lymphocyte_response",
            "title": "Лимфоцит-опосредованный провоспалительный иммунный ответ",
            "description": "Отражает активность адаптивного иммунного ответа с участием Т- и В-лимфоцитов, NK-клеток и антигенпрезентирующих молекул.",
            "summary_text": "Выраженная активация противоопухолевого иммунитета",
            "summary_icon": "↑",
            "summary_tone": "red",
            "items": [
                {"label": "MHCI", "value": 4.96},
                {"label": "MHCII", "value": -0.31},
                {"label": "Коактивационные молекулы", "value": -0.20},
                {"label": "Эффекторные клетки", "value": 2.50},
                {"label": "NK-клетки", "value": 2.02},
                {"label": "T-клетки", "value": 3.91},
                {"label": "B-клетки", "value": 0.44},
                {"label": "Th1-сигнатура", "value": 2.97},
                {"label": "Th2-сигнатура", "value": 0.41},
            ],
        },
        {
            "key": "fibrosis",
            "title": "Фибротические процессы",
            "description": "Характеризуют степень фиброза опухолевой стромы, ангиогенеза и ремоделирования внеклеточного матрикса.",
            "summary_text": "Процессы фиброза подавлены",
            "summary_icon": "↓",
            "summary_tone": "blue",
            "items": [
                {"label": "CAF", "value": -3.60},
                {"label": "Матрикс", "value": -4.06},
                {"label": "Ремоделирование матрикса", "value": -1.60},
                {"label": "Ангиогенез", "value": -2.23},
                {"label": "Эндотелий", "value": -2.79},
            ],
        },
        {
            "key": "myeloid_inflammation",
            "title": "Миелоидно-опосредованное воспаление",
            "description": "Включает активность макрофагов M1-типа, нейтрофилов и противоопухолевых цитокинов.",
            "summary_text": "Умеренная активация",
            "summary_icon": "•",
            "summary_tone": "neutral",
            "items": [
                {"label": "M1-сигнатуры", "value": 0.01},
                {"label": "Противоопухолевые цитокины", "value": 0.02},
                {"label": "Ингибирование контрольных точек", "value": 0.83},
                {"label": "Нейтрофильная сигнатура", "value": -0.38},
                {"label": "Трафик гранулоцитов", "value": -1.39},
            ],
        },
        {
            "key": "immunosuppression",
            "title": "Иммуносупрессия",
            "description": "Отражает наличие иммуносупрессивных клеток (Tregs, MDSC) и проопухолевых цитокинов в микроокружении.",
            "summary_text": "Минимальная иммуносупрессия",
            "summary_icon": "•",
            "summary_tone": "neutral",
            "items": [
                {"label": "T-регуляторные клетки", "value": 0.77},
                {"label": "MDSC", "value": -0.41},
                {"label": "Трафик MDSC", "value": -0.43},
                {"label": "Макрофаги", "value": 0.25},
                {"label": "Проопухолевые цитокины", "value": -0.65},
            ],
        },
        {
            "key": "proliferation_invasion",
            "title": "Пролиферативно-инвазивные характеристики",
            "description": "Характеризуют скорость деления опухолевых клеток и эпителиально-мезенхимальный переход.",
            "summary_text": "Пролиферация снижена",
            "summary_icon": "↓",
            "summary_tone": "blue",
            "items": [
                {"label": "Скорость пролиферации", "value": -2.12},
                {"label": "EMT-сигнатура", "value": 0.86},
            ],
        },
    ],
    "legend_min": -5.0,
    "legend_max": 5.0,
}


TONE_DEFAULTS = {
    "red": {"icon": "↑", "text": "#EF4444"},
    "blue": {"icon": "↓", "text": "#2563EB"},
    "neutral": {"icon": "•", "text": "#4B5563"},
    "green": {"icon": "↑", "text": "#16A34A"},
}


def _to_float(value: Any, fallback: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return fallback


def _normalize_items(items: Any, default_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not isinstance(items, list) or not items:
        return deepcopy(default_items)

    normalized: list[dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        label = str(item.get("label", "")).strip()
        if not label:
            continue
        value = max(-5.0, min(5.0, _to_float(item.get("value"), 0.0)))
        normalized.append({"label": label, "value": round(value, 2)})

    return normalized or deepcopy(default_items)


def load_immune_signatures(sample: str) -> dict[str, Any]:
    stored = read_json(immune_signatures_path(sample), DEFAULT_IMMUNE_SIGNATURES)
    groups_in = stored.get("groups") if isinstance(stored, dict) else None

    default_by_key = {group["key"]: group for group in DEFAULT_IMMUNE_SIGNATURES["groups"]}
    normalized_groups: list[dict[str, Any]] = []

    if isinstance(groups_in, list) and groups_in:
        for group in groups_in:
            if not isinstance(group, dict):
                continue
            key = str(group.get("key", "")).strip()
            base = deepcopy(default_by_key.get(key, {}))
            merged = deepcopy(base)
            merged.update(group)
            if not merged.get("key"):
                continue
            merged["title"] = str(merged.get("title", "")).strip() or merged["key"]
            merged["description"] = str(merged.get("description", "")).strip()
            merged["summary_text"] = str(merged.get("summary_text", "")).strip()
            tone = str(merged.get("summary_tone", "neutral")).strip().lower()
            if tone not in TONE_DEFAULTS:
                tone = "neutral"
            merged["summary_tone"] = tone
            merged["summary_icon"] = str(merged.get("summary_icon", TONE_DEFAULTS[tone]["icon"])).strip() or TONE_DEFAULTS[tone]["icon"]
            merged["items"] = _normalize_items(merged.get("items"), base.get("items", []))
            normalized_groups.append(merged)
    else:
        normalized_groups = deepcopy(DEFAULT_IMMUNE_SIGNATURES["groups"])

    return {
        "groups": normalized_groups,
        "legend_min": _to_float(stored.get("legend_min"), DEFAULT_IMMUNE_SIGNATURES["legend_min"]),
        "legend_max": _to_float(stored.get("legend_max"), DEFAULT_IMMUNE_SIGNATURES["legend_max"]),
    }
