from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path
from typing import Any

import pandas as pd

from core.io_utils import path_token, read_json, read_text
from core.paths import rare_events_path, starfusion_path


TMB_TOOLTIP_TEXT = (
    "Пороговые значения TMB: менее 10 — в пределах нормы; от 10 до 12 — выше нормы; "
    "более 12 — высокая мутационная нагрузка."
)

HOTSPOT_RULES = {
    "BRAF": re.compile(r"V600[EKR]", re.I),
    "KRAS": re.compile(r"G12|G13|Q61", re.I),
    "HRAS": re.compile(r"G13D|G13S|Q61K", re.I),
    "NRAS": re.compile(r"Q61", re.I),
}
LOF_CONSEQUENCES = (
    "stop_gained",
    "frameshift_variant",
    "splice_acceptor_variant",
    "splice_donor_variant",
    "start_lost",
    "stop_lost",
)
DRIVER_GENES = {"BRAF", "KRAS", "HRAS", "NRAS", "NF1", "TP53", "CDKN2A", "PTEN"}
GENE_PRIORITY = {"BRAF": 1, "NRAS": 2, "KRAS": 3, "HRAS": 4, "NF1": 5, "TP53": 6, "CDKN2A": 7, "PTEN": 8}


@lru_cache(maxsize=256)
def _read_tmb_value_cached(path_str: str, mtime_ns: int) -> float | None:
    if mtime_ns < 0:
        return None
    text = Path(path_str).read_text(encoding="utf-8", errors="ignore")
    match = re.search(r"TMB\s*=\s*([0-9]+(?:\.[0-9]+)?)", text)
    if not match:
        return None
    return float(match.group(1))


def read_tmb_value(path: Path) -> float | None:
    path_str, mtime_ns = path_token(path)
    try:
        return _read_tmb_value_cached(path_str, mtime_ns)
    except Exception:
        return None


def classify_tmb(value: float | None) -> tuple[str, str, str]:
    if value is None:
        return "Нет данных", "#6B7280", TMB_TOOLTIP_TEXT
    if value < 10:
        return "В пределах нормы", "#16A34A", TMB_TOOLTIP_TEXT
    if 10 <= value <= 12:
        return "Выше нормы", "#F59E0B", TMB_TOOLTIP_TEXT
    return "Высокая нагрузка", "#DC2626", TMB_TOOLTIP_TEXT


def tmb_scale_position(value: float | None, max_value: float = 30.0) -> float:
    if value is None:
        return 0.0
    clipped = max(0.0, min(float(value), max_value))
    return round((clipped / max_value) * 100.0, 2)


def _severity_rank(consequence: str) -> int:
    order = {
        "stop_gained": 1,
        "frameshift_variant": 2,
        "splice_acceptor_variant": 3,
        "splice_donor_variant": 4,
        "missense_variant": 5,
        "inframe_insertion": 6,
        "inframe_deletion": 7,
        "protein_altering_variant": 8,
    }
    for key, rank in order.items():
        if key in consequence:
            return rank
    return 99


def _protein_hit(gene: str, protein_change: str, consequence: str) -> bool:
    gene = gene.upper()
    consequence = consequence.lower()
    protein_change = protein_change.upper()

    if gene in HOTSPOT_RULES:
        return bool(HOTSPOT_RULES[gene].search(protein_change))

    if gene == "NF1":
        return True

    if gene in {"TP53", "CDKN2A", "PTEN"}:
        if any(tag in consequence for tag in LOF_CONSEQUENCES):
            return True
        return protein_change not in {"", "—", "NAN"}

    return False


@lru_cache(maxsize=128)
def _load_key_somatic_variants_cached(path_str: str, mtime_ns: int) -> pd.DataFrame:
    if mtime_ns < 0:
        return pd.DataFrame(columns=["Ген", "Белковое изменение", "Нуклеотидное изменение"])

    try:
        df = pd.read_csv(path_str, sep="	")
    except Exception:
        return pd.DataFrame(columns=["Ген", "Белковое изменение", "Нуклеотидное изменение"])

    if df.empty or "gene_symbol" not in df.columns:
        return pd.DataFrame(columns=["Ген", "Белковое изменение", "Нуклеотидное изменение"])

    work = df.copy()
    work["gene_symbol"] = work["gene_symbol"].astype(str).str.upper()
    work["consequence"] = work.get("consequence", "").astype(str)
    work["aa_change"] = work.get("aa_change", "").astype(str)
    work["cds_change"] = work.get("cds_change", "").astype(str)

    work = work[work["gene_symbol"].isin(DRIVER_GENES)]
    work = work[~work["consequence"].str.contains("synonymous_variant|intron_variant|upstream_gene_variant|downstream_gene_variant|intergenic_variant", case=False, na=False)]

    work = work[
        work.apply(
            lambda row: _protein_hit(
                str(row.get("gene_symbol", "")),
                str(row.get("aa_change", "")),
                str(row.get("consequence", "")),
            ),
            axis=1,
        )
    ]

    if work.empty:
        return pd.DataFrame(columns=["Ген", "Белковое изменение", "Нуклеотидное изменение"])

    work["_priority"] = work["gene_symbol"].map(lambda x: GENE_PRIORITY.get(str(x), 99))
    work["_rank"] = work["consequence"].astype(str).str.lower().map(_severity_rank)
    work = work.sort_values(["_priority", "_rank", "gene_symbol"], ascending=[True, True, True])

    out = work[["gene_symbol", "aa_change", "cds_change"]].copy()
    out = out.rename(columns={
        "gene_symbol": "Ген",
        "aa_change": "Белковое изменение",
        "cds_change": "Нуклеотидное изменение",
    })
    out = out.drop_duplicates().reset_index(drop=True)
    return out


