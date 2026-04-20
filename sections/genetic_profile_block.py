from __future__ import annotations

from html import escape as esc

import streamlit as st

from core.genetic_profile import (
    TMB_TOOLTIP_TEXT,
    classify_tmb,
    load_hla_class_i,
    load_key_somatic_variants,
    read_tmb_value,
    tmb_scale_position,
)
from core.paths import norma_alleles_path, tmb_path, vep_ann_path
from core.state import cancel_edit, save_edit, start_edit


HLA_HETERO_FIRST_COLOR = "#2563EB"
HLA_HETERO_SECOND_COLOR = "#86EFAC"
HLA_HOMO_COLOR = "#22C55E"


# Это функция для блока «отрисовки html». Она нужна для того, чтобы вынести отдельный шаг логики в самостоятельную и читаемую часть кода.
# Используется в следующих блоках: sections/genetic_profile_block.py, sections/immune_markers_block.py, sections/immune_signatures_block.py.
# На вход: html.
# На выход: None.
def _render_html(html: str) -> None:
    st.markdown(html.strip(), unsafe_allow_html=True)


# Это функция для блока «сборки tmb card». Она нужна для того, чтобы вынести отдельный шаг логики в самостоятельную и читаемую часть кода.
# Используется в следующих блоках: sections/genetic_profile_block.py, core/recommendations.py.
# На вход: sample.
# На выход: str.
def _build_tmb_card(sample: str) -> str:
    tmb_value = read_tmb_value(tmb_path(sample))
    status, color, _ = classify_tmb(tmb_value)
    tmb_text = f"{tmb_value:.2f}" if tmb_value is not None else "—"
    marker_left = tmb_scale_position(tmb_value)
    scale_marker_text = "30+" if tmb_value is not None and tmb_value > 30 else tmb_text
    marker_edge_class = ""
    if marker_left <= 6:
        marker_edge_class = " genetic-tmb-marker--edge-left"
    elif marker_left >= 94:
        marker_edge_class = " genetic-tmb-marker--edge-right"

    return "".join(
        [
            '<div class="genetic-card genetic-card-top-row">',
            '<div class="genetic-card-head">',
            '<div class="genetic-subblock-title-row genetic-subblock-title-row--compact">',
            '<div class="genetic-subblock-title-text">🧬 Оценка мутационной нагрузки (TMB)</div>',
            '</div>',
            '<div class="genetic-subblock-subtitle genetic-subblock-subtitle--inside-card">Потенциальный ответ на иммунотерапию</div>',
            '</div>',
            '<div class="genetic-card-body genetic-card-body--centered">',
            '<div class="genetic-kv-stack">',
            '<div class="genetic-kv-row">',
            '<div class="genetic-mini-label">TMB:</div>',
            f'<div class="genetic-tmb-inline-value" style="color:{color};">{esc(tmb_text)}</div>',
            '</div>',
            '<div class="genetic-kv-row">',
            '<div class="genetic-mini-label">Статус:</div>',
            f'<div class="genetic-status-inline-text">{esc(status)}</div>',
            '</div>',
            '</div>',
            '<div class="genetic-tmb-scale-wrap">',
            '<div class="genetic-tmb-scale">',
            '<div class="genetic-tmb-zone genetic-tmb-zone--low"></div>',
            '<div class="genetic-tmb-zone genetic-tmb-zone--mid"></div>',
            '<div class="genetic-tmb-zone genetic-tmb-zone--high"></div>',
            f'<div class="genetic-tmb-marker{marker_edge_class}" style="left:{marker_left}% ;">',
            f'<span class="genetic-tmb-marker-value">{esc(scale_marker_text)}</span>',
            '</div>',
            '</div>',
            '<div class="genetic-tmb-ticks">',
            '<span>0</span>',
            '<span>10</span>',
            '<span>12</span>',
            '<span>30+</span>',
            '</div>',
            '</div>',
            '<div class="genetic-threshold-hint-wrap">',
            '<div class="genetic-tooltip">',
            'ℹ Как интерпретировать показатель',
            f'<span class="genetic-tooltip-text">{esc(TMB_TOOLTIP_TEXT)}</span>',
            '</div>',
            '</div>',
            '</div>',
            '</div>',
        ]
    )


