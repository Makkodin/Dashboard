from __future__ import annotations

from copy import deepcopy
from datetime import date
from pathlib import Path

import streamlit as st

from core.io_utils import read_json, serialize_date, write_json
from core.paths import (
    biomaterial_path,
    contacts_text_path,
    list_samples,
    meta_path,
    patient_path,
    rare_events_path,
)

DEFAULT_META = {
    "report_number": "",
    "report_date": date.today().isoformat(),
    "status_value": "финальный",
}

DEFAULT_PATIENT = {
    "fio": "",
    "age": "",
    "sex": "",
    "patient_id": "",
    "family_history": "",
    "diagnosis": "",
    "tnm_stage": "",
    "histology": "",
}

DEFAULT_BIOMATERIAL = {
    "biopsy_site": "",
    "tumor_percent": "",
    "storage": "",
    "organization": "",
}

DEFAULT_RARE_EVENTS = {
    "text": "Не выявлены",
}

DEFAULT_CONTACTS_TEXT = """Лаборатория: НИЦЭМ им. Н.Ф. Гамалеи
Директор: д.б.н. Логунов Д.Ю.
Адрес: 123098, г.Москва, ул. Гамалеи, д. 18
тел: +7 (499)193 30 01
Факс: +7(499)193-61-83
E mail: info@gamaleya.org
Версия отчета: v1

НИЦЭМ им. Н.Ф. Гамалеи © 2026"""

EDIT_FLAGS = {
    "meta": "edit_meta",
    "patient": "edit_patient",
    "biomaterial": "edit_biomaterial",
    "rare_events": "edit_rare_events",
    "contacts": "edit_contacts",
}

EDIT_DATA_KEYS = {
    "meta": "meta_data",
    "patient": "patient_data",
    "biomaterial": "biomaterial_data",
    "rare_events": "rare_events_data",
    "contacts": "contacts_text",
}

EDIT_DRAFT_KEYS = {
    "meta": "meta_draft",
    "patient": "patient_draft",
    "biomaterial": "biomaterial_draft",
    "rare_events": "rare_events_draft",
    "contacts": "contacts_draft",
}

JSON_DEFAULTS = {
    "meta": DEFAULT_META,
    "patient": DEFAULT_PATIENT,
    "biomaterial": DEFAULT_BIOMATERIAL,
    "rare_events": DEFAULT_RARE_EVENTS,
}

JSON_PATHS = {
    "meta": meta_path,
    "patient": patient_path,
    "biomaterial": biomaterial_path,
    "rare_events": rare_events_path,
}


def _read_text(path: Path, default: str) -> str:
    if not path.exists():
        return default
    try:
        text = path.read_text(encoding="utf-8")
        return text if text.strip() else default
    except Exception:
        return default


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def ensure_state() -> None:
    if "selected_sample" not in st.session_state:
        samples = list_samples()
        st.session_state["selected_sample"] = samples[0] if samples else ""

    if "loaded_sample" not in st.session_state:
        st.session_state["loaded_sample"] = None

    for flag in EDIT_FLAGS.values():
        if flag not in st.session_state:
            st.session_state[flag] = False


def load_sample_state(sample: str) -> None:
    for block_name, default_data in JSON_DEFAULTS.items():
        data_key = EDIT_DATA_KEYS[block_name]
        draft_key = EDIT_DRAFT_KEYS[block_name]
        flag_key = EDIT_FLAGS[block_name]
        path_func = JSON_PATHS[block_name]

        st.session_state[data_key] = read_json(path_func(sample), default_data)
        st.session_state[draft_key] = deepcopy(st.session_state[data_key])
        st.session_state[flag_key] = False

    contacts_text = _read_text(contacts_text_path(sample), DEFAULT_CONTACTS_TEXT)
    st.session_state["contacts_text"] = contacts_text
    st.session_state["contacts_draft"] = contacts_text
    st.session_state["edit_contacts"] = False

    st.session_state["loaded_sample"] = sample


def sync_sample_state() -> None:
    current = st.session_state.get("selected_sample", "")
    loaded = st.session_state.get("loaded_sample")
    if current and current != loaded:
        load_sample_state(current)


def start_edit(block_name: str) -> None:
    if block_name not in EDIT_FLAGS:
        return
    st.session_state[EDIT_DRAFT_KEYS[block_name]] = deepcopy(st.session_state[EDIT_DATA_KEYS[block_name]])
    st.session_state[EDIT_FLAGS[block_name]] = True


def cancel_edit(block_name: str) -> None:
    if block_name not in EDIT_FLAGS:
        return
    st.session_state[EDIT_DRAFT_KEYS[block_name]] = deepcopy(st.session_state[EDIT_DATA_KEYS[block_name]])
    st.session_state[EDIT_FLAGS[block_name]] = False


def save_edit(block_name: str) -> None:
    sample = st.session_state.get("selected_sample", "")
    if not sample or block_name not in EDIT_FLAGS:
        return

    if block_name == "contacts":
        text = str(st.session_state["contacts_draft"])
        st.session_state["contacts_text"] = text
        _write_text(contacts_text_path(sample), text)
        st.session_state["edit_contacts"] = False
        return

    data = deepcopy(st.session_state[EDIT_DRAFT_KEYS[block_name]])
    if block_name == "meta":
        data["report_date"] = serialize_date(data.get("report_date"))

    st.session_state[EDIT_DATA_KEYS[block_name]] = data
    write_json(JSON_PATHS[block_name](sample), data)
    st.session_state[EDIT_FLAGS[block_name]] = False


def dashboard_mode_text() -> str:
    labels = {
        "meta": "Метаданные отчёта",
        "patient": "Информация о пациенте",
        "biomaterial": "Информация о биоматериале",
        "rare_events": "Редкие генетические события",
        "contacts": "Контакты",
    }
    active = [labels[name] for name, flag in EDIT_FLAGS.items() if st.session_state.get(flag, False)]
    if active:
        return "Редактирование: " + ", ".join(active)
    return "Просмотр"
