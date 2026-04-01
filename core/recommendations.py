from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

from core.genetic_profile import load_hla_class_i, load_key_somatic_variants, read_tmb_value
from core.immune_status import load_immune_status
from core.io_utils import read_json
from core.paths import norma_alleles_path, tmb_path, vep_ann_path

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


def _recommendations_path(sample: str) -> Path:
    return Path("data") / sample / "edit" / "recommendations.json"


def _fmt_mut_per_mb(value: float | None) -> str:
    if value is None:
        return "нет данных"
    value_rounded = round(float(value), 2)
    text = f"{value_rounded:.2f}".rstrip("0").rstrip(".")
    return f"{text} мутаций/Мб"


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def _build_tmb_card(sample: str) -> dict[str, Any]:
    tmb_value = read_tmb_value(tmb_path(sample))
    if tmb_value is None:
        return {
            "tag": "УРОВЕНЬ TMB",
            "title": "Недостаточно данных по мутационной нагрузке",
            "body": "Файл с оценкой TMB отсутствует или не содержит распознаваемого значения. Для окончательной интерпретации необходимо подтвердить показатель мутационной нагрузки.",
            "tone": "gray",
        }

    if tmb_value > 12:
        title = "Высокая мутационная нагрузка"
        body = (
            f"Выявлена высокая мутационная нагрузка (TMB: {_fmt_mut_per_mb(tmb_value)}), что значительно превышает порог высокого уровня. "
            "Высокий TMB может быть связан с увеличением числа неоантигенов и с большей вероятностью ответа на ингибиторы контрольных точек (анти-PD-1/PD-L1)."
        )
        tone = "orange"
    elif tmb_value >= 10:
        title = "Погранично повышенная мутационная нагрузка"
        body = (
            f"Показатель TMB составляет {_fmt_mut_per_mb(tmb_value)} и находится в погранично повышенном диапазоне. "
            "Вероятность пользы от иммунотерапии может быть умеренной и должна интерпретироваться совместно с иммунным подтипом и экспрессией иммунных маркеров."
        )
        tone = "orange"
    else:
        title = "Низкая мутационная нагрузка"
        body = (
            f"Показатель TMB составляет {_fmt_mut_per_mb(tmb_value)} и не достигает порога высокой мутационной нагрузки. "
            "Сам по себе такой уровень TMB реже ассоциирован с выраженным ответом на иммунотерапию и требует опоры на дополнительные иммунологические маркеры."
        )
        tone = "gray"

    return {"tag": "УРОВЕНЬ TMB", "title": title, "body": body, "tone": tone}


_SUBTYPE_LABELS = {
    "IE": "Иммуно-богатый профиль опухоли",
    "IM": "Смешанный иммунный профиль опухоли",
    "ID": "Иммуно-дефицитный профиль опухоли",
}


def _build_subtype_card(sample: str) -> dict[str, Any]:
    status = load_immune_status(sample)
    subtype_code = str(status.get("tumor_subtype_class", "")).upper()
    subtype_title = _SUBTYPE_LABELS.get(subtype_code, "Иммунный профиль опухоли")
    total_immune = _safe_float(status.get("total_immune_percent"), 0.0)
    cd8_treg = _safe_float(status.get("cd8_treg_ratio"), 0.0)
    effector = _safe_float(status.get("effector_t_cells_percent"), 0.0)

    if subtype_code == "IE":
        body = (
            f"Иммунопрофилирование указывает на принадлежность к наиболее иммунно-активному подтипу. "
            f"Суммарная доля иммунных клеток составляет {total_immune:.1f}%, доля эффекторных T-клеток — {effector:.1f}%, соотношение CD8/Treg — {cd8_treg:.2f}. "
            "Такой профиль обычно ассоциирован с более высокой вероятностью ответа на иммунотерапию."
        )
        tone = "green"
    elif subtype_code == "ID":
        body = (
            f"Профиль соответствует иммунно-дефицитному варианту: суммарная доля иммунных клеток составляет {total_immune:.1f}%, а эффекторный T-клеточный компонент выражен ограниченно. "
            "Для усиления противоопухолевого ответа может потребоваться опора на дополнительные молекулярные и таргетные стратегии."
        )
        tone = "gray"
    else:
        body = (
            f"Профиль опухоли имеет смешанные иммунные характеристики. Суммарная доля иммунных клеток составляет {total_immune:.1f}%, доля эффекторных T-клеток — {effector:.1f}%, соотношение CD8/Treg — {cd8_treg:.2f}. "
            "Клиническая значимость такого профиля зависит от сочетания иммунной активности и стромально-супрессивного компонента."
        )
        tone = "green"

    return {"tag": "ИММУННЫЙ ПОДТИП", "title": subtype_title, "body": body, "tone": tone}


DRIVER_HINTS = {
    "BRAF": "Опухоль может быть чувствительна к комбинации ингибиторов BRAF + MEK, что открывает возможность таргетной терапии параллельно с иммунотерапевтическими подходами.",
    "NRAS": "Наличие активирующей мутации NRAS поддерживает биологию MAPK-сигналинга; прямой таргетный опцион ограничен, но мутация важна для стратификации и оценки комбинированных подходов.",
    "KIT": "Мутации KIT могут быть потенциальной мишенью для таргетной терапии у части пациентов и требуют клинико-молекулярной валидации конкретного варианта.",
    "NF1": "Нарушение NF1 указывает на дерегуляцию MAPK-пути и может сопровождать повышенную иммуногенность опухоли, но требует интерпретации в общем молекулярном контексте.",
    "TP53": "Изменение TP53 отражает геномную нестабильность и учитывается как дополнительный неблагоприятный молекулярный фактор, однако само по себе не формирует стандартную таргетную опцию.",
    "TERT": "Изменения TERT поддерживают репликативный потенциал опухоли и учитываются как значимый молекулярный признак при интегральной интерпретации.",
}


TARGET_DRIVER_GENES = ("BRAF", "NRAS", "KIT", "NF1", "TP53", "TERT")


def _pick_driver_variant(sample: str) -> tuple[str | None, str | None, str | None]:
    df = load_key_somatic_variants(vep_ann_path(sample))
    if df.empty:
        return None, None, None

    for gene in TARGET_DRIVER_GENES:
        sub = df[df["Ген"].astype(str).str.upper() == gene]
        if not sub.empty:
            row = sub.iloc[0]
            aa = str(row.get("Белковое изменение", "")).strip() or None
            cds = str(row.get("Нуклеотидное изменение", "")).strip() or None
            return gene, aa, cds
    return None, None, None


def _build_driver_card(sample: str) -> dict[str, Any]:
    gene, aa, cds = _pick_driver_variant(sample)
    if not gene:
        return {
            "tag": "ДРАЙВЕРНАЯ МУТАЦИЯ",
            "title": "Клинически значимая драйверная мутация не выделена",
            "body": "Среди ключевых соматических вариантов не выявлена драйверная мутация с очевидной интерпретацией для текущего набора рекомендаций. Решение о терапии следует опирать на иммунные показатели и клинический контекст.",
            "tone": "gray",
        }

    variant_bits = [gene]
    if aa and aa != "—":
        variant_bits.append(aa)
    variant_title = " ".join(variant_bits)

    cds_text = f" ({cds})" if cds and cds != "—" else ""
    hint = DRIVER_HINTS.get(gene, "Выявленный вариант требует интерпретации в клиническом и молекулярном контексте опухоли.")

    if gene == "BRAF":
        title = f"{variant_title} — мишень для таргетной терапии"
        tone = "blue"
    else:
        title = f"{variant_title} — клинически значимый молекулярный признак"
        tone = "blue"

    body = f"Обнаружена мутация {variant_title}{cds_text}. {hint}"
    return {"tag": "ДРАЙВЕРНАЯ МУТАЦИЯ", "title": title, "body": body, "tone": tone}


