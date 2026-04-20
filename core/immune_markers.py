from __future__ import annotations

import base64
import csv
from functools import lru_cache
import math
import re
from copy import deepcopy
from typing import Any

from core.io_utils import path_token, read_json, read_json_file
from core.paths import (
    defaults_immune_markers_path,
    immune_markers_path,
    immune_markers_reference_legacy_path,
    immune_markers_reference_path,
    rsem_gene_tpm_path,
    rsem_test_gene_tpm_path,
)

FALLBACK = {"section_subtitle": "", "panels": [], "reference": {}}
LEVEL_COLORS = {"LOW": "#3B82F6", "MEDIUM": "#EAB308", "HIGH": "#EF4444"}
LEVEL_LABELS = {"LOW": "Низкий", "MEDIUM": "Средний", "HIGH": "Высокий"}


# Это функция для блока «clamp». Она нужна для того, чтобы вынести отдельный шаг логики в самостоятельную и читаемую часть кода.
# Используется в следующих блоках: core/immune_markers.py.
# На вход: value, low, high.
# На выход: float.
def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


# Это функция для нормализации имени гена, нужна перед дальнейшей обработкой и сопоставлением записей между разными таблицами.
# Используется в следующих блоках: core/immune_markers.py.
# На вход: raw.
# На выход: str.
def _normalize_gene_symbol(raw: Any) -> str:
    text = str(raw).strip()
    if not text:
        return ""
    if "|" in text:
        parts = [part.strip() for part in text.split("|") if part.strip()]
        non_ensg = [part for part in parts if not part.upper().startswith("ENSG")]
        text = non_ensg[-1] if non_ensg else parts[-1]
    return text.split(".")[0].strip().upper()


# Это функция для блока «maybe float». Она нужна для того, чтобы вынести отдельный шаг логики в самостоятельную и читаемую часть кода.
# Используется в следующих блоках: core/immune_markers.py.
# На вход: value.
# На выход: float  или  None.
def _maybe_float(value: Any) -> float | None:
    try:
        if value in (None, ""):
            return None
        return float(value)
    except Exception:
        return None


# Это функция для блока «first existing пути». Она нужна для того, чтобы вынести отдельный шаг логики в самостоятельную и читаемую часть кода.
# Используется в следующих блоках: core/immune_markers.py.
# На вход: paths.
# На выход: результат дальнейшего шага обработки.
def _first_existing_path(*paths):
    for path in paths:
        if path.exists():
            return path
    return None


# Это функция для блока «detect gene column». Она нужна для того, чтобы вынести отдельный шаг логики в самостоятельную и читаемую часть кода.
# Используется в следующих блоках: core/immune_markers.py.
# На вход: headers.
# На выход: str.
def _detect_gene_column(headers: list[str]) -> str:
    preferred = ["gene_symbol", "gene", "Gene", "gene_name", "symbol", "Symbol", "GENE", "GeneName", "gene_id", "geneID"]
    for name in preferred:
        if name in headers:
            return name
    return headers[0]


# Это функция для блока «образца base». Она нужна для того, чтобы вынести отдельный шаг логики в самостоятельную и читаемую часть кода.
# Используется в следующих блоках: core/immune_markers.py.
# На вход: value.
# На выход: str.
def _sample_base(value: str) -> str:
    text = str(value or "").strip()
    text = re.sub(r"_(19|20)\d{2}$", "", text)
    return text.lower()


# Это функция для блока «matching образца names». Она нужна для того, чтобы вынести отдельный шаг логики в самостоятельную и читаемую часть кода.
# Используется в следующих блоках: core/immune_markers.py.
# На вход: sample, names.
# На выход: список[str].
def _matching_sample_names(sample: str, names: list[str] | tuple[str, ...]) -> list[str]:
    if not sample:
        return []
    sample_clean = str(sample).strip().lower()
    sample_base = _sample_base(sample)
    exact = [name for name in names if str(name).strip().lower() == sample_clean]
    if exact:
        return exact
    base_matches = [name for name in names if _sample_base(str(name)) == sample_base]
    return base_matches


@lru_cache(maxsize=128)
# Это функция для чтения данных, связанных с блоком «чтения expression значений cached». 
# Используется в следующих блоках: core/immune_markers.py.
# На вход: path_str, mtime_ns.
# На выход: кортеж[кортеж[str, float], ...].
def _read_expression_values_cached(path_str: str, mtime_ns: int) -> tuple[tuple[str, float], ...]:
    if mtime_ns < 0:
        return tuple()
    try:
        with open(path_str, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f, delimiter="\t")
            headers = reader.fieldnames or []
            if not headers:
                return tuple()
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
            return tuple(sorted(out.items()))
    except Exception:
        return tuple()


