from __future__ import annotations

import streamlit as st

from core.state import dashboard_section_options, save_section_selection


def render_dashboard_section_picker() -> None:
    st.markdown(
        '''
        <div class="section-picker-marker"></div>
        <div class="section-picker-head">
            <div class="section-picker-title">Выберите разделы для отрисовки</div>
            <div class="section-picker-subtitle">
                Перед открытием дашборда можно отметить, какие разделы нужно показать.
                Например, только «Клиническая информация» и «Рекомендации».
            </div>
        </div>
        ''',
        unsafe_allow_html=True,
    )

    options = dashboard_section_options()
    grid_cols = st.columns(3, gap="large")
    for idx, (key, label) in enumerate(options):
        with grid_cols[idx % 3]:
            st.checkbox(label, key=f"section_picker_{key}")

    selected = [key for key, _ in options if st.session_state.get(f"section_picker_{key}", False)]

    action_cols = st.columns([8, 1.2, 1.2, 1.4], gap="small")
    with action_cols[1]:
        if st.button("Все", key="section_picker_select_all"):
            for key, _ in options:
                st.session_state[f"section_picker_{key}"] = True
            st.rerun()
    with action_cols[2]:
        if st.button("Снять", key="section_picker_clear_all"):
            for key, _ in options:
                st.session_state[f"section_picker_{key}"] = False
            st.rerun()
    with action_cols[3]:
        if st.button("Открыть", key="section_picker_open", type="primary", disabled=not selected):
            save_section_selection(selected)
            st.rerun()

    if not selected:
        st.warning("Нужно выбрать хотя бы один раздел.")