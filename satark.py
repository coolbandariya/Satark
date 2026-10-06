# 🧰 CORE PYTHON / SYSTEM
import os
from pathlib import Path
import re
import random
import time
import math
import json
import html
from datetime import datetime
from zoneinfo import ZoneInfo

# SATARK always displays timestamps in India Standard Time, regardless
# of what timezone the server the app happens to be running on is set
# to (e.g. most cloud hosts default to UTC, which made History/PDF
# timestamps look "wrong" — several hours off from local time).
IST = ZoneInfo("Asia/Kolkata")


def now_ist():
    return datetime.now(IST)

# 🌐 WEB / URL HANDLING
from urllib.error import HTTPError, URLError

# 🤖 AI / WEB APP
import streamlit as st
import streamlit.components.v1 as components

# 📄 FILE & IMAGE PROCESSING

# 📑 PDF GENERATION
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer,
    Table, TableStyle, PageBreak, KeepTogether
)
from reports import make_pdf_report
from satark_utils import safe_text, clean_json_text, normalize_check_value, check_class, THREAT_CHECKS, OFFICIAL_VERIFICATION_SOURCES
from radar_background import render_radar_background
from stepper_component import render_stepper
from analysis_engine import (
    clamp_score,
    is_scam_claim,
    normalize_result_consistency,
    risk_label,
    build_fallback_threat_analysis,
    build_final_conclusion,
    calibrate_confidence,
    normalize_result,
)
from input_processing import (
    MAX_PDF_BYTES,
    MAX_IMAGE_BYTES,
    _uploaded_size,
    extract_pdf_text,
    image_to_data_url,
    images_to_data_urls,
    uploaded_fingerprint,
    single_file_fingerprint,
)


# ============================================================
# SATARK — Smart AI Threat Analysis & Risk Knowledge
# Streamlit entry point; feature modules are kept separate where practical
#
# Keeps the original SATARK analysis flow, while adding:
# - automatic Groq model discovery
# - resilient model selection based on provider discovery
# - improved result presentation
# - session history + report export
# - Scam Challenge
# - SATARK Academy
# - Classroom Mode
# - evidence / confidence / actions
# - privacy-first session storage
#
# CHANGES IN THIS VERSION:
# 1. calibrate_confidence() no longer force-floors confidence to 95-99.99%.
#    It now reports a value that actually reflects model + evidence strength,
#    across the full 0-100 range.
# 2. render_result() color-codes the confidence metric (red/amber/green)
#    so low-confidence results are visually distinct.
# 3. VISION_MODEL_PREFERENCES is now a real fallback chain instead of a
#    single hardcoded model; analyze_with_groq tries each in order instead
#    of giving up after the first failure.
# 4. is_scam_claim / normalize_result_consistency now trust the model's
#    explicit threat_category field first, and only fall back to regex
#    parsing of prose when the category is missing/ambiguous. This makes
#    scam/phishing detection less fragile to wording changes.
# 5. SYSTEM_PROMPT's confidence instruction is now explicit about using the
#    full 0-100 range honestly instead of defaulting high.
# 6. NEW: Video scanner mode. Videos are analyzed by extracting a handful of
#    representative frames (via OpenCV) and, when ffmpeg/moviepy is available,
#    transcribing the audio track (via Groq Whisper) so speech-based scam
#    signals aren't missed. Frames + transcript are fed into the same
#    analyze_with_groq pipeline used for images/text.
# ============================================================

