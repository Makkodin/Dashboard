from functools import lru_cache
from pathlib import Path

from core.io_utils import dir_token

BASE_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = BASE_DIR / "assets"
DATA_ROOT = BASE_DIR / "data"
DEFAULTS_ROOT = BASE_DIR / "defaults"


# Это функция для блока «образца dir». Она нужна для того, чтобы вынести отдельный шаг логики в самостоятельную и читаемую часть кода.
# Используется в следующих блоках: core/immune_status.py, core/paths.py.
# На вход: sample.
# На выход: Path.
def sample_dir(sample: str) -> Path:
    return DATA_ROOT / sample


# Это функция для блока «edit dir». Она нужна для того, чтобы вынести отдельный шаг логики в самостоятельную и читаемую часть кода.
# Используется в следующих блоках: core/paths.py.
# На вход: sample.
# На выход: Path.
def edit_dir(sample: str) -> Path:
    return sample_dir(sample) / "edit"


# Это функция для блока «таймлайна пути». Она нужна для того, чтобы вынести отдельный шаг логики в самостоятельную и читаемую часть кода.
# Используется в следующих блоках: core/timeline.py.
# На вход: sample.
# На выход: Path.
def timeline_path(sample: str) -> Path:
    return sample_dir(sample) / "Timeline.json"


# Это функция для блока «таймлайна edit пути». Она нужна для того, чтобы вынести отдельный шаг логики в самостоятельную и читаемую часть кода.
# Используется в следующих блоках: core/timeline.py.
# На вход: sample.
# На выход: Path.
def timeline_edit_path(sample: str) -> Path:
    return edit_dir(sample) / "treatment_timeline.json"


# Это функция для блока «метаданных пути». Она нужна для того, чтобы вынести отдельный шаг логики в самостоятельную и читаемую часть кода.
# Используется в следующих блоках: core/state.py.
# На вход: sample.
# На выход: Path.
def meta_path(sample: str) -> Path:
    return edit_dir(sample) / "meta.json"


# Это функция для блока «пациента пути». Она нужна для того, чтобы вынести отдельный шаг логики в самостоятельную и читаемую часть кода.
# Используется в следующих блоках: core/state.py.
# На вход: sample.
# На выход: Path.
def patient_path(sample: str) -> Path:
    return edit_dir(sample) / "patient.json"


# Это функция для блока «биоматериала пути». Она нужна для того, чтобы вынести отдельный шаг логики в самостоятельную и читаемую часть кода.
# Используется в следующих блоках: core/state.py.
# На вход: sample.
# На выход: Path.
def biomaterial_path(sample: str) -> Path:
    return edit_dir(sample) / "biomaterial.json"


# Это функция для блока «редких событий пути». Она нужна для того, чтобы вынести отдельный шаг логики в самостоятельную и читаемую часть кода.
# Используется в следующих блоках: core/genetic_profile.py, core/state.py.
# На вход: sample.
# На выход: Path.
def rare_events_path(sample: str) -> Path:
    return edit_dir(sample) / "rare_events.json"


# Это функция для блока «иммунного профиля иммунного статуса пути». Она нужна для того, чтобы вынести отдельный шаг логики в самостоятельную и читаемую часть кода.
# Используется в следующих блоках: core/immune_status.py.
# На вход: sample.
# На выход: Path.
def immune_status_path(sample: str) -> Path:
    return edit_dir(sample) / "immune_status.json"


# Это функция для блока «иммунного профиля иммунных сигнатур пути». Она нужна для того, чтобы вынести отдельный шаг логики в самостоятельную и читаемую часть кода.
# Используется в следующих блоках: core/immune_signatures.py.
# На вход: sample.
# На выход: Path.
def immune_signatures_path(sample: str) -> Path:
    return edit_dir(sample) / "immune_signatures.json"


# Это функция для блока «иммунного профиля иммунных маркеров пути». Она нужна для того, чтобы вынести отдельный шаг логики в самостоятельную и читаемую часть кода.
# Используется в следующих блоках: core/immune_markers.py.
# На вход: sample.
# На выход: Path.
def immune_markers_path(sample: str) -> Path:
    return edit_dir(sample) / "immune_markers.json"


