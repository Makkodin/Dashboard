from __future__ import annotations

import streamlit as st

from core.state import (
    apply_pending_dashboard_section_action,
    confirm_section_selection_from_picker,
    dashboard_section_options,
    queue_clear_all_dashboard_sections,
    queue_select_all_dashboard_sections,
)


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

    apply_pending_dashboard_section_action()
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
        st.button(
            "Все",
            key="section_picker_select_all",
            use_container_width=True,
            on_click=queue_select_all_dashboard_sections,
        )
    with action_cols[2]:
        st.button(
            "Снять",
            key="section_picker_clear_all",
            use_container_width=True,
            on_click=queue_clear_all_dashboard_sections,
        )
    with action_cols[3]:
        st.button(
            "Открыть",
            key="section_picker_open",
            use_container_width=True,
            disabled=not selected,
            on_click=confirm_section_selection_from_picker,
        )

    if not selected:
        st.warning("Нужно выбрать хотя бы один раздел.")
