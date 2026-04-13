import streamlit as st

from core.io_utils import esc, parse_iso_date
from core.state import cancel_edit, save_edit, start_edit


def status_badge_html(status_value: str) -> str:
    status_clean = str(status_value).strip().lower()
    badge_class = "meta-status-final" if status_clean == "финальный" else "meta-status-temp"
    return f'<span class="meta-status-badge {badge_class}">{esc(status_value)}</span>'


def render_meta_block():
    left, right = st.columns([20, 1], gap="small")

    with left:
        st.markdown(
            """
            <div class="meta-block-title-row">
                <div class="meta-block-title-text">📝 Метаданные отчёта</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with right:
        st.button(
            "✎",
            key="edit_btn_meta",
            help="Редактировать блок",
            on_click=start_edit,
            args=("meta",),
            type="secondary",
        )

    if st.session_state["edit_meta"]:
        draft = dict(st.session_state["meta_draft"])

        c1, c2, c3 = st.columns(3, gap="medium")

        with c1:
            draft["report_number"] = st.text_input(
                "Номер отчета",
                value=draft.get("report_number", ""),
                key="meta_edit_report_number",
            )

        with c2:
            draft["report_date"] = st.date_input(
                "Дата формирования",
                value=parse_iso_date(draft.get("report_date")),
                key="meta_edit_report_date",
            )

        with c3:
            current_status = draft.get("status_value", "финальный")
            idx = 0 if current_status == "финальный" else 1
            draft["status_value"] = st.selectbox(
                "Статус",
                ["финальный", "временный"],
                index=idx,
                key="meta_edit_status_value",
            )

        st.session_state["meta_draft"] = draft

        _, action_left, action_right = st.columns([8.6, 1, 1], gap="small")

        with action_left:
            st.button("Сохранить", key="save_meta", on_click=save_edit, args=("meta",), type="primary")

        with action_right:
            st.button("Отмена", key="cancel_meta", on_click=cancel_edit, args=("meta",), type="secondary")

        return

    data = st.session_state["meta_data"]
    report_number = data.get("report_number", "")
    date_str = parse_iso_date(data.get("report_date")).strftime("%d.%m.%Y")
    badge_html = status_badge_html(data.get("status_value", "финальный"))

    st.markdown(
        f"""
        <div class="meta-block-card">
            <div class="meta-block-grid">
                <div class="meta-block-item"><b>Номер отчета:</b> {esc(report_number) if str(report_number).strip() else "—"}</div>
                <div class="meta-block-item"><b>Дата формирования:</b> {esc(date_str)}</div>
                <div class="meta-block-item"><b>Статус:</b> {badge_html}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )