from __future__ import annotations

import base64
import csv
import math
from copy import deepcopy
from pathlib import Path
from typing import Any

from core.io_utils import read_json
from core.paths import immune_markers_path, rsem_gene_tpm_path, rsem_test_gene_tpm_path

SECTION_SUBTITLE = "Уровень относительно меланомной когорты TCGA"

MARKER_REFERENCE = {
    "PDCD1": {"mean": 1.65, "sd": 0.78, "default_value": 1.08, "default_percentile": 29, "default_level": "LOW"},
    "CTLA4": {"mean": 1.85, "sd": 0.62, "default_value": 1.92, "default_percentile": 48, "default_level": "LOW"},
    "LAG3": {"mean": 2.05, "sd": 0.68, "default_value": 2.14, "default_percentile": 55, "default_level": "MEDIUM"},
    "CXCL9": {"mean": 2.10, "sd": 0.56, "default_value": 2.05, "default_percentile": 47, "default_level": "MEDIUM"},
    "CXCL10": {"mean": 2.20, "sd": 0.58, "default_value": 2.24, "default_percentile": 52, "default_level": "MEDIUM"},
    "CXCL11": {"mean": 1.88, "sd": 0.62, "default_value": 1.78, "default_percentile": 42, "default_level": "MEDIUM"},
    "STAT1": {"mean": 2.70, "sd": 0.36, "default_value": 3.02, "default_percentile": 76, "default_level": "HIGH"},
    "STAT2": {"mean": 2.86, "sd": 0.19, "default_value": 3.37, "default_percentile": 100, "default_level": "HIGH"},
    "CD274": {"mean": 1.72, "sd": 0.39, "default_value": 2.18, "default_percentile": 75, "default_level": "HIGH"},
    "FOXP3": {"mean": 1.55, "sd": 0.44, "default_value": 1.36, "default_percentile": 33, "default_level": "MEDIUM"},
    "IL2RA": {"mean": 1.62, "sd": 0.34, "default_value": 1.66, "default_percentile": 52, "default_level": "MEDIUM"},
    "MRC1": {"mean": 1.98, "sd": 0.33, "default_value": 1.92, "default_percentile": 43, "default_level": "MEDIUM"},
}