def _build_hla_card(sample: str) -> dict[str, Any]:
    rows = load_hla_class_i(norma_alleles_path(sample))
    if not rows:
        return {
            "tag": "HLA-I ПРОФИЛЬ",
            "title": "Недостаточно данных для интерпретации HLA-I",
            "body": "Файл HLA-типирования отсутствует или не содержит полного набора локусов HLA-A, HLA-B и HLA-C.",
            "tone": "gray",
        }

    homo_loci: list[str] = []
    protective_hits: list[str] = []
    allele_summary: list[str] = []

    for row in rows:
        locus = str(row.get("Локус", ""))
        a1 = str(row.get("Аллель 1", "—"))
        a2 = str(row.get("Аллель 2", "—"))
        status = str(row.get("Статус", ""))
        allele_summary.append(f"{locus}: {a1}/{a2}")
        if status == "Гомозигота":
            homo_loci.append(locus)
        for allele in (a1, a2):
            if any(allele.startswith(prefix) for prefix in PROTECTIVE_HLA):
                protective_hits.append(allele)

    if homo_loci:
        loci_text = ", ".join(homo_loci)
        body = (
            f"В HLA-профиле выявлена гомозиготность по локусам {loci_text}. "
            f"Набор аллелей: {'; '.join(allele_summary)}. Гомозиготность по локусам HLA-I может быть связана со снижением разнообразия презентируемых опухолевых антигенов и с меньшей выраженностью противоопухолевого иммунного ответа."
        )
        if protective_hits:
            uniq = ", ".join(sorted(set(protective_hits)))
            body += f" При этом обнаружены потенциально благоприятные аллели: {uniq}."
        tone = "red"
        title = "Выявлены признаки ограниченного разнообразия HLA-I"
        tag = "РИСКОВЫЕ HLA"
    else:
        body = (
            f"Профиль HLA-I остаётся гетерозиготным по ключевым локусам ({'; '.join(allele_summary)}), что поддерживает разнообразие антиген-презентирующего репертуара. "
            "Такой вариант обычно рассматривается как более благоприятный с точки зрения иммунного распознавания опухоли."
        )
        if protective_hits:
            uniq = ", ".join(sorted(set(protective_hits)))
            body += f" Обнаружены потенциально благоприятные аллели: {uniq}."
        tone = "green"
        title = "Сохранено разнообразие HLA-I профиля"
        tag = "HLA-I ПРОФИЛЬ"

    return {"tag": tag, "title": title, "body": body, "tone": tone}


def _auto_cards(sample: str) -> list[dict[str, Any]]:
    cards = [
        _build_tmb_card(sample),
        _build_subtype_card(sample),
        _build_driver_card(sample),
        _build_hla_card(sample),
    ]
    for idx, card in enumerate(cards, start=1):
        style = deepcopy(CARD_STYLES.get(card.get("tone", "gray"), CARD_STYLES["gray"]))
        card["index"] = f"{idx:02d}"
        card["style"] = style
    return cards


def load_recommendations(sample: str) -> dict[str, Any]:
    stored = read_json(_recommendations_path(sample), DEFAULT_RECOMMENDATIONS)
    result = deepcopy(DEFAULT_RECOMMENDATIONS)
    result.update(stored)

    cards = result.get("cards") or []
    if not cards:
        result["cards"] = _auto_cards(sample)
        return result

    normalized_cards: list[dict[str, Any]] = []
    for idx, raw in enumerate(cards, start=1):
        card = {
            "index": str(raw.get("index") or f"{idx:02d}"),
            "tag": str(raw.get("tag", "РЕКОМЕНДАЦИЯ")),
            "title": str(raw.get("title", "")),
            "body": str(raw.get("body", "")),
            "tone": str(raw.get("tone", "gray")),
        }
        card["style"] = deepcopy(CARD_STYLES.get(card["tone"], CARD_STYLES["gray"]))
        normalized_cards.append(card)
    result["cards"] = normalized_cards
    return result
