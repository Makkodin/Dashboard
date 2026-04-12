from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = BASE_DIR / "assets"
DATA_ROOT = BASE_DIR / "data"
DEFAULTS_ROOT = BASE_DIR / "defaults"


def sample_dir(sample: str) -> Path:
    return DATA_ROOT / sample


def edit_dir(sample: str) -> Path:
    return sample_dir(sample) / "edit"


def timeline_path(sample: str) -> Path:
    return sample_dir(sample) / "Timeline.json"


def timeline_edit_path(sample: str) -> Path:
    return edit_dir(sample) / "treatment_timeline.json"


def meta_path(sample: str) -> Path:
    return edit_dir(sample) / "meta.json"


def patient_path(sample: str) -> Path:
    return edit_dir(sample) / "patient.json"


def biomaterial_path(sample: str) -> Path:
    return edit_dir(sample) / "biomaterial.json"


def rare_events_path(sample: str) -> Path:
    return edit_dir(sample) / "rare_events.json"


def immune_status_path(sample: str) -> Path:
    return edit_dir(sample) / "immune_status.json"


def immune_signatures_path(sample: str) -> Path:
    return edit_dir(sample) / "immune_signatures.json"


def immune_markers_path(sample: str) -> Path:
    return edit_dir(sample) / "immune_markers.json"


def recommendations_path(sample: str) -> Path:
    return edit_dir(sample) / "recommendations.json"


def contacts_text_path(sample: str) -> Path:
    return edit_dir(sample) / "contacts.txt"


def annotation_blocks_path(sample: str) -> Path:
    return edit_dir(sample) / "annotation_blocks.txt"


def defaults_contacts_text_path() -> Path:
    return DEFAULTS_ROOT / "contacts.txt"


def defaults_annotation_blocks_path() -> Path:
    return DEFAULTS_ROOT / "annotation_blocks.txt"


def defaults_immune_status_path() -> Path:
    return DEFAULTS_ROOT / "immune_status.json"


def defaults_immune_signatures_path() -> Path:
    return DEFAULTS_ROOT / "immune_signatures.json"


def defaults_immune_markers_path() -> Path:
    return DEFAULTS_ROOT / "immune_markers.json"


def classified_samples_path() -> Path:
    return BASE_DIR / "classified_samples.tsv"


def immune_signature_scores_path() -> Path:
    return BASE_DIR / "scores2025_2026.tsv"


def tmb_path(sample: str) -> Path:
    return sample_dir(sample) / "tmb.txt"


def vep_ann_path(sample: str) -> Path:
    return sample_dir(sample) / "tumor_vs_norma.merged_VEP.ann.tsv"


def mhci_path(sample: str) -> Path:
    return sample_dir(sample) / "mhcI.epitopes.scored.tsv"


def norma_alleles_path(sample: str) -> Path:
    return sample_dir(sample) / "norma.alleles.tsv"


def rsem_gene_tpm_path(sample: str) -> Path:
    return sample_dir(sample) / "rsem.merged.gene_tpm.tsv"


def rsem_test_gene_tpm_path(sample: str) -> Path:
    return sample_dir(sample) / "rsem_test.merged.gene_tpm.tsv"


def starfusion_path(sample: str) -> Path:
    return sample_dir(sample) / "starfusion.abridged.coding_effect.tsv"


def list_samples() -> list[str]:
    if not DATA_ROOT.exists():
        return []
    return sorted([p.name for p in DATA_ROOT.iterdir() if p.is_dir()])
