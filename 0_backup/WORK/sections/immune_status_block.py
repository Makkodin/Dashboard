from __future__ import annotations

import streamlit as st

from core.immune_status import load_immune_status
from core.io_utils import esc


SUBTYPE_CLASS_STYLES = {
    "IE": ("Иммуно-богатая", "#DCFCE7", "#166534"),
    "IM": ("Смешанная иммунная", "#DBEAFE", "#1D4ED8"),
    "ID": ("Иммуно-дефицитная", "#F3E8FF", "#7E22CE"),
}


def _render_html(html: str) -> None:
    st.markdown(html.strip(), unsafe_allow_html=True)


def _purity_tone(purity_percent: float) -> tuple[str, str]:
    if purity_percent >= 60:
        return "#FCE7F3", "#9D174D"
    if purity_percent >= 35:
        return "#EDE9FE", "#6D28D9"
    return "#F3E8FF", "#7E22CE"


def _stack_bar_html(composition: list[dict]) -> str:
    segments: list[str] = []
    for item in reversed(composition):
        segments.append(
            f'<div class="immune-status-stack-segment" style="height:{item["value"]:.2f}%; background:{esc(item["color"])};" title="{esc(item["label"])} — {item["value"]:.1f}%"></div>'
        )
    return "".join(segments)


def _composition_rows_html(composition: list[dict]) -> str:
    rows: list[str] = []
    for item in composition:
        rows.append(
            "".join(
                [
                    '<div class="immune-status-row">',
                    '<div class="immune-status-row-label-wrap">',
                    f'<span class="immune-status-row-dot" style="background:{esc(item["color"])};"></span>',
                    f'<span class="immune-status-row-label">{esc(item["label"])} </span>',
                    '</div>',
                    '<div class="immune-status-row-bar-track">',
                    f'<div class="immune-status-row-bar-fill" style="width:{item["value"]:.1f}%; background:{esc(item["color"])};"></div>',
                    '</div>',
                    f'<div class="immune-status-row-value">{item["value"]:.1f}%</div>',
                    '</div>',
                ]
            )
        )
    return "".join(rows)


def render_immune_status_block():
    sample = st.session_state.get("selected_sample", "")
    if not sample:
        st.warning("Не выбран SAMPLE.")
        return

    data = load_immune_status(sample)

    purity_percent = float(data["purity_percent"])
    purity_bg, purity_fg = _purity_tone(purity_percent)

    subtype_code = str(data.get("tumor_subtype_class", "IE")).upper()
    subtype_title, subtype_bg, subtype_fg = SUBTYPE_CLASS_STYLES.get(
        subtype_code,
        ("Иммуно-богатая", "#DCFCE7", "#166534"),
    )

    subtype_text = data.get("tumor_subtype_title") or subtype_title
    subtype_description = data.get("tumor_subtype_description") or ""
    total_immune = float(data["total_immune_percent"])
    cd8_treg_ratio = float(data["cd8_treg_ratio"])
    effector_t_cells = float(data["effector_t_cells_percent"])
    composition = data["composition"]
    interpretation_text = data.get("interpretation_text", "")

    purity_fill = max(0.0, min(100.0, purity_percent))

    html = "".join(
        [
            '<div class="section-common-title-frame">',
            '<div class="section-common-title-text">Иммунный статус</div>',
            '</div>',
            '<div class="immune-status-grid">',
            '<div class="immune-status-left-col">',
            '<div class="immune-status-card immune-status-card--compact">',
            '<div class="immune-status-card-title">Чистота опухоли (Tumor Purity)</div>',
            '<div class="immune-status-card-caption">Чистота опухоли — это доля опухолевых клеток в образце ткани</div>',
            '<div class="immune-status-purity-panel">',
            f'<div class="immune-status-purity-badge" style="background:{purity_bg}; color:{purity_fg};">{purity_percent:.1f}%</div>',
            '<div class="immune-status-purity-meta">',
            '<div class="immune-status-purity-label">Доля опухолевых клеток</div>',
            '<div class="immune-status-purity-bar-track">',
            f'<div class="immune-status-purity-bar-fill" style="width:{purity_fill:.1f}%; background:{purity_fg};"></div>',
            '</div>',
            '</div>',
            '</div>',
            '</div>',
            '<div class="immune-status-card immune-status-card--subtype">',
            '<div class="immune-status-card-title">Подтип опухоли</div>',
            f'<div class="immune-status-subtype-badge" style="background:{subtype_bg}; color:{subtype_fg};">{esc(subtype_text)} (класс {esc(subtype_code)})</div>',
            f'<div class="immune-status-subtype-text">{esc(subtype_description)}</div>',
            '</div>',
            '</div>',
            '<div class="immune-status-right-col-wrap">',
            '<div class="immune-status-card immune-status-card--deconv">',
            '<div class="immune-status-card-head">',
            '<div class="immune-status-card-title">Деконволюция клеточного состава</div>',
            '</div>',
            '<div class="immune-status-deconv-layout">',
            '<div class="immune-status-stack-col">',
            '<div class="immune-status-stack-wrap">',
            f'{_stack_bar_html(composition)}',
            '</div>',
            '</div>',
            '<div class="immune-status-right-col">',
            '<div class="immune-status-metrics-row">',
            '<div class="immune-status-metric-card immune-status-metric-card--blue">',
            '<div class="immune-status-metric-label">Всего иммунных клеток</div>',
            f'<div class="immune-status-metric-value">{total_immune:.1f}%</div>',
            '</div>',
            '<div class="immune-status-metric-card immune-status-metric-card--green">',
            '<div class="immune-status-metric-label">CD8⁺/Treg</div>',
            f'<div class="immune-status-metric-value">{cd8_treg_ratio:.2f}</div>',
            '</div>',
            '<div class="immune-status-metric-card immune-status-metric-card--violet">',
            '<div class="immune-status-metric-label">Эффект. T-клетки</div>',
            f'<div class="immune-status-metric-value">{effector_t_cells:.1f}%</div>',
            '</div>',
            '</div>',
            '<div class="immune-status-rows">',
            f'{_composition_rows_html(composition)}',
            '</div>',
            '</div>',
            '</div>',
            '</div>',
            '<div class="immune-status-card immune-status-card--interpretation">',
            '<div class="immune-status-card-title">Интерпретация</div>',
            f'<div class="immune-status-interpretation-text">{esc(interpretation_text)}</div>',
            '</div>',
            '</div>',
        ]
    )

    _render_html(html)
