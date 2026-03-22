from __future__ import annotations

from typing import Any


def normalize_text(v: str) -> str:
    return str(v).strip().lower()


def build_timeline_items(timeline_data: dict[str, Any]) -> list[dict[str, str]]:
    items = []
    for stage_name, payload in timeline_data.items():
        items.append(
            {
                "stage": str(stage_name),
                "date": str(payload.get("Дата", "—")),
                "desc": str(payload.get("Описание", "—")),
            }
        )
    return items


def get_timeline_item_classes(items: list[dict[str, str]]) -> list[str]:
    classes = ["tl-default"] * len(items)

    surgery_indices = []
    progression_indices = []

    for i, item in enumerate(items):
        stage = normalize_text(item["stage"])
        if "хирург" in stage:
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