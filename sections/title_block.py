import base64
from functools import lru_cache
from pathlib import Path

import streamlit as st

from core.paths import ASSETS_DIR


@lru_cache(maxsize=8)
def _img_to_data_uri_cached(path_str: str, mtime_ns: int) -> str:
    path = Path(path_str)
    ext = path.suffix.lower().replace(".", "")
    mime = "image/png" if ext == "png" else f"image/{ext}"
    b64 = base64.b64encode(path.read_bytes()).decode("utf-8")
    return f"data:{mime};base64,{b64}"


def _img_to_data_uri(path: Path) -> str:
    try:
        return _img_to_data_uri_cached(str(path.resolve()), path.stat().st_mtime_ns)
    except OSError:
        return ""


def render_title_block():
    logo_path = ASSETS_DIR / "logo.png"

    left, right = st.columns([6, 4], gap="large")

    with left:
        st.markdown(
            """
            <div class="title-block-shell title-block-left">
                <div class="title-block-main-text">
                    Заключение по результатами комплексного<br>
                    молекулярно-генетического исследования
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with right:
        if logo_path.exists():
            logo_src = _img_to_data_uri(logo_path)
            st.markdown(
                f"""
                <div class="title-block-shell title-block-right">
                    <img src="{logo_src}" class="title-block-logo-img" alt="logo">
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                """
                <div class="title-block-shell title-block-right title-block-logo-placeholder">
                    Логотип
                </div>
                """,
                unsafe_allow_html=True,
            )
