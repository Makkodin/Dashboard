from __future__ import annotations

import streamlit as st

from core.io_utils import esc

DEFAULT_CONTACTS_TEXT = """Лаборатория: НИЦЭМ им. Н.Ф. Гамалеи
Директор: д.б.н. Логунов Д.Ю.
Адрес: 123098, г.Москва, ул. Гамалеи, д. 18
тел: +7 (499)193 30 01
Факс: +7(499)193-61-83
E mail: info@gamaleya.org
Версия отчета: v1

НИЦЭМ им. Н.Ф. Гамалеи © 2026"""

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
    mapping: dict[str, str] = {key: "" for key in ORDER}
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
    return (
        '<div class="contacts-kv">'
        f'<div class="contacts-kv-label">{esc(label)}:</div>'
        f'<div class="contacts-kv-value">{safe_value}</div>'
        '</div>'
    )


def render_contacts_block() -> None:
    contacts_text = st.session_state.get("contacts_text", DEFAULT_CONTACTS_TEXT)
    mapping, copyright_line = _parse_contacts_text(contacts_text)

    cols_html: list[str] = []
    for group in COLUMN_GROUPS:
        items = "".join(_kv_html(label, mapping.get(label, "")) for label in group)
        cols_html.append(f'<div class="contacts-grid-col">{items}</div>')

    html = (
        '<div class="contacts-card">'
        f'<div class="contacts-grid">{"".join(cols_html)}</div>'
        '<div class="contacts-footer-row">'
        f'<div class="contacts-copyright">{esc(copyright_line)}</div>'
        '</div>'
        '</div>'
    )
    st.markdown(html, unsafe_allow_html=True)
