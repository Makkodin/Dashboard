from pathlib import Path

ASSETS_DIR = Path("assets")
DATA_ROOT = Path("data")


def sample_dir(sample: str) -> Path:
    return DATA_ROOT / sample


def edit_dir(sample: str) -> Path:
    return sample_dir(sample) / "edit"


def timeline_path(sample: str) -> Path:
    return sample_dir(sample) / "Timeline.json"


def meta_path(sample: str) -> Path:
    return edit_dir(sample) / "meta.json"


def patient_path(sample: str) -> Path:
    return edit_dir(sample) / "patient.json"


def biomaterial_path(sample: str) -> Path:
    return edit_dir(sample) / "biomaterial.json"


def rare_events_path(sample: str) -> Path:
    return edit_dir(sample) / "rare_events.json"


def tmb_path(sample: str) -> Path:
    return sample_dir(sample) / "tmb.txt"


def vep_ann_path(sample: str) -> Path:
    return sample_dir(sample) / "tumor_vs_norma.merged_VEP.ann.tsv"


def mhci_path(sample: str) -> Path:
    return sample_dir(sample) / "mhcI.epitopes.scored.tsv"


def norma_alleles_path(sample: str) -> Path:
    return sample_dir(sample) / "norma.alleles.tsv"


def list_samples() -> list[str]:
    if not DATA_ROOT.exists():
        return []
    return sorted([p.name for p in DATA_ROOT.iterdir() if p.is_dir()])