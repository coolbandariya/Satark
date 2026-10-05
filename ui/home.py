"""SATARK home experience."""
import streamlit as st

from ui.demo import get_demo_result


def render_home():
    st.markdown(
        '<div class="home-intro">'
        '<div class="home-intro-title">Clear answers for suspicious content.</div>'
        '<div class="home-intro-copy">'
        'Start with what you received—not a complicated security dashboard. '
        'SATARK turns suspicious content into evidence, practical next steps, '
        'and an easy-to-understand assessment.'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="home-grid">'
        '<div class="home-card"><div class="home-card-index">01 / CHECK</div>'
        '<div class="home-card-title">Messages & links</div>'
        '<div class="home-card-copy">Inspect messages, URLs, phishing patterns, impersonation and social-engineering pressure.</div></div>'
        '<div class="home-card"><div class="home-card-index">02 / SEE</div>'
        '<div class="home-card-title">Images & documents</div>'
        '<div class="home-card-copy">Review screenshots, QR images and text-based PDFs for visible warning signs.</div></div>'
        '<div class="home-card"><div class="home-card-index">03 / LEARN</div>'
        '<div class="home-card-title">Understand the result</div>'
        '<div class="home-card-copy">See evidence, confidence, recommendations and clear next steps—not just a score.</div></div>'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="home-trust">'
        '<span><strong>TEXT</strong> messages</span>'
        '<span><strong>URL</strong> links</span>'
        '<span><strong>IMAGE</strong> screenshots</span>'
        '<span><strong>PDF</strong> documents</span>'
        '<span><strong>VIDEO</strong> frames + audio</span>'
        '<span><strong>SESSION</strong> temporary history</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="home-actions">', unsafe_allow_html=True)
    if st.button("Start checking →", use_container_width=True, type="primary", key="goto_analyze"):
        st.session_state.page = "Analyze"
        st.session_state.scroll_to_scanners = True
        st.session_state.demo_mode = False
        st.rerun()

    if st.button("See a sample result", use_container_width=True, key="demo_result"):
        st.session_state.result = get_demo_result()
        st.session_state.mode = "Text"
        st.session_state.demo_mode = True
        st.session_state.page = "Analyze"
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
