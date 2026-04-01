from __future__ import annotations

import streamlit as st

from core.immune_signatures import TONE_DEFAULTS, load_immune_signatures
from core.io_utils import esc


def _render_html(html: str) -> None:
    st.markdown(html.strip(), unsafe_allow_html=True)


def _mix_channel(a: int, b: int, t: float) -> int:
    return round(a + (b - a) * t)


def _score_to_fill(value: float) -> str:
    ratio = min(abs(value) / 5.0, 1.0)

    if value > 0.15:
        pale = (248, 200, 206)
        strong = (239, 68, 68)
    elif value < -0.15:
        pale = (191, 219, 254)
        strong = (29, 78, 216)
    else:
        pale = (229, 231, 235)
        strong = (209, 213, 219)

    rgb = tuple(_mix_channel(pale[i], strong[i], ratio) for i in range(3))
    return f"rgb({rgb[0]}, {rgb[1]}, {rgb[2]})"


def _summary_html(summary_text: str, summary_icon: str, summary_tone: str) -> str:
    tone = TONE_DEFAULTS.get(summary_tone, TONE_DEFAULTS["neutral"])
    icon = esc(summary_icon or tone["icon"])
    return "".join(
        [
            f'<div class="immune-sign-summary immune-sign-summary--{esc(summary_tone)}" style="color:{tone["text"]};">',
            f'<span class="immune-sign-summary-icon">{icon}</span>',
            f'<span class="immune-sign-summary-text">{esc(summary_text)}</span>',
            '</div>',
        ]
    )


def _items_html(items: list[dict]) -> str:
    rows: list[str] = []
    for item in items:
        value = float(item["value"])
        rows.append(
            "".join(
                [
                    '<div class="immune-sign-row">',
                    f'<div class="immune-sign-row-label">{esc(item["label"])}</div>',
                    '<div class="immune-sign-row-bar">',
                    f'<div class="immune-sign-row-bar-fill" style="background:{_score_to_fill(value)};"></div>',
                    '</div>',
                    f'<div class="immune-sign-row-value">{value:.2f}</div>',
                    '</div>',
                ]
            )
        )
    return ''.join(rows)


def _card_html(group: dict) -> str:
    return "".join(
        [
            '<div class="immune-sign-card">',
            f'<div class="immune-sign-card-title">{esc(group["title"])}</div>',
            f'<div class="immune-sign-card-desc">{esc(group["description"])}</div>',
            _summary_html(group.get("summary_text", ""), group.get("summary_icon", "•"), group.get("summary_tone", "neutral")),
            '<div class="immune-sign-rows">',
            _items_html(group.get("items", [])),
            '</div>',
            '</div>',
        ]
    )


def render_immune_signatures_block():
    sample = st.session_state.get("selected_sample", "")
    if not sample:
        st.warning("Не выбран SAMPLE.")
        return

    data = load_immune_signatures(sample)
    groups = data["groups"]

    top_left = next((g for g in groups if g["key"] == "lymphocyte_response"), groups[0])
    top_right = next((g for g in groups if g["key"] == "fibrosis"), None)
    mid_left = next((g for g in groups if g["key"] == "myeloid_inflammation"), None)
    mid_right = next((g for g in groups if g["key"] == "immunosuppression"), None)
    bottom_left = next((g for g in groups if g["key"] == "proliferation_invasion"), None)

    html = ''.join(
        [
            '<div class="section-common-title-frame">',
            '<div class="section-common-title-text">Иммунные сигнатуры</div>',
            '</div>',
            '<div class="immune-sign-grid">',
            f'<div class="immune-sign-grid-item">{_card_html(top_left)}</div>',
            f'<div class="immune-sign-grid-item">{_card_html(top_right)}</div>' if top_right else '<div></div>',
            f'<div class="immune-sign-grid-item">{_card_html(mid_left)}</div>' if mid_left else '<div></div>',
            f'<div class="immune-sign-grid-item">{_card_html(mid_right)}</div>' if mid_right else '<div></div>',
            f'<div class="immune-sign-grid-item immune-sign-grid-item--narrow">{_card_html(bottom_left)}</div>' if bottom_left else '<div></div>',
            '<div class="immune-sign-grid-spacer"></div>',
            '<div class="immune-sign-legend">',
            '<div class="immune-sign-legend-title">Оценка обогащения</div>',
            '<div class="immune-sign-legend-scale">',
            f'<span class="immune-sign-legend-label immune-sign-legend-label--left">{data["legend_min"]:.0f}</span>',
            '<span class="immune-sign-legend-label immune-sign-legend-label--center">0</span>',
            f'<span class="immune-sign-legend-label immune-sign-legend-label--right">{data["legend_max"]:.0f}</span>',
            '</div>',
            '</div>',
            '</div>',
        ]
    )

    _render_html(html)