# Это функция для чтения данных, связанных с блоком «чтения expression значений». 
# Используется в следующих блоках: core/immune_markers.py.
# На вход: sample.
# На выход: словарь[str, float].
def _read_expression_values(sample: str) -> dict[str, float]:
    path = _first_existing_path(rsem_gene_tpm_path(sample), rsem_test_gene_tpm_path(sample))
    if path is None:
        return {}
    path_str, mtime_ns = path_token(path)
    return dict(_read_expression_values_cached(path_str, mtime_ns))


# Это функция для блока «log2 tpm». Она нужна для того, чтобы вынести отдельный шаг логики в самостоятельную и читаемую часть кода.
# Используется в следующих блоках: core/immune_markers.py.
# На вход: value.
# На выход: float.
def _log2_tpm(value: float) -> float:
    return math.log2(max(0.0, value) + 1.0)


# Это функция для блока «normal cdf». Она нужна для того, чтобы вынести отдельный шаг логики в самостоятельную и читаемую часть кода.
# Используется в следующих блоках: core/immune_markers.py.
# На вход: x, mean, sd.
# На выход: float.
def _normal_cdf(x: float, mean: float, sd: float) -> float:
    z = (x - mean) / max(sd, 1e-6)
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


# Это функция для блока «percentile from значения». Она нужна для того, чтобы вынести отдельный шаг логики в самостоятельную и читаемую часть кода.
# Используется в следующих блоках: core/immune_markers.py.
# На вход: value, mean, sd.
# На выход: int.
def _percentile_from_value(value: float, mean: float, sd: float) -> int:
    pct = round(_normal_cdf(value, mean, sd) * 100)
    return int(_clamp(pct, 1, 100))


# Это функция для блока «level from percentile». Она нужна для того, чтобы вынести отдельный шаг логики в самостоятельную и читаемую часть кода.
# Используется в следующих блоках: core/immune_markers.py.
# На вход: percentile.
# На выход: str.
def _level_from_percentile(percentile: int) -> str:
    if percentile >= 75:
        return "HIGH"
    if percentile >= 35:
        return "MEDIUM"
    return "LOW"


# Это функция для блока «svg to data uri». Она нужна для того, чтобы вынести отдельный шаг логики в самостоятельную и читаемую часть кода.
# Используется в следующих блоках: core/immune_markers.py.
# На вход: svg_text.
# На выход: str.
def _svg_to_data_uri(svg_text: str) -> str:
    return "data:image/svg+xml;base64," + base64.b64encode(svg_text.encode("utf-8")).decode("utf-8")


@lru_cache(maxsize=32)
# Это функция для чтения данных, связанных с блоком «чтения reference matrix cached». 
# Используется в следующих блоках: core/immune_markers.py.
# На вход: path_str, mtime_ns.
# На выход: кортеж[словарь[str, словарь[str, float]], кортеж[str, ...]].
def _read_reference_matrix_cached(path_str: str, mtime_ns: int) -> tuple[dict[str, dict[str, float]], tuple[str, ...]]:
    if mtime_ns < 0:
        return {}, tuple()
    try:
        with open(path_str, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f, delimiter="	")
            headers = reader.fieldnames or []
            if not headers:
                return {}, tuple()
            gene_col = _detect_gene_column(headers)
            value_cols = [h for h in headers if h != gene_col]
            matrix: dict[str, dict[str, float]] = {}
            for row in reader:
                gene = _normalize_gene_symbol(row.get(gene_col, ""))
                if not gene:
                    continue
                gene_values: dict[str, float] = {}
                for col in value_cols:
                    value = _maybe_float(row.get(col))
                    if value is not None:
                        gene_values[col] = float(value)
                if gene_values:
                    matrix[gene] = gene_values
            return matrix, tuple(value_cols)
    except Exception:
        return {}, tuple()


# Это функция для чтения данных, связанных с блоком «чтения reference matrix». 
# Используется в следующих блоках: core/immune_markers.py.
# На вход: функция не ожидает обязательных входных параметров.
# На выход: кортеж[словарь[str, словарь[str, float]], кортеж[str, ...], str].
def _read_reference_matrix() -> tuple[dict[str, dict[str, float]], tuple[str, ...], str]:
    path = _first_existing_path(immune_markers_reference_path(), immune_markers_reference_legacy_path())
    if path is None:
        return {}, tuple(), "референсная когорта"
    path_str, mtime_ns = path_token(path)
    matrix, columns = _read_reference_matrix_cached(path_str, mtime_ns)
    return matrix, columns, "референсная когорта"


