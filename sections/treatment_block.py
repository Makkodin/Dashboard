from __future__ import annotations

from datetime import date

import streamlit as st

from core.io_utils import esc, parse_iso_date
from core.state import cancel_edit, save_edit, start_edit
from core.timeline import (
    TIMELINE_ICON_OPTIONS,
    add_empty_treatment_item,
    get_timeline_item_classes,
)
from core.timeline_icons import icon_svg, resolve_timeline_icon, svg_to_data_uri

REGULAR_NODE_FR = 2.3
REPORT_NODE_FR = 1.0

ICON_DISPLAY = {
    "surgery": "✂️ Хирургия",
    "progression": "⚠️ Прогрессирование",
    "immunotherapy": "🛡️ Иммунотерапия",
    "treatment": "✚ Лечение",
}


def _timeline_palette(cls: str) -> tuple[str, str, str]:
    if cls == "tl-surgery-old":
        return "#94A3B8", "#CBD5E1", "#64748B"
    if cls == "tl-progression":
        return "#DC2626", "#FCA5A5", "#991B1B"
    if cls == "tl-latest":
        return "#16A34A", "#86EFAC", "#166534"
    return "#2563EB", "#BFDBFE", "#1D4ED8"


def _render_html(html: str) -> None:
    st.markdown(html.strip(), unsafe_allow_html=True)


def _report_date_text() -> str:
    meta_data = st.session_state.get("meta_data", {})
    raw_date = meta_data.get("report_date")
    if raw_date:
        try:
            return parse_iso_date(raw_date).strftime("%d.%m.%Y")
        except Exception:
            pass
    return date.today().strftime("%d.%m.%Y")


def _timeline_layout_vars(item_count: int) -> str:
    total_fr = item_count * REGULAR_NODE_FR + REPORT_NODE_FR
    start_pct = (REGULAR_NODE_FR / 2) / total_fr * 100
    end_pct = ((item_count * REGULAR_NODE_FR) + REPORT_NODE_FR / 2) / total_fr * 100
    columns = " ".join([f"{REGULAR_NODE_FR}fr"] * item_count + [f"{REPORT_NODE_FR}fr"])
    return f"--timeline-line-start:{start_pct:.4f}%; --timeline-line-end:{end_pct:.4f}%; grid-template-columns:{columns};"


def _render_timeline_preview(items: list[dict[str, str]]) -> None:
    if not items:
        _render_html('<div class="treatment-block-empty-card"><div class="treatment-block-empty">Нет данных для отображения</div></div>')
        return

    classes = get_timeline_item_classes(items)
    node_html_parts: list[str] = []

    for item, cls in zip(items, classes):
        line_color, badge_bg, badge_text = _timeline_palette(cls)
        icon_type = item.get("icon") or resolve_timeline_icon(item.get("stage", ""))
        icon_bg = item.get("icon_bg") or badge_bg
        icon_uri = svg_to_data_uri(icon_svg(icon_type, line_color))
        node_html_parts.append(
            "".join(
                [
                    '<div class="treatment-node">',
                    '<div class="treatment-node-inner">',
                    f'<div class="treatment-date-pill" style="color:{badge_text}; background:{badge_bg};">{esc(item.get("date", ""))}</div>',
                    f'<div class="treatment-node-icon-wrap" style="background:{esc(icon_bg)};"><img class="treatment-node-icon" src="{icon_uri}" alt="timeline icon" /></div>',
                    '<div class="treatment-node-content">',
                    f'<div class="treatment-stage">{esc(item.get("stage", ""))}</div>',
                    f'<div class="treatment-desc">{esc(item.get("desc", ""))}</div>',
                    "</div></div></div>",
                ]
            )
        )

    report_date = _report_date_text()
    node_html_parts.append(
        "".join(
            [
                '<div class="treatment-node treatment-node--report">',
                '<div class="treatment-node-inner treatment-node-inner--report">',
                '<div class="treatment-report-anchor">',
                f'<div class="treatment-report-pill">Формирование отчета<br>{esc(report_date)}</div>',
                "</div></div></div>",
            ]
        )
    )

    layout_vars = _timeline_layout_vars(len(items))
    _render_html(
        "".join(
            [
                '<div class="treatment-timeline-shell">',
                f'<div class="treatment-timeline-track" style="{layout_vars}">',
                "".join(node_html_parts),
                "</div></div>",
            ]
        )
    )


def _add_treatment_item() -> None:
    st.session_state["treatment_draft"] = add_empty_treatment_item(st.session_state.get("treatment_draft", []))


