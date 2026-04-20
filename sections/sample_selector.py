import streamlit as st

from core.paths import list_samples


# Это функция для отрисовки блока «образца селектора» в интерфейсе дашборда.
# Используется в следующих блоках: app.py.
# На вход: функция не ожидает обязательных входных параметров.
# На выход: результат дальнейшего шага обработки.
def render_sample_selector():
    samples = list_samples()

    with st.sidebar:
        st.markdown(
            """
            <div class="sample-selector-title">
                Информация о данных
            </div>
            """,
            unsafe_allow_html=True,
        )

        if samples:
            current = st.session_state.get("selected_sample", samples[0])
            idx = samples.index(current) if current in samples else 0

            st.selectbox(
                "SAMPLE",
                samples,
                index=idx,
                key="selected_sample",
                label_visibility="collapsed",
            )
        else:
            st.text_input("SAMPLE", value="", disabled=True, label_visibility="collapsed")
            st.markdown(
                """
                <div class="sample-selector-warning">
                    В папке data/ нет sample-папок.
                </div>
                """,
                unsafe_allow_html=True,
            )

        sample = st.session_state.get("selected_sample", "")
        if sample:
            st.markdown(
                f"""
                <div class="sample-selector-info-box">
                    <div class="sample-selector-path-row">
                        <span class="sample-selector-path-label">Текущий путь:</span>
                        <span class="sample-selector-path-value">data/{sample}/</span>
                    </div>
                    <div class="sample-selector-path-row">
                        <span class="sample-selector-path-label">Редактируемые данные:</span>
                        <span class="sample-selector-path-value">data/{sample}/edit/</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )