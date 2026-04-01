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


def _render_html(html: str) -> None:
    st.markdown(html.strip(), unsafe_allow_html=True)


def _build_tmb_card(sample: str) -> str:
    tmb_value = read_tmb_value(tmb_path(sample))
    status, color, _ = classify_tmb(tmb_value)
    tmb_text = f"{tmb_value:.2f}" if tmb_value is not None else "—"
    marker_left = tmb_scale_position(tmb_value)

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
            f'<div class="genetic-tmb-marker" style="left:{marker_left}%;">',
            f'<span class="genetic-tmb-marker-value">{esc(tmb_text)}</span>',
            '</div>',
            '</div>',
            '<div class="genetic-tmb-ticks">',
            '<span>0</span>',
            '<span>10</span>',
            '<span>12</span>',
            '<span>80+</span>',
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

    allele_1_cells: list[str] = []
    allele_2_cells: list[str] = []

    for locus in loci:
        item = by_locus.get(locus, {"allele_1": "—", "allele_2": "—", "status": "Гетерозигота"})

        if item["status"] == "Гомозигота":
            allele_1_color = HLA_HOMO_COLOR
            allele_2_color = HLA_HOMO_COLOR
        else:
            allele_1_color = HLA_HETERO_FIRST_COLOR
            allele_2_color = HLA_HETERO_SECOND_COLOR

        allele_1_cells.append(
            f'<td class="genetic-hla-allele" style="color:{allele_1_color};">{esc(str(item["allele_1"]))}</td>'
        )
        allele_2_cells.append(
            f'<td class="genetic-hla-allele" style="color:{allele_2_color};">{esc(str(item["allele_2"]))}</td>'
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
            '<thead><tr><th>Локус</th><th>HLA-A</th><th>HLA-B</th><th>HLA-C</th></tr></thead>',
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

        draft["text"] = st.text_area(
            "Редкие генетические события",
            value=draft.get("text", "Не выявлены"),
            height=110,
            key="rare_events_edit_text",
        )
        st.session_state["rare_events_draft"] = draft

        action_left, action_right, _ = st.columns([1, 1, 6])

        with action_left:
            st.button("Сохранить", key="save_rare_events", on_click=save_edit, args=("rare_events",), type="primary")

        with action_right:
            st.button("Отмена", key="cancel_rare_events", on_click=cancel_edit, args=("rare_events",), type="secondary")
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
