from pathlib import Path

import streamlit as st

from core.state import ensure_state, is_section_enabled, open_section_picker, sync_sample_state
from sections.annotation_blocks import render_annotation_blocks
from sections.biomaterial_block import render_biomaterial_block
from sections.contacts_block import render_contacts_block
from sections.footer_mode import render_bottom_mode_indicator
from sections.genetic_profile_block import render_genetic_profile_block
from sections.immune_markers_block import render_immune_markers_block
from sections.immune_signatures_block import render_immune_signatures_block
from sections.immune_status_block import render_immune_status_block
from sections.meta_block import render_meta_block
from sections.patient_block import render_patient_block
from sections.recommendations_block import render_recommendations_block
from sections.sample_selector import render_sample_selector
from sections.section_picker import render_dashboard_section_picker
from sections.title_block import render_title_block
from sections.treatment_block import render_treatment_block


def load_css_folder(folder: str = "styles_css"):
    css_dir = Path(folder)
    if not css_dir.exists():
        st.error(f"Папка {folder} не найдена")
        return

    css_files = sorted(css_dir.glob("*.css"))
    parts: list[str] = []

    for css_file in css_files:
        parts.append(f"/* FILE: {css_file.name} */\n")
        parts.append(css_file.read_text(encoding="utf-8"))
        parts.append("\n\n")

    if parts:
        st.markdown(f"<style>{''.join(parts)}</style>", unsafe_allow_html=True)


def _render_clinical_info_section() -> None:
    st.markdown(
        '''
        <div class="section-common-title-frame">
            <div class="section-common-title-text">Клиническая информация</div>
        </div>
        ''',
        unsafe_allow_html=True,
    )
    render_patient_block()
    render_treatment_block()
    render_biomaterial_block()


st.set_page_config(
    page_title="Клинический отчет",
    layout="wide",
    initial_sidebar_state="collapsed",
)

load_css_folder()

ensure_state()
render_sample_selector()
sync_sample_state()

with st.sidebar:
    st.divider()
    if st.button("Выбрать разделы", use_container_width=True):
        open_section_picker()
        st.rerun()

if not st.session_state.get("dashboard_sections_confirmed", False):
    render_dashboard_section_picker()
    st.stop()

render_title_block()

if is_section_enabled("meta"):
    render_meta_block()

if is_section_enabled("clinical"):
    _render_clinical_info_section()

if is_section_enabled("genetic"):
    render_genetic_profile_block()

if is_section_enabled("immune_status"):
    render_immune_status_block()

if is_section_enabled("immune_signatures"):
    render_immune_signatures_block()

if is_section_enabled("immune_markers"):
    render_immune_markers_block()

if is_section_enabled("recommendations"):
    render_recommendations_block()

if is_section_enabled("contacts"):
    render_contacts_block()

if is_section_enabled("annotations"):
    render_annotation_blocks()

render_bottom_mode_indicator()
