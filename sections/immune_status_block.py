from __future__ import annotations

import streamlit as st

from core.immune_status import load_immune_status
from core.io_utils import esc


SUBTYPE_CLASS_STYLES = {
    "IE": ("#DCFCE7", "#166534"),
    "IE/F": ("#ECFCCB", "#3F6212"),
    "IM": ("#DBEAFE", "#1D4ED8"),
    "D": ("#F3E8FF", "#7E22CE"),
    "ID": ("#F3E8FF", "#7E22CE"),
}

PURITY_TOOLTIP = (
    "Показывает долю опухолевых клеток в исследуемом образце. "
    "Чем показатель выше, тем меньше примесь стромальных и иммунных клеток."
)
SUBTYPE_TOOLTIP = (
    "Подтип описывает характер микроокружения опухоли: выраженность иммунной инфильтрации, стромы и связанных процессов. "
    "Он помогает интерпретировать вероятность ответа на терапию."
)
DECONV_TOOLTIP = (
    "Деконволюция оценивает относительный вклад разных популяций клеток в образце по транскриптомным данным. "
    "Проценты показывают структуру микроокружения опухоли."
)
TOTAL_IMMUNE_TOOLTIP = (
    "Суммарная доля иммунных клеток в образце. Более высокий показатель обычно отражает более выраженную иммунную инфильтрацию."
)
CD8_TREG_TOOLTIP = (
    "Соотношение эффекторных CD8+ T-клеток к регуляторным T-клеткам. Более высокое значение обычно соответствует менее подавленному иммунному ответу."
)
EFFECTOR_T_TOOLTIP = (
    "Доля CD8 и CD4 T-клеток, связанных с активным противоопухолевым ответом."
)
INTERPRETATION_TOOLTIP = (
    "Краткий сводный вывод по составу клеток и ключевым иммунным метрикам образца."
)


def _render_html(html: str) -> None:
    st.markdown(html.strip(), unsafe_allow_html=True)


def _tooltip_html(label: str, text: str) -> str:
    safe_label = esc(label)
    safe_text = esc(text)
    return "".join([
        '<div class="immune-status-tooltip">',
        safe_label,
        f'<span class="immune-status-tooltip-text">{safe_text}</span>',
        '</div>',
    ])


def _metric_label_html(text: str, tooltip: str) -> str:
    return "".join([
        '<div class="immune-status-metric-label-row">',
        f'<div class="immune-status-metric-label">{esc(text)}</div>',
        _tooltip_html("ℹ", tooltip),
        '</div>',
    ])


def _purity_tone(purity_percent: float) -> tuple[str, str]:
    if purity_percent >= 60:
        return "#FCE7F3", "#9D174D"
    if purity_percent >= 35:
        return "#EDE9FE", "#6D28D9"
    return "#F3E8FF", "#7E22CE"


def _stack_bar_html(composition: list[dict]) -> str:
    return ''.join(
        f'<div class="immune-status-stack-segment" style="height:{item["value"]:.2f}%; background:{esc(item["color"])};" title="{esc(item["label"])} — {item["value"]:.1f}%"></div>'
        for item in reversed(composition)
    )


def _composition_rows_html(composition: list[dict]) -> str:
    rows = []
    for item in composition:
        item_tooltip = (
            f"{item['label']}: {item['value']:.1f}% от клеточного состава образца. "
            "Это относительная доля данной популяции в деконволюции."
        )
        rows.append(''.join([
            '<div class="immune-status-row">',
            '<div class="immune-status-row-label-wrap">',
            f'<span class="immune-status-row-dot" style="background:{esc(item["color"])};"></span>',
            f'<span class="immune-status-row-label">{esc(item["label"])} </span>',
            _tooltip_html("ℹ", item_tooltip),
            '</div>',
            '<div class="immune-status-row-bar-track">',
            f'<div class="immune-status-row-bar-fill" style="width:{item["value"]:.1f}%; background:{esc(item["color"])};"></div>',
            '</div>',
            f'<div class="immune-status-row-value">{item["value"]:.1f}%</div>',
            '</div>',
        ]))
    return ''.join(rows)


