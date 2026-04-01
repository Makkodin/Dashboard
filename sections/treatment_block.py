from __future__ import annotations

from datetime import date

import streamlit as st

from core.io_utils import esc, load_timeline, parse_iso_date
from core.paths import timeline_path
from core.timeline import build_timeline_items, get_timeline_item_classes
from core.timeline_icons import icon_svg, resolve_timeline_icon, svg_to_data_uri


REGULAR_NODE_FR = 2.3
REPORT_NODE_FR = 1.0


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
    end_pct = 100 - ((REPORT_NODE_FR / 2) / total_fr * 100)
    columns = " ".join([f"{REGULAR_NODE_FR}fr"] * item_count + [f"{REPORT_NODE_FR}fr"])
    return f"--timeline-line-start:{start_pct:.4f}%; --timeline-line-end:{end_pct:.4f}%; grid-template-columns:{columns};"


def render_timeline_horizontal(sample: str):
    data = load_timeline(timeline_path(sample))
    items = build_timeline_items(data)

    if not items:
        _render_html(
            """
            <div class="treatment-block-empty-card">
                <div class="treatment-block-empty">Нет данных для отображения</div>
            </div>
            """
        )
        return

    classes = get_timeline_item_classes(items)
    node_html_parts: list[str] = []

    for item, cls in zip(items, classes):
        line_color, badge_bg, badge_text = _timeline_palette(cls)
        icon_type = resolve_timeline_icon(item["stage"])
        icon_uri = svg_to_data_uri(icon_svg(icon_type, line_color))

        node_html_parts.append(
            "".join(
                [
                    '<div class="treatment-node">',
                    '<div class="treatment-node-inner">',
                    f'<div class="treatment-date-pill" style="color:{badge_text}; background:{badge_bg};">{esc(item["date"])}</div>',
                    f'<div class="treatment-node-icon-wrap" style="--node-badge-bg:{badge_bg};">',
                    f'<img class="treatment-node-icon" src="{icon_uri}" alt="timeline icon" />',
                    "</div>",
                    '<div class="treatment-node-content">',
                    f'<div class="treatment-stage">{esc(item["stage"])}</div>',
                    f'<div class="treatment-desc">{esc(item["desc"])}</div>',
                    "</div>",
                    "</div>",
                    "</div>",
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
                "</div>",
                "</div>",
                "</div>",
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
                "</div>",
                "</div>",
            ]
        )
    )



def render_treatment_block():
    left, right = st.columns([20, 1], gap="small")

    with left:
        _render_html(
            """
            <div class="treatment-block-title-row">
                <div class="treatment-block-title-text">💊 История лечения</div>
            </div>
            """
        )

    with right:
        st.markdown("&nbsp;", unsafe_allow_html=True)

    sample = st.session_state.get("selected_sample", "")
    if sample:
        render_timeline_horizontal(sample)
    else:
        st.warning("Не выбран SAMPLE.")