# Это функция для блока «reference distribution for gene». Она нужна для того, чтобы вынести отдельный шаг логики в самостоятельную и читаемую часть кода.
# Используется в следующих блоках: core/immune_markers.py.
# На вход: sample, gene.
# На выход: кортеж[список[кортеж[str, float]], float  или  None, str].
def _reference_distribution_for_gene(sample: str, gene: str) -> tuple[list[tuple[str, float]], float | None, str]:
    matrix, columns, source_label = _read_reference_matrix()
    gene_values = matrix.get(gene, {})
    if not gene_values:
        return [], None, source_label

    matched_names = set(_matching_sample_names(sample, columns))
    patient_value = None
    reference_items: list[tuple[str, float]] = []

    for col in columns:
        value = gene_values.get(col)
        if value is None:
            continue
        if col in matched_names:
            if patient_value is None:
                patient_value = float(value)
            continue
        reference_items.append((col, float(value)))

    return reference_items, patient_value, source_label


# Это функция для блока «histogram svg from reference». Она нужна для того, чтобы вынести отдельный шаг логики в самостоятельную и читаемую часть кода.
# Используется в следующих блоках: core/immune_markers.py.
# На вход: sample_value, reference_items, legend_left, legend_right.
# На выход: str.
def _histogram_svg_from_reference(
    sample_value: float,
    reference_items: list[tuple[str, float]],
    legend_left: str = "референс",
    legend_right: str = "образец",
) -> str:
    width, height = 320, 194
    left, right, top, bottom = 42, 10, 42, 48
    plot_w = width - left - right
    plot_h = height - top - bottom
    bins = 24

    reference_values = [value for _, value in reference_items]
    all_values = list(reference_values) + [sample_value]
    x_min = min(all_values) if all_values else 0.0
    x_max = max(all_values) if all_values else 1.0
    if math.isclose(x_min, x_max):
        x_min = max(0.0, x_min - 1.0)
        x_max = x_max + 1.0
    padding = max((x_max - x_min) * 0.06, 0.2)
    x_min = max(0.0, x_min - padding)
    x_max = x_max + padding

    edges = [x_min + i * (x_max - x_min) / bins for i in range(bins + 1)]

    tcga_values = [value for name, value in reference_items if str(name).startswith("TCGA")]
    bg_values = [value for name, value in reference_items if str(name).startswith("blo") or str(name).startswith("ger")]
    other_values = [value for name, value in reference_items if not (str(name).startswith("TCGA") or str(name).startswith("blo") or str(name).startswith("ger"))]

    # Это функция для блока «bin counts». Она нужна для того, чтобы вынести отдельный шаг логики в самостоятельную и читаемую часть кода.
    # Используется в следующих блоках: core/immune_markers.py.
    # На вход: values.
    # На выход: список[int].
    def _bin_counts(values: list[float]) -> list[int]:
        counts = [0] * bins
        if not values:
            return counts
        span = max(x_max - x_min, 1e-6)
        for value in values:
            idx = int((value - x_min) / span * bins)
            idx = max(0, min(bins - 1, idx if value < x_max else bins - 1))
            counts[idx] += 1
        return counts

    if tcga_values or bg_values:
        counts_primary = _bin_counts(tcga_values)
        counts_secondary = _bin_counts(bg_values)
        primary_label = "TCGA"
        secondary_label = "blo/ger"
    else:
        counts_primary = _bin_counts(other_values)
        counts_secondary = [0] * bins
        primary_label = legend_left
        secondary_label = ""

    total_counts = [a + b for a, b in zip(counts_primary, counts_secondary)]
    max_count = max(max(total_counts, default=0), 1)

    span = max(x_max - x_min, 1e-6)
    sample_bin = int((sample_value - x_min) / span * bins)
    sample_bin = max(0, min(bins - 1, sample_bin if sample_value < x_max else bins - 1))

    bin_w = plot_w / bins
    bars: list[str] = []
    selected_outline = ""

    for idx in range(bins):
        x = left + idx * bin_w + 1
        w = max(3.0, bin_w - 2)

        primary_h_px = (counts_primary[idx] / max_count) * plot_h
        if primary_h_px > 0:
            y = top + plot_h - primary_h_px
            bars.append(
                f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{primary_h_px:.1f}" '
                'rx="1.5" fill="#4169E1" fill-opacity="0.60" />'
            )

        secondary_h_px = (counts_secondary[idx] / max_count) * plot_h
        if secondary_h_px > 0:
            y2 = top + plot_h - secondary_h_px
            bars.append(
                f'<rect x="{x:.1f}" y="{y2:.1f}" width="{w:.1f}" height="{secondary_h_px:.1f}" '
                'rx="1.5" fill="#FF6347" fill-opacity="0.60" />'
            )

        if idx == sample_bin:
            outline_h_px = (total_counts[idx] / max_count) * plot_h
            outline_h_px = max(outline_h_px, 2.0)
            outline_y = top + plot_h - outline_h_px
            selected_outline = (
                f'<rect x="{x:.1f}" y="{outline_y:.1f}" width="{w:.1f}" height="{outline_h_px:.1f}" '
                'rx="1.5" fill="none" stroke="#111827" stroke-width="2" />'
            )

    tick_elems = []
    for val in [x_min, (x_min + x_max) / 2, x_max]:
        px = left + (val - x_min) / span * plot_w
        tick_elems.append(f'<line x1="{px:.1f}" y1="{top+plot_h}" x2="{px:.1f}" y2="{top+plot_h+4}" stroke="#6B7280" stroke-width="1" />')
        tick_elems.append(f'<text x="{px:.1f}" y="{height-24}" font-size="10" text-anchor="middle" fill="#4B5563">{val:.1f}</text>')

    legend_parts = [
        '<rect x="18" y="10" width="18" height="8" rx="1.5" fill="#4169E1" fill-opacity="0.60"/>',
        f'<text x="42" y="17" font-size="12" fill="#374151">{primary_label}</text>',
    ]
    if secondary_label:
        legend_parts += [
            '<rect x="18" y="26" width="18" height="8" rx="1.5" fill="#FF6347" fill-opacity="0.60"/>',
            f'<text x="42" y="33" font-size="12" fill="#374151">{secondary_label}</text>',
        ]
    else:
        legend_parts += [
            '<rect x="18" y="26" width="18" height="8" rx="1.5" fill="none" stroke="#111827" stroke-width="1.5"/>',
            f'<text x="42" y="33" font-size="12" fill="#374151">{legend_right}</text>',
        ]

    return ''.join([
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect x="0.5" y="0.5" width="319" height="193" rx="8" fill="#FFFFFF" stroke="#E5E7EB"/>',
        ''.join(legend_parts),
        f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top+plot_h}" stroke="#111827" stroke-width="1.2"/>',
        f'<line x1="{left}" y1="{top+plot_h}" x2="{left+plot_w}" y2="{top+plot_h}" stroke="#111827" stroke-width="1.2"/>',
        ''.join(tick_elems),
        ''.join(bars),
        selected_outline,
        f'<text x="14" y="{top+plot_h/2:.1f}" font-size="11" font-weight="600" text-anchor="middle" fill="#111827" transform="rotate(-90 14 {top+plot_h/2:.1f})">N</text>',
        f'<text x="{left+plot_w/2:.1f}" y="{height-6}" font-size="11" font-weight="600" text-anchor="middle" fill="#111827">Log2(TPM+1)</text>',
        '</svg>',
    ])