st.set_page_config(
    page_title="SATARK — AI Threat Analyzer",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ----------------------------- CSS ----------------------------

st.markdown(
    "<style>" + Path(__file__).with_name("styles.css").read_text(encoding="utf-8") + "</style>",
    unsafe_allow_html=True,
)

# Full-screen OGL radar backdrop; content remains above it via CSS z-index.
render_radar_background()

# --------------------------- Helpers --------------------------

def analyze_with_groq(client, content, mode, role, image_data_urls=None, available_models=None):
    """Run a SATARK analysis using an appropriate Groq model.

    Vision requests now try each model in VISION_MODEL_PREFERENCES in order
    instead of a single hardcoded model, so a deprecated/inaccessible vision
    model no longer breaks image/QR/video analysis entirely. Text scans keep
    the existing SATARK text-model fallback chain. Video mode reuses the
    vision pipeline: frames are converted to data URLs before this function
    is called, exactly like the Image mode.

    The model-list endpoint is treated as a hint only: if the key can call the
    model successfully, SATARK proceeds even when model discovery is incomplete.
    """
    available_models = available_models or set()
    image_data_urls = list(image_data_urls or [])

    if len(image_data_urls) > 6:
        image_data_urls = image_data_urls[:6]

    user_prompt = f"""
Analysis type: {mode}
User profile: {role}

Analyze this content carefully:
{content}

Return a complete SATARK result using the required JSON schema. Do not omit
fields. For threat_analysis, use exactly one of: Detected, Needs review,
Not detected, Low, Medium, High.
"""

    def call(model, repair=False):
        common = {
            "model": model,
            "temperature": 0 if repair else 0.1,
            "max_tokens": 900 if not repair else 800,
            "response_format": {"type": "json_object"},
        }

        if image_data_urls:
            # Respect per-model image-count limits (e.g. Qwen accepts at most
            # 3 images per request) instead of sending every frame/image and
            # letting the API reject the whole call.
            per_model_limit = VISION_MODEL_IMAGE_LIMITS.get(model, len(image_data_urls))
            urls_for_model = image_data_urls[:per_model_limit]
            multimodal_content = [{"type": "text", "text": user_prompt}]
            for image_url in urls_for_model:
                multimodal_content.append({
                    "type": "image_url",
                    "image_url": {"url": image_url},
                })
            common["messages"] = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": multimodal_content},
            ]
            common["reasoning_effort"] = "none"
        else:
            common["messages"] = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ]

        return client.chat.completions.create(**common)

    if image_data_urls:
        # Try every configured vision model in order rather than only the
        # first one. This is the fallback chain fix — previously the loop
        # below would `break` after a single failure for image requests.
        discovered_first = [m for m in VISION_MODEL_PREFERENCES if m in available_models]
        undiscovered_fallbacks = [m for m in VISION_MODEL_PREFERENCES if m not in available_models]
        candidates = discovered_first + undiscovered_fallbacks
    else:
        discovered_first = [m for m in TEXT_MODEL_PREFERENCES if m in available_models]
        undiscovered_fallbacks = [m for m in TEXT_MODEL_PREFERENCES if m not in available_models]
        candidates = discovered_first + undiscovered_fallbacks

    errors = []
    rate_limited = False

    for model in candidates:
        try:
            response = call(model)
            raw = response.choices[0].message.content or ""

            # Groq normally returns a string. Be defensive if an SDK version
            # exposes structured content instead.
            if not isinstance(raw, str):
                if isinstance(raw, list):
                    raw = "".join(
                        item.get("text", "") if isinstance(item, dict) else str(item)
                        for item in raw
                    )
                else:
                    raw = str(raw)

            raw = raw.strip()
            if not raw:
                raise RuntimeError("The AI model returned an empty response.")

            try:
                parsed = json.loads(clean_json_text(raw))
            except (json.JSONDecodeError, TypeError, ValueError) as parse_error:
                # JSON mode should make this uncommon. If a provider/SDK still
                # returns malformed content, perform one controlled repair call
                # with JSON mode enabled instead of falling through to another
                # unrelated model.
                repair_prompt = (
                    "Convert the following SATARK analysis into one valid JSON object. "
                    "Return ONLY JSON. Use exactly these top-level keys: "
                    "risk_score, confidence, threat_category, verdict, summary, "
                    "key_indicators, recommendations, scam_pattern, threat_analysis, "
                    "final_conclusion.\n\n"
                    + raw
                )
                original_prompt = user_prompt
                user_prompt = repair_prompt
                try:
                    repair_response = call(model, repair=True)
                finally:
                    user_prompt = original_prompt

                repaired = repair_response.choices[0].message.content or ""
                if not isinstance(repaired, str):
                    repaired = str(repaired)
                repaired = repaired.strip()
                if not repaired:
                    raise RuntimeError("The AI model returned an empty JSON repair response.")
                parsed = json.loads(clean_json_text(repaired))
                raw = repaired

            if not isinstance(parsed, dict):
                raise RuntimeError("The AI model returned JSON, but it was not a JSON object.")

            result = normalize_result(parsed, raw, model)
            result["scam_pattern"] = safe_text(
                parsed.get("scam_pattern", result.get("threat_category", "Needs review")),
                result.get("threat_category", "Needs review"),
            )
            return normalize_result_consistency(result)

        except Exception as exc:
            # Classify rate limits before discarding provider details. SDK errors
            # can include request metadata, so never return their raw text to users.
            error_text = str(exc).lower()
            rate_limited = rate_limited or "rate_limit_exceeded" in error_text or "request too large" in error_text
            errors.append(f"{model}: {type(exc).__name__}")
            # Move on to the next candidate model instead of giving up
            # immediately — this applies to text, image and video requests now.
            continue

    detail = "Provider requests failed for the configured models. Check the server logs and provider status for diagnostics."
    kind = "image/QR/video" if image_data_urls else "text"

    if image_data_urls:
        hint = (
            "\n\nThis looks like a Groq rate-limit (tokens-per-minute) issue on the free/on-demand "
            "tier rather than a broken model. Wait a minute and try again with fewer or smaller "
            "images, or upgrade the Groq account tier."
        ) if rate_limited else ""
        raise RuntimeError(
            "SATARK could not complete the visual analysis with any configured "
            "vision model (tried: " + ", ".join(candidates) + "). Please verify "
            "that this Groq API key/project has access to at least one supported "
            "vision model and try again.\n" + detail + hint
        )

    raise RuntimeError(
        f"SATARK could not complete the {kind} analysis with any configured Groq model.\n{detail}"
    )


# ---------------------- UI/result helpers ----------------------
def render_threat_analysis(result):
    rows = []
    for check in THREAT_CHECKS:
        value = safe_text(result.get("threat_analysis", {}).get(check, "Needs review"), "Needs review")
        cls = check_class(value)
        icon = "✖" if cls == "check-clear" else "✓" if cls == "check-detected" else "•"
        rows.append(f'<tr><td>{html.escape(check)}</td><td class="{cls}">{icon} {html.escape(value)}</td></tr>')
    table = (
        '<table class="report-table"><thead><tr><th>Security Check</th><th>Result</th></tr></thead>'
        '<tbody>' + ''.join(rows) + '</tbody></table>'
    )
    legend = (
        '<div class="status-legend">'
        '<div class="status-legend-title">How to read the results</div>'
        '<span class="status-item"><span class="status-detected">✓ Detected</span> — sufficient evidence that the indicator is present.</span>'
        '<span class="status-item"><span class="status-review">• Needs review</span> — evidence is ambiguous or insufficient; verify it manually.</span>'
        '<span class="status-item"><span class="status-clear">✖ Not detected</span> — no meaningful evidence of that indicator was found.</span>'
        '</div>'
    )
    st.markdown(f'<section class="report-section"><h3>🔎 Threat Analysis</h3>{table}{legend}</section>', unsafe_allow_html=True)


