from pathlib import Path

import streamlit as st

from core.state import ensure_state, sync_sample_state
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


st.set_page_config(
    page_title="Клинический отчет",
    layout="wide",
    initial_sidebar_state="collapsed",
)

load_css_folder()

ensure_state()
render_sample_selector()
sync_sample_state()

render_title_block()
render_meta_block()

st.markdown(
    """
    <div class="section-common-title-frame">
        <div class="section-common-title-text">Клиническая информация</div>
    </div>
    """,
    unsafe_allow_html=True,
)

render_patient_block()
render_treatment_block()
render_biomaterial_block()
render_genetic_profile_block()
render_immune_status_block()
render_immune_signatures_block()
render_immune_markers_block()
render_recommendations_block()
render_contacts_block()
render_annotation_blocks()
render_bottom_mode_indicator()