# Это функция для блока «histogram svg fallback». Она нужна для того, чтобы вынести отдельный шаг логики в самостоятельную и читаемую часть кода.
# Используется в следующих блоках: core/immune_markers.py.
# На вход: sample_value, mean, sd, legend_left, legend_right.
# На выход: str.
def _histogram_svg_fallback(sample_value: float, mean: float, sd: float, legend_left: str = "TCGA", legend_right: str = "образец") -> str:
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

    sample_frac = (sample_x - x_min) / max(x_max - x_min, 1e-6)
    bars = []
    selected_outline = ""
    bin_w = plot_w / bins
    for idx, frac in enumerate(heights):
        bar_h = frac * plot_h
        x = left + idx * bin_w + 1
        y = top + plot_h - bar_h
        w = max(3.0, bin_w - 2)
        bars.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{bar_h:.1f}" rx="1.5" fill="#8FA8EE" />')
        if idx == sample_bin:
            patient_h = sample_frac * plot_h
            patient_w = max(3.0, w * 0.52)
            patient_x = x + (w - patient_w) / 2
            patient_y = top + plot_h - patient_h
            bars.append(f'<rect x="{patient_x:.1f}" y="{patient_y:.1f}" width="{patient_w:.1f}" height="{patient_h:.1f}" rx="1.5" fill="#F09984" />')
            frame_h = max(bar_h, patient_h)
            frame_y = top + plot_h - frame_h
            selected_outline = f'<rect x="{x:.1f}" y="{frame_y:.1f}" width="{w:.1f}" height="{frame_h:.1f}" rx="1.5" fill="none" stroke="#111827" stroke-width="2" />'

    tick_elems = []
    for val in [x_min, (x_min + x_max) / 2, x_max]:
        px = left + (val - x_min) / max(x_max - x_min, 1e-6) * plot_w
        tick_elems.append(f'<line x1="{px:.1f}" y1="{top+plot_h}" x2="{px:.1f}" y2="{top+plot_h+4}" stroke="#6B7280" stroke-width="1" />')
        tick_elems.append(f'<text x="{px:.1f}" y="{height-24}" font-size="10" text-anchor="middle" fill="#4B5563">{val:.1f}</text>')

    legend = ''.join([
        '<rect x="18" y="10" width="18" height="8" rx="1.5" fill="#8FA8EE"/>',
        f'<text x="42" y="17" font-size="12" fill="#374151">{legend_left}</text>',
        '<rect x="18" y="26" width="18" height="8" rx="1.5" fill="#F09984"/>',
        f'<text x="42" y="33" font-size="12" fill="#374151">{legend_right}</text>',
    ])

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


