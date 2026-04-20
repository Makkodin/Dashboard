from __future__ import annotations

from copy import deepcopy
from typing import Any

from core.genetic_profile import load_hla_class_i, load_key_somatic_variants, read_tmb_value
from core.immune_status import load_immune_status
from core.io_utils import read_json
from core.paths import norma_alleles_path, recommendations_path, tmb_path, vep_ann_path

DEFAULT_RECOMMENDATIONS = {
    "section_title": "Результаты биоинформатического анализа",
    "section_subtitle": "Интегративная интерпретация молекулярного профиля пациента",
    "cards": [],
}
CARD_STYLES = {
    "orange": {"accent": "#FB923C", "soft": "#FFF7ED", "tag_bg": "#FFEDD5", "tag_fg": "#EA580C"},
    "green": {"accent": "#22C55E", "soft": "#F0FDF4", "tag_bg": "#DCFCE7", "tag_fg": "#15803D"},
    "blue": {"accent": "#60A5FA", "soft": "#EFF6FF", "tag_bg": "#DBEAFE", "tag_fg": "#2563EB"},
    "red": {"accent": "#F87171", "soft": "#FEF2F2", "tag_bg": "#FEE2E2", "tag_fg": "#DC2626"},
    "gray": {"accent": "#94A3B8", "soft": "#F8FAFC", "tag_bg": "#E2E8F0", "tag_fg": "#475569"},
}
PROTECTIVE_HLA = ("A*02", "B*44", "B*35")
SUBTYPE_LABELS = {
    "IE": "Иммуно-богатый профиль опухоли",
    "IE/F": "Иммуно-богатый профиль с фиброзным компонентом",
    "IM": "Смешанный иммунный профиль опухоли",
    "D": "Иммуно-дефицитный профиль опухоли",
    "ID": "Иммуно-дефицитный профиль опухоли",
}
DRIVER_HINTS = {
    "BRAF": "Опухоль может быть чувствительна к комбинации ингибиторов BRAF + MEK, что открывает возможность таргетной терапии параллельно с иммунотерапевтическими подходами.",
    "KRAS": "Мутация KRAS поддерживает активацию MAPK-пути и учитывается как значимый драйверный признак при интерпретации терапевтических опций.",
    "HRAS": "Мутация HRAS указывает на активацию MAPK-сигналинга и требует интерпретации в клинико-молекулярном контексте опухоли.",
    "NRAS": "Наличие активирующей мутации NRAS поддерживает биологию MAPK-сигналинга; прямой таргетный опцион ограничен, но мутация важна для стратификации и оценки комбинированных подходов.",
    "NF1": "Нарушение NF1 указывает на дерегуляцию MAPK-пути и может сопровождать повышенную иммуногенность опухоли, но требует интерпретации в общем молекулярном контексте.",
    "TP53": "Изменение TP53 отражает геномную нестабильность и учитывается как дополнительный неблагоприятный молекулярный фактор.",
    "CDKN2A": "Нарушение CDKN2A связано с потерей контроля клеточного цикла и учитывается как клинически значимый драйверный признак.",
    "PTEN": "Потеря PTEN может сопровождаться активацией PI3K/AKT-пути и изменением чувствительности к терапии.",
}
TARGET_DRIVER_GENES = ("BRAF", "NRAS", "KRAS", "HRAS", "NF1", "TP53", "CDKN2A", "PTEN")


# Это функция для блока «нормализации cards». Она нужна для того, чтобы вынести отдельный шаг логики в самостоятельную и читаемую часть кода.
# Используется в следующих блоках: core/recommendations.py.
# На вход: cards.
# На выход: список[словарь[str, Any]].
def _normalize_cards(cards: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for idx, raw_card in enumerate(cards, start=1):
        if not isinstance(raw_card, dict):
            continue
        card = deepcopy(raw_card)
        tone = str(card.get("tone", "gray")).strip().lower() or "gray"
        if tone not in CARD_STYLES:
            tone = "gray"
        card["tone"] = tone
        card["index"] = str(card.get("index") or f"{idx:02d}")
        card["style"] = deepcopy(card.get("style") or CARD_STYLES[tone])
        normalized.append(card)
    return normalized


# Это функция для блока «fmt mut per mb». Она нужна для того, чтобы вынести отдельный шаг логики в самостоятельную и читаемую часть кода.
# Используется в следующих блоках: core/recommendations.py.
# На вход: value.
# На выход: str.
def _fmt_mut_per_mb(value: float | None) -> str:
    if value is None:
        return "нет данных"
    text = f"{float(value):.2f}".rstrip("0").rstrip(".")
    return f"{text} мутаций/Мб"


# Это функция для блока «safe float». Она нужна для того, чтобы вынести отдельный шаг логики в самостоятельную и читаемую часть кода.
# Используется в следующих блоках: core/immune_status.py, core/recommendations.py.
# На вход: value, default.
# На выход: float.
def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


# Это функция для блока «сборки tmb card». Она нужна для того, чтобы вынести отдельный шаг логики в самостоятельную и читаемую часть кода.
# Используется в следующих блоках: sections/genetic_profile_block.py, core/recommendations.py.
# На вход: sample.
# На выход: словарь[str, Any].
def _build_tmb_card(sample: str) -> dict[str, Any]:
    tmb_value = read_tmb_value(tmb_path(sample))
    if tmb_value is None:
        return {"tag": "УРОВЕНЬ TMB", "title": "Недостаточно данных по мутационной нагрузке", "body": "Файл с оценкой TMB отсутствует или не содержит распознаваемого значения.", "tone": "gray"}
    if tmb_value > 12:
        return {"tag": "УРОВЕНЬ TMB", "title": "Высокая мутационная нагрузка", "body": f"Выявлена высокая мутационная нагрузка (TMB: {_fmt_mut_per_mb(tmb_value)}), что считается благоприятным признаком для рассмотрения иммунотерапии ингибиторами контрольных точек.", "tone": "orange"}
    if tmb_value >= 10:
        return {"tag": "УРОВЕНЬ TMB", "title": "Погранично повышенная мутационная нагрузка", "body": f"Показатель TMB составляет {_fmt_mut_per_mb(tmb_value)} и находится в погранично повышенном диапазоне. Интерпретацию следует проводить совместно с иммунным подтипом и иммунными маркерами.", "tone": "orange"}
    return {"tag": "УРОВЕНЬ TMB", "title": "Низкая мутационная нагрузка", "body": f"Показатель TMB составляет {_fmt_mut_per_mb(tmb_value)} и не достигает порога высокой мутационной нагрузки.", "tone": "gray"}


# Это функция для блока «сборки subtype card». Она нужна для того, чтобы вынести отдельный шаг логики в самостоятельную и читаемую часть кода.
# Используется в следующих блоках: core/recommendations.py.
# На вход: sample.
# На выход: словарь[str, Any].
def _build_subtype_card(sample: str) -> dict[str, Any]:
    status = load_immune_status(sample)
    subtype_code = str(status.get("tumor_subtype_class", "")).upper()
    subtype_title = SUBTYPE_LABELS.get(subtype_code, "Иммунный профиль опухоли")
    total_immune = _safe_float(status.get("total_immune_percent"), 0.0)
    cd8_treg = _safe_float(status.get("cd8_treg_ratio"), 0.0)
    effector = _safe_float(status.get("effector_t_cells_percent"), 0.0)
    body = (
        f"Иммунопрофилирование указывает на подтип {subtype_code or '—'}. Суммарная доля иммунных клеток составляет {total_immune:.1f}%, "
        f"доля эффекторных T-клеток — {effector:.1f}%, соотношение CD8/Treg — {cd8_treg:.2f}."
    )
    tone = "green" if subtype_code.startswith("IE") else ("gray" if subtype_code in {"D", "ID"} else "blue")
    return {"tag": "ИММУННЫЙ ПОДТИП", "title": subtype_title, "body": body, "tone": tone}


# Это функция для блока «pick driver варианта». Она нужна для того, чтобы вынести отдельный шаг логики в самостоятельную и читаемую часть кода.
# Используется в следующих блоках: core/recommendations.py.
# На вход: sample.
# На выход: кортеж[str  или  None, str  или  None, str  или  None].
def _pick_driver_variant(sample: str) -> tuple[str | None, str | None, str | None]:
    df = load_key_somatic_variants(vep_ann_path(sample))
    if df.empty:
        return None, None, None
    for gene in TARGET_DRIVER_GENES:
        sub = df[df["Ген"].astype(str).str.upper() == gene]
        if not sub.empty:
            row = sub.iloc[0]
            return gene, str(row.get("Белковое изменение", "")).strip(), str(row.get("Нуклеотидное изменение", "")).strip()
    return None, None, None


# Это функция для блока «сборки driver card». Она нужна для того, чтобы вынести отдельный шаг логики в самостоятельную и читаемую часть кода.
# Используется в следующих блоках: core/recommendations.py.
# На вход: sample.
# На выход: словарь[str, Any].
def _build_driver_card(sample: str) -> dict[str, Any]:
    gene, aa, cds = _pick_driver_variant(sample)
    if not gene:
        return {"tag": "ДРАЙВЕРНАЯ МУТАЦИЯ", "title": "Клинически значимая драйверная мутация не выделена", "body": "Среди ключевых соматических вариантов не выявлена драйверная мутация для автоматического вывода в рекомендации.", "tone": "gray"}
    variant = " ".join([bit for bit in [gene, aa if aa and aa != "—" else ""] if bit])
    cds_text = f" ({cds})" if cds and cds != "—" else ""
    return {"tag": "ДРАЙВЕРНАЯ МУТАЦИЯ", "title": f"{variant} — клинически значимый молекулярный признак", "body": f"Обнаружена мутация {variant}{cds_text}. {DRIVER_HINTS.get(gene, 'Выявленный вариант требует клинической интерпретации.')}", "tone": "blue"}


# Это функция для блока «сборки HLA-профиля card». Она нужна для того, чтобы вынести отдельный шаг логики в самостоятельную и читаемую часть кода.
# Используется в следующих блоках: sections/genetic_profile_block.py, core/recommendations.py.
# На вход: sample.
# На выход: словарь[str, Any].
def _build_hla_card(sample: str) -> dict[str, Any]:
    rows = load_hla_class_i(norma_alleles_path(sample))
    if not rows:
        return {"tag": "HLA-I ПРОФИЛЬ", "title": "Недостаточно данных для интерпретации HLA-I", "body": "Файл HLA-типирования отсутствует или не содержит полного набора локусов HLA-A, HLA-B и HLA-C.", "tone": "gray"}
    homo_loci, protective_hits, allele_summary = [], [], []
    for row in rows:
        locus = str(row.get("locus", ""))
        a1 = str(row.get("allele_1", "—"))
        a2 = str(row.get("allele_2", "—"))
        status = str(row.get("status", ""))
        allele_summary.append(f"{locus}: {a1}/{a2}")
        if status == "Гомозигота":
            homo_loci.append(locus)
        for allele in (a1, a2):
            if any(allele.startswith(prefix) for prefix in PROTECTIVE_HLA):
                protective_hits.append(allele)
    if homo_loci:
        body = f"В HLA-профиле выявлена гомозиготность по локусам {', '.join(homo_loci)}. Гомозиготность HLA-I рассматривается как неблагоприятный прогностический признак. Набор аллелей: {'; '.join(allele_summary)}."
        tone = "red"
        title = "Выявлены признаки ограниченного разнообразия HLA-I"
        tag = "РИСКОВЫЕ HLA"
    else:
        body = f"Профиль HLA-I остаётся гетерозиготным по ключевым локусам ({'; '.join(allele_summary)}), что поддерживает разнообразие антиген-презентирующего репертуара."
        tone = "green"
        title = "Сохранено разнообразие HLA-I профиля"
        tag = "HLA-I ПРОФИЛЬ"
    if protective_hits:
        body += f" Обнаружены потенциально благоприятные аллели: {', '.join(sorted(set(protective_hits)))}."
    return {"tag": tag, "title": title, "body": body, "tone": tone}


# Это функция для блока «auto cards». Она нужна для того, чтобы вынести отдельный шаг логики в самостоятельную и читаемую часть кода.
# Используется в следующих блоках: core/recommendations.py.
# На вход: sample.
# На выход: список[словарь[str, Any]].
def _auto_cards(sample: str) -> list[dict[str, Any]]:
    cards = [_build_tmb_card(sample), _build_subtype_card(sample), _build_driver_card(sample), _build_hla_card(sample)]
    return _normalize_cards(cards)


# Это функция для загрузки данных, связанных с блоком «загрузки рекомендаций». 
# Используется в следующих блоках: sections/recommendations_block.py.
# На вход: sample.
# На выход: словарь[str, Any].
def load_recommendations(sample: str) -> dict[str, Any]:
    stored = read_json(recommendations_path(sample), DEFAULT_RECOMMENDATIONS)
    result = deepcopy(DEFAULT_RECOMMENDATIONS)
    result.update(stored)
    if not result.get("cards"):
        result["cards"] = _auto_cards(sample)
        return result
    result["cards"] = _normalize_cards(result.get("cards", []))
    return result
