from __future__ import annotations

from copy import deepcopy
from datetime import date

import streamlit as st

from core.io_utils import read_json, serialize_date, write_json
from core.paths import biomaterial_path, list_samples, meta_path, patient_path, rare_events_path

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

def ensure_state():
    if "selected_sample" not in st.session_state:
        samples = list_samples()
        st.session_state["selected_sample"] = samples[0] if samples else ""

    if "loaded_sample" not in st.session_state:
        st.session_state["loaded_sample"] = None

    if "edit_meta" not in st.session_state:
        st.session_state["edit_meta"] = False
    if "edit_patient" not in st.session_state:
        st.session_state["edit_patient"] = False
    if "edit_biomaterial" not in st.session_state:
        st.session_state["edit_biomaterial"] = False
    if "edit_rare_events" not in st.session_state:
        st.session_state["edit_rare_events"] = False

def load_sample_state(sample: str):
    st.session_state["meta_data"] = read_json(meta_path(sample), DEFAULT_META)
    st.session_state["patient_data"] = read_json(patient_path(sample), DEFAULT_PATIENT)
    st.session_state["biomaterial_data"] = read_json(biomaterial_path(sample), DEFAULT_BIOMATERIAL)

    st.session_state["meta_draft"] = deepcopy(st.session_state["meta_data"])
    st.session_state["patient_draft"] = deepcopy(st.session_state["patient_data"])
    st.session_state["biomaterial_draft"] = deepcopy(st.session_state["biomaterial_data"])

    st.session_state["edit_meta"] = False
    st.session_state["edit_patient"] = False
    st.session_state["edit_biomaterial"] = False

    st.session_state["loaded_sample"] = sample

    st.session_state["rare_events_data"] = read_json(rare_events_path(sample), DEFAULT_RARE_EVENTS)
    st.session_state["rare_events_draft"] = deepcopy(st.session_state["rare_events_data"])
    st.session_state["edit_rare_events"] = False

def sync_sample_state():
    current = st.session_state.get("selected_sample", "")
    loaded = st.session_state.get("loaded_sample")
    if current and current != loaded:
        load_sample_state(current)


def start_edit(block_name: str):
    if block_name == "meta":
        st.session_state["meta_draft"] = deepcopy(st.session_state["meta_data"])
        st.session_state["edit_meta"] = True
    elif block_name == "patient":
        st.session_state["patient_draft"] = deepcopy(st.session_state["patient_data"])
        st.session_state["edit_patient"] = True
    elif block_name == "biomaterial":
        st.session_state["biomaterial_draft"] = deepcopy(st.session_state["biomaterial_data"])
        st.session_state["edit_biomaterial"] = True
    elif block_name == "rare_events":
        st.session_state["rare_events_draft"] = deepcopy(st.session_state["rare_events_data"])
        st.session_state["edit_rare_events"] = True


def cancel_edit(block_name: str):
    if block_name == "meta":
        st.session_state["meta_draft"] = deepcopy(st.session_state["meta_data"])
        st.session_state["edit_meta"] = False
    elif block_name == "patient":
        st.session_state["patient_draft"] = deepcopy(st.session_state["patient_data"])
        st.session_state["edit_patient"] = False
    elif block_name == "biomaterial":
        st.session_state["biomaterial_draft"] = deepcopy(st.session_state["biomaterial_data"])
        st.session_state["edit_biomaterial"] = False
    elif block_name == "rare_events":
        st.session_state["rare_events_draft"] = deepcopy(st.session_state["rare_events_data"])
        st.session_state["edit_rare_events"] = False


def save_edit(block_name: str):
    sample = st.session_state.get("selected_sample", "")
    if not sample:
        return


    if block_name == "meta":
        data = deepcopy(st.session_state["meta_draft"])
        data["report_date"] = serialize_date(data.get("report_date"))
        st.session_state["meta_data"] = data
        write_json(meta_path(sample), data)
        st.session_state["edit_meta"] = False

    elif block_name == "patient":
        data = deepcopy(st.session_state["patient_draft"])
        st.session_state["patient_data"] = data
        write_json(patient_path(sample), data)
        st.session_state["edit_patient"] = False

    elif block_name == "biomaterial":
        data = deepcopy(st.session_state["biomaterial_draft"])
        st.session_state["biomaterial_data"] = data
        write_json(biomaterial_path(sample), data)
        st.session_state["edit_biomaterial"] = False
    elif block_name == "rare_events":
        data = deepcopy(st.session_state["rare_events_draft"])
        st.session_state["rare_events_data"] = data
        write_json(rare_events_path(sample), data)
        st.session_state["edit_rare_events"] = False


def dashboard_mode_text() -> str:
    active = []
    if st.session_state.get("edit_meta", False):
        active.append("Метаданные отчёта")
    if st.session_state.get("edit_patient", False):
        active.append("Информация о пациенте")
    if st.session_state.get("edit_biomaterial", False):
        active.append("Информация о биоматериале")
    if st.session_state.get("edit_rare_events", False):
        active.append("Редкие генетические события")

    if active:
        return "Редактирование: " + ", ".join(active)
    return "Просмотр"