def render_verification_sources(result):
    rows=[]
    for item in result.get("verification_sources", OFFICIAL_VERIFICATION_SOURCES):
        source=html.escape(safe_text(item.get("source")))
        purpose=html.escape(safe_text(item.get("purpose")))
        website=safe_text(item.get("website"))
        safe_href=html.escape(website, quote=True)
        safe_label=html.escape(website)
        rows.append(f'<tr><td>{source}</td><td>{purpose}</td><td><a class="source-link" href="{safe_href}" target="_blank">{safe_label}</a></td></tr>')
    table=(
        '<table class="report-table"><thead><tr><th>Source</th><th>Purpose</th><th>Official Website</th></tr></thead>'
        '<tbody>'+''.join(rows)+'</tbody></table>'
    )
    st.markdown(f'<section class="report-section"><h3>📚 Official Verification Sources</h3>{table}</section>', unsafe_allow_html=True)


def confidence_css_class(confidence):
    """Color-code the confidence metric so low-confidence results are visually
    distinct instead of looking identical to high-confidence ones."""
    if confidence >= 85:
        return "safe"
    if confidence >= 50:
        return "caution"
    return "critical"


def render_result(result):
    score = clamp_score(result.get("risk_score",50))
    label, css = risk_label(score, result.get("threat_category", ""))
    indicators = result.get("key_indicators", [])
    recs = result.get("recommendations", [])
    confidence = float(result.get("confidence",70.0))
    conf_css = confidence_css_class(confidence)
    category = html.escape(result.get("threat_category","Needs review"))
    verdict = html.escape(result.get("verdict","Manual review recommended."))
    pattern = html.escape(result.get("scam_pattern", category))

    st.markdown('<div class="result">', unsafe_allow_html=True)
    st.markdown('<div class="result-head">🛡️ SATARK Security Report</div><div class="eyebrow">Evidence-first AI assessment • advisory, not a guarantee</div>', unsafe_allow_html=True)
    a,b,c,d = st.columns(4)
    with a: st.markdown(f'<div class="metric"><div class="metric-label">Threat level</div><div class="metric-value {css}">{label}</div></div>',unsafe_allow_html=True)
    with b: st.markdown(f'<div class="metric"><div class="metric-label">Risk score</div><div class="metric-value">{score}/100</div></div>',unsafe_allow_html=True)
    with c: st.markdown(f'<div class="metric"><div class="metric-label">Pattern</div><div class="metric-value" style="font-size:1rem">{pattern}</div></div>',unsafe_allow_html=True)
    with d: st.markdown(f'<div class="metric"><div class="metric-label">AI confidence</div><div class="metric-value {conf_css}">{confidence:.2f}%</div></div>',unsafe_allow_html=True)
    st.markdown(f'<div class="bar"><div style="width:{score}%"></div></div>',unsafe_allow_html=True)
    if confidence < 50:
        st.info("ℹ️ Confidence is low — the evidence found was limited or ambiguous. Treat this result as a starting point, not a final answer, and verify manually.")
    st.markdown(f'<div class="verdict"><strong>Final verdict</strong><br>{verdict}</div>',unsafe_allow_html=True)

    if result.get("summary"):
        st.markdown("### 🔎 What SATARK found")
        st.markdown(f'<p style="color:#e4e4ea;line-height:1.8">{html.escape(result["summary"])}</p>', unsafe_allow_html=True)

    left,right = st.columns(2)
    with left:
        st.markdown('<div class="evidence"><strong>🧩 Evidence detected</strong>',unsafe_allow_html=True)
        if indicators:
            for item in indicators:
                st.markdown(f'<div class="evidence-item">⚠️ {html.escape(item)}</div>',unsafe_allow_html=True)
        else:
            st.markdown('<div class="evidence-item">No specific indicators were returned.</div>',unsafe_allow_html=True)
        st.markdown('</div>',unsafe_allow_html=True)
    with right:
        st.markdown('<div class="evidence"><strong>🧭 What to do now</strong>',unsafe_allow_html=True)
        if recs:
            for item in recs:
                st.markdown(f'<div class="action-item"><span>✓</span><span>{html.escape(item)}</span></div>',unsafe_allow_html=True)
        else:
            st.markdown('<div class="action-item">Review the content manually before acting.</div>',unsafe_allow_html=True)
        st.markdown('</div>',unsafe_allow_html=True)
    st.markdown('</div>',unsafe_allow_html=True)

    render_threat_analysis(result)
    render_verification_sources(result)

    conclusion = html.escape(build_final_conclusion(result))
    st.markdown(f'<section class="report-section"><h3>💡 Final Conclusion</h3><div class="conclusion-card">{conclusion}</div></section>', unsafe_allow_html=True)