# Это функция для блока «сборки card». Она нужна для того, чтобы вынести отдельный шаг логики в самостоятельную и читаемую часть кода.
# Используется в следующих блоках: core/immune_markers.py.
# На вход: card_cfg, reference, expression_values, sample.
# На выход: словарь[str, Any].
def _build_card(card_cfg: dict[str, Any], reference: dict[str, Any], expression_values: dict[str, float], sample: str) -> dict[str, Any]:
    gene = str(card_cfg.get("gene", "")).upper()
    ref = reference.get(gene, {})
    mean = float(ref.get("mean", 2.0))
    sd = float(ref.get("sd", 0.5))

    reference_items, cohort_patient_value, source_label = _reference_distribution_for_gene(sample, gene)
    tpm = expression_values.get(gene)
    if tpm is not None:
        sample_value = round(_log2_tpm(tpm), 2)
    elif cohort_patient_value is not None:
        sample_value = round(float(cohort_patient_value), 2)
    else:
        sample_value = float(ref.get("default_value", 1.5))

    if reference_items:
        reference_values = [value for _, value in reference_items]
        percentile = int(_clamp(round(sum(value <= sample_value for value in reference_values) / len(reference_values) * 100), 1, 100))
        level = _level_from_percentile(percentile)
        svg_uri = _svg_to_data_uri(_histogram_svg_from_reference(sample_value, reference_items, legend_left=source_label, legend_right="образец"))
    elif tpm is not None or cohort_patient_value is not None:
        percentile = _percentile_from_value(sample_value, mean, sd)
        level = _level_from_percentile(percentile)
        svg_uri = _svg_to_data_uri(_histogram_svg_fallback(sample_value, mean, sd, legend_left="TCGA", legend_right="образец"))
    else:
        percentile = int(ref.get("default_percentile", 50))
        level = str(ref.get("default_level", "MEDIUM")).upper()
        svg_uri = _svg_to_data_uri(_histogram_svg_fallback(sample_value, mean, sd, legend_left="TCGA", legend_right="образец"))

    return {
        "gene": gene,
        "description": str(card_cfg.get("description", "")),
        "sample_value": sample_value,
        "percentile": percentile,
        "level": level,
        "level_label": LEVEL_LABELS.get(level, level),
        "level_color": LEVEL_COLORS.get(level, "#6B7280"),
        "svg_uri": svg_uri,
    }


# Это функция для загрузки данных, связанных с блоком «загрузки иммунного профиля иммунных маркеров». 
# Используется в следующих блоках: sections/immune_markers_block.py.
# На вход: sample.
# На выход: словарь[str, Any].
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
        cards = [_build_card(card, reference, expression_values, sample) for card in merged.get("cards", []) if isinstance(card, dict)]
        merged["cards"] = cards
        panels.append(merged)

    return {
        "section_subtitle": str(result.get("section_subtitle", FALLBACK["section_subtitle"])),
        "panels": panels,
    }
