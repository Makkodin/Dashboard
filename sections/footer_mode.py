from __future__ import annotations

import streamlit as st
import streamlit.components.v1 as components

from core.io_utils import esc
from core.state import dashboard_mode_text


# Это функция для отрисовки блока «bottom mode indicator» в интерфейсе дашборда.
# Используется в следующих блоках: app.py.
# На вход: функция не ожидает обязательных входных параметров.
# На выход: результат дальнейшего шага обработки.
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
            const PRINT_GRACE_MS = 1500;

            function allowNextPrint(doc) {
                doc.documentElement.dataset.pdfPrintAllowedUntil = String(Date.now() + PRINT_GRACE_MS);
            }

            function isPrintAllowed(doc) {
                const until = Number(doc.documentElement.dataset.pdfPrintAllowedUntil || 0);
                return Date.now() <= until;
            }

            function showPrintHint(doc) {
                const existing = doc.getElementById('pdf-print-hotkey-hint');
                if (existing) {
                    existing.style.opacity = '1';
                    clearTimeout(window.__pdfPrintHintTimer);
                    window.__pdfPrintHintTimer = setTimeout(function () {
                        existing.style.opacity = '0';
                    }, 2200);
                    return;
                }

                const hint = doc.createElement('div');
                hint.id = 'pdf-print-hotkey-hint';
                hint.textContent = 'Печать через Ctrl+P отключена. Используйте кнопку «Сохранить как PDF».';
                hint.style.position = 'fixed';
                hint.style.right = '16px';
                hint.style.bottom = '16px';
                hint.style.zIndex = '2147483647';
                hint.style.maxWidth = 'min(420px, calc(100vw - 32px))';
                hint.style.padding = '12px 14px';
                hint.style.borderRadius = '12px';
                hint.style.background = 'rgba(17, 24, 39, 0.94)';
                hint.style.color = '#FFFFFF';
                hint.style.fontSize = '14px';
                hint.style.lineHeight = '1.35';
                hint.style.boxShadow = '0 10px 30px rgba(0,0,0,0.22)';
                hint.style.transition = 'opacity 0.18s ease';
                hint.style.opacity = '1';
                doc.body.appendChild(hint);

                clearTimeout(window.__pdfPrintHintTimer);
                window.__pdfPrintHintTimer = setTimeout(function () {
                    hint.style.opacity = '0';
                }, 2200);
            }

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
                    allowNextPrint(doc);
                    window.parent.focus();
                    window.parent.print();
                });
            }

            function bindPrintBlockers() {
                const doc = window.parent.document;
                if (doc.documentElement.dataset.printHotkeyBound === '1') {
                    return;
                }
                doc.documentElement.dataset.printHotkeyBound = '1';

                doc.addEventListener('keydown', function (event) {
                    const key = String(event.key || '').toLowerCase();
                    if ((event.ctrlKey || event.metaKey) && key === 'p' && !isPrintAllowed(doc)) {
                        event.preventDefault();
                        event.stopPropagation();
                        event.stopImmediatePropagation();
                        showPrintHint(doc);
                    }
                }, true);

                window.parent.addEventListener('beforeprint', function (event) {
                    if (isPrintAllowed(doc)) {
                        return;
                    }
                    if (event && typeof event.preventDefault === 'function') {
                        event.preventDefault();
                    }
                    showPrintHint(doc);
                });
            }

            bindPrintButton();
            bindPrintBlockers();

            const observer = new MutationObserver(function () {
                bindPrintButton();
                bindPrintBlockers();
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
