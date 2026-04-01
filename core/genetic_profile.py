from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd


PATHOGENIC_CHECK = ["BRAF", "NRAS", "KRAS", "HRAS", "TP53", "NF1", "KIT", "TERT"]
TMB_TOOLTIP_TEXT = (
    "Пороговые значения TMB: менее 10 — в пределах нормы; от 10 до 12 — выше нормы; "
    "более 12 — высокая мутационная нагрузка."
)


def read_tmb_value(path: Path) -> float | None:
    if not path.exists():
        return None

    text = path.read_text(encoding="utf-8", errors="ignore")
    match = re.search(r"TMB\s*=\s*([0-9]+(?:\.[0-9]+)?)", text)
    if not match:
        return None
    return float(match.group(1))


def classify_tmb(value: float | None) -> tuple[str, str, str]:
    if value is None:
        return "Нет данных", "#6B7280", TMB_TOOLTIP_TEXT

    if value < 10:
        return "В пределах нормы", "#16A34A", TMB_TOOLTIP_TEXT
    if 10 <= value <= 12:
        return "Выше нормы", "#F59E0B", TMB_TOOLTIP_TEXT
    return "Высокая нагрузка", "#DC2626", TMB_TOOLTIP_TEXT


def tmb_scale_position(value: float | None, max_value: float = 80.0) -> float:
    if value is None:
        return 0.0
    clipped = max(0.0, min(float(value), max_value))
    return round((clipped / max_value) * 100.0, 2)


def load_key_somatic_variants(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()

    df = pd.read_csv(path, sep="\t")
    if df.empty:
        return df

    if "gene_symbol" not in df.columns or "consequence" not in df.columns:
        return pd.DataFrame()

    work = df.copy()
    work["gene_symbol"] = work["gene_symbol"].astype(str)
    work["consequence"] = work["consequence"].astype(str)

    work = work[work["gene_symbol"].isin(PATHOGENIC_CHECK)]

    exclude = [
        "synonymous_variant",
        "intron_variant",
        "upstream_gene_variant",
        "downstream_gene_variant",
        "intergenic_variant",
    ]
    pattern = "|".join(map(re.escape, exclude))
    work = work[~work["consequence"].str.contains(pattern, case=False, na=False)]

    severity_order = {
        "stop_gained": 1,
        "frameshift_variant": 2,
        "splice_acceptor_variant": 3,
        "splice_donor_variant": 4,
        "missense_variant": 5,
        "inframe_insertion": 6,
        "inframe_deletion": 7,
        "protein_altering_variant": 8,
        "UTR_variant": 20,
    }

    def rank_consequence(c: str) -> int:
        for key, rank in severity_order.items():
            if key in c:
                return rank
        return 99

    work["_rank"] = work["consequence"].apply(rank_consequence)

    preferred_cols = ["gene_symbol", "aa_change", "cds_change"]
    for col in preferred_cols:
        if col not in work.columns:
            work[col] = ""

    work = work.sort_values(["_rank", "gene_symbol"], ascending=[True, True])

    out = work[preferred_cols].copy()
    out = out.rename(
        columns={
            "gene_symbol": "Ген",
            "aa_change": "Белковое изменение",
            "cds_change": "Нуклеотидное изменение",
        }
    )
    return out.reset_index(drop=True)


def load_hla_class_i(path: Path) -> list[dict]:
    if not path.exists():
        return []

    df = pd.read_csv(path, sep="\t")
    if df.empty:
        return []

    needed = ["Locus", "Allele"]
    if not all(col in df.columns for col in needed):
        return []

    result = []

    for locus in ["A", "B", "C"]:
        sub = df[df["Locus"].astype(str) == locus]["Allele"].astype(str).tolist()

        allele_1 = sub[0] if len(sub) > 0 else "—"
        allele_2 = sub[1] if len(sub) > 1 else "—"

        normalized_1 = allele_1.replace("G", "").replace("N", "")
        normalized_2 = allele_2.replace("G", "").replace("N", "")
        zygosity = "Гомозигота" if normalized_1 == normalized_2 and allele_1 != "—" else "Гетерозигота"

        result.append(
            {
                "locus": f"HLA-{locus}",
                "allele_1": allele_1,
                "allele_2": allele_2,
                "status": zygosity,
            }
        )

    return result


def load_rare_events_text(edit_path: Path) -> str:
    if not edit_path.exists():
        return "Не выявлены"

    try:
        data = json.loads(edit_path.read_text(encoding="utf-8"))
        return str(data.get("text", "Не выявлены"))
    except Exception:
        return "Не выявлены"


def save_rare_events_text(edit_path: Path, text: str) -> None:
    edit_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"text": text}
    edit_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