def add_history(result, mode):
    if "history" not in st.session_state: st.session_state.history=[]
    entry = {
        "time": now_ist().strftime("%d %b %Y, %I:%M %p") + " IST",
        "mode": mode,
        "score": clamp_score(result.get("risk_score",50)),
        "category": result.get("threat_category","Needs review"),
        "verdict": result.get("verdict",""),
        "result": result,
    }
    st.session_state.history.insert(0,entry)
    st.session_state.history=st.session_state.history[:20]



# ==============================================================
# SCAM CHALLENGE v2 — GAME ENGINE (100 levels x 10 questions)
# Integrated module: CSS, question generators, game state,
# and render functions for the in-app Scam Challenge page.
# ==============================================================

from scam_challenge import (
    SC_CSS,
    sc_init_state,
    render_scam_challenge,
)


def init_state():
    defaults={
        "mode":"Text","result":None,"history":[],"page":"Home",
        "challenge_index":0,"challenge_score":0,"challenge_answered":False,
        "available_models":set(),"text_model":None,"vision_model":None,
        "last_input_fingerprint":"","analysis_request_id":"",
    }
    for k,v in defaults.items():
        if k not in st.session_state: st.session_state[k]=v
init_state()
sc_init_state()  # Scam Challenge v2 session-state defaults

# --------------------------- Sidebar ---------------------------
with st.sidebar:
    st.markdown('<div class="brand"><div class="brand-logo">SATARK <span class="brand-dot">◦</span></div><div class="brand-tag">Smart AI Threat Analysis & Risk Knowledge</div></div>',unsafe_allow_html=True)
    st.markdown('<div class="side-label">Navigate</div>',unsafe_allow_html=True)
    for page,label in [("Home","🏠 Home"),("Analyze","🔎 Check something"),("History","🕘 History"),("Challenge","🎯 Scam Challenge"),("Academy","🎓 SATARK Academy"),("Classroom","👨‍🏫 Classroom Mode")]:
        if st.button(label,key=f"nav_{page}",use_container_width=True): st.session_state.page=page; st.rerun()
    st.markdown('<div class="side-label">API configuration</div>',unsafe_allow_html=True)
    env_key=os.getenv("GROQ_API_KEY","")
    api_key=st.text_input("🔑 Groq API Key",value=env_key,type="password",placeholder="Paste your Groq API key",help="Kept in the Streamlit session; not intentionally written to disk by SATARK.")
    if api_key:
        if st.button("Check AI connection",key="check_ai",use_container_width=True):
            try:
                client=get_client(api_key); available=discover_models(client)
                st.session_state.available_models=available
                st.session_state.text_model=choose_model(available,TEXT_MODEL_PREFERENCES)
                st.session_state.vision_model=choose_model(available,VISION_MODEL_PREFERENCES)
                if st.session_state.text_model and st.session_state.vision_model: st.success("AI connected • text + vision available")
                elif st.session_state.text_model: st.warning("AI connected • text available, no vision model exposed to this key")
                else: st.error("API key is accepted but no supported SATARK text model was found.")
            except Exception as exc: st.error(f"Could not check Groq ({type(exc).__name__}). Verify the key, network, and provider status.")
    st.markdown('<div class="side-label">Personalization</div>',unsafe_allow_html=True)
    role=st.selectbox("👤 Who are you?",["Student","Teacher","Working professional","Parent / Guardian","Senior user","Security learner"],index=0)
    st.markdown('<div class="privacy"><strong>🔒 Privacy first</strong><br>SATARK keeps history only in this Streamlit session. Submitted content is not intentionally saved to disk by this app. Content is sent to Groq only when you analyze it. Avoid passwords, private keys and secrets.</div>',unsafe_allow_html=True)

# ---------------------------- Hero -----------------------------
st.markdown('<section class="hero"><div class="pill">AI SECURITY • EXPLAIN • LEARN • PROTECT</div><h1><span class="hero-primary">Think it’s a scam?</span><br><span class="hero-secondary">Let <span class="hero-brand">SATARK</span> check it.</span></h1><p><strong>Paste a message, inspect a link, upload a screenshot, video, or analyze a PDF.</strong><br>SATARK explains the risk in simple language and shows the evidence behind its assessment.</p></section>',unsafe_allow_html=True)

# --------------------------- Pages -----------------------------
# --------------------------- Pages -----------------------------

if st.session_state.page == "Home":

    st.markdown(
        '<div class="home-intro">'
        '<div class="home-intro-title">Security analysis without the noise.</div>'
        '<div class="home-intro-copy">'
        'Start with what you received, not with a complicated security dashboard. '
        'SATARK turns suspicious content into clear evidence, practical next steps, '
        'and a result you can understand.'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="home-grid">'
        '<div class="home-card"><div class="home-card-index">01 / CHECK</div>'
        '<div class="home-card-title">Messages & links</div>'
        '<div class="home-card-copy">Inspect suspicious text, URLs, phishing patterns and social-engineering pressure.</div></div>'
        '<div class="home-card"><div class="home-card-index">02 / SEE</div>'
        '<div class="home-card-title">Images & documents</div>'
        '<div class="home-card-copy">Review screenshots, QR-related images and text-based PDFs for visible warning signs.</div></div>'
        '<div class="home-card"><div class="home-card-index">03 / LEARN</div>'
        '<div class="home-card-title">Understand the result</div>'
        '<div class="home-card-copy">See evidence, confidence, recommendations and the reasoning behind the assessment.</div></div>'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="section-title" style="margin-top:2rem;">How SATARK works</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-copy">A quick four-step guide before you start analyzing suspicious content.</div>', unsafe_allow_html=True)
    render_stepper()

    st.markdown(
        '<div class="home-trust">'
        '<span><strong>TEXT</strong> analysis</span>'
        '<span><strong>URL</strong> safety checks</span>'
        '<span><strong>IMAGE</strong> vision</span>'
        '<span><strong>PDF</strong> extraction</span>'
        '<span><strong>VIDEO</strong> frame + audio</span>'
        '<span><strong>SESSION</strong> history only</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="analyze">', unsafe_allow_html=True)

    if st.button(
        "Start a security check  →",
        use_container_width=True,
        type="primary",
        key="goto_analyze"
    ):
        st.session_state.page = "Analyze"
        st.session_state.scroll_to_scanners = True
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)


