from __future__ import annotations

import streamlit as st

from core.immune_markers import load_immune_markers
from core.io_utils import esc


GENE_INTERPRETATION_TOOLTIP = (
    "Показатель сравнивает экспрессию гена в образце с референсной меланомной когортой TCGA. "
    "Процентиль показывает относительное положение образца в распределении, а уровень "
    "«низкий / средний / высокий» — упрощённую категорию этого положения."
)


# Это функция для блока «отрисовки html». Она нужна для того, чтобы вынести отдельный шаг логики в самостоятельную и читаемую часть кода.
# Используется в следующих блоках: sections/genetic_profile_block.py, sections/immune_markers_block.py, sections/immune_signatures_block.py.
# На вход: html.
# На выход: None.
def _render_html(html: str) -> None:
    st.markdown(html.strip(), unsafe_allow_html=True)


# Это функция для блока «тултипа html». Она нужна для того, чтобы вынести отдельный шаг логики в самостоятельную и читаемую часть кода.
# Используется в следующих блоках: sections/immune_markers_block.py, sections/immune_signatures_block.py.
# На вход: label, text.
# На выход: str.
def _tooltip_html(label: str, text: str) -> str:
    safe_label = esc(label)
    safe_text = esc(text)
    return "".join([
        '<div class="immune-marker-tooltip">',
        safe_label,
        f'<span class="immune-marker-tooltip-text">{safe_text}</span>',
        '</div>',
    ])


# Это функция для блока «card html». Она нужна для того, чтобы вынести отдельный шаг логики в самостоятельную и читаемую часть кода.
# Используется в следующих блоках: sections/immune_markers_block.py, sections/immune_signatures_block.py.
# На вход: card.
# На выход: str.
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


# Это функция для блока «grid class for count». Она нужна для того, чтобы вынести отдельный шаг логики в самостоятельную и читаемую часть кода.
# Используется в следующих блоках: sections/immune_markers_block.py.
# На вход: card_count.
# На выход: str.
def _grid_class_for_count(card_count: int) -> str:
    if card_count <= 3:
        return 'immune-marker-panel-grid immune-marker-panel-grid--3'
    return 'immune-marker-panel-grid immune-marker-panel-grid--4'


# Это функция для блока «grid row html». Она нужна для того, чтобы вынести отдельный шаг логики в самостоятельную и читаемую часть кода.
# Используется в следующих блоках: sections/immune_markers_block.py, sections/immune_signatures_block.py.
# На вход: cards, extra_class.
# На выход: str.
def _grid_row_html(cards: list[dict], extra_class: str = "") -> str:
    classes = _grid_class_for_count(len(cards))
    if extra_class:
        classes += f" {extra_class}"
    return f'<div class="{classes}">{"".join(_card_html(card) for card in cards)}</div>'


# Это функция для блока «panel html». Она нужна для того, чтобы вынести отдельный шаг логики в самостоятельную и читаемую часть кода.
# Используется в следующих блоках: sections/immune_markers_block.py.
# На вход: panel.
# На выход: str.
def _panel_html(panel: dict) -> str:
    cards = list(panel.get('cards', []))
    panel_tooltip = " ".join(
        part
        for part in [
            str(panel.get("subtitle", "")).strip(),
            str(panel.get("note", "")).strip(),
        ]
        if part
    )

    html_parts = [
        '<div class="immune-marker-panel">',
        f'<div class="immune-marker-panel-title">{esc(panel.get("title", ""))}</div>',
        f'<div class="immune-marker-panel-subtitle">{esc(panel.get("subtitle", ""))}</div>',
        '<div class="immune-marker-panel-info-row">',
        _tooltip_html("ℹ Как интерпретировать показатель", panel_tooltip),
        '</div>',
    ]

    if len(cards) == 5:
        html_parts.append(_grid_row_html(cards[:3], "immune-marker-panel-grid-row immune-marker-panel-grid-row--top"))
        html_parts.append(_grid_row_html(cards[3:], "immune-marker-panel-grid-row immune-marker-panel-grid-row--bottom"))
    else:
        html_parts.append(
            f'<div class="{_grid_class_for_count(len(cards))}">'
            f'{"".join(_card_html(card) for card in cards)}'
            '</div>'
        )

    html_parts.append(f'<div class="immune-marker-panel-note">{esc(panel.get("note", ""))}</div>')
    html_parts.append('</div>')
    return ''.join(html_parts)


# Это функция для отрисовки блока «иммунного профиля иммунных маркеров block» в интерфейсе дашборда.
# Используется в следующих блоках: app.py.
# На вход: функция не ожидает обязательных входных параметров.
# На выход: результат дальнейшего шага обработки.
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
        ''.join(_panel_html(panel) for panel in panels),
    ])

    _render_html(html)