def render_immune_status_block() -> None:
    sample = st.session_state.get("selected_sample", "")
    if not sample:
        st.warning("Не выбран SAMPLE.")
        return
    data = load_immune_status(sample)
    purity_percent = float(data["purity_percent"])
    purity_bg, purity_fg = _purity_tone(purity_percent)
    subtype_code = str(data.get("tumor_subtype_class", "")).upper()
    subtype_bg, subtype_fg = SUBTYPE_CLASS_STYLES.get(subtype_code, ("#DCFCE7", "#166534"))
    subtype_text = data.get("tumor_subtype_title") or subtype_code or "—"
    subtype_description = data.get("tumor_subtype_description") or ""
    total_immune = float(data["total_immune_percent"])
    cd8_treg_ratio = float(data["cd8_treg_ratio"])
    effector_t_cells = float(data["effector_t_cells_percent"])
    composition = data["composition"]
    purity_fill = max(0.0, min(100.0, purity_percent))
    interpretation = str(data.get("interpretation", "")).strip()
    html = ''.join([
        '<div class="section-common-title-frame"><div class="section-common-title-text">Иммунный статус</div></div>',
        '<div class="immune-status-grid">',
        '<div class="immune-status-left-col">',
        '<div class="immune-status-card immune-status-card--compact">',
        '<div class="immune-status-card-title">Чистота опухоли (Tumor Purity)</div>',
        '<div class="immune-status-card-caption">Чистота опухоли — это доля опухолевых клеток в образце ткани</div>',
        '<div class="immune-status-card-info-row">',
        _tooltip_html("ℹ Как интерпретировать показатель", PURITY_TOOLTIP),
        '</div>',
        '<div class="immune-status-purity-panel">',
        f'<div class="immune-status-purity-badge" style="background:{purity_bg}; color:{purity_fg};">{purity_percent:.1f}%</div>',
        '<div class="immune-status-purity-meta"><div class="immune-status-purity-label">Доля опухолевых клеток</div><div class="immune-status-purity-bar-track">',
        f'<div class="immune-status-purity-bar-fill" style="width:{purity_fill:.1f}%; background:{purity_fg};"></div>',
        '</div></div></div></div>',
        '<div class="immune-status-card immune-status-card--subtype">',
        '<div class="immune-status-card-title">Подтип опухоли</div>',
        '<div class="immune-status-card-info-row">',
        _tooltip_html("ℹ Как интерпретировать показатель", SUBTYPE_TOOLTIP),
        '</div>',
        f'<div class="immune-status-subtype-badge" style="background:{subtype_bg}; color:{subtype_fg};">{esc(subtype_text)} (класс {esc(subtype_code)})</div>',
        f'<div class="immune-status-subtype-text">{esc(subtype_description)}</div>',
        '</div></div>',
        '<div class="immune-status-card immune-status-card--deconv">',
        '<div class="immune-status-card-head"><div class="immune-status-card-title">Деконволюция клеточного состава</div></div>',
        '<div class="immune-status-card-info-row immune-status-card-info-row--tight">',
        _tooltip_html("ℹ Как интерпретировать показатель", DECONV_TOOLTIP),
        '</div>',
        '<div class="immune-status-deconv-layout"><div class="immune-status-stack-col"><div class="immune-status-stack-wrap">',
        _stack_bar_html(composition),
        '</div></div><div class="immune-status-right-col">',
        '<div class="immune-status-metrics-row">',
        f'<div class="immune-status-metric-card immune-status-metric-card--blue">{_metric_label_html("Всего иммунных клеток", TOTAL_IMMUNE_TOOLTIP)}<div class="immune-status-metric-value">{total_immune:.1f}%</div></div>',
        f'<div class="immune-status-metric-card immune-status-metric-card--green">{_metric_label_html("CD8⁺/Treg", CD8_TREG_TOOLTIP)}<div class="immune-status-metric-value">{cd8_treg_ratio:.2f}</div></div>',
        f'<div class="immune-status-metric-card immune-status-metric-card--violet">{_metric_label_html("Эффект. T-клетки", EFFECTOR_T_TOOLTIP)}<div class="immune-status-metric-value">{effector_t_cells:.1f}%</div></div>',
        '</div><div class="immune-status-rows">',
        _composition_rows_html(composition),
        '</div></div></div>',
        '<div class="immune-status-interpretation-card">',
        '<div class="immune-status-card-title">Интерпретация</div>',
        '<div class="immune-status-card-info-row immune-status-card-info-row--tight">',
        _tooltip_html("ℹ Как интерпретировать показатель", INTERPRETATION_TOOLTIP),
        '</div>',
        f'<div class="immune-status-interpretation-text">{esc(interpretation)}</div>',
        '</div>',
        '</div></div>',
    ])
    _render_html(html)
