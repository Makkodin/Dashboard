from __future__ import annotations

import streamlit as st

from core.immune_markers import load_immune_markers
from core.io_utils import esc


def _render_html(html: str) -> None:
    st.markdown(html.strip(), unsafe_allow_html=True)


def _card_html(card: dict) -> str:
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
        '</div>',
        '</div>',
    ])


def _panel_columns_class(card_count: int) -> str:
    if card_count <= 3:
        return 'immune-marker-panel-grid immune-marker-panel-grid--3'
    if card_count == 4:
        return 'immune-marker-panel-grid immune-marker-panel-grid--4'
    return 'immune-marker-panel-grid immune-marker-panel-grid--5'


def _panel_html(panel: dict) -> str:
    cards = panel.get('cards', [])
    return ''.join([
        '<div class="immune-marker-panel">',
        f'<div class="immune-marker-panel-title">{esc(panel.get("title", ""))}</div>',
        f'<div class="immune-marker-panel-subtitle">{esc(panel.get("subtitle", ""))}</div>',
        f'<div class="{_panel_columns_class(len(cards))}">',
        ''.join(_card_html(card) for card in cards),
        '</div>',
        f'<div class="immune-marker-panel-note">{esc(panel.get("note", ""))}</div>',
        '</div>',
    ])


def render_immune_markers_block():
    sample = st.session_state.get('selected_sample', '')
    if not sample:
        st.warning('Не выбран SAMPLE.')
        return

    data = load_immune_markers(sample)
    panels = data.get('panels', [])

    html = ''.join([
        '<div class="section-common-title-frame">',
        '<div class="section-common-title-text">Иммунные маркеры</div>',
        '</div>',
        f'<div class="immune-marker-section-subtitle">{esc(data.get("section_subtitle", ""))}</div>',
        ''.join(_panel_html(panel) for panel in panels),
    ])

    _render_html(html)
