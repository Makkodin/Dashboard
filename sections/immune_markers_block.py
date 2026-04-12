from __future__ import annotations

import streamlit as st

from core.immune_markers import load_immune_markers
from core.io_utils import esc


GENE_INTERPRETATION_TOOLTIP = (
    "Показатель сравнивает экспрессию гена в образце с референсной меланомной когортой TCGA. "
    "Процентиль показывает относительное положение образца в распределении, а уровень "
    "«низкий / средний / высокий» — упрощённую категорию этого положения."
)


def _render_html(html: str) -> None:
    st.markdown(html.strip(), unsafe_allow_html=True)


def _tooltip_html(label: str, text: str) -> str:
    safe_label = esc(label)
    safe_text = esc(text)
    return "".join([
        '<div class="immune-marker-tooltip">',
        safe_label,
        f'<span class="immune-marker-tooltip-text">{safe_text}</span>',
        '</div>',
    ])


def _card_html(card: dict) -> str:
    tooltip_text = " ".join(
        part
        for part in [
            str(card.get("description", "")).strip(),
            GENE_INTERPRETATION_TOOLTIP,
            f"Текущий процентиль: {int(card['percentile'])}%.",
        ]
        if part
    )
    return ''.join([
        '<div class="immune-marker-card">',
        f'<div class="immune-marker-gene">{esc(card["gene"])}</div>',
        f'<div class="immune-marker-desc">{esc(card["description"])}</div>',
        f'<div class="immune-marker-chart-wrap"><img class="immune-marker-chart" src="{card["svg_uri"]}" alt="{esc(card["gene"])} chart" /></div>',
        '<div class="immune-marker-meta">',
        '<div class="immune-marker-meta-row">',
        '<div class="immune-marker-meta-label">Уровень:</div>',
        f'<div class="immune-marker-badge immune-marker-badge--{esc(str(card["level"]).lower())}" style="color:{esc(card["level_color"])}; border-color:{esc(card["level_color"])}33; background:{esc(card["level_color"])}14;">{esc(str(card.get("level_label", card["level"])))}</div>',
        '</div>',
        '<div class="immune-marker-meta-row">',
        '<div class="immune-marker-meta-label">Процентиль:</div>',
        f'<div class="immune-marker-meta-value">{int(card["percentile"])}%</div>',
        '</div>',
        '<div class="immune-marker-card-info-row">',
        _tooltip_html("ℹ Как интерпретировать показатель", tooltip_text),
        '</div>',
        '</div>',
        '</div>',
    ])


def _panel_columns_class(card_count: int) -> str:
    if card_count <= 3:
        return 'immune-marker-panel-grid immune-marker-panel-grid--3'
    if card_count == 4:
        return 'immune-marker-panel-grid immune-marker-panel-grid--4'
    return 'immune-marker-panel-grid immune-marker-panel-grid--5'


def _grid_row_html(cards: list[dict], extra_class: str = "") -> str:
    classes = _panel_columns_class(len(cards))
    if extra_class:
        classes += f" {extra_class}"
    return f'<div class="{classes}">{"".join(_card_html(card) for card in cards)}</div>'


def _panel_html(panel: dict, panel_index: int) -> str:
    cards = list(panel.get('cards', []))
    panel_tooltip = " ".join(
        part
        for part in [
            str(panel.get("subtitle", "")).strip(),
            str(panel.get("note", "")).strip(),
        ]
        if part
    )

    top_cards = cards[:4]
    bottom_cards = cards[4:]

    html_parts = [
        f'<div class="immune-marker-panel immune-marker-panel--{panel_index + 1}">',
        f'<div class="immune-marker-panel-title">{esc(panel.get("title", ""))}</div>',
        f'<div class="immune-marker-panel-subtitle">{esc(panel.get("subtitle", ""))}</div>',
        '<div class="immune-marker-panel-info-row">',
        _tooltip_html("ℹ Как интерпретировать показатель", panel_tooltip),
        '</div>',
    ]

    if top_cards:
        html_parts.append(_grid_row_html(top_cards, "immune-marker-panel-grid-row immune-marker-panel-grid-row--top"))

    html_parts.extend([
        '<div class="immune-marker-panel-footer">',
    ])

    if bottom_cards:
        html_parts.append(_grid_row_html(bottom_cards, "immune-marker-panel-grid-row immune-marker-panel-grid-row--bottom"))

    html_parts.append(f'<div class="immune-marker-panel-note">{esc(panel.get("note", ""))}</div>')
    html_parts.append('</div>')
    html_parts.append('</div>')
    return ''.join(html_parts)


def render_immune_markers_block():
    sample = st.session_state.get('selected_sample', '')
    if not sample:
        st.warning('Не выбран SAMPLE.')
        return

    data = load_immune_markers(sample)
    panels = data.get('panels', [])

    html = ''.join([
        '<div class="immune-markers-section">',
        '<div class="section-common-title-frame">',
        '<div class="section-common-title-text">Иммунные маркеры</div>',
        '</div>',
        f'<div class="immune-marker-section-subtitle">{esc(data.get("section_subtitle", ""))}</div>',
        ''.join(_panel_html(panel, idx) for idx, panel in enumerate(panels)),
        '</div>',
    ])

    _render_html(html)
