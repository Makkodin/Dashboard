from __future__ import annotations

import streamlit as st

from core.io_utils import esc, load_timeline
from core.paths import timeline_path
from core.timeline import build_timeline_items, get_timeline_item_classes
from core.timeline_icons import icon_svg, resolve_timeline_icon, svg_to_data_uri


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
                    f'<div class="treatment-node-icon-wrap" style="--node-line:{line_color}; --node-badge-bg:{badge_bg};">',
                    f'<img class="treatment-node-icon" src="{icon_uri}" alt="timeline icon" />',
                    "</div>",
                    '<div class="treatment-node-content">',
                    f'<div class="treatment-stage">{esc(item["stage"])}</div>',
                    f'<div class="treatment-desc">{esc(item["desc"])}</div>',
                    f'<div class="treatment-date-pill" style="color:{badge_text}; background:{badge_bg};">{esc(item["date"])}</div>',
                    "</div>",
                    "</div>",
                ]
            )
        )

    _render_html(
        "".join(
            [
                '<div class="treatment-timeline-shell">',
                '<div class="treatment-timeline-track">',
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
