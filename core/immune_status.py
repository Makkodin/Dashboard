from __future__ import annotations

from copy import deepcopy
import csv
from functools import lru_cache
import re
from pathlib import Path
from typing import Any

from core.genetic_profile import read_tmb_value
from core.io_utils import dir_token, path_token, read_json_file
from core.paths import (
    classified_samples_path,
    defaults_immune_status_path,
    immune_status_path,
    sample_dir,
    tmb_path,
)


DEFAULT_STATUS_FALLBACK = {
    "purity_percent": None,
    "tumor_subtype_title": "",
    "tumor_subtype_class": "",
    "tumor_subtype_description": "",
    "composition": [],
    "subtype_catalog": {},
}


def _safe_float(value: Any) -> float | None:
    try:
        if value in (None, ""):
            return None
        return float(value)
    except Exception:
        return None


@lru_cache(maxsize=128)
def _extract_purity_from_filename_cached(folder_str: str, folder_mtime_ns: int) -> float | None:
    folder = Path(folder_str)
    if folder_mtime_ns < 0 or not folder.exists():
        return None
    for path in folder.glob("cellularity_check_*.txt"):
        match = re.search(r"cellularity_check_(\d+(?:\.\d+)?)", path.name)
        if match:
            value = _safe_float(match.group(1))
            if value is None:
                continue
            if value <= 1:
                return round(value * 100, 1)
            return round(value, 1)
    return None


def _extract_purity_from_filename(folder: Path) -> float | None:
    folder_str, folder_mtime_ns = dir_token(folder)
    return _extract_purity_from_filename_cached(folder_str, folder_mtime_ns)


def _normalize_composition(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cleaned = []
    total = 0.0
    for item in items or []:
        if not isinstance(item, dict):
            continue
        label = str(item.get("label", "")).strip()
        if not label:
            continue
        value = max(_safe_float(item.get("value")) or 0.0, 0.0)
        total += value
        cleaned.append({
            "label": label,
            "value": value,
            "color": str(item.get("color", "#94A3B8")),
            "immune": bool(item.get("immune", False)),
        })
    if not cleaned or total <= 0:
        return []
    return [{**item, "value": round(item["value"] / total * 100, 1)} for item in cleaned]


def _normalize_sample_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", str(value).lower())


@lru_cache(maxsize=256)
def _match_sample_code_cached(sample: str, path_str: str, mtime_ns: int) -> str:
    if mtime_ns < 0:
        return ""
    target = _normalize_sample_key(sample)
    try:
        with open(path_str, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f, delimiter="\t")
            name_col = (reader.fieldnames or [""])[0]
            value_col = "TME" if "TME" in (reader.fieldnames or []) else None
            if not value_col:
                return ""
            best_match = ""
            for row in reader:
                raw_name = str(row.get(name_col, ""))
                if not raw_name:
                    continue
                normalized = _normalize_sample_key(raw_name)
                if normalized == target or normalized.startswith(target):
                    best_match = str(row.get(value_col, "")).strip()
                    if normalized == target:
                        break
            return best_match
    except Exception:
        return ""


def _match_sample_code(sample: str, source_path: Path) -> str:
    path_str, mtime_ns = path_token(source_path)
    return _match_sample_code_cached(sample, path_str, mtime_ns)


def _catalog_entry(catalog: dict[str, Any], code: str) -> dict[str, str]:
    entry = catalog.get(code) if isinstance(catalog, dict) else None
    if isinstance(entry, dict):
        return {
            "title": str(entry.get("title", "")).strip(),
            "description": str(entry.get("description", "")).strip(),
        }
    return {"title": "", "description": ""}


def _infer_subtype(catalog: dict[str, Any], tmb_value: float | None, purity_percent: float | None) -> tuple[str, str, str]:
    if tmb_value is not None and tmb_value >= 12:
        code = "IE"
    elif purity_percent is not None and purity_percent >= 60:
        code = "D"
    else:
        code = "IM"
    entry = _catalog_entry(catalog, code)
    title = entry["title"] or code
    description = entry["description"]
    return title, code, description


def _compute_total_immune_percent(composition: list[dict[str, Any]]) -> float:
    return round(sum(item["value"] for item in composition if item.get("immune")), 1)


def _compute_cd8_treg_ratio(composition: list[dict[str, Any]]) -> float:
    cd8 = next((item["value"] for item in composition if item["label"] == "CD8 Т-клетки"), 0.0)
    treg = next((item["value"] for item in composition if item["label"] == "T-рег. лимфоциты"), 0.0)
    if treg <= 0:
        return round(cd8, 2)
    return round(cd8 / treg, 2)


def _compute_effector_t_cells(composition: list[dict[str, Any]]) -> float:
    value = 0.0
    for label in ("CD8 Т-клетки", "CD4 Т-клетки"):
        value += next((item["value"] for item in composition if item["label"] == label), 0.0)
    return round(value, 1)


def build_immune_interpretation(data: dict[str, Any]) -> str:
    composition = data.get("composition", [])
    by_label = {item["label"]: float(item["value"]) for item in composition}
    total_immune = float(data.get("total_immune_percent", 0.0))
    cd8_treg = float(data.get("cd8_treg_ratio", 0.0))
    effector = float(data.get("effector_t_cells_percent", 0.0))
    fibro = by_label.get("Фибробласты", 0.0)
    endothelium = by_label.get("Эндотелий", 0.0)
    cd8 = by_label.get("CD8 Т-клетки", 0.0)
    cd4 = by_label.get("CD4 Т-клетки", 0.0)
    monocytes = by_label.get("Моноцит. клетки", 0.0)
    b_cells = by_label.get("B клетки", 0.0)
    nk = by_label.get("NK клетки", 0.0)
    treg = by_label.get("T-рег. лимфоциты", 0.0)
    other = by_label.get("Другие", 0.0)

    parts = []
    if total_immune >= 50:
        parts.append(f"Иммунная инфильтрация выражена: суммарная доля иммунных клеток составляет {total_immune:.1f}%.")
    else:
        parts.append(f"Иммунная инфильтрация умеренная: суммарная доля иммунных клеток составляет {total_immune:.1f}%.")

    parts.append(
        f"Наиболее заметный вклад вносят CD8 Т-клетки ({cd8:.1f}%), CD4 Т-клетки ({cd4:.1f}%) и моноцитарные клетки ({monocytes:.1f}%)."
    )
    parts.append(
        f"Соотношение CD8/Treg равно {cd8_treg:.2f}, а доля эффекторных T-клеток составляет {effector:.1f}%."
    )
    parts.append(
        f"Стромальный компонент представлен фибробластами ({fibro:.1f}%) и эндотелием ({endothelium:.1f}%), суммарно {fibro + endothelium:.1f}%."
    )
    parts.append(
        f"Дополнительный вклад в микросреду вносят B клетки ({b_cells:.1f}%), NK клетки ({nk:.1f}%), регуляторные T-клетки ({treg:.1f}%) и прочие клетки ({other:.1f}%)."
    )
    return " ".join(parts)


def load_immune_status(sample: str) -> dict[str, Any]:
    defaults = read_json_file(defaults_immune_status_path(), DEFAULT_STATUS_FALLBACK)
    if not isinstance(defaults, dict):
        defaults = deepcopy(DEFAULT_STATUS_FALLBACK)

    stored_path = immune_status_path(sample)

    # ВАЖНО:
    # если файла нет, stored должен быть ПУСТЫМ, а не defaults,
    # иначе defaults ошибочно считаются данными образца
    stored = read_json_file(stored_path, {})
    if not isinstance(stored, dict):
        stored = {}

    result = deepcopy(defaults)
    result.update(stored)

    stored_composition = _normalize_composition(stored.get("composition", []))
    default_composition = _normalize_composition(defaults.get("composition", []))

    if stored_composition:
        result["composition"] = stored_composition
        composition_source = "sample_file"
    elif default_composition:
        result["composition"] = default_composition
        composition_source = "defaults"
    else:
        result["composition"] = []
        composition_source = "missing"

    stored_purity = _safe_float(stored.get("purity_percent"))
    extracted_purity = _extract_purity_from_filename(sample_dir(sample))
    if stored_purity is not None:
        purity_percent = stored_purity
        purity_source = "sample_file"
    elif extracted_purity is not None:
        purity_percent = extracted_purity
        purity_source = "sample_folder"
    else:
        purity_percent = 0.0
        purity_source = "missing"
    result["purity_percent"] = round(purity_percent, 1)

    subtype_catalog = result.get("subtype_catalog", {})
    stored_subtype = str(stored.get("tumor_subtype_class", "")).strip()
    classified_subtype = _match_sample_code(sample, classified_samples_path()) if not stored_subtype else ""
    subtype_code = stored_subtype or classified_subtype

    if subtype_code:
        entry = _catalog_entry(subtype_catalog, subtype_code)
        result["tumor_subtype_class"] = subtype_code
        result["tumor_subtype_title"] = str(result.get("tumor_subtype_title") or entry["title"] or subtype_code)
        result["tumor_subtype_description"] = str(result.get("tumor_subtype_description") or entry["description"])
        subtype_source = "sample_file" if stored_subtype else "classified_table"
    else:
        title, code, description = _infer_subtype(
            subtype_catalog,
            read_tmb_value(tmb_path(sample)),
            purity_percent
        )
        result["tumor_subtype_class"] = code
        result["tumor_subtype_title"] = str(result.get("tumor_subtype_title") or title)
        result["tumor_subtype_description"] = str(result.get("tumor_subtype_description") or description)
        subtype_source = "heuristic"

    total_immune = _safe_float(result.get("total_immune_percent"))
    if total_immune is None:
        total_immune = _compute_total_immune_percent(result["composition"])
    result["total_immune_percent"] = round(total_immune, 1)

    cd8_treg_ratio = _safe_float(result.get("cd8_treg_ratio"))
    if cd8_treg_ratio is None:
        cd8_treg_ratio = _compute_cd8_treg_ratio(result["composition"])
    result["cd8_treg_ratio"] = round(cd8_treg_ratio, 2)

    effector_t_cells = _safe_float(result.get("effector_t_cells_percent"))
    if effector_t_cells is None:
        effector_t_cells = _compute_effector_t_cells(result["composition"])
    result["effector_t_cells_percent"] = round(effector_t_cells, 1)

    has_stored_interpretation = bool(str(stored.get("interpretation", "")).strip())
    result["interpretation"] = str(result.get("interpretation") or build_immune_interpretation(result))

    result["data_quality"] = {
        "composition_source": composition_source,
        "composition_is_placeholder": composition_source != "sample_file",
        "purity_source": purity_source,
        "purity_is_placeholder": purity_source == "missing",
        "subtype_source": subtype_source,
        "subtype_is_placeholder": subtype_source == "heuristic",
        "interpretation_source": "sample_file" if has_stored_interpretation else "auto_generated",
        "interpretation_is_placeholder": (not has_stored_interpretation) and composition_source != "sample_file",
    }
    return result