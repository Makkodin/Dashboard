from __future__ import annotations

import streamlit as st

from core.immune_signatures import TONE_DEFAULTS, load_immune_signatures
from core.io_utils import esc


GENERAL_SIGNATURE_TOOLTIP = (
    "Сигнатуры показаны как нормализованные score относительно референсной меланомной когорты. "
    "Значение около 0 соответствует среднему уровню, положительные значения — большей активности процесса, "
    "отрицательные — меньшей. Чем насыщеннее цвет, тем сильнее отклонение."
)

ITEM_TOOLTIPS = {
    "MHCI": "Сигнатура активности молекул MHC-I, связанных с презентацией антигенов CD8+ T-клеткам.",
    "MHCII": "Сигнатура активности молекул MHC-II, связанных с презентацией антигенов CD4+ T-клеткам и антигенпрезентацией.",
    "Коактивационные молекулы": "Показывает активность коактивационных сигналов, усиливающих запуск и поддержание иммунного ответа.",
    "Эффекторные клетки": "Отражает выраженность популяций, непосредственно вовлечённых в противоопухолевый иммунный ответ.",
    "NK-клетки": "Характеризует активность естественных киллеров, участвующих в врождённом противоопухолевом ответе.",
    "T-клетки": "Показывает общую выраженность T-клеточного компонента иммунного микроокружения.",
    "B-клетки": "Отражает вклад B-лимфоцитов в иммунное микроокружение опухоли.",
    "Th1-сигнатура": "Сигнатура провоспалительного Th1-ответа, обычно связанного с клеточным противоопухолевым иммунитетом.",
    "Th2-сигнатура": "Сигнатура Th2-ответа, связанного с гуморальным иммунитетом и регуляцией воспаления.",
    "CAF": "Сигнатура опухоль-ассоциированных фибробластов, отражающая вклад стромы в микроокружение опухоли.",
    "Матрикс": "Характеризует выраженность компонентов внеклеточного матрикса.",
    "Ремоделирование матрикса": "Показывает активность процессов перестройки внеклеточного матрикса.",
    "Ангиогенез": "Отражает активность образования новых сосудов в опухолевом микроокружении.",
    "Эндотелий": "Сигнатура эндотелиального компонента и сосудистого русла опухоли.",
    "M1-сигнатуры": "Отражает признаки провоспалительных M1-подобных макрофагов.",
    "Противоопухолевые цитокины": "Показывает активность цитокинов, связанных с противоопухолевым воспалительным ответом.",
    "Ингибирование контрольных точек": "Характеризует экспрессионные признаки, связанные с pathway иммунных контрольных точек.",
    "Нейтрофильная сигнатура": "Отражает вклад нейтрофильного компонента в микроокружение опухоли.",
    "Трафик гранулоцитов": "Показывает признаки рекрутирования и миграции гранулоцитов в опухоль.",
    "T-регуляторные клетки": "Отражает вклад Treg-клеток, связанных с иммунным подавлением.",
    "MDSC": "Сигнатура миелоидных супрессорных клеток, подавляющих противоопухолевый иммунитет.",
    "Трафик MDSC": "Показывает признаки миграции и накопления MDSC в микроокружении опухоли.",
    "Макрофаги": "Характеризует общий вклад макрофагального компонента в опухолевое микроокружение.",
    "Проопухолевые цитокины": "Показывает активность цитокинов, способствующих иммуносупрессии и поддержке опухоли.",
    "Скорость пролиферации": "Отражает интенсивность деления опухолевых клеток.",
    "EMT-сигнатура": "Сигнатура эпителиально-мезенхимального перехода, связанного с инвазией и пластичностью опухоли.",
}


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


def _tooltip_html(label: str, text: str) -> str:
    safe_label = esc(label)
    safe_text = esc(text)
    return "".join([
        '<div class="immune-sign-tooltip">',
        safe_label,
        f'<span class="immune-sign-tooltip-text">{safe_text}</span>',
        '</div>',
    ])


def _summary_html(summary_text: str, summary_icon: str, summary_tone: str) -> str:
    tone = TONE_DEFAULTS.get(summary_tone, TONE_DEFAULTS["neutral"])
    icon = esc(summary_icon or tone["icon"])
    return "".join([
        f'<div class="immune-sign-summary immune-sign-summary--{esc(summary_tone)}" style="color:{tone["text"]};">',
        f'<span class="immune-sign-summary-icon">{icon}</span>',
        f'<span class="immune-sign-summary-text">{esc(summary_text)}</span>',
        '</div>',
    ])


def _item_tooltip_text(item: dict) -> str:
    label = str(item.get("label", "")).strip()
    return ITEM_TOOLTIPS.get(
        label,
        "Показывает относительную выраженность данной сигнатуры по сравнению с референсной меланомной когортой."
    )


def _items_html(items: list[dict]) -> str:
    rows: list[str] = []
    for item in items:
        value = float(item["value"])
        rows.append("".join([
            '<div class="immune-sign-row">',
            f'<div class="immune-sign-row-label">{esc(item["label"])}</div>',
            '<div class="immune-sign-row-info">',
            _tooltip_html("ℹ", _item_tooltip_text(item)),
            '</div>',
            '<div class="immune-sign-row-bar">',
            f'<div class="immune-sign-row-bar-fill" style="background:{_score_to_fill(value)};"></div>',
            '</div>',
            f'<div class="immune-sign-row-value">{value:.2f}</div>',
            '</div>',
        ]))
    return ''.join(rows)


def _card_html(group: dict) -> str:
    card_tooltip = " ".join(
        part
        for part in [
            str(group.get("description", "")).strip(),
            GENERAL_SIGNATURE_TOOLTIP,
        ]
        if part
    )
    return "".join([
        '<div class="immune-sign-card">',
        f'<div class="immune-sign-card-title">{esc(group["title"])}</div>',
        f'<div class="immune-sign-card-desc">{esc(group["description"])}</div>',
        _summary_html(group.get("summary_text", ""), group.get("summary_icon", "•"), group.get("summary_tone", "neutral")),
        '<div class="immune-sign-card-info-row">',
        _tooltip_html("ℹ Как интерпретировать показатель", card_tooltip),
        '</div>',
        '<div class="immune-sign-rows">',
        _items_html(group.get("items", [])),
        '</div>',
        '</div>',
    ])


def _grid_row_html(left_group: dict | None, right_group: dict | None, *, left_narrow: bool = False, row_class: str = "") -> str:
    classes = "immune-sign-grid immune-sign-print-row"
    if row_class:
        classes += f" {row_class}"
    left_class = "immune-sign-grid-item immune-sign-grid-item--narrow" if left_narrow else "immune-sign-grid-item"
    left_html = f'<div class="{left_class}">{_card_html(left_group)}</div>' if left_group else '<div></div>'
    right_html = f'<div class="immune-sign-grid-item">{_card_html(right_group)}</div>' if right_group else '<div class="immune-sign-grid-spacer"></div>'
    return "".join([
        f'<div class="{classes}">',
        left_html,
        right_html,
        '</div>',
    ])


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

    html = ''.join([
        '<div class="immune-sign-section">',
        '<div class="immune-sign-print-intro">',
        '<div class="section-common-title-frame"><div class="section-common-title-text">Иммунные сигнатуры</div></div>',
        '<div class="immune-sign-legend-panel">',
        '<div class="immune-sign-legend-panel-title">Цветовая шкала для всех сигнатур</div>',
        '<div class="immune-sign-legend-panel-subtitle">Отрицательные значения смещены к синему, положительные — к красному. Насыщенность отражает силу обогащения.</div>',
        '<div class="immune-sign-legend-panel-info">',
        _tooltip_html("ℹ Как читать шкалу", GENERAL_SIGNATURE_TOOLTIP),
        '</div>',
        '<div class="immune-sign-legend">',
        '<div class="immune-sign-legend-scale">',
        f'<span class="immune-sign-legend-label immune-sign-legend-label--left">{data["legend_min"]:.0f}</span>',
        '<span class="immune-sign-legend-label immune-sign-legend-label--center">0</span>',
        f'<span class="immune-sign-legend-label immune-sign-legend-label--right">{data["legend_max"]:.0f}</span>',
        '</div>',
        '</div>',
        '</div>',
        _grid_row_html(top_left, top_right, row_class="immune-sign-print-row--first"),
        '</div>',
        _grid_row_html(mid_left, mid_right, row_class="immune-sign-print-row--second"),
        _grid_row_html(bottom_left, None, left_narrow=True, row_class="immune-sign-print-row--third"),
        '</div>',
    ])
    _render_html(html)