# Это функция для блока «рекомендаций пути». Она нужна для того, чтобы вынести отдельный шаг логики в самостоятельную и читаемую часть кода.
# Используется в следующих блоках: core/recommendations.py.
# На вход: sample.
# На выход: Path.
def recommendations_path(sample: str) -> Path:
    return edit_dir(sample) / "recommendations.json"


# Это функция для блока «контактов текста пути». Она нужна для того, чтобы вынести отдельный шаг логики в самостоятельную и читаемую часть кода.
# Используется в следующих блоках: core/state.py.
# На вход: sample.
# На выход: Path.
def contacts_text_path(sample: str) -> Path:
    return edit_dir(sample) / "contacts.txt"


# Это функция для блока «аннотаций blocks пути». Она нужна для того, чтобы вынести отдельный шаг логики в самостоятельную и читаемую часть кода.
# Используется в следующих блоках: sections/annotation_blocks.py.
# На вход: sample.
# На выход: Path.
def annotation_blocks_path(sample: str) -> Path:
    return edit_dir(sample) / "annotation_blocks.txt"


# Это функция для блока «defaults контактов текста пути». Она нужна для того, чтобы вынести отдельный шаг логики в самостоятельную и читаемую часть кода.
# Используется в следующих блоках: core/state.py.
# На вход: функция не ожидает обязательных входных параметров.
# На выход: Path.
def defaults_contacts_text_path() -> Path:
    return DEFAULTS_ROOT / "contacts.txt"


# Это функция для блока «defaults аннотаций blocks пути». Она нужна для того, чтобы вынести отдельный шаг логики в самостоятельную и читаемую часть кода.
# Используется в следующих блоках: sections/annotation_blocks.py.
# На вход: функция не ожидает обязательных входных параметров.
# На выход: Path.
def defaults_annotation_blocks_path() -> Path:
    return DEFAULTS_ROOT / "annotation_blocks.txt"


# Это функция для блока «defaults иммунного профиля иммунного статуса пути». Она нужна для того, чтобы вынести отдельный шаг логики в самостоятельную и читаемую часть кода.
# Используется в следующих блоках: core/immune_status.py.
# На вход: функция не ожидает обязательных входных параметров.
# На выход: Path.
def defaults_immune_status_path() -> Path:
    return DEFAULTS_ROOT / "immune_status.json"


# Это функция для блока «defaults иммунного профиля иммунных сигнатур пути». Она нужна для того, чтобы вынести отдельный шаг логики в самостоятельную и читаемую часть кода.
# Используется в следующих блоках: core/immune_signatures.py.
# На вход: функция не ожидает обязательных входных параметров.
# На выход: Path.
def defaults_immune_signatures_path() -> Path:
    return DEFAULTS_ROOT / "immune_signatures.json"


# Это функция для блока «defaults иммунного профиля иммунных маркеров пути». Она нужна для того, чтобы вынести отдельный шаг логики в самостоятельную и читаемую часть кода.
# Используется в следующих блоках: core/immune_markers.py.
# На вход: функция не ожидает обязательных входных параметров.
# На выход: Path.
def defaults_immune_markers_path() -> Path:
    return DEFAULTS_ROOT / "immune_markers.json"


# Это функция для блока «classified samples пути». Она нужна для того, чтобы вынести отдельный шаг логики в самостоятельную и читаемую часть кода.
# Используется в следующих блоках: core/immune_status.py.
# На вход: функция не ожидает обязательных входных параметров.
# На выход: Path.
def classified_samples_path() -> Path:
    return DATA_ROOT / "classified_samples.tsv"


# Это функция для блока «иммунного профиля signature scores пути». Она нужна для того, чтобы вынести отдельный шаг логики в самостоятельную и читаемую часть кода.
# Используется в следующих блоках: core/immune_signatures.py.
# На вход: функция не ожидает обязательных входных параметров.
# На выход: Path.
def immune_signature_scores_path() -> Path:
    return DATA_ROOT / "scores2025_2026.tsv"


# Это функция для блока «иммунного профиля иммунных маркеров reference пути». Она нужна для того, чтобы вынести отдельный шаг логики в самостоятельную и читаемую часть кода.
# Используется в следующих блоках: core/immune_markers.py.
# На вход: функция не ожидает обязательных входных параметров.
# На выход: Path.
def immune_markers_reference_path() -> Path:
    return DATA_ROOT / "log_tpm_2025_2026.csv"


# Это функция для блока «иммунного профиля иммунных маркеров reference legacy пути». Она нужна для того, чтобы вынести отдельный шаг логики в самостоятельную и читаемую часть кода.
# Используется в следующих блоках: core/immune_markers.py.
# На вход: функция не ожидает обязательных входных параметров.
# На выход: Path.
def immune_markers_reference_legacy_path() -> Path:
    return BASE_DIR / "log_tpm_2025_2026.csv"


# Это функция для блока «tmb пути». Она нужна для того, чтобы вынести отдельный шаг логики в самостоятельную и читаемую часть кода.
# Используется в следующих блоках: sections/genetic_profile_block.py, core/immune_status.py.
# На вход: sample.
# На выход: Path.
def tmb_path(sample: str) -> Path:
    return sample_dir(sample) / "tmb.txt"


# Это функция для блока «vep ann пути». Она нужна для того, чтобы вынести отдельный шаг логики в самостоятельную и читаемую часть кода.
# Используется в следующих блоках: sections/genetic_profile_block.py, core/recommendations.py.
# На вход: sample.
# На выход: Path.
def vep_ann_path(sample: str) -> Path:
    return sample_dir(sample) / "tumor_vs_norma.merged_VEP.ann.tsv"


# Это функция для блока «mhci пути». Она нужна для того, чтобы вынести отдельный шаг логики в самостоятельную и читаемую часть кода.
# Используется внутри модуля paths и в связанных с ним блоках интерфейса.
# На вход: sample.
# На выход: Path.
def mhci_path(sample: str) -> Path:
    return sample_dir(sample) / "mhcI.epitopes.scored.tsv"


# Это функция для блока «norma alleles пути». Она нужна для того, чтобы вынести отдельный шаг логики в самостоятельную и читаемую часть кода.
# Используется в следующих блоках: sections/genetic_profile_block.py, core/recommendations.py.
# На вход: sample.
# На выход: Path.
def norma_alleles_path(sample: str) -> Path:
    return sample_dir(sample) / "norma.alleles.tsv"


# Это функция для блока «rsem gene tpm пути». Она нужна для того, чтобы вынести отдельный шаг логики в самостоятельную и читаемую часть кода.
# Используется в следующих блоках: core/immune_markers.py.
# На вход: sample.
# На выход: Path.
def rsem_gene_tpm_path(sample: str) -> Path:
    return sample_dir(sample) / "rsem.merged.gene_tpm.tsv"


# Это функция для блока «rsem test gene tpm пути». Она нужна для того, чтобы вынести отдельный шаг логики в самостоятельную и читаемую часть кода.
# Используется в следующих блоках: core/immune_markers.py.
# На вход: sample.
# На выход: Path.
def rsem_test_gene_tpm_path(sample: str) -> Path:
    return sample_dir(sample) / "rsem_test.merged.gene_tpm.tsv"


# Это функция для чтения и подготовки данных по фьюжн-событиям для дальнейшего показа в интерфейсе.
# Используется в следующих блоках: core/genetic_profile.py.
# На вход: sample.
# На выход: Path.
def starfusion_path(sample: str) -> Path:
    return sample_dir(sample) / "starfusion.abridged.coding_effect.tsv"


@lru_cache(maxsize=8)
# Это функция для блока «list samples cached». Она нужна для того, чтобы вынести отдельный шаг логики в самостоятельную и читаемую часть кода.
# Используется в следующих блоках: core/paths.py.
# На вход: root_str, root_mtime_ns.
# На выход: кортеж[str, ...].
def _list_samples_cached(root_str: str, root_mtime_ns: int) -> tuple[str, ...]:
    root = Path(root_str)
    if root_mtime_ns < 0 or not root.exists():
        return tuple()
    return tuple(sorted(p.name for p in root.iterdir() if p.is_dir()))


# Это функция для блока «list samples». Она нужна для того, чтобы вынести отдельный шаг логики в самостоятельную и читаемую часть кода.
# Используется в следующих блоках: sections/sample_selector.py, core/state.py.
# На вход: функция не ожидает обязательных входных параметров.
# На выход: список[str].
def list_samples() -> list[str]:
    root_str, root_mtime_ns = dir_token(DATA_ROOT)
    return list(_list_samples_cached(root_str, root_mtime_ns))