DEFAULT_IMMUNE_MARKERS = {
    "panels": [
        {
            "key": "checkpoint_markers",
            "title": "Экспрессионные маркеры ингибиторов контрольных точек",
            "subtitle": "Потенциал иммунной системы к противоопухолевому ответу",
            "note": "Экспрессия ингибиторов контрольных точек отражает потенциал иммунной системы к противоопухолевому ответу. Высокие уровни могут указывать на чувствительность к иммунотерапии.",
            "cards": [
                {"gene": "PDCD1", "description": "Высокая экспрессия PD-1/PD-L1 ассоциирована с агрессивными формами рака."},
                {"gene": "CTLA4", "description": "Высокая экспрессия CTLA4 часто коррелирует с более высокой вероятностью ответа на иммунотерапию."},
                {"gene": "LAG3", "description": "Высокий уровень LAG3 коррелирует с неблагоприятным прогнозом, прогрессированием опухоли и устойчивостью к терапии."},
            ],
        },
        {
            "key": "ifng_signature",
            "title": "IFN-γ сигнатура",
            "subtitle": "Активация противоопухолевого иммунного ответа",
            "note": "IFN-γ сигнатура отражает активацию противоопухолевого иммунного ответа. Высокая экспрессия может указывать на воспалительное микроокружение опухоли.",
            "cards": [
                {"gene": "CXCL9", "description": "Хемокин, привлекающий эффекторные T-клетки в опухолевое микроокружение."},
                {"gene": "CXCL10", "description": "Хемокин, способствующий миграции активированных T-клеток и NK-клеток."},
                {"gene": "CXCL11", "description": "Хемокин, регулирующий привлечение лимфоцитов к месту воспаления и в опухоль."},
                {"gene": "STAT1", "description": "Транскрипционный фактор, активируемый IFN-γ, играет ключевую роль в противоопухолевом иммунитете."},
                {"gene": "STAT2", "description": "Участвует в передаче сигналов интерферона I типа и активации противовирусного иммунного ответа."},
            ],
        },
        {
            "key": "immunosuppression_markers",
            "title": "Иммуносупрессия",
            "subtitle": "Маркеры иммунного подавления",
            "note": "Маркеры иммуносупрессии отражают степень подавления противоопухолевого иммунного ответа в микроокружении опухоли. Высокие уровни иммуносупрессивных факторов могут указывать на необходимость комбинированной иммунотерапии.",
            "cards": [
                {"gene": "CD274", "description": "Экспрессия PD-L1 на опухолевых клетках подавляет T-клеточный ответ через PD-1 рецептор. Высокий уровень связан с иммуносупрессивным микроокружением и предиктивен для ответа на анти-PD-1/PD-L1 терапию."},
                {"gene": "FOXP3", "description": "Транскрипционный фактор регуляторных T-клеток (Treg). Высокий уровень FOXP3+ инфильтрации ассоциирован с иммуносупрессией и снижением противоопухолевого иммунного ответа."},
                {"gene": "IL2RA", "description": "Альфа-субъединица рецептора IL-2, экспрессируется активированными T-клетками и Treg. Высокая экспрессия может указывать на накопление Treg в опухолевом микроокружении."},
                {"gene": "MRC1", "description": "Рецептор маннозы — маркер M2-поляризованных макрофагов. Высокий уровень MRC1 свидетельствует об иммуносупрессивном фенотипе TAM (опухоль-ассоциированных макрофагов)."},
            ],
        },
    ]
}


LEVEL_COLORS = {
    "LOW": "#3B82F6",
    "MEDIUM": "#EAB308",
    "HIGH": "#EF4444",
}

LEVEL_LABELS = {
    "LOW": "Низкий",
    "MEDIUM": "Средний",
    "HIGH": "Высокий",
}


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _normalize_gene_symbol(raw: Any) -> str:
    text = str(raw).strip()
    if not text:
        return ""
    if "|" in text:
        parts = [part.strip() for part in text.split("|") if part.strip()]
        non_ensg = [part for part in parts if not part.upper().startswith("ENSG")]
        if non_ensg:
            text = non_ensg[-1]
        else:
            text = parts[-1]
    text = text.split(".")[0].strip()
    return text.upper()


def _first_existing_path(*paths: Path) -> Path | None:
    for path in paths:
        if path.exists():
            return path
    return None


def _detect_gene_column(headers: list[str]) -> str:
    preferred = [
        "gene_symbol",
        "gene",
        "Gene",
        "gene_name",
        "symbol",
        "Symbol",
        "GENE",
        "GeneName",
        "gene_id",
        "geneID",
    ]
    for name in preferred:
        if name in headers:
            return name
    return headers[0]


def _maybe_float(value: Any) -> float | None:
    try:
        if value in (None, ""):
            return None
        return float(value)
    except Exception:
        return None


def _read_expression_values(sample: str) -> dict[str, float]:
    path = _first_existing_path(rsem_gene_tpm_path(sample), rsem_test_gene_tpm_path(sample))
    if path is None:
        return {}

    try:
        with open(path, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f, delimiter="	")
            headers = reader.fieldnames or []
            if not headers:
                return {}
            gene_col = _detect_gene_column(headers)
            value_cols = [h for h in headers if h != gene_col]
            out: dict[str, float] = {}
            for row in reader:
                gene = _normalize_gene_symbol(row.get(gene_col, ""))
                if not gene:
                    continue
                value = None
                for col in value_cols:
                    value = _maybe_float(row.get(col))
                    if value is not None:
                        break
                if value is None:
                    continue
                prev = out.get(gene)
                if prev is None or value > prev:
                    out[gene] = value
            return out
    except Exception:
        return {}


