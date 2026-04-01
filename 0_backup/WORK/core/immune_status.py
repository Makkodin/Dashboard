from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import re
from typing import Any

from core.genetic_profile import read_tmb_value
from core.io_utils import read_json
from core.paths import immune_status_path, sample_dir, tmb_path

DEFAULT_COMPOSITION = [
    {"label": "B клетки", "value": 4.2, "color": "#7C3AED", "immune": True},
    {"label": "CD8 Т-клетки", "value": 17.1, "color": "#2563EB", "immune": True},
    {"label": "Фибробласты", "value": 12.8, "color": "#22C55E", "immune": False},
    {"label": "NK клетки", "value": 4.8, "color": "#A855F7", "immune": True},
    {"label": "Другие", "value": 21.7, "color": "#A3A3A3", "immune": False},
    {"label": "CD4 Т-клетки", "value": 15.8, "color": "#60A5FA", "immune": True},
    {"label": "Эндотелий", "value": 9.1, "color": "#F472B6", "immune": False},
    {"label": "Моноцит. клетки", "value": 8.6, "color": "#EF4444", "immune": True},
    {"label": "T-рег. лимфоциты", "value": 5.9, "color": "#7DD3FC", "immune": True},
]

DEFAULT_IMMUNE_STATUS = {
    "purity_percent": None,
    "tumor_subtype_title": "",
    "tumor_subtype_class": "",
    "tumor_subtype_description": "",
    "total_immune_percent": None,
    "cd8_treg_ratio": None,
    "effector_t_cells_percent": None,
    "composition": deepcopy(DEFAULT_COMPOSITION),
}


SUBTYPE_TEXT = {
    "IE": {
        "title": "Иммуно-богатая",
        "description": (
            "Характеризуется высоким уровнем иммунной инфильтрации и выраженной "
            "цитолитической активностью. Такой профиль обычно ассоциирован с "
            "повышенной вероятностью ответа на иммунотерапию и более благоприятным прогнозом."
        ),
    },
    "IM": {
        "title": "Смешанная иммунная",
        "description": (
            "Опухоль сочетает признаки иммунной инфильтрации и стромального компонента. "
            "Ответ на иммунотерапию возможен, но зависит от выраженности эффекторного иммунного ответа."
        ),
    },
    "ID": {
        "title": "Иммуно-дефицитная",
        "description": (
            "Характеризуется низкой иммунной инфильтрацией и ограниченной представленностью эффекторных клеток. "
            "Такой профиль чаще связан со сниженной вероятностью выраженного ответа на иммунотерапию."
        ),
    },
}


def _extract_purity_from_filename(folder: Path) -> float | None:
    if not folder.exists():
        return None

    for path in folder.glob("cellularity_check_*.txt"):
        match = re.search(r"cellularity_check_(\d+(?:\.\d+)?)", path.name)
        if match:
            try:
                value = float(match.group(1))
                if value <= 1:
                    return round(value * 100, 1)
                return round(value, 1)
            except Exception:
                continue
    return None


