"""Premium editorial home dashboard for SATARK + FIRSTLIGHT."""
import streamlit as st
from ui.demo import get_demo_result


def render_home():
    """Render a polished, evidence-first product landing workspace."""
    st.markdown(
        '<section class="ih-hero">'
        '<div class="ih-hero-glow" aria-hidden="true"></div>'
        '<div class="ih-hero-copy">'
        '<div class="ih-kicker"><span class="ih-live-dot"></span> DIGITAL TRUST · INCIDENT INTELLIGENCE</div>'
        '<h1>Pause the panic.<br><span>Find the signal.</span></h1>'
        '<p class="ih-lede">A calmer way to investigate suspicious digital content. Turn messages, links, screenshots, QR codes and incident logs into clear signals, evidence you can inspect, and next steps you can control.</p>'
        '<div class="ih-hero-actions"><span class="ih-proof"><b>01</b> Observe</span><span class="ih-proof"><b>02</b> Verify</span><span class="ih-proof"><b>03</b> Decide</span></div>'
        '<div class="ih-micro-note"><span class="ih-check">✓</span> Evidence-led · Explainable · Human-reviewed</div>'
        '</div>'
        '<aside class="ih-console" aria-label="Illustrative investigation report">'
        '<div class="ih-console-top"><div class="ih-console-brand"><span class="ih-console-mark">S</span><div><b>SATARK</b><small>THREAT INTELLIGENCE</small></div></div><span class="ih-demo-chip">SAMPLE REPORT</span></div>'
        '<div class="ih-console-divider"></div>'
        '<div class="ih-console-eyebrow">INCOMING MESSAGE <span>EXAMPLE 001</span></div>'
        '<div class="ih-message"><div class="ih-avatar">!</div><div><b>Account security notice</b><p>Your access will be suspended. Verify your account immediately.</p><small>Illustrative text · not a live scan</small></div></div>'
        '<div class="ih-signal-heading"><span>OBSERVABLE SIGNALS</span><span>02 FOUND</span></div>'
        '<div class="ih-signal"><span class="ih-signal-icon ih-amber">↗</span><div><b>Urgency language</b><small>Pressure to act before verifying</small></div><span class="ih-signal-status">REVIEW</span></div>'
        '<div class="ih-signal"><span class="ih-signal-icon ih-violet">⌁</span><div><b>Account action requested</b><small>Verify the destination independently</small></div><span class="ih-signal-status">CHECK</span></div>'
        '<div class="ih-console-foot"><span class="ih-foot-dot"></span> Signals are observations — not proof of fraud.</div>'
        '</aside>'
        '<div class="ih-orbit ih-orbit-one" aria-hidden="true">↗</div><div class="ih-orbit ih-orbit-two" aria-hidden="true">◈</div>'
        '</section>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<section class="ih-focus">'
        '<div class="ih-focus-index">01 / FLAGSHIP WORKSPACE</div>'
        '<div class="ih-focus-main"><div class="ih-focus-title">FIRSTLIGHT <span>Incident Command</span></div>'
        '<p>Reconstruct what happened, preserve evidence integrity, correlate event patterns and review response proposals before simulated execution.</p></div>'
        '<div class="ih-focus-aside"><span class="ih-status-pill"><span></span> READY TO EXPLORE</span><div>Evidence timeline<br>Integrity checks<br>Auditable decisions</div></div>'
        '</section>',
        unsafe_allow_html=True,
    )
    if st.button("Enter FIRSTLIGHT Incident Command  →", type="primary", use_container_width=True, key="goto_firstlight"):
        st.session_state.page = "FIRSTLIGHT"
        st.rerun()

    st.markdown(
        '<section class="ih-section-head"><div><div class="ih-kicker">02 / THE TOOLKIT</div>'
        '<h2>One workspace.<br><span>More ways to verify.</span></h2></div>'
        '<p>Start with the artifact you have. Get a structured assessment without confusing a model’s opinion with verified fact.</p></section>'
        '<div class="ih-capability-grid">'
        '<article class="ih-capability ih-capability-featured"><div class="ih-cap-top"><span>01</span><span class="ih-cap-icon">⌘</span></div><h3>Message & text analysis</h3><p>Spot pressure tactics, credential requests, impersonation cues and suspicious patterns in messages.</p><div class="ih-cap-tags"><span>TEXT</span><span>SMS</span><span>EMAIL</span></div></article>'
        '<article class="ih-capability"><div class="ih-cap-top"><span>02</span><span class="ih-cap-icon">↗</span></div><h3>Links & websites</h3><p>Inspect URL structure and eligible page text while keeping uncertainty visible.</p><div class="ih-cap-tags"><span>URL</span><span>DOMAIN</span></div></article>'
        '<article class="ih-capability"><div class="ih-cap-top"><span>03</span><span class="ih-cap-icon">▧</span></div><h3>Images & QR codes</h3><p>Review embedded text and QR-related content without treating polished visuals as proof.</p><div class="ih-cap-tags"><span>IMAGE</span><span>QR</span></div></article>'
        '<article class="ih-capability"><div class="ih-cap-top"><span>04</span><span class="ih-cap-icon">▤</span></div><h3>Documents & video</h3><p>Extract supported PDF text and sample video frames, with optional audio transcription.</p><div class="ih-cap-tags"><span>PDF</span><span>VIDEO</span></div></article>'
        '</div>',
        unsafe_allow_html=True,
    )

    with st.container(key="home-actions"):
        col_primary, col_secondary = st.columns([1.15, 1], gap="small")
        with col_primary:
            if st.button("Start an investigation  →", width="stretch", type="primary", key="goto_analyze"):
                st.session_state.page = "Analyze"
                st.session_state.scroll_to_scanners = True
                st.session_state.demo_mode = False
                st.rerun()
        with col_secondary:
            if st.button("Explore a guided sample report", width="stretch", key="demo_result"):
                st.session_state.result = get_demo_result()
                st.session_state.mode = "Text"
                st.session_state.demo_mode = True
                st.session_state.page = "Analyze"
                st.rerun()

    st.markdown(
        '<section class="ih-method"><div class="ih-method-head"><div class="ih-kicker">03 / HOW IT WORKS</div>'
        '<h2>From uncertainty<br>to <span>informed action.</span></h2>'
        '<p>Built to make the reasoning inspectable — not to make decisions on your behalf.</p></div>'
        '<div class="ih-method-steps">'
        '<div class="ih-method-step"><span>01</span><div><b>Collect</b><p>Extract bounded, relevant signals from the content you submit.</p></div><i>↘</i></div>'
        '<div class="ih-method-step"><span>02</span><div><b>Investigate</b><p>Separate observable evidence from model-generated interpretation.</p></div><i>↘</i></div>'
        '<div class="ih-method-step"><span>03</span><div><b>Challenge</b><p>Identify missing context, uncertainty and claims that need checking.</p></div><i>↘</i></div>'
        '<div class="ih-method-step"><span>04</span><div><b>Decide</b><p>Review recommendations and independently verify consequential findings.</p></div><i>✓</i></div>'
        '</div></section>'
        '<section class="ih-trust"><div class="ih-trust-mark">i</div><div><div class="ih-trust-title">Designed for informed triage — not automatic truth.</div>'
        '<p>Risk scores are heuristic summaries; model confidence is not a calibrated probability. A missing signal does not prove content is safe. Avoid submitting passwords, OTPs, private keys or unnecessary personal data.</p></div><span class="ih-trust-label">USE WITH JUDGMENT</span></section>'
        '<footer class="ih-footer"><span>SATARK <b>×</b> FIRSTLIGHT</span><span>Clarity over panic. Evidence over assumption.</span></footer>',
        unsafe_allow_html=True,
    )