def load_key_somatic_variants(path: Path) -> pd.DataFrame:
    path_str, mtime_ns = path_token(path)
    return _load_key_somatic_variants_cached(path_str, mtime_ns).copy()


@lru_cache(maxsize=128)
def _load_hla_class_i_cached(path_str: str, mtime_ns: int) -> tuple[tuple[str, str, str, str], ...]:
    if mtime_ns < 0:
        return tuple()
    try:
        df = pd.read_csv(path_str, sep="	")
    except Exception:
        return tuple()
    if df.empty or not {"Locus", "Allele"}.issubset(df.columns):
        return []

    result = []
    for locus in ["A", "B", "C"]:
        sub = df[df["Locus"].astype(str) == locus]["Allele"].astype(str).tolist()
        allele_1 = sub[0] if len(sub) > 0 else "—"
        allele_2 = sub[1] if len(sub) > 1 else "—"
        normalized_1 = allele_1.replace("G", "").replace("N", "")
        normalized_2 = allele_2.replace("G", "").replace("N", "")
        zygosity = "Гомозигота" if normalized_1 == normalized_2 and allele_1 != "—" else "Гетерозигота"
        result.append((f"HLA-{locus}", allele_1, allele_2, zygosity))
    return tuple(result)


def load_hla_class_i(path: Path) -> list[dict[str, str]]:
    path_str, mtime_ns = path_token(path)
    return [
        {"locus": locus, "allele_1": allele_1, "allele_2": allele_2, "status": status}
        for locus, allele_1, allele_2, status in _load_hla_class_i_cached(path_str, mtime_ns)
    ]


@lru_cache(maxsize=128)
def _fusion_lines_from_file_cached(path_str: str, mtime_ns: int) -> tuple[str, ...]:
    if mtime_ns < 0:
        return tuple()
    try:
        df = pd.read_csv(path_str, sep="	")
    except Exception:
        return tuple()
    if df.empty:
        return []

    candidates: list[str] = []
    for _, row in df.head(10).iterrows():
        fusion = None
        for col in ["FusionName", "#FusionName", "fusion_name", "fusion"]:
            if col in df.columns and str(row.get(col, "")).strip() and str(row.get(col, "")).strip().lower() != "nan":
                fusion = str(row.get(col)).strip()
                break
        if not fusion:
            left = None
            right = None
            for col in ["LeftGene", "LeftBreakpoint"]:
                if col in df.columns and str(row.get(col, "")).strip():
                    left = str(row.get(col)).split("^")[0].strip()
                    break
            for col in ["RightGene", "RightBreakpoint"]:
                if col in df.columns and str(row.get(col, "")).strip():
                    right = str(row.get(col)).split("^")[0].strip()
                    break
            if left and right:
                fusion = f"{left}--{right}"
        if not fusion:
            continue
        detail = ""
        for col in ["annots", "PROT_FUSION_TYPE", "JunctionReadCount"]:
            if col in df.columns:
                value = str(row.get(col, "")).strip()
                if value and value.lower() != "nan":
                    detail = value
                    break
        candidates.append(f"{fusion}: {detail}" if detail else fusion)

    uniq = []
    seen = set()
    for line in candidates:
        if line not in seen:
            uniq.append(line)
            seen.add(line)
    return tuple(uniq[:5])


def _fusion_lines_from_file(path: Path) -> list[str]:
    path_str, mtime_ns = path_token(path)
    return list(_fusion_lines_from_file_cached(path_str, mtime_ns))


def load_rare_events_text(sample: str) -> str:
    manual = read_json(rare_events_path(sample), {"text": ""}).get("text", "")
    manual = str(manual).strip()
    if manual:
        return manual
    fusion_lines = _fusion_lines_from_file(starfusion_path(sample))
    if fusion_lines:
        return "\n".join(fusion_lines)
    return "Не выявлены"