def _log2_tpm(value: float) -> float:
    return math.log2(max(0.0, value) + 1.0)


def _normal_cdf(x: float, mean: float, sd: float) -> float:
    z = (x - mean) / max(sd, 1e-6)
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def _percentile_from_value(value: float, mean: float, sd: float) -> int:
    pct = round(_normal_cdf(value, mean, sd) * 100)
    return int(_clamp(pct, 1, 100))


def _level_from_percentile(percentile: int) -> str:
    if percentile >= 75:
        return "HIGH"
    if percentile >= 35:
        return "MEDIUM"
    return "LOW"


def _svg_to_data_uri(svg_text: str) -> str:
    b64 = base64.b64encode(svg_text.encode("utf-8")).decode("utf-8")
    return f"data:image/svg+xml;base64,{b64}"


def _histogram_svg(gene: str, sample_value: float, mean: float, sd: float) -> str:
    width = 320
    height = 194
    left = 42
    right = 10
    top = 42
    bottom = 48
    plot_w = width - left - right
    plot_h = height - top - bottom
    bins = 24
    x_min = max(0.0, mean - 3.2 * sd)
    x_max = max(x_min + 1.0, mean + 3.2 * sd)

    centers = [x_min + (i + 0.5) * (x_max - x_min) / bins for i in range(bins)]
    heights = [math.exp(-0.5 * ((c - mean) / max(sd, 1e-6)) ** 2) for c in centers]
    max_h = max(heights) if heights else 1.0
    heights = [h / max_h for h in heights]

    sample_x = _clamp(sample_value, x_min, x_max)
    sample_bin = int((sample_x - x_min) / max(x_max - x_min, 1e-6) * bins)
    sample_bin = max(0, min(bins - 1, sample_bin))

    bars = []
    selected_bar = None
    bin_w = plot_w / bins
    for idx, frac in enumerate(heights):
        bar_h = frac * plot_h
        x = left + idx * bin_w + 1
        y = top + plot_h - bar_h
        w = max(3.0, bin_w - 2)
        h = max(2.0, bar_h)
        bars.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="1.5" fill="#8FA8EE" />')
        if idx == sample_bin:
            bars.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="1.5" fill="#F09984" />')
            selected_bar = (x, y, w, h)

    x_ticks = [x_min, (x_min + x_max) / 2, x_max]
    tick_elems = []
    for val in x_ticks:
        px = left + (val - x_min) / max(x_max - x_min, 1e-6) * plot_w
        tick_elems.append(f'<line x1="{px:.1f}" y1="{top+plot_h}" x2="{px:.1f}" y2="{top+plot_h+4}" stroke="#6B7280" stroke-width="1" />')
        tick_elems.append(f'<text x="{px:.1f}" y="{height-24}" font-size="10" text-anchor="middle" fill="#4B5563">{val:.1f}</text>')

    y_ticks = []
    for frac, label in [(0.0, '0'), (0.5, ''), (1.0, '')]:
        py = top + plot_h - frac * plot_h
        y_ticks.append(f'<line x1="{left-4}" y1="{py:.1f}" x2="{left}" y2="{py:.1f}" stroke="#6B7280" stroke-width="1" />')
        if label:
            y_ticks.append(f'<text x="{left-8}" y="{py+3:.1f}" font-size="10" text-anchor="end" fill="#4B5563">{label}</text>')

    legend = ''.join([
        '<rect x="18" y="10" width="18" height="8" rx="1.5" fill="#8FA8EE"/>',
        '<text x="42" y="17" font-size="12" fill="#374151">TCGA</text>',
        '<rect x="18" y="26" width="18" height="8" rx="1.5" fill="#F09984"/>',
        '<text x="42" y="33" font-size="12" fill="#374151">образец</text>',
    ])

    selected_outline = ''
    if selected_bar is not None:
        x, y, w, h = selected_bar
        selected_outline = f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="1.5" fill="none" stroke="#111827" stroke-width="2" />'

    return ''.join([
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect x="0.5" y="0.5" width="319" height="193" rx="8" fill="#FFFFFF" stroke="#E5E7EB"/>',
        legend,
        f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top+plot_h}" stroke="#111827" stroke-width="1.2"/>',
        f'<line x1="{left}" y1="{top+plot_h}" x2="{left+plot_w}" y2="{top+plot_h}" stroke="#111827" stroke-width="1.2"/>',
        ''.join(y_ticks),
        ''.join(tick_elems),
        ''.join(bars),
        selected_outline,
        f'<text x="14" y="{top+plot_h/2:.1f}" font-size="11" font-weight="600" text-anchor="middle" fill="#111827" transform="rotate(-90 14 {top+plot_h/2:.1f})">N</text>',
        f'<text x="{left+plot_w/2:.1f}" y="{height-6}" font-size="11" font-weight="600" text-anchor="middle" fill="#111827">Log2(TPM+1)</text>',
        '</svg>',
    ])

