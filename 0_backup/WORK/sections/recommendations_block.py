from __future__ import annotations

from html import escape as esc

import streamlit as st

from core.recommendations import load_recommendations


ICON_BY_TONE = {
    "orange": "↗",
    "green": "🛡",
    "blue": "✦",
    "red": "⚠",
    "gray": "•",
}


def _render_html(html: str) -> None:
    st.markdown(html.strip(), unsafe_allow_html=True)


def render_recommendations_block():
    sample = st.session_state.get("selected_sample", "")
    if not sample:
        st.warning("Не выбран SAMPLE.")
        return

    data = load_recommendations(sample)
    cards = data.get("cards") or []

    _render_html(
        """
        <div class="section-common-title-frame">
            <div class="section-common-title-text">Рекомендации</div>
        </div>
        """
    )

    html_parts = [
        '<div class="recommendations-shell">',
        f'<div class="recommendations-heading">{esc(str(data.get("section_title", "Результаты биоинформатического анализа")))}</div>',
        f'<div class="recommendations-subheading">{esc(str(data.get("section_subtitle", "Интегративная интерпретация молекулярного профиля пациента")))}</div>',
    ]

    for card in cards:
        style = card.get("style", {})
        tone = str(card.get("tone", "gray"))
        icon = ICON_BY_TONE.get(tone, "•")
        html_parts.extend(
            [
                f'<div class="recommendation-card recommendation-card--{esc(tone)}" style="--rec-accent:{esc(style.get("accent", "#94A3B8"))}; --rec-soft:{esc(style.get("soft", "#F8FAFC"))}; --rec-tag-bg:{esc(style.get("tag_bg", "#E2E8F0"))}; --rec-tag-fg:{esc(style.get("tag_fg", "#475569"))};">',
                '<div class="recommendation-card-index-col">',
                f'<div class="recommendation-card-icon">{esc(icon)}</div>',
                f'<div class="recommendation-card-index">{esc(str(card.get("index", "01")))}</div>',
                '</div>',
                '<div class="recommendation-card-content">',
                f'<div class="recommendation-card-topline"><span class="recommendation-card-tag">{esc(str(card.get("tag", "РЕКОМЕНДАЦИЯ")))}</span><span class="recommendation-card-title">{esc(str(card.get("title", "")))}</span></div>',
                f'<div class="recommendation-card-body">{esc(str(card.get("body", "")))}</div>',
                '</div>',
                '</div>',
            ]
        )

    html_parts.append('</div>')
    _render_html("".join(html_parts))
