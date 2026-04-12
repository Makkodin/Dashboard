from functools import lru_cache
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from core.state import ensure_state, is_section_enabled, open_section_picker, sync_sample_state
from sections.annotation_blocks import render_annotation_blocks
from sections.biomaterial_block import render_biomaterial_block
from sections.contacts_block import render_contacts_block
from sections.footer_mode import render_bottom_mode_indicator
from sections.genetic_profile_block import render_genetic_profile_block
from sections.immune_markers_block import render_immune_markers_block
from sections.immune_signatures_block import render_immune_signatures_block
from sections.immune_status_block import render_immune_status_block
from sections.meta_block import render_meta_block
from sections.patient_block import render_patient_block
from sections.recommendations_block import render_recommendations_block
from sections.sample_selector import render_sample_selector
from sections.section_picker import render_dashboard_section_picker
from sections.title_block import render_title_block
from sections.treatment_block import render_treatment_block


@lru_cache(maxsize=8)
def _load_css_text_cached(signature: tuple[tuple[str, int], ...]) -> str:
    parts: list[str] = []
    for path_str, _mtime_ns in signature:
        css_path = Path(path_str)
        parts.append(f"/* FILE: {css_path.name} */\n")
        parts.append(css_path.read_text(encoding="utf-8"))
        parts.append("\n\n")
    return "".join(parts)


def load_css_folder(folder: str = "styles_css") -> None:
    css_dir = Path(folder)
    if not css_dir.exists():
        st.error(f"Папка {folder} не найдена")
        return

    css_files = sorted(css_dir.glob("*.css"))
    signature = tuple((str(css_file.resolve()), css_file.stat().st_mtime_ns) for css_file in css_files)
    if signature:
        st.markdown(f"<style>{_load_css_text_cached(signature)}</style>", unsafe_allow_html=True)



def render_global_loading_overlay() -> None:
    components.html(
        r'''
        <script>
        (function () {
            const parentDoc = window.parent.document;
            const OVERLAY_ID = "dashboard-global-loader";
            const STYLE_ID = "dashboard-global-loader-style";
            const ACTIVE_CLASS = "dashboard-loading-active";
            let hideTimer = null;

            function ensureStyle() {
                if (parentDoc.getElementById(STYLE_ID)) {
                    return;
                }

                const style = parentDoc.createElement("style");
                style.id = STYLE_ID;
                style.textContent = `
                    html.${ACTIVE_CLASS},
                    body.${ACTIVE_CLASS} {
                        cursor: progress !important;
                    }

                    #${OVERLAY_ID} {
                        position: fixed;
                        inset: 0;
                        z-index: 2147483647;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        background: rgba(255, 255, 255, 0.96);
                        opacity: 0;
                        visibility: hidden;
                        pointer-events: none;
                        transition: opacity 0.18s ease, visibility 0.18s ease;
                    }

                    #${OVERLAY_ID}.is-visible {
                        opacity: 1;
                        visibility: visible;
                        pointer-events: all;
                    }

                    #${OVERLAY_ID} .dashboard-loader-card {
                        min-width: 13.5rem;
                        max-width: 21rem;
                        padding: 1rem 1.25rem;
                        border-radius: 1rem;
                        border: 0.0625rem solid #D7E6FB;
                        background: #F3F8FF;
                        box-shadow: 0 0.75rem 2.5rem rgba(17, 24, 39, 0.10);
                        display: flex;
                        align-items: center;
                        gap: 0.875rem;
                        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
                    }

                    #${OVERLAY_ID} .dashboard-loader-spinner {
                        width: 1.75rem;
                        height: 1.75rem;
                        border-radius: 50%;
                        border: 0.1875rem solid rgba(30, 58, 138, 0.18);
                        border-top-color: #1E3A8A;
                        animation: dashboard-loader-spin 0.8s linear infinite;
                        flex: 0 0 auto;
                    }

                    #${OVERLAY_ID} .dashboard-loader-title {
                        color: #0F172A;
                        font-size: 0.9375rem;
                        line-height: 1.35;
                        font-weight: 700;
                    }

                    #${OVERLAY_ID} .dashboard-loader-subtitle {
                        color: #64748B;
                        font-size: 0.75rem;
                        line-height: 1.4;
                        margin-top: 0.125rem;
                    }

                    @keyframes dashboard-loader-spin {
                        to { transform: rotate(360deg); }
                    }
                `;
                parentDoc.head.appendChild(style);
            }

            function ensureOverlay() {
                let overlay = parentDoc.getElementById(OVERLAY_ID);
                if (overlay) {
                    return overlay;
                }

                overlay = parentDoc.createElement("div");
                overlay.id = OVERLAY_ID;
                overlay.innerHTML = `
                    <div class="dashboard-loader-card" role="status" aria-live="polite">
                        <div class="dashboard-loader-spinner"></div>
                        <div>
                            <div class="dashboard-loader-title">Загрузка дашборда...</div>
                            <div class="dashboard-loader-subtitle">Подготавливаем отображение разделов</div>
                        </div>
                    </div>
                `;
                parentDoc.body.appendChild(overlay);
                return overlay;
            }

            function showLoader() {
                const overlay = ensureOverlay();
                overlay.classList.add("is-visible");
                parentDoc.documentElement.classList.add(ACTIVE_CLASS);
                parentDoc.body.classList.add(ACTIVE_CLASS);
            }

            function hideLoader() {
                const overlay = ensureOverlay();
                overlay.classList.remove("is-visible");
                parentDoc.documentElement.classList.remove(ACTIVE_CLASS);
                parentDoc.body.classList.remove(ACTIVE_CLASS);
            }

            function scheduleHide(delay) {
                window.clearTimeout(hideTimer);
                hideTimer = window.setTimeout(hideLoader, delay);
            }

            function pickerVisible() {
                return Boolean(parentDoc.querySelector('.section-picker-marker'));
            }

            function isRelevantInteraction(target) {
                if (!target) {
                    return false;
                }

                const button = target.closest('button');
                if (button) {
                    const label = (button.innerText || button.textContent || '').trim();
                    if (["Выбрать разделы", "Открыть", "Все", "Снять"].includes(label)) {
                        return true;
                    }
                }

                if (!pickerVisible()) {
                    return false;
                }

                return Boolean(
                    target.closest('[data-testid="stCheckbox"]') ||
                    target.closest('input[type="checkbox"]') ||
                    target.closest('[data-testid="stButton"]')
                );
            }

            ensureStyle();
            showLoader();
            scheduleHide(700);

            if (!parentDoc.body.dataset.dashboardLoaderBound) {
                const observer = new MutationObserver(function () {
                    scheduleHide(450);
                });

                observer.observe(parentDoc.body, {
                    childList: true,
                    subtree: true,
                    attributes: true,
                    characterData: true,
                });

                parentDoc.addEventListener('click', function (event) {
                    if (isRelevantInteraction(event.target)) {
                        showLoader();
                    }
                }, true);

                parentDoc.addEventListener('change', function (event) {
                    if (isRelevantInteraction(event.target)) {
                        showLoader();
                    }
                }, true);

                parentDoc.body.dataset.dashboardLoaderBound = '1';
            }
        })();
        </script>
        ''',
        height=0,
        width=0,
    )


def _render_clinical_info_section() -> None:
    st.markdown(
        '''
        <div class="section-common-title-frame">
            <div class="section-common-title-text">Клиническая информация</div>
        </div>
        ''',
        unsafe_allow_html=True,
    )
    render_patient_block()
    render_treatment_block()
    render_biomaterial_block()


st.set_page_config(
    page_title="Клинический отчет",
    layout="wide",
    initial_sidebar_state="collapsed",
)

load_css_folder()
render_global_loading_overlay()

ensure_state()
render_sample_selector()
sync_sample_state()

with st.sidebar:
    st.divider()
    if st.button("Выбрать разделы", use_container_width=True):
        open_section_picker()

if not st.session_state.get("dashboard_sections_confirmed", False):
    render_dashboard_section_picker()
    if not st.session_state.get("dashboard_sections_confirmed", False):
        st.stop()

render_title_block()

if is_section_enabled("meta"):
    render_meta_block()

if is_section_enabled("clinical"):
    _render_clinical_info_section()

if is_section_enabled("genetic"):
    render_genetic_profile_block()

if is_section_enabled("immune_status"):
    render_immune_status_block()

if is_section_enabled("immune_signatures"):
    render_immune_signatures_block()

if is_section_enabled("immune_markers"):
    render_immune_markers_block()

if is_section_enabled("recommendations"):
    render_recommendations_block()

if is_section_enabled("contacts"):
    render_contacts_block()

if is_section_enabled("annotations"):
    render_annotation_blocks()

render_bottom_mode_indicator()
