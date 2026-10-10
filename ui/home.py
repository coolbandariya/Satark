"""Focused home dashboard for SATARK's evidence-first investigation workflow."""
import streamlit as st
from ui.demo import get_demo_result


def render_home():
    """Render the product overview without vanity metrics or unsupported claims."""
    st.markdown(
        '<section class="workspace-hero">'
        '<div class="workspace-hero-copy">'
        '<div class="workspace-eyebrow"><span class="status-dot"></span> DIGITAL THREAT INVESTIGATION · SESSION WORKSPACE</div>'
        '<h1>Know what you\'re looking at.<br><span>Before you act.</span></h1>'
        '<p>Turn suspicious messages, links, screenshots, QR codes, PDFs and clips into a structured investigation. See the observable signals, the AI assessment and what still needs verification.</p>'
        '<div class="workspace-trust-row"><span>Evidence first</span><span>·</span><span>Explainable signals</span><span>·</span><span>Human verification</span></div>'
        '</div>'
        '<aside class="workspace-preview" aria-label="Illustrative report preview">'
        '<div class="preview-topline"><span class="preview-icon">⌁</span><span>INVESTIGATION PREVIEW</span><span class="preview-demo">SAMPLE</span></div>'
        '<div class="preview-title">Suspicious account alert</div>'
        '<div class="preview-meta">Illustrative example · not a live scan</div>'
        '<div class="preview-risk-row"><div><div class="preview-label">Assessment</div><div class="preview-risk">Needs review</div></div><div class="preview-score"><span>—</span><small>no score shown</small></div></div>'
        '<div class="preview-divider"></div>'
        '<div class="preview-signal"><span class="preview-signal-icon">↗</span><div><strong>Link present</strong><small>A URL was observed in the submitted text.</small></div><span class="preview-tag">OBSERVED</span></div>'
        '<div class="preview-signal"><span class="preview-signal-icon">!</span><div><strong>Urgency language</strong><small>Pressure to act quickly may reduce verification.</small></div><span class="preview-tag preview-tag-review">REVIEW</span></div>'
        '<div class="preview-footnote">Signals are observations, not proof of fraud.</div>'
        '</aside>'
        '</section>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<section class="workspace-method" style="margin-top:18px">'
        '<div class="workspace-method-heading"><div class="workspace-eyebrow">FLAGSHIP WORKSPACE · FIRSTLIGHT</div>'
        '<div class="workspace-heading">Investigate incidents. Preserve evidence. Respond with control.</div>'
        '<p>Coordinate evidence collection, reconstruct a timeline, challenge integrity and review response proposals before simulated execution.</p></div>'
        '</section>',
        unsafe_allow_html=True,
    )
    if st.button("Open FIRSTLIGHT Incident Command →", type="primary", use_container_width=True, key="goto_firstlight"):
        st.session_state.page = "FIRSTLIGHT"
        st.rerun()

    st.markdown(
        '<div class="workspace-section-head"><div><div class="workspace-eyebrow">SECONDARY TOOLS · SATARK THREAT ANALYSIS</div>'
        '<div class="workspace-heading">Choose what you need to investigate</div></div>'
        '<div class="workspace-section-note">No account required · History is session-only</div></div>',
        unsafe_allow_html=True,
    )

    with st.container(key="home-actions"):
        col_primary, col_secondary = st.columns([1.2, 1], gap="small")
        with col_primary:
            if st.button(
                "Start an investigation →",
                width="stretch",
                type="primary",
                key="goto_analyze",
            ):
                st.session_state.page = "Analyze"
                st.session_state.scroll_to_scanners = True
                st.session_state.demo_mode = False
                st.rerun()
        with col_secondary:
            if st.button(
                "Open the guided sample report",
                width="stretch",
                key="demo_result",
            ):
                st.session_state.result = get_demo_result()
                st.session_state.mode = "Text"
                st.session_state.demo_mode = True
                st.session_state.page = "Analyze"
                st.rerun()

    st.markdown(
        '<div class="workspace-capabilities">'
        '<div class="capability-card"><div class="capability-icon">Aa</div><div class="capability-title">Text & messages</div><p>Inspect urgency, credential requests, impersonation cues and extracted indicators.</p><div class="capability-foot">TEXT</div></div>'
        '<div class="capability-card"><div class="capability-icon">↗</div><div class="capability-title">Links & websites</div><p>Review public URL structure and safely inspect eligible page text.</p><div class="capability-foot">URL</div></div>'
        '<div class="capability-card"><div class="capability-icon">▧</div><div class="capability-title">Images & QR codes</div><p>Analyze screenshots and QR-related images without assuming appearance proves authenticity.</p><div class="capability-foot">IMAGE · QR</div></div>'
        '<div class="capability-card"><div class="capability-icon">▤</div><div class="capability-title">Documents & clips</div><p>Extract supported PDF text and sample video frames, with optional audio transcription.</p><div class="capability-foot">PDF · VIDEO</div></div>'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<section class="workspace-method">'
        '<div class="workspace-method-heading"><div class="workspace-eyebrow">THE SATARK METHOD</div>'
        '<div class="workspace-heading">An assessment you can inspect</div>'
        '<p>AI can help interpret a threat, but it should not invent the evidence. SATARK keeps observations separate from conclusions.</p></div>'
        '<div class="method-steps">'
        '<div class="method-step"><span>01</span><div><strong>Collect</strong><p>Extract bounded, relevant signals from submitted content.</p></div></div>'
        '<div class="method-step"><span>02</span><div><strong>Investigate</strong><p>Review indicators and supported checks.</p></div></div>'
        '<div class="method-step"><span>03</span><div><strong>Challenge</strong><p>Notice uncertainty, missing context and unsupported claims.</p></div></div>'
        '<div class="method-step"><span>04</span><div><strong>Decide</strong><p>Read the report and verify consequential findings independently.</p></div></div>'
        '</div></section>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="workspace-disclaimer"><span class="disclaimer-mark">i</span><div><strong>Built for informed triage, not automatic truth.</strong><p>Risk scores are heuristic summaries, model confidence is not a calibrated probability, and a missing signal is not proof that content is safe. Avoid submitting passwords, OTPs, private keys or unnecessary personal data.</p></div></div>',
        unsafe_allow_html=True,
    )
