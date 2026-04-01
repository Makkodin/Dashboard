import streamlit as st

from core.io_utils import esc, load_timeline
from core.paths import timeline_path
from core.timeline import build_timeline_items, get_timeline_item_classes


def _timeline_colors(cls: str) -> tuple[str, str]:
    if cls == "tl-surgery-old":
        return "#9CA3AF", "#9CA3AF"
    if cls == "tl-progression":
        return "#DC2626", "#B91C1C"
    if cls == "tl-latest":
        return "#16A34A", "#15803D"
    return "#3B82F6", "#6B7280"


def render_timeline_horizontal(sample: str):
    data = load_timeline(timeline_path(sample))
    items = build_timeline_items(data)

    if not items:
        st.markdown(
            """
            <div class="treatment-block-empty-card">
                <div class="treatment-block-empty">Нет данных для отображения</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    classes = get_timeline_item_classes(items)

    with st.container(border=True):
        cols = st.columns(len(items), gap="medium")

        for i, (col, item, cls) in enumerate(zip(cols, items, classes)):
            dot_color, date_color = _timeline_colors(cls)

            with col:
                # Дата
                st.markdown(
                    f"""
                    <div class="treatment-date" style="color:{date_color};">
                        {esc(item["date"])}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                # Точка + линия
                line_cols = st.columns([1, 12], gap="small")
                with line_cols[0]:
                    st.markdown(
                        f"""
                        <div class="treatment-dot" style="background:{dot_color};"></div>
                        """,
                        unsafe_allow_html=True,
                    )
                with line_cols[1]:
                    if i < len(items) - 1:
                        st.markdown(
                            """
                            <div class="treatment-line"></div>
                            """,
                            unsafe_allow_html=True,
                        )
                    else:
                        st.markdown(
                            """
                            <div class="treatment-line treatment-line-hidden"></div>
                            """,
                            unsafe_allow_html=True,
                        )

                # ЕДИНЫЙ блок stage + desc
                st.markdown(
                    f"""
                    <div class="treatment-text-block">
                        <div class="treatment-stage">
                            {esc(item["stage"])}
                        </div>
                        <div class="treatment-desc">
                            {esc(item["desc"])}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )


def render_treatment_block():
    left, right = st.columns([20, 1], gap="small")

    with left:
        st.markdown(
            """
            <div class="treatment-block-title-row">
                <div class="treatment-block-title-text">💊 История лечения</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with right:
        st.markdown("&nbsp;", unsafe_allow_html=True)

    sample = st.session_state.get("selected_sample", "")
    if sample:
        render_timeline_horizontal(sample)
    else:
        st.warning("Не выбран SAMPLE.")