# Это функция для блока «сборки соматических card». Она нужна для того, чтобы вынести отдельный шаг логики в самостоятельную и читаемую часть кода.
# Используется в следующих блоках: sections/genetic_profile_block.py.
# На вход: sample.
# На выход: str.
def _build_somatic_card(sample: str) -> str:
    df = load_key_somatic_variants(vep_ann_path(sample))

    if df.empty:
        return "".join(
            [
                '<div class="genetic-card genetic-card-top-row">',
                '<div class="genetic-card-head">',
                '<div class="genetic-subblock-title-row genetic-subblock-title-row--compact">',
                '<div class="genetic-subblock-title-text">🧪 Ключевые соматические варианты</div>',
                '</div>',
                '<div class="genetic-subblock-subtitle genetic-subblock-subtitle--inside-card">Клинически значимые изменения</div>',
                '</div>',
                '<div class="genetic-card-body genetic-card-body--centered">',
                '<div class="genetic-empty-text">Ключевые соматические варианты не выявлены</div>',
                '</div>',
                '</div>',
            ]
        )

    rows_html = "".join(
        [
            "".join(
                [
                    '<tr>',
                    f'<td>{esc(str(row.get("Ген", "—") or "—"))}</td>',
                    f'<td>{esc(str(row.get("Белковое изменение", "—") or "—"))}</td>',
                    f'<td>{esc(str(row.get("Нуклеотидное изменение", "—") or "—"))}</td>',
                    '</tr>',
                ]
            )
            for _, row in df.iterrows()
        ]
    )

    return "".join(
        [
            '<div class="genetic-card genetic-card-top-row">',
            '<div class="genetic-card-head">',
            '<div class="genetic-subblock-title-row genetic-subblock-title-row--compact">',
            '<div class="genetic-subblock-title-text">🧪 Ключевые соматические варианты</div>',
            '</div>',
            '<div class="genetic-subblock-subtitle genetic-subblock-subtitle--inside-card">Клинически значимые изменения</div>',
            '</div>',
            '<div class="genetic-card-body genetic-card-body--centered">',
            '<div class="genetic-table-wrap genetic-table-wrap--compact">',
            '<table class="genetic-table genetic-table--compact">',
            '<thead><tr><th>Ген</th><th>Белковое изменение</th><th>Нуклеотидное изменение</th></tr></thead>',
            f'<tbody>{rows_html}</tbody>',
            '</table>',
            '</div>',
            '</div>',
            '</div>',
        ]
    )


# Это функция для блока «сборки HLA-профиля card». Она нужна для того, чтобы вынести отдельный шаг логики в самостоятельную и читаемую часть кода.
# Используется в следующих блоках: sections/genetic_profile_block.py, core/recommendations.py.
# На вход: sample.
# На выход: str.
def _build_hla_card(sample: str) -> str:
    hla_rows = load_hla_class_i(norma_alleles_path(sample))

    if not hla_rows:
        return "".join(
            [
                '<div class="genetic-card genetic-card-top-row">',
                '<div class="genetic-card-head">',
                '<div class="genetic-subblock-title-row genetic-subblock-title-row--compact">',
                '<div class="genetic-subblock-title-text">🧷 HLA гаплотипы</div>',
                '</div>',
                '<div class="genetic-subblock-subtitle genetic-subblock-subtitle--inside-card">Класс I</div>',
                '</div>',
                '<div class="genetic-card-body genetic-card-body--centered">',
                '<div class="genetic-empty-text">Данные HLA Class I не найдены</div>',
                '</div>',
                '</div>',
            ]
        )

    by_locus = {item["locus"]: item for item in hla_rows}
    loci = ["HLA-A", "HLA-B", "HLA-C"]

    header_cells: list[str] = []
    allele_1_cells: list[str] = []
    allele_2_cells: list[str] = []

    for locus in loci:
        item = by_locus.get(locus, {"allele_1": "—", "allele_2": "—", "status": "Гетерозигота"})
        is_homo = item["status"] == "Гомозигота"

        if is_homo:
            allele_1_color = HLA_HOMO_COLOR
            allele_2_color = HLA_HOMO_COLOR
            header_cells.append(
                ''.join(
                    [
                        '<th class="genetic-hla-cell-head">',
                        f'<div class="genetic-hla-box genetic-hla-box--top">{esc(locus)}</div>',
                        '</th>',
                    ]
                )
            )
            allele_1_cells.append(
                ''.join(
                    [
                        '<td class="genetic-hla-cell">',
                        f'<div class="genetic-hla-box genetic-hla-box--mid"><span style="color:{allele_1_color};">{esc(str(item["allele_1"]))}</span></div>',
                        '</td>',
                    ]
                )
            )
            allele_2_cells.append(
                ''.join(
                    [
                        '<td class="genetic-hla-cell">',
                        f'<div class="genetic-hla-box genetic-hla-box--bottom"><span style="color:{allele_2_color};">{esc(str(item["allele_2"]))}</span></div>',
                        '</td>',
                    ]
                )
            )
        else:
            allele_1_color = HLA_HETERO_FIRST_COLOR
            allele_2_color = HLA_HETERO_SECOND_COLOR
            header_cells.append(f'<th>{esc(locus)}</th>')
            allele_1_cells.append(
                f'<td class="genetic-hla-allele"><span style="color:{allele_1_color};">{esc(str(item["allele_1"]))}</span></td>'
            )
            allele_2_cells.append(
                f'<td class="genetic-hla-allele"><span style="color:{allele_2_color};">{esc(str(item["allele_2"]))}</span></td>'
            )

    return "".join(
        [
            '<div class="genetic-card genetic-card-top-row">',
            '<div class="genetic-card-head">',
            '<div class="genetic-subblock-title-row genetic-subblock-title-row--compact">',
            '<div class="genetic-subblock-title-text">🧷 HLA гаплотипы</div>',
            '</div>',
            '<div class="genetic-subblock-subtitle genetic-subblock-subtitle--inside-card">Класс I</div>',
            '</div>',
            '<div class="genetic-card-body genetic-card-body--centered">',
            '<div class="genetic-table-wrap">',
            '<table class="genetic-table genetic-table--hla">',
            '<thead><tr><th>Локус</th>',
            ''.join(header_cells),
            '</tr></thead>',
            '<tbody>',
            '<tr>',
            '<td class="genetic-table-row-title">Аллель 1</td>',
            ''.join(allele_1_cells),
            '</tr>',
            '<tr>',
            '<td class="genetic-table-row-title">Аллель 2</td>',
            ''.join(allele_2_cells),
            '</tr>',
            '</tbody>',
            '</table>',
            '</div>',
            '</div>',
            '</div>',
        ]
    )


