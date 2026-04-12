from __future__ import annotations

import base64
import csv
import math
from copy import deepcopy
from typing import Any

from core.io_utils import read_json, read_json_file
from core.paths import (
    defaults_immune_markers_path,
    immune_markers_path,
    rsem_gene_tpm_path,
    rsem_test_gene_tpm_path,
)

FALLBACK = {"section_subtitle": "Уровень относительно меланомной когорты TCGA", "panels": [], "reference": {}}
LEVEL_COLORS = {"LOW": "#3B82F6", "MEDIUM": "#EAB308", "HIGH": "#EF4444"}
LEVEL_LABELS = {"LOW": "Низкий", "MEDIUM": "Средний", "HIGH": "Высокий"}


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _normalize_gene_symbol(raw: Any) -> str:
    text = str(raw).strip()
    if not text:
        return ""
    if "|" in text:
        parts = [part.strip() for part in text.split("|") if part.strip()]
        non_ensg = [part for part in parts if not part.upper().startswith("ENSG")]
        text = non_ensg[-1] if non_ensg else parts[-1]
    return text.split(".")[0].strip().upper()


def _maybe_float(value: Any) -> float | None:
    try:
        if value in (None, ""):
            return None
        return float(value)
    except Exception:
        return None


def _first_existing_path(*paths):
    for path in paths:
        if path.exists():
            return path
    return None


def _detect_gene_column(headers: list[str]) -> str:
    preferred = ["gene_symbol", "gene", "Gene", "gene_name", "symbol", "Symbol", "GENE", "GeneName", "gene_id", "geneID"]
    for name in preferred:
        if name in headers:
            return name
    return headers[0]


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
            out = {}
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
    return "data:image/svg+xml;base64," + base64.b64encode(svg_text.encode("utf-8")).decode("utf-8")


def _histogram_svg(gene: str, sample_value: float, mean: float, sd: float) -> str:
    width, height = 320, 194
    left, right, top, bottom = 42, 10, 42, 48
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

    tick_elems = []
    for val in [x_min, (x_min + x_max) / 2, x_max]:
        px = left + (val - x_min) / max(x_max - x_min, 1e-6) * plot_w
        tick_elems.append(f'<line x1="{px:.1f}" y1="{top+plot_h}" x2="{px:.1f}" y2="{top+plot_h+4}" stroke="#6B7280" stroke-width="1" />')
        tick_elems.append(f'<text x="{px:.1f}" y="{height-24}" font-size="10" text-anchor="middle" fill="#4B5563">{val:.1f}</text>')

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
        ''.join(tick_elems),
        ''.join(bars),
        selected_outline,
        f'<text x="14" y="{top+plot_h/2:.1f}" font-size="11" font-weight="600" text-anchor="middle" fill="#111827" transform="rotate(-90 14 {top+plot_h/2:.1f})">N</text>',
        f'<text x="{left+plot_w/2:.1f}" y="{height-6}" font-size="11" font-weight="600" text-anchor="middle" fill="#111827">Log2(TPM+1)</text>',
        '</svg>',
    ])


def _build_card(card_cfg: dict[str, Any], reference: dict[str, Any], expression_values: dict[str, float]) -> dict[str, Any]:
    gene = str(card_cfg.get("gene", "")).upper()
    ref = reference.get(gene, {})
    mean = float(ref.get("mean", 2.0))
    sd = float(ref.get("sd", 0.5))
    tpm = expression_values.get(gene)
    if tpm is not None:
        sample_value = round(_log2_tpm(tpm), 2)
        percentile = _percentile_from_value(sample_value, mean, sd)
        level = _level_from_percentile(percentile)
    else:
        sample_value = float(ref.get("default_value", 1.5))
        percentile = int(ref.get("default_percentile", 50))
        level = str(ref.get("default_level", "MEDIUM")).upper()
    return {
        "gene": gene,
        "description": str(card_cfg.get("description", "")),
        "sample_value": sample_value,
        "percentile": percentile,
        "level": level,
        "level_label": LEVEL_LABELS.get(level, level),
        "level_color": LEVEL_COLORS.get(level, "#6B7280"),
        "svg_uri": _svg_to_data_uri(_histogram_svg(gene, sample_value, mean, sd)),
    }


def load_immune_markers(sample: str) -> dict[str, Any]:
    defaults = read_json_file(defaults_immune_markers_path(), FALLBACK)
    if not isinstance(defaults, dict):
        defaults = deepcopy(FALLBACK)
    stored = read_json(immune_markers_path(sample), defaults)
    result = deepcopy(defaults)
    if isinstance(stored, dict):
        result.update(stored)

    expression_values = _read_expression_values(sample)
    reference = result.get("reference", {}) if isinstance(result.get("reference"), dict) else {}
    panels = []
    for panel in result.get("panels", []):
        if not isinstance(panel, dict):
            continue
        merged = deepcopy(panel)
        cards = [_build_card(card, reference, expression_values) for card in merged.get("cards", []) if isinstance(card, dict)]
        merged["cards"] = cards
        panels.append(merged)

    return {
        "section_subtitle": str(result.get("section_subtitle", FALLBACK["section_subtitle"])),
        "panels": panels,
    }