def _build_card(gene: str, description: str, expression_values: dict[str, float]) -> dict[str, Any]:
    ref = MARKER_REFERENCE[gene]
    tpm = expression_values.get(gene)
    if tpm is not None:
        sample_value = round(_log2_tpm(tpm), 2)
        percentile = _percentile_from_value(sample_value, ref["mean"], ref["sd"])
        level = _level_from_percentile(percentile)
    else:
        sample_value = float(ref["default_value"])
        percentile = int(ref["default_percentile"])
        level = str(ref["default_level"])

    return {
        "gene": gene,
        "description": description,
        "sample_value": sample_value,
        "percentile": percentile,
        "level": level,
        "level_label": LEVEL_LABELS.get(level, level),
        "level_color": LEVEL_COLORS.get(level, "#6B7280"),
        "svg_uri": _svg_to_data_uri(_histogram_svg(gene, sample_value, ref["mean"], ref["sd"])),
    }


def load_immune_markers(sample: str) -> dict[str, Any]:
    stored = read_json(immune_markers_path(sample), DEFAULT_IMMUNE_MARKERS)
    expression_values = _read_expression_values(sample)
    panels_in = stored.get("panels") if isinstance(stored, dict) else None

    base_by_key = {panel["key"]: panel for panel in DEFAULT_IMMUNE_MARKERS["panels"]}
    normalized_panels: list[dict[str, Any]] = []

    if isinstance(panels_in, list) and panels_in:
        source_panels = panels_in
    else:
        source_panels = deepcopy(DEFAULT_IMMUNE_MARKERS["panels"])

    for panel in source_panels:
        if not isinstance(panel, dict):
            continue
        key = str(panel.get("key", "")).strip()
        base = deepcopy(base_by_key.get(key, {}))
        merged = deepcopy(base)
        merged.update(panel)
        cards_in = merged.get("cards") if isinstance(merged.get("cards"), list) else []
        cards: list[dict[str, Any]] = []
        for card in cards_in:
            if not isinstance(card, dict):
                continue
            gene = str(card.get("gene", "")).strip().upper()
            if gene not in MARKER_REFERENCE:
                continue
            cards.append(_build_card(gene, str(card.get("description", "")).strip(), expression_values))
        if not cards and key in base_by_key:
            for card in base_by_key[key]["cards"]:
                gene = card["gene"]
                cards.append(_build_card(gene, card["description"], expression_values))

        normalized_panels.append({
            "key": merged.get("key", key),
            "title": str(merged.get("title", "")).strip(),
            "subtitle": str(merged.get("subtitle", "")).strip(),
            "note": str(merged.get("note", "")).strip(),
            "cards": cards,
        })

    return {
        "section_subtitle": SECTION_SUBTITLE,
        "panels": normalized_panels,
    }
