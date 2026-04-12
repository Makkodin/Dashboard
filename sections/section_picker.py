from __future__ import annotations

import streamlit as st

from core.state import dashboard_section_options, save_section_selection


SECTION_DESCRIPTIONS = {
    "meta": "Номер отчёта, дата формирования и статус отчёта.",
    "clinical": "Информация о пациенте, история лечения и данные о биоматериале.",
    "genetic": "TMB, ключевые соматические варианты, HLA-гаплотипы и редкие генетические события.",
    "immune_status": "Чистота опухоли, иммунный подтип, клеточный состав и итоговая интерпретация.",
    "immune_signatures": "Иммунные и стромальные сигнатуры с цветовой шкалой и score-показателями.",
    "immune_markers": "Гены-маркеры с графиками распределения, процентилями и уровнями экспрессии.",
    "recommendations": "Карточки интегративной интерпретации молекулярного профиля пациента.",
    "contacts": "Лаборатория, контакты, версия отчёта и служебная информация.",
    "annotations": "Справочные текстовые пояснения по ключевым блокам отчёта.",
}


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
    grid_cols = st.columns(2, gap="medium")

    for idx, (key, label) in enumerate(options):
        with grid_cols[idx % 2]:
            with st.container(border=True):
                st.markdown('<div class="section-picker-option-marker"></div>', unsafe_allow_html=True)
                st.checkbox(label, key=f"section_picker_{key}")
                st.markdown(
                    f'<div class="section-picker-option-desc">{SECTION_DESCRIPTIONS.get(key, "")}</div>',
                    unsafe_allow_html=True,
                )

    selected = [key for key, _ in options if st.session_state.get(f"section_picker_{key}", False)]

    action_cols = st.columns([7, 1.2, 1.2, 1.2], gap="small")
    with action_cols[1]:
        if st.button("Все", key="section_picker_select_all", use_container_width=True):
            for key, _ in options:
                st.session_state[f"section_picker_{key}"] = True
            st.rerun()
    with action_cols[2]:
        if st.button("Снять", key="section_picker_clear_all", use_container_width=True):
            for key, _ in options:
                st.session_state[f"section_picker_{key}"] = False
            st.rerun()
    with action_cols[3]:
        if st.button("Открыть", key="section_picker_open", type="primary", use_container_width=True, disabled=not selected):
            save_section_selection(selected)
            st.rerun()

    if not selected:
        st.warning("Нужно выбрать хотя бы один раздел.")
