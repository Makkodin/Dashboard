import streamlit as st

from core.io_utils import esc
from core.state import dashboard_mode_text


def render_bottom_mode_indicator():
    mode_text = dashboard_mode_text()
    mode_class = "footer-mode-pill-edit" if "Редактирование:" in mode_text else "footer-mode-pill-view"

    st.markdown(
        f"""
        <div class="footer-mode-wrap">
            <span class="footer-mode-label">Режим дашборда:</span>
            <span class="footer-mode-pill {mode_class}">{esc(mode_text)}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )