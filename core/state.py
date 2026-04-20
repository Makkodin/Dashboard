from __future__ import annotations

from copy import deepcopy
from datetime import date

import streamlit as st

from core.genetic_profile import load_rare_events_text
from core.io_utils import read_json, read_text, serialize_date, write_json
from core.paths import (
    biomaterial_path,
    contacts_text_path,
    defaults_contacts_text_path,
    list_samples,
    meta_path,
    patient_path,
    rare_events_path,
)
from core.timeline import load_treatment_items, save_treatment_items

DEFAULT_META = {"report_number": "", "report_date": date.today().isoformat(), "status_value": "финальный"}
DEFAULT_PATIENT = {"fio": "", "age": "", "sex": "", "patient_id": "", "family_history": "", "diagnosis": "", "tnm_stage": "", "histology": ""}
DEFAULT_BIOMATERIAL = {"biopsy_site": "", "tumor_percent": "", "storage": "", "organization": ""}
DEFAULT_RARE_EVENTS = {"text": "Не выявлены"}

EDIT_FLAGS = {
    "meta": "edit_meta",
    "patient": "edit_patient",
    "treatment": "edit_treatment",
    "biomaterial": "edit_biomaterial",
    "rare_events": "edit_rare_events",
}
EDIT_DATA_KEYS = {
    "meta": "meta_data",
    "patient": "patient_data",
    "treatment": "treatment_data",
    "biomaterial": "biomaterial_data",
    "rare_events": "rare_events_data",
}
EDIT_DRAFT_KEYS = {
    "meta": "meta_draft",
    "patient": "patient_draft",
    "treatment": "treatment_draft",
    "biomaterial": "biomaterial_draft",
    "rare_events": "rare_events_draft",
}
JSON_DEFAULTS = {"meta": DEFAULT_META, "patient": DEFAULT_PATIENT, "biomaterial": DEFAULT_BIOMATERIAL, "rare_events": DEFAULT_RARE_EVENTS}
JSON_PATHS = {"meta": meta_path, "patient": patient_path, "biomaterial": biomaterial_path, "rare_events": rare_events_path}

SECTION_OPTIONS = [
    ("meta", "Метаданные отчёта"),
    ("clinical", "Клиническая информация"),
    ("genetic", "Генетический профиль"),
    ("immune_status", "Иммунный статус"),
    ("immune_signatures", "Иммунные сигнатуры"),
    ("immune_markers", "Иммунные маркеры"),
    ("recommendations", "Рекомендации"),
    ("contacts", "Контакты / Лаборатория"),
    ("annotations", "Аннотация блоков"),
]


# Это функция для блока «ensure состояния». Она нужна для того, чтобы вынести отдельный шаг логики в самостоятельную и читаемую часть кода.
# Используется в следующих блоках: app.py.
# На вход: функция не ожидает обязательных входных параметров.
# На выход: None.
def ensure_state() -> None:
    if "selected_sample" not in st.session_state:
        samples = list_samples()
        st.session_state["selected_sample"] = samples[0] if samples else ""
    if "loaded_sample" not in st.session_state:
        st.session_state["loaded_sample"] = None
    for flag in EDIT_FLAGS.values():
        if flag not in st.session_state:
            st.session_state[flag] = False

    if "dashboard_sections_selected" not in st.session_state:
        st.session_state["dashboard_sections_selected"] = []
    if "dashboard_sections_confirmed" not in st.session_state:
        st.session_state["dashboard_sections_confirmed"] = False
    if "dashboard_sections_pending_action" not in st.session_state:
        st.session_state["dashboard_sections_pending_action"] = None

    for key, _ in SECTION_OPTIONS:
        picker_key = f"section_picker_{key}"
        if picker_key not in st.session_state:
            st.session_state[picker_key] = key in st.session_state["dashboard_sections_selected"]


# Это функция для блока «dashboard раздела options». Она нужна для того, чтобы вынести отдельный шаг логики в самостоятельную и читаемую часть кода.
# Используется в следующих блоках: sections/section_picker.py.
# На вход: функция не ожидает обязательных входных параметров.
# На выход: список[кортеж[str, str]].
def dashboard_section_options() -> list[tuple[str, str]]:
    return SECTION_OPTIONS


