"""Home experience and offline demo entry point."""
import streamlit as st
from ui.demo import get_demo_result
from stepper_component import render_stepper


def render_home():
    st.markdown(
        '<section class="home-intro home-intro--editorial">'
        '<div class="home-kicker">DIGITAL THREAT TRIAGE · EVIDENCE FIRST</div>'
        '<div class="home-intro-title">Make uncertainty visible.<br><span>Then decide with evidence.</span></div>'
        '<div class="home-intro-copy">SATARK turns suspicious messages, links, screenshots, documents and clips into a structured security assessment — with risk, confidence, signals and safer next steps in one focused workspace.</div>'
        '</section>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="home-stats">'
        '<div><strong>06</strong><span>scanner modes</span></div>'
        '<div><strong>08</strong><span>threat signals</span></div>'
        '<div><strong>04</strong><span>decision stages</span></div>'
        '<div><strong>100%</strong><span>session-local history</span></div>'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="home-grid">'
        '<div class="home-card"><div class="home-card-index">01 / CHECK</div><div class="home-card-title">Messages & links</div><div class="home-card-copy">Investigate phishing, impersonation, urgency, credential requests and suspicious domains before you interact.</div><div class="home-card-meta">TEXT · URL</div></div>'
        '<div class="home-card"><div class="home-card-index">02 / INSPECT</div><div class="home-card-title">Images, QR & documents</div><div class="home-card-copy">Read visible evidence in screenshots, QR images and PDFs instead of judging by appearance alone.</div><div class="home-card-meta">IMAGE · QR · PDF</div></div>'
        '<div class="home-card"><div class="home-card-index">03 / DECIDE</div><div class="home-card-title">Evidence before confidence</div><div class="home-card-copy">Get risk, confidence, evidence and practical next steps without pretending an AI score is certainty.</div><div class="home-card-meta">VIDEO · AI REVIEW</div></div>'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="home-focus">'
        '<div><div class="home-focus-label">THE SATARK PRINCIPLE</div><div class="home-focus-title">Pause → verify → act.</div></div>'
        '<div class="home-focus-copy">A polished logo, familiar name or urgent message is not proof. SATARK separates what is visible from what still needs independent verification.</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="section-title home-how-title">How SATARK works</div>'
        '<div class="section-copy">A four-step path from suspicious content to a safer decision.</div>',
        unsafe_allow_html=True,
    )
    render_stepper()

    st.markdown(
        '<div class="home-trust">'
        '<span><strong>TEXT</strong> messages</span><span><strong>URL</strong> links</span>'
        '<span><strong>IMAGE</strong> screenshots</span><span><strong>PDF</strong> documents</span>'
        '<span><strong>QR</strong> scans</span><span><strong>VIDEO</strong> frames + audio</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    with st.container(horizontal=True, wrap=True, horizontal_alignment="center", vertical_alignment="center", gap="small", key="home-actions"):
        if st.button("Start an investigation →", width="stretch", type="primary", key="goto_analyze"):
            st.session_state.page = "Analyze"
            st.session_state.scroll_to_scanners = True
            st.session_state.demo_mode = False
            st.rerun()
        if st.button("Explore an offline sample result", width="stretch", key="demo_result"):
            st.session_state.result = get_demo_result()
            st.session_state.mode = "Text"
            st.session_state.demo_mode = True
            st.session_state.page = "Analyze"
            st.rerun()
