from __future__ import annotations

import streamlit as st

from core.io_utils import esc, read_text
from core.paths import annotation_blocks_path, defaults_annotation_blocks_path


DEFAULT_SECTION_TITLE = "Аннотация блоков"
SUBTITLES = {
    "HLA-гаплотипы (класс I)",
    "Опухолевая мутационная нагрузка (TMB)",
    "Альтерации гена BRAF",
    "Альтерации гена NRAS",
    "Альтерации гена NF1",
    "Молекулярный подтип triple-WT (BRAF/NF1/RAS дикого типа)",
}


# Это функция для отрисовки блока «аннотаций blocks» в интерфейсе дашборда.
# Используется в следующих блоках: app.py.
# На вход: функция не ожидает обязательных входных параметров.
# На выход: None.
def render_annotation_blocks() -> None:
    sample = st.session_state.get("selected_sample", "")
    if not sample:
        return

    fallback = read_text(defaults_annotation_blocks_path(), "")
    text = read_text(annotation_blocks_path(sample), fallback)
    lines = [line.rstrip() for line in text.splitlines()]

    html_parts = [
        '<div class="annotation-blocks-section">',
        '<div class="annotation-blocks-print-shell">',
        '<div class="section-common-title-frame annotation-section-title">',
        f'<div class="section-common-title-text">{esc(DEFAULT_SECTION_TITLE)}</div>',
        '</div>',
        '<div class="annotation-blocks-wrap">',
    ]
    for line in lines:
        stripped = line.strip()
        if not stripped:
            html_parts.append('<div class="annotation-blocks-gap"></div>')
            continue
        if stripped.endswith(":"):
            html_parts.append(f'<div class="annotation-blocks-title">{esc(stripped[:-1])}</div>')
        elif stripped in SUBTITLES:
            html_parts.append(f'<div class="annotation-blocks-subtitle">{esc(stripped)}</div>')
        elif stripped.startswith("•"):
            html_parts.append(f'<div class="annotation-blocks-bullet">{esc(stripped)}</div>')
        else:
            html_parts.append(f'<div class="annotation-blocks-text">{esc(stripped)}</div>')
    html_parts.append('</div>')
    html_parts.append('</div>')
    html_parts.append('</div>')
    st.markdown(''.join(html_parts), unsafe_allow_html=True)