# Это функция для блока «open раздела выбора». Она нужна для того, чтобы вынести отдельный шаг логики в самостоятельную и читаемую часть кода.
# Используется в следующих блоках: app.py.
# На вход: функция не ожидает обязательных входных параметров.
# На выход: None.
def open_section_picker() -> None:
    selected = set(st.session_state.get("dashboard_sections_selected", []))
    for key, _ in SECTION_OPTIONS:
        st.session_state[f"section_picker_{key}"] = key in selected
    st.session_state["dashboard_sections_confirmed"] = False


# Это функция для сохранения данных, связанных с блоком «сохранения раздела selection». 
# Используется в следующих блоках: core/state.py.
# На вход: section_keys.
# На выход: None.
def save_section_selection(section_keys: list[str]) -> None:
    allowed = {key for key, _ in SECTION_OPTIONS}
    cleaned = [key for key in section_keys if key in allowed]
    st.session_state["dashboard_sections_selected"] = cleaned
    st.session_state["dashboard_sections_confirmed"] = True


# Это функция для блока «confirm раздела selection from выбора». Она нужна для того, чтобы вынести отдельный шаг логики в самостоятельную и читаемую часть кода.
# Используется в следующих блоках: sections/section_picker.py.
# На вход: функция не ожидает обязательных входных параметров.
# На выход: None.
def confirm_section_selection_from_picker() -> None:
    selected = [key for key, _ in SECTION_OPTIONS if st.session_state.get(f"section_picker_{key}", False)]
    if selected:
        save_section_selection(selected)


# Это функция для блока «queue select all dashboard sections». Она нужна для того, чтобы вынести отдельный шаг логики в самостоятельную и читаемую часть кода.
# Используется в следующих блоках: sections/section_picker.py.
# На вход: функция не ожидает обязательных входных параметров.
# На выход: None.
def queue_select_all_dashboard_sections() -> None:
    st.session_state["dashboard_sections_pending_action"] = "select_all"


# Это функция для блока «queue clear all dashboard sections». Она нужна для того, чтобы вынести отдельный шаг логики в самостоятельную и читаемую часть кода.
# Используется в следующих блоках: sections/section_picker.py.
# На вход: функция не ожидает обязательных входных параметров.
# На выход: None.
def queue_clear_all_dashboard_sections() -> None:
    st.session_state["dashboard_sections_pending_action"] = "clear_all"


# Это функция для блока «apply pending dashboard раздела action». Она нужна для того, чтобы вынести отдельный шаг логики в самостоятельную и читаемую часть кода.
# Используется в следующих блоках: sections/section_picker.py.
# На вход: функция не ожидает обязательных входных параметров.
# На выход: None.
def apply_pending_dashboard_section_action() -> None:
    action = st.session_state.get("dashboard_sections_pending_action")
    if action == "select_all":
        for key, _ in SECTION_OPTIONS:
            st.session_state[f"section_picker_{key}"] = True
    elif action == "clear_all":
        for key, _ in SECTION_OPTIONS:
            st.session_state[f"section_picker_{key}"] = False
    st.session_state["dashboard_sections_pending_action"] = None


# Это функция для блока «is раздела enabled». Она нужна для того, чтобы вынести отдельный шаг логики в самостоятельную и читаемую часть кода.
# Используется в следующих блоках: app.py.
# На вход: section_key.
# На выход: bool.
def is_section_enabled(section_key: str) -> bool:
    return section_key in set(st.session_state.get("dashboard_sections_selected", []))


# Это функция для загрузки данных, связанных с блоком «загрузки редких событий block». 
# Используется в следующих блоках: core/state.py.
# На вход: sample.
# На выход: словарь.
def _load_rare_events_block(sample: str) -> dict:
    stored = read_json(rare_events_path(sample), {"text": ""})
    text = str(stored.get("text", "")).strip() or load_rare_events_text(sample)
    return {"text": text}


