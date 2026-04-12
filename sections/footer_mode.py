from __future__ import annotations

import streamlit as st
import streamlit.components.v1 as components

from core.io_utils import esc
from core.state import dashboard_mode_text


def render_bottom_mode_indicator():
    mode_text = dashboard_mode_text()
    mode_class = "footer-mode-pill-edit" if "Редактирование:" in mode_text else "footer-mode-pill-view"

    st.markdown(
        f'''
        <div class="footer-mode-wrap">
            <button type="button" class="footer-mode-pdf-button" data-pdf-print-trigger="1">
                Сохранить как PDF
            </button>
            <span class="footer-mode-label">Режим дашборда:</span>
            <span class="footer-mode-pill {mode_class}">{esc(mode_text)}</span>
        </div>
        ''',
        unsafe_allow_html=True,
    )

    components.html(
        '''
        <script>
        (function () {
            function bindPrintButton() {
                const doc = window.parent.document;
                const btn = doc.querySelector('[data-pdf-print-trigger="1"]');
                if (!btn || btn.dataset.printBound === "1") {
                    return;
                }

                btn.dataset.printBound = "1";
                btn.addEventListener("click", function (event) {
                    event.preventDefault();
                    event.stopPropagation();
                    window.parent.focus();
                    window.parent.print();
                });
            }

            bindPrintButton();

            const observer = new MutationObserver(function () {
                bindPrintButton();
            });

            observer.observe(window.parent.document.body, {
                childList: true,
                subtree: true
            });
        })();
        </script>
        ''',
        height=0,
        width=0,
    )