elif st.session_state.page == "Analyze":

    # ==========================================================
    # AUTO-SCROLL TO SCANNER SECTION
    # ==========================================================

    # Invisible anchor placed immediately before scanner cards
    st.markdown(
        '<div id="satark-scanner-anchor"></div>',
        unsafe_allow_html=True
    )

    # Scroll to scanner section only after clicking
    # "Let SATARK Check It" from the Home page.
    if st.session_state.get("scroll_to_scanners", False):

        import streamlit.components.v1 as components

        components.html(
            """
            <script>
            setTimeout(function() {

                const el =
                    window.parent.document.getElementById(
                        'satark-scanner-anchor'
                    );

                if (el) {
                    el.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }

            }, 300);
            </script>
            """,
            height=0,
        )

        st.session_state.scroll_to_scanners = False


    # ==========================================================
    # SCANNER SELECTION
    # ==========================================================

    st.markdown(
        '<div class="section-title">What do you want to check?</div>'
        '<div class="section-copy">'
        'Choose a scanner. Your original six SATARK modes remain available, plus Video.'
        '</div>',
        unsafe_allow_html=True
    )

    scanner_rows = [
        [
            ("Text", "💬", "Messages, posts and suspicious text"),
            ("URL", "🔗", "Websites and suspicious links"),
            ("Image", "🖼️", "Screenshots and images")
        ],
        [
            ("PDF", "📄", "Text-based documents"),
            ("QR", "▣", "QR screenshots and QR-related images"),
            ("Video", "🎬", "Suspicious clips, reels and voice-call recordings")
        ]
    ]

    for row in scanner_rows:

        cols = st.columns(3)

        for col, (name, icon, copy) in zip(cols, row):

            with col:

                active = st.session_state.mode == name

                st.markdown(
                    f'''
                    <div class="scanner {"active" if active else ""}">
                        <div class="scanner-icon">{icon}</div>
                        <div class="scanner-title">{name}</div>
                        <div class="scanner-copy">{copy}</div>
                    </div>
                    ''',
                    unsafe_allow_html=True
                )

                if st.button(
                    f"Use {name}",
                    key=f"scanner_{name}",
                    use_container_width=True
                ):
                    st.session_state.mode = name
                    st.session_state.result = None
                    st.session_state.last_input_fingerprint = ""
                    st.session_state.analysis_request_id = ""

                    # Unique trigger for EVERY scanner click.
                    # This makes the auto-scroll repeat indefinitely.
                    st.session_state.scroll_to_input_trigger = (
                        st.session_state.get("scroll_to_input_trigger", 0) + 1
                    )

                    st.rerun()


    # ==========================================================
    # SELECTED MODE
    # ==========================================================

    mode = st.session_state.mode


    # ==========================================================
    # AUTO-SCROLL TO INPUT SECTION
    # ==========================================================

    # Invisible anchor immediately above Security Analysis
    st.markdown(
        '<div id="satark-input-anchor"></div>',
        unsafe_allow_html=True
    )

    # A new number is generated every time one of the scanner
    # buttons is clicked. We only handle each number once, so
    # normal Streamlit reruns (typing/uploading) do not cause
    # unwanted scrolling.
    scroll_trigger = st.session_state.get(
        "scroll_to_input_trigger",
        0
    )

    handled_trigger = st.session_state.get(
        "handled_scroll_to_input_trigger",
        0
    )

    if scroll_trigger != handled_trigger:
        import streamlit.components.v1 as components

        components.html(
            f"""
            <script>
            (function() {{
                const trigger = "{scroll_trigger}";
                let attempts = 0;

                function scrollToSATARKInput() {{
                    const parentDoc = window.parent.document;

                    const el = parentDoc.getElementById(
                        "satark-input-anchor"
                    );

                    if (el) {{
                        el.scrollIntoView({{
                            behavior: "smooth",
                            block: "start"
                        }});
                        return true;
                    }}

                    return false;
                }}

                // Streamlit renders asynchronously after reruns,
                // so retry briefly until the anchor is available.
                const timer = setInterval(function() {{
                    attempts++;

                    if (
                        scrollToSATARKInput() ||
                        attempts >= 20
                    ) {{
                        clearInterval(timer);
                    }}
                }}, 100);
            }})();
            </script>
            """,
            height=0,
        )

        # Mark this trigger as handled. The next scanner click
        # creates a new trigger and therefore scrolls again.
        st.session_state.handled_scroll_to_input_trigger = (
            scroll_trigger
        )


    # ==========================================================
    # SECURITY ANALYSIS INPUT
    # ==========================================================

    st.markdown(
        f'<div class="section-title">🔎 Security Analysis</div>'
        f'<div class="section-copy">Selected: <strong>{mode}</strong></div>',
        unsafe_allow_html=True
    )

    uploaded = None
    image_data_urls = []
    video_file = None
    transcribe_audio = True


    # ==========================================================
    # TEXT
    # ==========================================================

    if mode == "Text":

        content = st.text_area(
            "Enter content",
            height=230,
            placeholder=(
                "Paste any message, post, SMS, "
                "social-media content or suspicious text here..."
            ),
            key=f"text_input_{mode}"
        )


    # ==========================================================
    # URL
    # ==========================================================

    elif mode == "URL":

        content = st.text_input(
            "Website URL",
            placeholder="https://example.com",
            key="url_input"
        )


    # ==========================================================
    # PDF
    # ==========================================================

    elif mode == "PDF":

        uploaded = st.file_uploader(
            "Upload PDF",
            type=["pdf"],
            max_upload_size=25,
            help="Best results come from text-based PDFs. Maximum size: 25 MB.",
            key="pdf_input"
        )

        content = ""


    # ==========================================================
    # VIDEO
    # ==========================================================

    elif mode == "Video":

        video_file = st.file_uploader(
            "Upload video",
            type=[
                "mp4",
                "mov",
                "avi",
                "webm",
                "mkv",
                "m4v"
            ],
            accept_multiple_files=False,
            max_upload_size=200,
            help=(
                "SATARK extracts a handful of representative "
                "frames and, when possible, transcribes the audio. "
                "Max 200 MB."
            ),
            key="video_input"
        )

        transcribe_audio = st.checkbox(
            "Also transcribe and analyze the audio track "
            "(recommended for voice-call/scam-call videos)",
            value=True,
            key="video_transcribe_toggle"
        )

        content = (
            "Analyze the sampled video frames "
            "(and transcript, if provided) together "
            "as one investigation."
        )

        if video_file is not None:
            st.video(video_file)

        uploaded = None


    # ==========================================================
    # IMAGE / QR
    # ==========================================================

    else:

        uploaded = st.file_uploader(
            "Upload image",
            type=[
                "png",
                "jpg",
                "jpeg",
                "webp"
            ],
            accept_multiple_files=True,
            max_upload_size=10,
            help=(
                "Upload one or more screenshots, QR images, "
                "email screenshots or suspicious images. "
                "SATARK will analyze the selected images together."
            ),
            key=f"image_input_{mode}"
        )

        content = (
            "Analyze all supplied images together. "
            "Inspect visible text, links, logos, QR-related content, "
            "suspicious instructions, impersonation and "
            "social-engineering signals, and cross-image evidence."
        )

        if uploaded and len(uploaded) > 5:

            st.info(
                "SATARK will analyze the first 5 selected images "
                "together to keep the request reliable."
            )


    # ==========================================================
    # INPUT FINGERPRINT
    # ==========================================================

    if mode in {"Image", "QR"}:

        current_input_fingerprint = uploaded_fingerprint(uploaded)

    elif mode == "Video":

        current_input_fingerprint = single_file_fingerprint(
            video_file
        )

    else:

        current_input_fingerprint = ""


    if (
        mode in {"Image", "QR", "Video"}
        and current_input_fingerprint
        != st.session_state.get(
            "last_input_fingerprint",
            ""
        )
    ):

        st.session_state.last_input_fingerprint = (
            current_input_fingerprint
        )

        if current_input_fingerprint:

            st.session_state.result = None


    # ==========================================================
    # ANALYZE BUTTON
    # ==========================================================

    st.markdown(
        '<div class="analyze">',
        unsafe_allow_html=True
    )

    analyze_clicked = st.button(
        "🔍 Analyze with SATARK",
        use_container_width=True,
        type="primary",
        key="analyze_button"
    )

    st.markdown(
        '</div>',
        unsafe_allow_html=True
    )


    # ==========================================================
    # RUN ANALYSIS
    # ==========================================================

    if analyze_clicked:

        if not safe_text(api_key):

            st.error(
                "🔑 Enter your Groq API key in the sidebar first."
            )

            st.stop()


        try:

            # Fresh request ID for every analysis
            st.session_state.analysis_request_id = (
                hashlib.sha256(
                    f"{datetime.now().isoformat()}|{mode}"
                    .encode("utf-8")
                ).hexdigest()[:16]
            )

            st.session_state.result = None
            st.session_state.vision_model = None

            client = get_client(api_key)

            st.markdown(
                '<div class="analysis-loader" '
                'aria-label="SATARK is analyzing">'
                '<span></span></div>',
                unsafe_allow_html=True
            )


            with st.spinner(
                "SATARK is reading the content, "
                "evaluating threat patterns and "
                "building your report…"
            ):

                available = discover_models(client)

                st.session_state.available_models = available


                # ==================================================
                # PREPARE INPUT
                # ==================================================

                if mode == "Text":

                    if not safe_text(content):

                        raise ValueError(
                            "Please enter some content to analyze."
                        )

                    prepared = content[:50000]


                elif mode == "URL":

                    if not safe_text(content):

                        raise ValueError(
                            "Please enter a URL."
                        )

                    prepared = fetch_url_text(content)

                    if not prepared.strip():

                        raise ValueError(
                            "The URL returned no readable content."
                        )


                elif mode == "PDF":

                    if uploaded is None:

                        raise ValueError(
                            "Please upload a PDF."
                        )

                    prepared = extract_pdf_text(uploaded)


                elif mode == "Video":

                    if video_file is None:

                        raise ValueError(
                            "Please upload a video."
                        )


                    if not _video_dependencies_available():

                        raise RuntimeError(
                            "Video analysis needs OpenCV installed "
                            "in this environment "
                            "(pip install opencv-python-headless "
                            "--break-system-packages), then restart "
                            "the app."
                        )


                    # ----------------------------------------------
                    # Extract representative frames
                    # ----------------------------------------------

                    frames, duration, warnings = (
                        extract_video_frames(video_file)
                    )

                    image_data_urls = (
                        pil_frames_to_data_urls(frames)
                    )


                    if not image_data_urls:

                        raise ValueError(
                            "SATARK could not extract usable "
                            "frames from this video."
                        )


                    if warnings:

                        st.warning(
                            "⚠️ " + " ".join(warnings)
                        )


                    # ----------------------------------------------
                    # Audio transcription
                    # ----------------------------------------------

                    transcript = ""

                    if transcribe_audio:

                        transcript = transcribe_video_audio(
                            video_file,
                            client
                        )


                    duration_note = (
                        f"Approx. duration: "
                        f"{duration:.1f} seconds. "
                        if duration
                        else ""
                    )


                    transcript_note = (

                        f"Audio transcript:\n{transcript}"

                        if transcript

                        else
                        "Audio transcript: not available "
                        "(silent, unsupported audio, or "
                        "transcription unavailable in this "
                        "environment)."
                    )


                    prepared = (
                        f"{content}\n"
                        f"{duration_note}"
                        f"Number of sampled frames: "
                        f"{len(image_data_urls)}.\n\n"
                        f"{transcript_note}"
                    )


                else:

                    if not uploaded:

                        raise ValueError(
                            "Please upload at least one image."
                        )


                    # ----------------------------------------------
                    # Fresh image conversion
                    # ----------------------------------------------

                    image_data_urls = (
                        images_to_data_urls(
                            uploaded[:5],
                            max_images=5
                        )
                    )


                    if not image_data_urls:

                        raise ValueError(
                            "The selected image(s) "
                            "could not be read."
                        )


                    prepared = (
                        f"{content}\n"
                        f"Number of images in this "
                        f"investigation: "
                        f"{len(image_data_urls)}"
                    )


                # ==================================================
                # BUILD PROMPT
                # ==================================================

                prompt = (
                    f"User profile: {role}\n"
                    f"Scanner mode: {mode}\n\n"
                    f"{prepared}"
                )


                # ==================================================
                # GROQ ANALYSIS
                # ==================================================

                result = analyze_with_groq(
                    client,
                    prompt,
                    mode,
                    role,
                    image_data_urls,
                    available
                )


            # ======================================================
            # SAVE RESULT
            # ======================================================

            st.session_state.result = result

            add_history(
                result,
                mode
            )

            st.session_state.page = "Analyze"

            st.success(
                "SATARK analysis complete."
            )


        except (ValueError, RuntimeError) as exc:

            st.error(
                f"⚠️ {exc}"
            )


        except (HTTPError, URLError) as exc:

            st.error(
                f"⚠️ Could not fetch that URL safely ({type(exc).__name__}). "
                "Check that the URL is reachable and publicly accessible."
            )


        except Exception as exc:

            st.error(
                "⚠️ SATARK could not complete the analysis. "
                "Check your API key, internet connection, "
                "input and model access."
            )

            with st.expander(
                "Technical details"
            ):

                st.code(
                    str(exc)
                )


    # ==========================================================
    # RESULT
    # ==========================================================

    if st.session_state.result:

        render_result(
            st.session_state.result
        )

        st.download_button(
            "📄 Download PDF report",
            make_pdf_report(
                st.session_state.result,
                mode
            ),
            file_name="SATARK_security_report.pdf",
            mime="application/pdf",
            use_container_width=True
        )


# ==============================================================
# HISTORY
# ==============================================================

elif st.session_state.page == "History":

    st.markdown(
        '<div class="section-title">🕘 Scan History</div>'
        '<div class="section-copy">'
        'Session-only history. Original submitted content is not '
        'stored here; only analysis results and metadata are retained.'
        '</div>',
        unsafe_allow_html=True
    )

    if st.session_state.history:

        if st.button(
            "Clear session history",
            key="clear_history"
        ):

            st.session_state.history = []
            st.session_state.result = None
            st.rerun()


        for i, entry in enumerate(
            st.session_state.history
        ):

            score = entry["score"]

            label, css = risk_label(
                score,
                entry.get("category", "")
            )


            with st.expander(
                f"{entry['mode']} • "
                f"{entry['category']} • "
                f"{score}/100 • "
                f"{entry['time']}"
            ):

                st.markdown(
                    f'<span class="badge">{label}</span> '
                    f'<span class="badge">'
                    f'{html.escape(entry["category"])}'
                    f'</span>',
                    unsafe_allow_html=True
                )

                st.write(
                    entry["verdict"]
                )


                c1, c2 = st.columns(2)


                with c1:

                    if st.button(
                        "Open result",
                        key=f"history_open_{i}"
                    ):

                        st.session_state.result = (
                            entry["result"]
                        )

                        st.session_state.mode = (
                            entry["mode"]
                        )

                        st.session_state.page = (
                            "Analyze"
                        )

                        st.rerun()


                with c2:

                    st.download_button(
                        "📄 Export PDF",
                        make_pdf_report(
                            entry["result"],
                            entry["mode"]
                        ),
                        file_name=(
                            f"SATARK_report_{i+1}.pdf"
                        ),
                        mime="application/pdf",
                        key=f"history_dl_{i}"
                    )

    else:

        st.info(
            "No scans yet. Analyze something suspicious "
            "and it will appear here for this session."
        )


# ==============================================================
# SCAM CHALLENGE
# ==============================================================

elif st.session_state.page == "Challenge":

    # Scam Challenge v2: dedicated CSS is scoped to this page only so the
    # rest of SATARK's UI/UX (Home, Analyze, History, Academy, Classroom)
    # remains completely unchanged.
    st.markdown(SC_CSS, unsafe_allow_html=True)
    st.markdown(
        '<div class="pill" style="margin-bottom:14px">AI SECURITY • GAME • LEARN</div>',
        unsafe_allow_html=True,
    )
    render_scam_challenge()


elif st.session_state.page == "Academy":

    st.markdown(
        '<div class="section-title">🎓 SATARK Academy</div>'
        '<div class="section-copy">'
        'Learn the patterns behind the scams instead of relying '
        'on AI forever.'
        '</div>',
        unsafe_allow_html=True
    )


    lessons = [

        (
            "🎣",
            "Phishing",
            "Fake messages and pages designed to steal "
            "credentials or information."
        ),

        (
            "⏰",
            "Urgency manipulation",
            "Pressure tactics that make you act before you verify."
        ),

        (
            "👤",
            "Impersonation",
            "Attackers pretending to be banks, schools, "
            "companies, friends or officials."
        ),

        (
            "🔗",
            "Suspicious links",
            "Look-alike domains, strange paths, redirects "
            "and unexpected login pages."
        ),

        (
            "💳",
            "Payment fraud",
            "Fake fees, refunds, prizes, QR payments "
            "and requests for money."
        ),

        (
            "🔐",
            "Account takeover",
            "Attempts to obtain passwords, OTPs, recovery "
            "codes or session access."
        )

    ]


    cols = st.columns(3)


    for i, (icon, title, copy) in enumerate(
        lessons
    ):

        with cols[i % 3]:

            st.markdown(
                f'''
                <div class="feature-card">
                    <div class="feature-icon">{icon}</div>
                    <div class="feature-title">{title}</div>
                    <div class="feature-copy">{copy}</div>
                </div>
                ''',
                unsafe_allow_html=True
            )


    st.markdown(
        "### A simple rule to remember"
    )


    st.info(
        "STOP → VERIFY → ACT. If a message creates pressure, "
        "asks for secrets, or requests money, pause and verify "
        "through an independent official channel."
    )