# Это функция для загрузки данных, связанных с блоком «загрузки образца состояния». 
# Используется в следующих блоках: core/state.py.
# На вход: sample.
# На выход: None.
def load_sample_state(sample: str) -> None:
    for block_name, default_data in JSON_DEFAULTS.items():
        data_key = EDIT_DATA_KEYS[block_name]
        draft_key = EDIT_DRAFT_KEYS[block_name]
        flag_key = EDIT_FLAGS[block_name]
        if block_name == "rare_events":
            st.session_state[data_key] = _load_rare_events_block(sample)
        else:
            st.session_state[data_key] = read_json(JSON_PATHS[block_name](sample), default_data)
        st.session_state[draft_key] = deepcopy(st.session_state[data_key])
        st.session_state[flag_key] = False

    st.session_state["treatment_data"] = load_treatment_items(sample)
    st.session_state["treatment_draft"] = deepcopy(st.session_state["treatment_data"])
    st.session_state["edit_treatment"] = False

    default_contacts = read_text(defaults_contacts_text_path(), "")
    st.session_state["contacts_text"] = read_text(contacts_text_path(sample), default_contacts)
    st.session_state["loaded_sample"] = sample


# Это функция для блока «sync образца состояния». Она нужна для того, чтобы вынести отдельный шаг логики в самостоятельную и читаемую часть кода.
# Используется в следующих блоках: app.py.
# На вход: функция не ожидает обязательных входных параметров.
# На выход: None.
def sync_sample_state() -> None:
    current = st.session_state.get("selected_sample", "")
    loaded = st.session_state.get("loaded_sample")
    if current and current != loaded:
        load_sample_state(current)


# Это функция для блока «start edit». Она нужна для того, чтобы вынести отдельный шаг логики в самостоятельную и читаемую часть кода.
# Используется в следующих блоках: sections/biomaterial_block.py, sections/genetic_profile_block.py.
# На вход: block_name.
# На выход: None.
def start_edit(block_name: str) -> None:
    if block_name not in EDIT_FLAGS:
        return
    st.session_state[EDIT_DRAFT_KEYS[block_name]] = deepcopy(st.session_state[EDIT_DATA_KEYS[block_name]])
    st.session_state[EDIT_FLAGS[block_name]] = True


# Это функция для блока «cancel edit». Она нужна для того, чтобы вынести отдельный шаг логики в самостоятельную и читаемую часть кода.
# Используется в следующих блоках: sections/biomaterial_block.py, sections/genetic_profile_block.py.
# На вход: block_name.
# На выход: None.
def cancel_edit(block_name: str) -> None:
    if block_name not in EDIT_FLAGS:
        return
    st.session_state[EDIT_DRAFT_KEYS[block_name]] = deepcopy(st.session_state[EDIT_DATA_KEYS[block_name]])
    st.session_state[EDIT_FLAGS[block_name]] = False


# Это функция для сохранения данных, связанных с блоком «сохранения edit». 
# Используется в следующих блоках: sections/biomaterial_block.py, sections/genetic_profile_block.py.
# На вход: block_name.
# На выход: None.
def save_edit(block_name: str) -> None:
    sample = st.session_state.get("selected_sample", "")
    if not sample or block_name not in EDIT_FLAGS:
        return

    if block_name == "treatment":
        data = deepcopy(st.session_state["treatment_draft"])
        st.session_state["treatment_data"] = data
        save_treatment_items(sample, data)
        st.session_state["edit_treatment"] = False
        return

    data = deepcopy(st.session_state[EDIT_DRAFT_KEYS[block_name]])
    if block_name == "meta":
        data["report_date"] = serialize_date(data.get("report_date"))
    st.session_state[EDIT_DATA_KEYS[block_name]] = data
    write_json(JSON_PATHS[block_name](sample), data)
    st.session_state[EDIT_FLAGS[block_name]] = False


# Это функция для блока «dashboard mode текста». Она нужна для того, чтобы вынести отдельный шаг логики в самостоятельную и читаемую часть кода.
# Используется в следующих блоках: sections/footer_mode.py.
# На вход: функция не ожидает обязательных входных параметров.
# На выход: str.
def dashboard_mode_text() -> str:
    labels = {
        "meta": "Метаданные отчёта",
        "patient": "Информация о пациенте",
        "treatment": "История лечения",
        "biomaterial": "Информация о биоматериале",
        "rare_events": "Редкие генетические события",
    }
    active = [labels[name] for name, flag in EDIT_FLAGS.items() if st.session_state.get(flag, False)]
    if active:
        return "Редактирование: " + ", ".join(active)
    return "Просмотр"