def _normalize_composition(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cleaned: list[dict[str, Any]] = []
    total = 0.0

    for item in items:
        label = str(item.get("label", "")).strip()
        if not label:
            continue
        try:
            value = float(item.get("value", 0))
        except Exception:
            value = 0.0
        value = max(value, 0.0)
        total += value
        cleaned.append(
            {
                "label": label,
                "value": value,
                "color": str(item.get("color", "#94A3B8")),
                "immune": bool(item.get("immune", False)),
            }
        )

    if not cleaned or total <= 0:
        return deepcopy(DEFAULT_COMPOSITION)

    normalized: list[dict[str, Any]] = []
    for item in cleaned:
        normalized.append({**item, "value": round(item["value"] / total * 100, 1)})
    return normalized


def _infer_subtype(tmb_value: float | None, purity_percent: float | None) -> tuple[str, str, str]:
    if tmb_value is not None and tmb_value >= 12:
        code = "IE"
    elif purity_percent is not None and purity_percent >= 60:
        code = "ID"
    else:
        code = "IM"

    subtype = SUBTYPE_TEXT[code]
    return subtype["title"], code, subtype["description"]


def _compute_total_immune_percent(composition: list[dict[str, Any]]) -> float:
    return round(sum(item["value"] for item in composition if item.get("immune")), 1)


def _compute_cd8_treg_ratio(composition: list[dict[str, Any]]) -> float:
    cd8 = next((item["value"] for item in composition if item["label"] == "CD8 Т-клетки"), 0.0)
    treg = next((item["value"] for item in composition if item["label"] == "T-рег. лимфоциты"), 0.0)
    if treg <= 0:
        return round(cd8, 2)
    return round(cd8 / treg, 2)


def _compute_effector_t_cells(composition: list[dict[str, Any]]) -> float:
    effectors = 0.0
    for label in ("CD8 Т-клетки", "CD4 Т-клетки"):
        effectors += next((item["value"] for item in composition if item["label"] == label), 0.0)
    return round(effectors, 1)


def build_immune_interpretation(
    composition: list[dict[str, Any]],
    total_immune_percent: float,
    cd8_treg_ratio: float,
    effector_t_cells_percent: float,
) -> str:
    comp = {item["label"]: float(item["value"]) for item in composition}

    b_cells = comp.get("B клетки", 0.0)
    cd8 = comp.get("CD8 Т-клетки", 0.0)
    fibro = comp.get("Фибробласты", 0.0)
    nk = comp.get("NK клетки", 0.0)
    other = comp.get("Другие", 0.0)
    cd4 = comp.get("CD4 Т-клетки", 0.0)
    endothelium = comp.get("Эндотелий", 0.0)
    monocytes = comp.get("Моноцит. клетки", 0.0)
    treg = comp.get("T-рег. лимфоциты", 0.0)

    if total_immune_percent >= 50:
        line1 = (
            f"Иммунная инфильтрация выражена: суммарная доля иммунных клеток составляет {total_immune_percent:.1f}%. "
            f"Наиболее заметный вклад вносят CD8 Т-клетки ({cd8:.1f}%), CD4 Т-клетки ({cd4:.1f}%) и моноцитарные клетки ({monocytes:.1f}%)."
        )
    elif total_immune_percent >= 35:
        line1 = (
            f"Иммунная инфильтрация умеренная: суммарная доля иммунных клеток составляет {total_immune_percent:.1f}%. "
            f"Основные иммунные популяции представлены CD8 Т-клетками ({cd8:.1f}%) и CD4 Т-клетками ({cd4:.1f}%)."
        )
    else:
        line1 = (
            f"Иммунная инфильтрация снижена: суммарная доля иммунных клеток составляет {total_immune_percent:.1f}%. "
            f"Эффекторные иммунные популяции представлены ограниченно."
        )

    if cd8_treg_ratio >= 2.0:
        line2 = (
            f"Соотношение CD8/Treg равно {cd8_treg_ratio:.2f}, что указывает на преобладание эффекторного цитотоксического компонента "
            f"над регуляторным супрессивным звеном; доля эффекторных T-клеток составляет {effector_t_cells_percent:.1f}%."
        )
    else:
        line2 = (
            f"Соотношение CD8/Treg равно {cd8_treg_ratio:.2f}; выраженного преобладания эффекторного звена над регуляторным не наблюдается. "
            f"Суммарная доля эффекторных T-клеток составляет {effector_t_cells_percent:.1f}%."
        )

    stromal = fibro + endothelium
    suppressive = monocytes + treg
    line3 = (
        f"Стромальный компонент представлен фибробластами ({fibro:.1f}%) и эндотелием ({endothelium:.1f}%), суммарно {stromal:.1f}%. "
        f"Дополнительный вклад в микросреду вносят B клетки ({b_cells:.1f}%), NK клетки ({nk:.1f}%), регуляторные T-клетки ({treg:.1f}%) и прочие клетки ({other:.1f}%)."
    )

    if stromal >= 20 or suppressive >= 14:
        line4 = (
            f"В целом профиль сочетает активный иммунный ответ с заметным стромально-супрессивным компонентом, "
            f"что может влиять на выраженность противоопухолевой активности."
        )
    else:
        line4 = (
            f"В целом профиль соответствует иммунно-активной микросреде без выраженного преобладания стромально-супрессивного компонента."
        )

    return " ".join([line1, line2, line3, line4])


def load_immune_status(sample: str) -> dict[str, Any]:
    folder = sample_dir(sample)
    stored = read_json(immune_status_path(sample), DEFAULT_IMMUNE_STATUS)

    result = deepcopy(DEFAULT_IMMUNE_STATUS)
    result.update(stored)

    composition = result.get("composition") or deepcopy(DEFAULT_COMPOSITION)
    result["composition"] = _normalize_composition(composition)

    purity_percent = result.get("purity_percent")
    if purity_percent in (None, ""):
        purity_percent = _extract_purity_from_filename(folder)
    try:
        purity_percent = float(purity_percent) if purity_percent is not None else None
    except Exception:
        purity_percent = None
    if purity_percent is None:
        purity_percent = 29.0
    result["purity_percent"] = round(purity_percent, 1)

    tmb_value = read_tmb_value(tmb_path(sample))
    if not result.get("tumor_subtype_title") or not result.get("tumor_subtype_class"):
        title, subtype_class, description = _infer_subtype(tmb_value, result["purity_percent"])
        result["tumor_subtype_title"] = title
        result["tumor_subtype_class"] = subtype_class
        if not result.get("tumor_subtype_description"):
            result["tumor_subtype_description"] = description

    if result.get("total_immune_percent") in (None, ""):
        result["total_immune_percent"] = _compute_total_immune_percent(result["composition"])
    else:
        result["total_immune_percent"] = round(float(result["total_immune_percent"]), 1)

    if result.get("cd8_treg_ratio") in (None, ""):
        result["cd8_treg_ratio"] = _compute_cd8_treg_ratio(result["composition"])
    else:
        result["cd8_treg_ratio"] = round(float(result["cd8_treg_ratio"]), 2)

    if result.get("effector_t_cells_percent") in (None, ""):
        result["effector_t_cells_percent"] = _compute_effector_t_cells(result["composition"])
    else:
        result["effector_t_cells_percent"] = round(float(result["effector_t_cells_percent"]), 1)

    result["interpretation_text"] = build_immune_interpretation(
        result["composition"],
        result["total_immune_percent"],
        result["cd8_treg_ratio"],
        result["effector_t_cells_percent"],
    )

    return result
