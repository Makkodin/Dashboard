import streamlit as st

from core.io_utils import esc
from core.state import cancel_edit, save_edit, start_edit


def _render_patient_card_html(rows: list[tuple[str, str]]) -> str:
    rows_html = ""
    for label, value in rows:
        value_text = esc(value) if str(value).strip() else "—"
        rows_html += f"""
        <div class="patient-block-row">
            <div class="patient-block-label">{esc(label)}</div>
            <div class="patient-block-value">{value_text}</div>
        </div>
        """
    return f'<div class="patient-block-card">{rows_html}</div>'


def render_patient_block():
    left, right = st.columns([20, 1], gap="small")

    with left:
        st.markdown(
            """
            <div class="patient-block-title-row">
                <div class="patient-block-title-text">👤 Информация о пациенте</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with right:
        st.button(
            "✎",
            key="edit_btn_patient",
            help="Редактировать блок",
            on_click=start_edit,
            args=("patient",),
            type="secondary",
        )

    if st.session_state["edit_patient"]:
        draft = dict(st.session_state["patient_draft"])

        st.info("Изменения применяются после нажатия кнопки «Сохранить». Если не сохранить, правки не будут зафиксированы.")

        with st.form("patient_edit_form", clear_on_submit=False):
            col1, col2 = st.columns(2, gap="medium")

            with col1:
                draft["fio"] = st.text_input("ФИО", value=draft.get("fio", ""), key="patient_edit_fio")
                draft["age"] = st.text_input("Возраст", value=draft.get("age", ""), key="patient_edit_age")

                options = ["", "мужской", "женский"]
                current_sex = draft.get("sex", "")
                idx = options.index(current_sex) if current_sex in options else 0
                draft["sex"] = st.selectbox("Пол", options, index=idx, key="patient_edit_sex")

                draft["patient_id"] = st.text_input("ID пациента", value=draft.get("patient_id", ""), key="patient_edit_id")

                draft["family_history"] = st.text_area(
                    "Семейный анамнез",
                    value=draft.get("family_history", ""),
                    height=110,
                    key="patient_edit_family_history",
                )

            with col2:
                draft["diagnosis"] = st.text_area(
                    "Диагноз",
                    value=draft.get("diagnosis", ""),
                    height=90,
                    key="patient_edit_diagnosis",
                )

                draft["tnm_stage"] = st.text_input("Стадия TNM", value=draft.get("tnm_stage", ""), key="patient_edit_tnm")

                draft["histology"] = st.text_area(
                    "Гистология",
                    value=draft.get("histology", ""),
                    height=145,
                    key="patient_edit_histology",
                )

            st.session_state["patient_draft"] = draft

            _, action_left, action_right = st.columns([8.6, 1, 1], gap="small")
            with action_left:
                submitted = st.form_submit_button("Сохранить")
            with action_right:
                cancelled = st.form_submit_button("Отмена")

        if submitted:
            save_edit("patient")
            st.rerun()

        if cancelled:
            cancel_edit("patient")
            st.rerun()

        return

    data = st.session_state["patient_data"]

    left_card_html = _render_patient_card_html(
        rows=[
            ("ФИО", data.get("fio", "")),
            ("Возраст", data.get("age", "")),
            ("Пол", data.get("sex", "")),
            ("ID", data.get("patient_id", "")),
            ("Семейный анамнез", data.get("family_history", "")),
        ]
    )

    right_card_html = _render_patient_card_html(
        rows=[
            ("Диагноз", data.get("diagnosis", "")),
            ("Стадия TNM", data.get("tnm_stage", "")),
            ("Гистология", data.get("histology", "")),
        ]
    )

    st.markdown(
        f"""
        <div class="patient-block-grid">
            {left_card_html}
            {right_card_html}
        </div>
        """,
        unsafe_allow_html=True,
    )
