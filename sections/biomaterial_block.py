import streamlit as st

from core.io_utils import esc
from core.state import cancel_edit, save_edit, start_edit


# Это функция для блока «отрисовки биоматериала card html». Она нужна для того, чтобы вынести отдельный шаг логики в самостоятельную и читаемую часть кода.
# Используется в следующих блоках: sections/biomaterial_block.py.
# На вход: rows.
# На выход: str.
def _render_biomaterial_card_html(rows: list[tuple[str, str]]) -> str:
    rows_html = ""
    for label, value in rows:
        value_text = esc(value) if str(value).strip() else "—"
        rows_html += f"""
        <div class="biomaterial-block-row">
            <div class="biomaterial-block-label">{esc(label)}</div>
            <div class="biomaterial-block-value">{value_text}</div>
        </div>
        """
    return f'<div class="biomaterial-block-card">{rows_html}</div>'


# Это функция для отрисовки блока «биоматериала block» в интерфейсе дашборда.
# Используется в следующих блоках: app.py.
# На вход: функция не ожидает обязательных входных параметров.
# На выход: результат дальнейшего шага обработки.
def render_biomaterial_block():
    left, right = st.columns([20, 1], gap="small")

    with left:
        st.markdown(
            """
            <div class="biomaterial-block-title-row">
                <div class="biomaterial-block-title-text">🧪 Информация о биоматериале</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with right:
        st.button(
            "✎",
            key="edit_btn_biomaterial",
            help="Редактировать блок",
            on_click=start_edit,
            args=("biomaterial",),
            type="secondary",
        )

    if st.session_state["edit_biomaterial"]:
        draft = dict(st.session_state["biomaterial_draft"])

        st.info("Изменения применяются после нажатия кнопки «Сохранить». Если не сохранить, правки не будут зафиксированы.")

        with st.form("biomaterial_edit_form", clear_on_submit=False):
            b1, b2 = st.columns(2, gap="medium")
            b3, b4 = st.columns(2, gap="medium")

            with b1:
                draft["biopsy_site"] = st.text_input(
                    "Сайт биопсии",
                    value=draft.get("biopsy_site", ""),
                    key="biomaterial_edit_biopsy_site",
                )
            with b2:
                draft["tumor_percent"] = st.text_input(
                    "Количество опухоли в биоматериале",
                    value=draft.get("tumor_percent", ""),
                    key="biomaterial_edit_tumor_percent",
                )
            with b3:
                draft["storage"] = st.text_input(
                    "Хранение образца",
                    value=draft.get("storage", ""),
                    key="biomaterial_edit_storage",
                )
            with b4:
                draft["organization"] = st.text_input(
                    "Организация, из которой пришла биопсия",
                    value=draft.get("organization", ""),
                    key="biomaterial_edit_organization",
                )

            st.session_state["biomaterial_draft"] = draft

            _, action_left, action_right = st.columns([8.6, 1, 1], gap="small")
            with action_left:
                submitted = st.form_submit_button("Сохранить")
            with action_right:
                cancelled = st.form_submit_button("Отмена")

        if submitted:
            save_edit("biomaterial")
            st.rerun()

        if cancelled:
            cancel_edit("biomaterial")
            st.rerun()

        return

    data = st.session_state["biomaterial_data"]

    card_1 = _render_biomaterial_card_html(
        rows=[("Сайт биопсии", data.get("biopsy_site", ""))]
    )
    card_2 = _render_biomaterial_card_html(
        rows=[("Количество опухоли в биоматериале", data.get("tumor_percent", ""))]
    )
    card_3 = _render_biomaterial_card_html(
        rows=[("Хранение образца", data.get("storage", ""))]
    )
    card_4 = _render_biomaterial_card_html(
        rows=[("Организация", data.get("organization", ""))]
    )

    st.markdown(
        f"""
        <div class="biomaterial-block-grid">
            {card_1}
            {card_2}
            {card_3}
            {card_4}
        </div>
        """,
        unsafe_allow_html=True,
    )