# Это функция для отрисовки блока «генетического профиля профиля block» в интерфейсе дашборда.
# Используется в следующих блоках: app.py.
# На вход: функция не ожидает обязательных входных параметров.
# На выход: результат дальнейшего шага обработки.
def render_genetic_profile_block():
    sample = st.session_state.get("selected_sample", "")
    if not sample:
        st.warning("Не выбран SAMPLE.")
        return

    _render_html(
        """
        <div class="section-common-title-frame">
            <div class="section-common-title-text">Генетический профиль</div>
        </div>
        """
    )

    top_grid_html = "".join(
        [
            '<div class="genetic-top-grid">',
            f'<div class="genetic-top-grid-item genetic-top-grid-item--3">{_build_tmb_card(sample)}</div>',
            f'<div class="genetic-top-grid-item genetic-top-grid-item--3">{_build_somatic_card(sample)}</div>',
            f'<div class="genetic-top-grid-item genetic-top-grid-item--4">{_build_hla_card(sample)}</div>',
            '</div>',
        ]
    )
    _render_html(top_grid_html)
    render_rare_events_block(sample)


# Это функция для отрисовки блока «редких событий block» в интерфейсе дашборда.
# Используется в следующих блоках: sections/genetic_profile_block.py.
# На вход: sample.
# На выход: результат дальнейшего шага обработки.
def render_rare_events_block(sample: str):
    left, right = st.columns([20, 1], gap="small")

    with left:
        _render_html(
            """
            <div class="genetic-subblock-title-row genetic-subblock-title-row--outside">
                <div class="genetic-subblock-title-text">🧾 Редкие генетические события</div>
            </div>
            """
        )

    with right:
        st.button(
            "✎",
            key="edit_btn_rare_events",
            help="Редактировать блок",
            on_click=start_edit,
            args=("rare_events",),
            type="secondary",
        )

    if st.session_state.get("edit_rare_events", False):
        draft = dict(st.session_state["rare_events_draft"])

        st.info("Изменения применяются после нажатия кнопки «Сохранить». Если не сохранить, правки не будут зафиксированы.")

        with st.form("rare_events_edit_form", clear_on_submit=False):
            draft["text"] = st.text_area(
                "Редкие генетические события",
                value=draft.get("text", "Не выявлены"),
                height=110,
                key="rare_events_edit_text",
            )
            st.session_state["rare_events_draft"] = draft

            _, action_left, action_right = st.columns([8.6, 1, 1], gap="small")

            with action_left:
                submitted = st.form_submit_button("Сохранить")

            with action_right:
                cancelled = st.form_submit_button("Отмена")

        if submitted:
            save_edit("rare_events")
            st.rerun()

        if cancelled:
            cancel_edit("rare_events")
            st.rerun()
        return

    text = st.session_state.get("rare_events_data", {}).get("text", "Не выявлены")
    _render_html(
        "".join(
            [
                '<div class="genetic-card genetic-card-rare-events">',
                f'<div class="genetic-rare-text">{esc(text)}</div>',
                '</div>',
            ]
        )
    )
