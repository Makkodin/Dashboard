from __future__ import annotations

import streamlit as st

from core.io_utils import esc

ORDER = [
    "Лаборатория",
    "Директор",
    "Адрес",
    "тел",
    "Факс",
    "E mail",
    "Версия отчета",
]
COLUMN_GROUPS = [
    ["Лаборатория", "Директор"],
    ["Адрес", "тел"],
    ["Факс", "E mail"],
    ["Версия отчета"],
]


def _parse_contacts_text(text: str) -> tuple[dict[str, str], str]:
    mapping = {key: "" for key in ORDER}
    copyright_line = ""
    for raw_line in str(text).splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if ":" in line:
            label, value = line.split(":", 1)
            label = label.strip()
            value = value.strip()
            if label in mapping:
                mapping[label] = value
                continue
        copyright_line = line
    return mapping, copyright_line


def _kv_html(label: str, value: str) -> str:
    safe_value = esc(value) if str(value).strip() else "—"
    label_html = f'<div class="contacts-kv-label">{esc(label)}:</div>' if str(label).strip() else ""
    return (
        '<div class="contacts-kv">'
        f'{label_html}'
        f'<div class="contacts-kv-value">{safe_value}</div>'
        '</div>'
    )


def render_contacts_block() -> None:
    contacts_text = str(st.session_state.get("contacts_text", "")).strip()
    if not contacts_text:
        return

    mapping, copyright_line = _parse_contacts_text(contacts_text)
    cols_html = []

    for idx, group in enumerate(COLUMN_GROUPS):
        items_html = []
        for label in group:
            items_html.append(_kv_html(label, mapping.get(label, "")))

        if idx == len(COLUMN_GROUPS) - 1 and copyright_line:
            items_html.append(_kv_html("", copyright_line))

        cols_html.append(f'<div class="contacts-grid-col">{"".join(items_html)}</div>')

    html = (
        '<div class="contacts-section">'
        '<div class="contacts-print-shell">'
        '<div class="contacts-card">'
        f'<div class="contacts-grid">{"".join(cols_html)}</div>'
        '</div>'
        '</div>'
        '</div>'
    )
    st.markdown(html, unsafe_allow_html=True)