# ==============================================================
# CLASSROOM
# ==============================================================

elif st.session_state.page == "Classroom":

    st.markdown(
        '<div class="section-title">👨‍🏫 Classroom Mode</div>'
        '<div class="section-copy">'
        'A simple teacher-facing view for using SATARK '
        'as a cyber-safety learning tool.'
        '</div>',
        unsafe_allow_html=True
    )


    history = st.session_state.history

    total = len(history)

    avg = (
        round(
            sum(x["score"] for x in history) / total
        )
        if total
        else 0
    )

    high = sum(
        1
        for x in history
        if x["score"] >= 70
    )


    a, b, c = st.columns(3)


    with a:

        st.markdown(
            f'''
            <div class="metric">
                <div class="metric-label">
                    Scans this session
                </div>
                <div class="metric-value">
                    {total}
                </div>
            </div>
            ''',
            unsafe_allow_html=True
        )


    with b:

        st.markdown(
            f'''
            <div class="metric">
                <div class="metric-label">
                    Average risk
                </div>
                <div class="metric-value">
                    {avg}/100
                </div>
            </div>
            ''',
            unsafe_allow_html=True
        )


    with c:

        st.markdown(
            f'''
            <div class="metric">
                <div class="metric-label">
                    High-risk findings
                </div>
                <div class="metric-value critical">
                    {high}
                </div>
            </div>
            ''',
            unsafe_allow_html=True
        )


    st.markdown(
        "### Suggested classroom flow"
    )


    st.markdown(
        "**1.** Give students a suspicious message.  "
        "**2.** Ask them to identify warning signs.  "
        "**3.** Run it through SATARK.  "
        "**4.** Compare the evidence.  "
        "**5.** Use Scam Challenge to reinforce the lesson."
    )


    st.markdown(
        "### Common patterns in this session"
    )


    counts = {}


    for item in history:

        key = item["category"]

        counts[key] = counts.get(key, 0) + 1


    if counts:

        for k, v in sorted(
            counts.items(),
            key=lambda x: x[1],
            reverse=True
        ):

            st.write(
                f"• **{k}** — {v} scan(s)"
            )

    else:

        st.info(
            "Run a few example scans to populate "
            "classroom statistics."
        )


# ==============================================================
# FOOTER
# ==============================================================

st.markdown(
    '<div class="footer">'
    'SATARK • Smart AI Threat Analysis & Risk Knowledge<br>'
    'AI analysis is advisory. Always verify high-impact security '
    'decisions independently.<br>'
    'Session history is temporary and does not intentionally '
    'preserve submitted source content.'
    '</div>',
    unsafe_allow_html=True
)