def _remove_treatment_item(idx: int) -> None:
    items = list(st.session_state.get("treatment_draft", []))
    if 0 <= idx < len(items):
        items.pop(idx)
    st.session_state["treatment_draft"] = items


def _render_stage_editor(idx: int, item: dict[str, str], icon_keys: list[str]) -> dict[str, str]:
    item_id = str(item.get("id", "")).strip() or f"stage_{idx}"
    with st.container(border=True):
        _render_html('<div class="treatment-edit-card">')

        head_left, head_right = st.columns([12, 1], gap="small")
        with head_left:
            st.markdown(f'<div class="treatment-edit-stage-label">Этап {idx + 1}</div>', unsafe_allow_html=True)
        with head_right:
            st.button(
                "✕",
                key=f"remove_treatment_{item_id}",
                on_click=_remove_treatment_item,
                args=(idx,),
                type="secondary",
                help="Удалить этап",
                use_container_width=True,
            )

        row1_left, row1_mid, row1_right = st.columns([1.45, 0.85, 0.70], gap="small")
        with row1_left:
            stage = st.text_input(
                "Название этапа",
                value=item.get("stage", ""),
                key=f"treat_stage_{item_id}",
            )

        current_icon = item.get("icon", "treatment")
        with row1_mid:
            icon = st.selectbox(
                "Значок",
                options=icon_keys,
                index=icon_keys.index(current_icon) if current_icon in icon_keys else 0,
                format_func=lambda x: ICON_DISPLAY.get(x, x),
                key=f"treat_icon_{item_id}",
            )

        with row1_right:
            icon_bg = st.color_picker(
                "Фон",
                value=item.get("icon_bg") or "#BFDBFE",
                key=f"treat_icon_bg_{item_id}",
            )

        row2_left, row2_right = st.columns([0.95, 1.55], gap="small")
        with row2_left:
            date_value = st.text_input(
                "Дата",
                value=item.get("date", ""),
                key=f"treat_date_{item_id}",
                placeholder="например, Май 2025",
            )
        with row2_right:
            desc = st.text_area(
                "Описание",
                value=item.get("desc", ""),
                key=f"treat_desc_{item_id}",
                height=92,
            )

        _render_html('</div>')

    return {
        "id": item_id,
        "stage": stage,
        "date": date_value,
        "desc": desc,
        "icon": icon,
        "icon_bg": icon_bg,
    }


def _render_edit_form() -> None:
    items = list(st.session_state.get("treatment_draft", []))
    if not items:
        items = add_empty_treatment_item([])
        st.session_state["treatment_draft"] = items

    icon_keys = [key for key, _ in TIMELINE_ICON_OPTIONS]
    updated_items: list[dict[str, str]] = []

    _render_html('<div class="treatment-edit-grid">')
    for start in range(0, len(items), 2):
        cols = st.columns(2, gap="medium")
        for offset in range(2):
            idx = start + offset
            if idx >= len(items):
                continue
            with cols[offset]:
                updated_items.append(_render_stage_editor(idx, items[idx], icon_keys))
    _render_html('</div>')

    st.session_state["treatment_draft"] = updated_items

    action_left, action_fill, action_right = st.columns([2.2, 5.6, 2.2], gap="small")
    with action_left:
        st.button(
            "+ Добавить этап",
            key="add_treatment_item",
            on_click=_add_treatment_item,
            type="secondary",
        )
    with action_right:
        save_col, cancel_col = st.columns([1, 1], gap="small")
        with save_col:
            st.button(
                "Сохранить",
                key="save_treatment",
                on_click=save_edit,
                args=("treatment",),
                type="primary",
                use_container_width=True,
            )
        with cancel_col:
            st.button(
                "Отмена",
                key="cancel_treatment",
                on_click=cancel_edit,
                args=("treatment",),
                type="secondary",
                use_container_width=True,
            )


def render_treatment_block() -> None:
    title_col, action_col = st.columns([20, 1], gap="small")
    with title_col:
        _render_html('<div class="treatment-block-title-row"><div class="treatment-block-title-text">💊 История лечения</div></div>')
    with action_col:
        st.button(
            "✎",
            key="edit_btn_treatment",
            help="Редактировать блок",
            on_click=start_edit,
            args=("treatment",),
            type="secondary",
        )

    items = st.session_state.get(
        "treatment_draft" if st.session_state.get("edit_treatment", False) else "treatment_data",
        [],
    )
    _render_timeline_preview(items)

    if st.session_state.get("edit_treatment", False):
        _render_edit_form()
