# 🧰 CORE PYTHON / SYSTEM
import os
import re
import random
import time
import math
import json
import base64
import hashlib
import socket
import ipaddress
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
from html.parser import HTMLParser
from urllib.parse import urlparse
from urllib.request import Request, urlopen, HTTPRedirectHandler, build_opener
from urllib.error import HTTPError, URLError

# 🤖 AI / WEB APP
import streamlit as st
import streamlit.components.v1 as components
from groq import Groq

# 📄 FILE & IMAGE PROCESSING
from pypdf import PdfReader
from PIL import Image

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


# ============================================================
# SATARK — Smart AI Threat Analysis & Risk Knowledge
# FINAL single-file Streamlit application
#
# Keeps the original SATARK analysis flow, while adding:
# - automatic Groq model discovery
# - resilient vision-model selection (now with fallback chain)
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
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&family=Sora:wght@500;600;700;800&display=swap');

:root {
    --bg:#050505;
    --surface:#111113;
    --surface2:#18181b;
    --line:rgba(255,255,255,.10);
    --line2:rgba(255,255,255,.16);
    --text:#f7f7f9;
    --soft:#e1e1e6;
    --muted:#b4b4bd;
    --violet:#a99cff;
    --violet2:rgba(155,140,255,.13);
    --safe:#30d158;
    --warn:#ffb340;
    --danger:#ff453a;
}

*{box-sizing:border-box}

html,body,[class*="css"]{
    font-family:"Manrope",sans-serif;
}

body{
    background:var(--bg);
    color:var(--text);
}

h1,h2,h3,h4,h5,h6{
    color:#f5f5f7!important;
}

div[data-testid="stMarkdownContainer"] p,
div[data-testid="stMarkdownContainer"] li{
    color:#e2e2e8!important;
}

div[data-testid="stCaptionContainer"]{
    color:#c8c8d1!important;
}

a{
    color:#a99cff;
}

.stApp{
    min-height:100vh;
    background:
        radial-gradient(circle at 50% -10%,rgba(155,140,255,.09),transparent 30rem),
        radial-gradient(circle at 90% 35%,rgba(255,255,255,.035),transparent 25rem),
        linear-gradient(180deg,#050505 0%,#080809 55%,#050505 100%);
}

.block-container{
    max-width:1480px;
    padding:1.2rem clamp(1rem,3vw,3rem) 4rem;
}

[data-testid="stSidebar"]{
    background:linear-gradient(180deg,#0a0a0b,#060607);
    border-right:1px solid rgba(255,255,255,.08);
}

[data-testid="stSidebar"]>div:first-child{
    padding-top:1.1rem;
}

[data-testid="stSidebar"] label{
    color:#f5f5f7!important;
    font-weight:650!important;
}

[data-testid="stSidebar"] input::placeholder{
    color:#8f8f98!important;
}

.brand{
    padding:8px 4px 24px;
}

.brand-logo{
    font-family:Sora;
    font-weight:900;
    font-size:1.55rem;
    letter-spacing:-.06em;
    color:#ffffff;
    text-shadow:0 0 22px rgba(169,156,255,.22);
}

.brand-dot{
    color:#c9c1ff;
    text-shadow:0 0 10px rgba(169,156,255,.65);
}

.brand-tag{
    margin-top:5px;
    color:var(--muted);
    font-size:.78rem;
    line-height:1.45;
}

.side-label{
    margin:19px 0 8px;
    color:#8f8f98;
    font-size:.67rem;
    font-weight:800;
    letter-spacing:.16em;
    text-transform:uppercase;
}

.privacy{
    padding:14px;
    border:1px solid var(--line);
    border-radius:15px;
    background:rgba(255,255,255,.035);
    color:var(--soft);
    font-size:.78rem;
    line-height:1.55;
}

/* HERO */

.hero{
    position:relative;
    overflow:hidden;
    padding:clamp(2rem,4vw,3.2rem) 1.5rem;
    margin-bottom:1.6rem;
    border:1px solid var(--line);
    border-radius:22px;
    text-align:center;
    background:
        radial-gradient(circle at 50% 0%,rgba(255,255,255,.085),transparent 38%),
        radial-gradient(circle at 82% 70%,rgba(155,140,255,.07),transparent 28%),
        linear-gradient(145deg,rgba(25,25,28,.82),rgba(9,9,10,.92));
    box-shadow:
        0 20px 60px rgba(0,0,0,.4),
        inset 0 1px 0 rgba(255,255,255,.06);
    backdrop-filter:blur(24px);
    -webkit-backdrop-filter:blur(24px);
}

.hero:before{
    content:"";
    position:absolute;
    width:280px;
    height:280px;
    left:50%;
    top:-240px;
    transform:translateX(-50%);
    border-radius:50%;
    background:rgba(255,255,255,.08);
    filter:blur(70px);
    pointer-events:none;
}

.hero:after{
    content:"";
    position:absolute;
    left:15%;
    right:15%;
    bottom:0;
    height:1px;
    background:linear-gradient(
        90deg,
        transparent,
        rgba(214,179,106,.65),
        transparent
    );
}

.pill{
    position:relative;
    display:inline-flex;
    align-items:center;
    min-height:28px;
    padding:5px 12px;
    border:1px solid rgba(214,179,106,.36);
    border-radius:999px;
    color:#e8d5a7;
    background:rgba(214,179,106,.07);
    font-size:.62rem;
    font-weight:800;
    letter-spacing:.13em;
}

.hero h1{
    position:relative;
    margin:14px 0 8px;
    font-family:Sora,"Manrope",sans-serif;
    font-size:clamp(1.6rem,3.2vw,2.35rem);
    line-height:1.08;
    letter-spacing:-.03em;
    color:var(--text);
}

.hero h1 .hero-primary{
    display:inline-block;
    font-weight:500;
    color:#f3f3f6;
    font-size:.9em;
}

.hero h1 .hero-secondary{
    display:inline-block;
    font-weight:500;
    color:#e6e6eb;
    font-size:.9em;
}

.hero h1 .hero-brand{
    font-weight:800;
    color:#ffffff;
    background:linear-gradient(
        105deg,
        #ffffff 8%,
        #e2defe 55%,
        #a99cff 100%
    );
    -webkit-background-clip:text;
    background-clip:text;
    color:transparent;
}

.hero p{
    position:relative;
    max-width:640px;
    margin:0 auto;
    color:#bfc0c8;
    font-size:clamp(.82rem,1.3vw,.92rem);
    line-height:1.55;
}

.hero p strong{
    color:#f0f0f3;
    font-weight:700;
}

.hero-actions{
    margin-top:16px;
}

/* SECTION */

.section-title{
    margin:1.4rem 0 .35rem;
    font-family:Sora;
    font-size:1.3rem;
    font-weight:750;
    color:#f2f2f5;
}

.section-copy{
    margin:0 0 .8rem;
    color:#d0d0d8;
    font-size:.88rem;
}

.section-copy strong{
    color:#f0f0f3;
    font-weight:650;
}

/* BUTTONS */

div[data-testid="stButton"]>button{
    min-height:46px;
    border-radius:13px;
    border:1px solid var(--line);
    background:rgba(255,255,255,.045);
    color:var(--text);
    font-weight:700;
    transition:.2s ease;
}

div[data-testid="stButton"]>button:hover{
    transform:translateY(-2px);
    border-color:rgba(155,140,255,.48);
    background:rgba(155,140,255,.08);
    box-shadow:0 15px 35px rgba(0,0,0,.28);
}

div[data-testid="stButton"]>button[kind="primary"]{
    border-color:rgba(155,140,255,.55);
    background:linear-gradient(135deg,#28233f,#15151a);
}

/* SCANNER / TOOLS */

.scanner{
    min-height:96px;
    padding:12px 10px;
    border:1px solid var(--line);
    border-radius:14px;
    background:rgba(255,255,255,.035);
    text-align:center;
    display:flex;
    flex-direction:column;
    align-items:center;
    justify-content:center;
    transition:.2s ease;
    cursor:pointer;
}

.scanner:hover{
    transform:translateY(-3px);
    border-color:rgba(169,156,255,.48);
    background:rgba(155,140,255,.07);
    box-shadow:0 14px 35px rgba(0,0,0,.25);
}

.scanner-icon{
    font-size:1.45rem;
    line-height:1;
    margin-bottom:6px;
}

.scanner-title{
    margin-top:2px;
    font-size:.88rem;
    font-weight:800;
    color:#f4f4f7;
}

.scanner-copy{
    margin-top:4px;
    color:#c9c9d2;
    font-size:.72rem;
    line-height:1.35;
    max-width:135px;
}

.active{
    border-color:rgba(169,156,255,.72);
    background:rgba(155,140,255,.11);
    box-shadow:
        0 0 0 1px rgba(155,140,255,.12),
        0 12px 30px rgba(0,0,0,.22);
}

/* INPUTS */

textarea,
[data-testid="stTextInput"] input,
[data-baseweb="select"]>div{
    font-size:16px!important;
    color:var(--text)!important;
    background:#141416!important;
    border:1px solid var(--line)!important;
    border-radius:13px!important;
}

textarea::placeholder,
[data-testid="stTextInput"] input::placeholder{
    color:#9a9aa4!important;
    opacity:1!important;
}

textarea:focus,
[data-testid="stTextInput"] input:focus{
    border-color:rgba(155,140,255,.7)!important;
    box-shadow:0 0 0 3px rgba(155,140,255,.12)!important;
}

[data-baseweb="select"] input{
    caret-color:transparent!important;
}

[data-baseweb="popover"],
[data-baseweb="menu"]{
    background:#19191c!important;
    border:1px solid var(--line)!important;
    border-radius:13px!important;
    color:#fff!important;
}

[data-baseweb="menu"] [role="option"]{
    background:transparent!important;
    color:#fff!important;
    min-height:44px!important;
}

.stFileUploader>div{
    border-radius:14px!important;
}

[data-testid="stFileUploaderDropzone"]{
    min-height:125px!important;
    border:1.5px dashed rgba(155,140,255,.42)!important;
    border-radius:15px!important;
    background:rgba(155,140,255,.035)!important;
}

[data-testid="stFileUploader"] *{
    color:#e1e1e6!important;
}

/* ANALYZE BUTTON */

.analyze{
    margin-top:10px;
}

.analyze div[data-testid="stButton"]>button{
    min-height:53px;
    border-radius:999px;
    font-size:1rem;
    background:linear-gradient(135deg,#2a2443,#151519);
}

/* RESULT */

.result{
    padding:24px;
    margin-top:20px;
    border:1px solid var(--line);
    border-radius:22px;
    background:linear-gradient(
        145deg,
        rgba(255,255,255,.055),
        rgba(255,255,255,.018)
    );
    box-shadow:0 25px 65px rgba(0,0,0,.25);
}

.result-head{
    font-family:Sora;
    font-size:1.3rem;
    font-weight:800;
    color:#f5f5f7;
}

.eyebrow{
    color:#c9c9d2;
    font-size:.75rem;
    margin-top:4px;
}

.metric{
    min-height:96px;
    padding:13px;
    border:1px solid var(--line);
    border-radius:13px;
    background:rgba(255,255,255,.03);
}

.metric-label{
    color:#d0d0d8;
    font-size:.68rem;
    font-weight:800;
    letter-spacing:.1em;
    text-transform:uppercase;
}

.metric-value{
    margin-top:7px;
    font-family:Sora;
    font-size:1.4rem;
    font-weight:800;
    color:#f5f5f7;
}

.safe{
    color:var(--safe);
}

.caution{
    color:var(--warn);
}

.critical{
    color:var(--danger);
}

.bar{
    height:10px;
    margin:12px 0;
    border-radius:999px;
    background:#252528;
    overflow:hidden;
}

.bar>div{
    height:100%;
    background:linear-gradient(
        90deg,
        var(--safe),
        var(--warn),
        var(--danger)
    );
    border-radius:inherit;
}

.verdict{
    padding:17px;
    margin-top:14px;
    border-left:3px solid var(--violet);
    border-radius:12px;
    background:var(--violet2);
    line-height:1.65;
    color:#e1e1e6;
}

.verdict strong{
    color:#ffffff;
}

.evidence,
.action,
.info-card,
.challenge-card{
    height:100%;
    padding:17px;
    border:1px solid var(--line);
    border-radius:16px;
    background:rgba(255,255,255,.03);
}

.evidence>strong,
.action>strong{
    color:#f4f4f7;
}

.evidence-item{
    padding:10px 0;
    border-bottom:1px solid rgba(255,255,255,.08);
    color:#e0e0e5;
}

.evidence-item:last-child{
    border-bottom:0;
}

.action-item{
    display:flex;
    gap:10px;
    padding:9px 0;
    color:#e0e0e5;
}

.badge{
    display:inline-block;
    padding:5px 9px;
    border-radius:999px;
    background:rgba(155,140,255,.1);
    border:1px solid rgba(155,140,255,.2);
    color:#cfc9ff;
    font-size:.7rem;
    font-weight:800;
}

.confidence{
    font-size:.82rem;
    color:#bdbdc5;
}


/* COMPACT + SYMMETRIC CARDS */
[data-testid="stHorizontalBlock"]{
    align-items:stretch!important;
    gap:0.7rem!important;
}
[data-testid="stHorizontalBlock"] > [data-testid="column"]{
    display:flex!important;
    flex-direction:column!important;
    align-items:stretch!important;
}
[data-testid="stHorizontalBlock"] > [data-testid="column"] > div{
    display:flex!important;
    flex-direction:column!important;
    flex:1 1 auto!important;
}
[data-testid="stHorizontalBlock"] > [data-testid="column"] div[data-testid="stMarkdownContainer"]{
    display:flex!important;
    flex-direction:column!important;
    flex:1 1 auto!important;
}
.scanner,
.feature-card,
.metric,
.evidence,
.action,
.info-card,
.challenge-card{
    width:100%!important;
    height:100%!important;
    flex:1 1 auto!important;
    margin:0!important;
    justify-content:center!important;
}
.scanner-title{
    line-height:1.2;
}
.scanner-copy{
    line-height:1.25;
}

/* FEATURE CARDS */

.feature-card{
    padding:15px;
    border:1px solid var(--line);
    border-radius:14px;
    background:rgba(255,255,255,.03);
    height:100%;
}

.feature-icon{
    font-size:1.4rem;
}

.feature-title{
    margin-top:8px;
    font-weight:800;
    color:#f1f1f4;
}

.feature-copy{
    margin-top:5px;
    color:#d0d0d8;
    font-size:.78rem;
    line-height:1.5;
}

/* CHALLENGE */

.challenge-q{
    font-family:Sora;
    font-size:1.15rem;
    font-weight:750;
    line-height:1.45;
    color:#f1f1f4;
}

.challenge-answer{
    padding:13px;
    border-radius:12px;
    background:rgba(255,255,255,.04);
    border:1px solid var(--line);
    color:#f0f0f3;
    line-height:1.55;
}

/* REPORT */

.report-section{
    margin-top:24px;
    padding:22px;
    border:1px solid rgba(255,255,255,.12);
    border-radius:20px;
    background:linear-gradient(
        145deg,
        rgba(255,255,255,.055),
        rgba(255,255,255,.018)
    );
    box-shadow:0 18px 45px rgba(0,0,0,.18);
}

.report-section h3{
    margin:0 0 14px;
    font-family:Sora,sans-serif;
    color:#ffffff;
    font-size:1.15rem;
    font-weight:800;
    letter-spacing:-.02em;
}

.report-section p{
    color:#e4e4ea;
    line-height:1.75;
    margin:.45rem 0;
}

.report-table{
    width:100%;
    border-collapse:collapse;
    overflow:hidden;
    border-radius:12px;
    border:1px solid rgba(255,255,255,.11);
}

.report-table th{
    padding:12px 13px;
    text-align:left;
    color:#ffffff;
    background:rgba(169,156,255,.13);
    font-size:.78rem;
    letter-spacing:.04em;
}

.report-table td{
    padding:11px 13px;
    color:#ededf2;
    border-top:1px solid rgba(255,255,255,.09);
    vertical-align:top;
    font-size:.84rem;
}

.report-table tr:nth-child(even) td{
    background:rgba(255,255,255,.025);
}

.check-detected{
    color:#4dff88;
    font-weight:850;
}

.check-clear{
    color:#ff526b;
    font-weight:850;
}

.check-low{
    color:#ffd34d;
    font-weight:850;
}

.check-review{
    color:#ffd34d;
    font-weight:850;
}

.status-legend{
    margin-top:14px;
    padding:13px 15px;
    border:1px solid rgba(255,255,255,.10);
    border-radius:13px;
    background:rgba(255,255,255,.025);
    color:#e7e7ed;
    font-size:.78rem;
    line-height:1.65;
}

.status-legend-title{
    font-weight:800;
    color:#ffffff;
    margin-bottom:5px;
}

.status-item{
    display:inline-block;
    margin-right:18px;
    margin-top:3px;
}

.status-detected{
    color:#4dff88;
    font-weight:850;
}

.status-review{
    color:#ffd34d;
    font-weight:850;
}

.status-clear{
    color:#ff526b;
    font-weight:850;
}

.source-link{
    color:#a99cff!important;
    text-decoration:underline!important;
    text-decoration-thickness:1px!important;
    text-underline-offset:3px;
}

.conclusion-card{
    padding:18px 20px;
    border-left:3px solid #a99cff;
    border-radius:14px;
    background:linear-gradient(
        135deg,
        rgba(169,156,255,.14),
        rgba(169,156,255,.05)
    );
    color:#f0f0f4;
    line-height:1.75;
}

/* LOADER */

.analysis-loader{
    height:5px;
    border-radius:999px;
    margin:10px 0 4px;
    overflow:hidden;
    background:rgba(255,255,255,.10);
    box-shadow:0 0 0 1px rgba(255,255,255,.06);
}

.analysis-loader span{
    display:block;
    width:42%;
    height:100%;
    border-radius:999px;
    background:linear-gradient(
        90deg,
        #a99cff,
        #e7e1ff,
        #a99cff
    );
    box-shadow:0 0 18px rgba(169,156,255,.9);
    animation:satark-loader 1.25s ease-in-out infinite;
}

@keyframes satark-loader{
    0%{
        transform:translateX(-120%);
    }
    100%{
        transform:translateX(270%);
    }
}

/* FOOTER */

.footer{
    margin-top:4rem;
    padding-top:1.2rem;
    border-top:1px solid var(--line);
    text-align:center;
    color:#64646b;
    font-size:.74rem;
    line-height:1.6;
}

.stAlert{
    border-radius:13px!important;
}

[data-testid="stDownloadButton"] button{
    background:#ffffff!important;
    color:#17171a!important;
    border:1px solid #ffffff!important;
    font-weight:800!important;
    min-height:50px!important;
}

[data-testid="stDownloadButton"] button:hover{
    background:#f1efff!important;
    color:#17171a!important;
    border-color:#c8c0ff!important;
}

[data-testid="stDownloadButton"] button p,
[data-testid="stDownloadButton"] button span{
    color:#17171a!important;
    font-weight:800!important;
}

[data-testid="stFileUploaderDropzoneInstructions"] div{
    color:#e9e9ef!important;
}

/* MOBILE */

@media(max-width:768px){

    .block-container{
        padding:.7rem .65rem 3rem;
    }

    .hero{
        padding:2.2rem .85rem;
        border-radius:18px;
    }

    .hero h1{
        font-size:clamp(1.5rem,7vw,2rem);
        line-height:1.1;
    }

    .hero p{
        font-size:.8rem;
    }

    .scanner{
        min-height:88px;
        padding:10px 8px;
    }

    .scanner-icon{
        font-size:1.3rem;
    }

    .scanner-title{
        font-size:.9rem;
    }

    .scanner-copy{
        font-size:.68rem;
    }

    div[data-testid="stButton"]>button{
        width:100%;
    }

    .result{
        padding:17px;
    }
}
</style>
""",
    unsafe_allow_html=True,
)
# --------------------------- Helpers --------------------------

def safe_text(value, default=""):  # cleans the text
    if value is None:
        return default
    return str(value).strip()




def clamp_score(value):
    try:
        return max(0, min(100, int(float(value))))  # limits score to 0–100
    except (TypeError, ValueError):
        st.warning(
            "⚠️ Threat score unavailable: Insufficient security indicators "
            "were found to make a reliable assessment. Please provide more "
            "complete information and try again."
        )
        return 50




def is_scam_claim(category, verdict, summary=""):
    """Detect a scam claim, trusting the model's explicit threat_category field first.

    The category field is a constrained enum the model was explicitly asked to
    fill in, so it is a far more reliable signal than re-deriving "is this a
    scam" from free-text prose. Regex parsing of the verdict/summary is now
    only a fallback for when the category is missing or ambiguous (e.g. still
    "Needs review"), rather than the primary signal.
    """
    category_text = safe_text(category).strip().lower()

    if category_text == "scam":
        return True

    if category_text and category_text not in {"needs review", ""}:
        # The model gave a specific, non-scam category (e.g. "Safe", "Phishing",
        # "Malware"). Trust it instead of re-scanning prose that might mention
        # the word "scam" in a hedged, comparative, or negated sentence.
        return False

    text = " ".join(
        safe_text(v) for v in (category, verdict, summary)
    ).lower()

    negative_patterns = (
        r"\bnot\s+(?:necessarily\s+)?(?:a\s+)?scam\b",
        r"\bno\s+(?:evidence\s+of\s+)?(?:a\s+)?scam\b",
        r"\b(?:does|do)\s+not\s+(?:appear|seem)\s+to\s+be\s+(?:a\s+)?scam\b",
        r"\bunlikely\s+to\s+be\s+(?:a\s+)?scam\b",
        r"\b(?:cannot|can't)\s+(?:confirm|verify)\s+(?:that\s+it\s+is\s+)?(?:a\s+)?scam\b",
        r"\bno\s+clear\s+indication\s+of\s+(?:a\s+)?scam\b",
    )

    if any(re.search(pattern, text) for pattern in negative_patterns):
        return False

    return bool(re.search(r"\bscam\b", text))




def normalize_result_consistency(result):
    """Keep scam/phishing category, risk score and displayed verdict consistent."""
    category = safe_text(
        result.get("threat_category", "Needs review"),
        "Needs review"
    )
    verdict = safe_text(
        result.get("verdict", "Manual review recommended."),
        "Manual review recommended."
    )
    summary = safe_text(result.get("summary", ""))

    category_lower = category.lower()
    combined_text = f"{category} {verdict} {summary}".lower()

    is_scam = is_scam_claim(category, verdict, summary)

    # Prefer the explicit category for phishing too; fall back to phrase
    # matching only when the category doesn't already say "Phishing".
    is_phishing = category_lower == "phishing" or bool(re.search(
        r"\b(phishing attempt|phishing attack|phishing link|phishing message|is phishing|appears to be phishing)\b",
        combined_text
    ))

    if is_scam or is_phishing:
        if is_scam:
            result["threat_category"] = "Scam"

        result["risk_score"] = max(
            70,
            clamp_score(result.get("risk_score", 50))
        )

        if is_scam and not re.search(r"\bscam\b", verdict.lower()):
            result["verdict"] = "This message is a scam and should not be trusted."

    else:
        result["risk_score"] = clamp_score(
            result.get("risk_score", 50)
        )

    return result

#-------------------------------------------------------------------------------------------------















def risk_label(score, category=""):
    score = clamp_score(score)
    if safe_text(category).lower() == "scam":
        return "SCAM", "critical"
    if score < 35:
        return "SAFE", "safe"
    if score < 70:
        return "CAUTION", "caution"
    return "CRITICAL THREAT", "critical"


def clean_json_text(text):
    text = safe_text(text)
    text = re.sub(r"```(?:json)?\s*", "", text, flags=re.I)
    start = text.find("{")
    end = text.rfind("}")
    return text[start:end + 1] if start != -1 and end > start else text




THREAT_CHECKS = [
    "Scam Indicators",
    "Phishing Signs",
    "Deepfake Risk",
    "Fake Information",
    "Suspicious Links",
    "Impersonation",
    "Malware Indicators",
    "Social Engineering",
]




OFFICIAL_VERIFICATION_SOURCES = [
    {
        "source": "National Cyber Crime Reporting Portal (NCRP)",
        "purpose": "Report cybercrime and financial fraud, and check or report suspicious identifiers such as phone numbers, email IDs, URLs and social-media accounts.",
        "website": "https://www.cybercrime.gov.in/",
    },
    {
        "source": "Indian Cybercrime Coordination Centre (I4C)",
        "purpose": "Government of India initiative coordinating cybercrime prevention, analysis, reporting and response.",
        "website": "https://i4c.mha.gov.in/",
    },
    {
        "source": "CERT-In",
        "purpose": "India's national agency for cybersecurity incident response, alerts, advisories and security guidance.",
        "website": "https://www.cert-in.org.in/",
    },
    {
        "source": "Reserve Bank of India (RBI)",
        "purpose": "Official guidance on banking, digital payments, OTP/PIN safety and prevention of financial and payment fraud.",
        "website": "https://www.rbi.org.in/",
    },
    {
        "source": "National Payments Corporation of India (NPCI)",
        "purpose": "Official information and safety guidance for UPI and India's retail payment systems.",
        "website": "https://www.npci.org.in/",
    },
    {
        "source": "Securities and Exchange Board of India (SEBI)",
        "purpose": "Official investor-protection resources for identifying investment scams, unregistered entities and fraudulent schemes.",
        "website": "https://www.sebi.gov.in/",
    },
    {
        "source": "Sanchar Saathi — Department of Telecommunications",
        "purpose": "Report suspected fraudulent calls, SMS and WhatsApp communications and check mobile connections and handset information.",
        "website": "https://www.sancharsaathi.gov.in/",
    },
    {
        "source": "UIDAI",
        "purpose": "Official Aadhaar services and security guidance for protecting Aadhaar-related identity information.",
        "website": "https://uidai.gov.in/",
    },
    {
        "source": "IRDAI",
        "purpose": "Official insurance-sector guidance and consumer awareness regarding insurance fraud and cybersecurity risks.",
        "website": "https://irdai.gov.in/",
    },
    {
        "source": "National Consumer Helpline (NCH)",
        "purpose": "Government consumer grievance platform for consumer fraud and complaint-related support.",
        "website": "https://consumerhelpline.gov.in/",
    },
    {
        "source": "Employees' Provident Fund Organisation (EPFO)",
        "purpose": "Official guidance for protecting EPFO, UAN and pension-related information from impersonation and fraud.",
        "website": "https://www.epfindia.gov.in/",
    },
    {
        "source": "Income Tax Department",
        "purpose": "Official tax-related services and guidance for identifying fraudulent tax, PAN and income-tax communications.",
        "website": "https://www.incometax.gov.in/",
    },
    {
        "source": "Ministry of Corporate Affairs (MCA)",
        "purpose": "Official company and corporate information for cross-checking registered businesses and corporate identities.",
        "website": "https://www.mca.gov.in/",
    },
]



def normalize_check_value(value):
    if isinstance(value, bool):
        return "Detected" if value else "Not detected"
    if isinstance(value, (int, float)):
        if value >= 70:
            return "High"
        if value >= 35:
            return "Medium"
        return "Low"
    text = safe_text(value)
    if not text:
        return "Needs review"
    return text[:80]


def check_class(value):
    text = safe_text(value).lower()

    if any(x in text for x in (
        "not detected", "none", "no sign", "clear", "false", "absent"
    )):
        return "check-clear"

    if "low" in text:
        return "check-low"

    if any(x in text for x in (
        "detected", "present", "high", "yes", "true", "strong"
    )):
        return "check-detected"

    return "check-review"







#-------------------------------------------------------------------------------------------


def build_fallback_threat_analysis(result):
    category = safe_text(result.get("threat_category", "")).lower()
    indicators = " ".join(result.get("key_indicators", [])).lower()
    summary = safe_text(result.get("summary", "")).lower()
    verdict = safe_text(result.get("verdict", "")).lower()

    text = category + " " + indicators + " " + summary + " " + verdict

    def has(*terms):
        return any(term in text for term in terms)

    public_figure_claim = has(
        "public figure", "celebrity", "politician",
        "brand ambassador", "endorsement", "endorses",
        "celebrity endorsement", "public figure endorsement"
    )

    deepfake = has(
        "deepfake", "deep fake", "synthetic media",
        "ai-generated", "ai generated", "manipulated image",
        "face manipulation", "digitally manipulated"
    )

    fake_claim = has(
        "fake", "false", "fabricat", "misinformation",
        "misleading", "unverified", "unsupported claim",
        "false claim", "deceptive"
    )

    return {
        "Scam Indicators": "Detected" if has(
            "scam", "fraud", "prize", "fee"
        ) else "Needs review",

        "Phishing Signs": "Detected" if has(
            "phishing", "credential", "login", "password", "otp"
        ) else "Needs review",

        "Deepfake Risk": (
            "High" if deepfake
            else "Medium" if public_figure_claim
            else "Low"
        ),

        "Fake Information": "Detected" if fake_claim else "Needs review",

        "Suspicious Links": "Detected" if has(
            "suspicious link", "malicious link", "url", "domain"
        ) else "Needs review",

        "Impersonation": "Detected" if (
            public_figure_claim or has(
                "impersonation", "impersonat",
                "pretend", "fake authority"
            )
        ) else "Needs review",

        "Malware Indicators": "Detected" if has(
            "malware", "trojan", "ransomware", "apk", "virus"
        ) else "Not detected",

        "Social Engineering": "Detected" if has(
            "social engineering", "urgency", "pressure", "manipulation"
        ) else "Needs review",
    }




def build_final_conclusion(result):
    existing = safe_text(result.get("final_conclusion", ""))
    if existing:
        return existing
    label, _ = risk_label(result.get("risk_score", 50), result.get("threat_category", ""))
    summary = safe_text(result.get("summary", ""))
    verdict = safe_text(result.get("verdict", "Manual review recommended."))
    if summary:
        return f"SATARK assessed this item as {label.lower()} based on the evidence identified during analysis. {summary} {verdict} Verify the source independently before taking any high-impact action."
    return f"SATARK assessed this item as {label.lower()}. {verdict} Verify the source independently before taking any high-impact action."


def calibrate_confidence(data, result):
    """Report a SATARK confidence value that reflects real evidence strength.

    Unlike the previous implementation, this does NOT force the value into a
    fixed high band. The raw model confidence is kept as ``model_confidence``
    for auditability, and the user-facing ``confidence`` is the raw value
    adjusted only slightly by how complete/ambiguous the supporting evidence
    is. Weak or ambiguous evidence can and should produce a low confidence
    score — that is the whole point of showing it.
    """
    try:
        raw_conf = float(data.get("confidence", result.get("confidence", 70)))
    except (TypeError, ValueError):
        raw_conf = 70.0
    raw_conf = max(0.0, min(100.0, raw_conf))
    result["model_confidence"] = round(raw_conf, 2)

    checks = result.get("threat_analysis", {}) or {}
    review_count = sum(1 for value in checks.values() if check_class(value) == "check-review")
    evidence_count = len(result.get("key_indicators", []))

    # Ambiguous/unresolved checks should pull confidence down, not up.
    ambiguity_penalty = (review_count / max(1, len(THREAT_CHECKS))) * 20.0

    # Well-evidenced findings get a small, capped bonus — not a floor.
    evidence_bonus = min(5.0, evidence_count * 1.0)

    calibrated = raw_conf - ambiguity_penalty + evidence_bonus
    result["confidence"] = round(max(0.0, min(100.0, calibrated)), 2)
    return result


def normalize_result(data, raw="", model_used=""):
    if not isinstance(data, dict):
        data = {}
    indicators = data.get("key_indicators", data.get("indicators", []))
    recommendations = data.get("recommendations", data.get("safety_recommendations", []))
    if isinstance(indicators, str): indicators = [indicators]
    if isinstance(recommendations, str): recommendations = [recommendations]
    if not isinstance(indicators, list): indicators = []
    if not isinstance(recommendations, list): recommendations = []

    raw_checks = data.get("threat_analysis", {})
    if not isinstance(raw_checks, dict):
        raw_checks = {}
    threat_analysis = {
        check: normalize_check_value(raw_checks.get(check, ""))
        for check in THREAT_CHECKS
    }

    result = {
        "risk_score": clamp_score(data.get("risk_score", data.get("threat_score", 50))),
        "threat_category": safe_text(data.get("threat_category", data.get("category", "Needs review")), "Needs review"),
        "verdict": safe_text(data.get("verdict", data.get("final_verdict", "Manual review recommended.")), "Manual review recommended."),
        "summary": safe_text(data.get("summary", data.get("executive_summary", ""))),
        "key_indicators": [safe_text(x) for x in indicators if safe_text(x)][:8],
        "recommendations": [safe_text(x) for x in recommendations if safe_text(x)][:8],
        "confidence": clamp_score(data.get("confidence", 70)),
        "model_used": model_used or safe_text(data.get("model_used", "")),
        "scam_pattern": safe_text(data.get("scam_pattern", data.get("pattern", ""))),
        "threat_analysis": threat_analysis,
        "final_conclusion": safe_text(data.get("final_conclusion", data.get("conclusion", ""))),
        "verification_sources": OFFICIAL_VERIFICATION_SOURCES,
        "raw": raw,
    }
    result = normalize_result_consistency(result)
    if not result["scam_pattern"]:
        result["scam_pattern"] = result["threat_category"]
    fallback = build_fallback_threat_analysis(result)
    for check in THREAT_CHECKS:
        if result["threat_analysis"][check] == "Needs review":
            result["threat_analysis"][check] = fallback[check]
    result["final_conclusion"] = build_final_conclusion(result)
    result = calibrate_confidence(data, result)
    return result


class VisibleTextParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.skip_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag.lower() in {"script", "style", "noscript", "svg"}:
            self.skip_depth += 1

    def handle_endtag(self, tag):
        if tag.lower() in {"script", "style", "noscript", "svg"} and self.skip_depth:
            self.skip_depth -= 1

    def handle_data(self, data):
        if not self.skip_depth and data.strip():
            self.parts.append(data.strip())

    def text(self):
        return "\n".join(self.parts)


def is_public_url(url):
    parsed = urlparse(safe_text(url))
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return False
    host = parsed.hostname.lower()
    if host in {"localhost", "localhost.localdomain"}:
        return False
    try:
        addresses = socket.getaddrinfo(host, None)
        for item in addresses:
            ip = ipaddress.ip_address(item[4][0])
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_reserved:
                return False
    except (socket.gaierror, ValueError, OSError):
        return True
    return True


class SafeRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not is_public_url(newurl):
            raise ValueError("The URL redirects to a private or unsafe network address.")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch_url_text(url):
    url = safe_text(url)
    if not is_public_url(url):
        raise ValueError("For safety, only public HTTP/HTTPS URLs can be fetched.")
    request = Request(url, headers={"User-Agent":"SATARK-Security-Analyzer/2.0", "Accept":"text/html,application/xhtml+xml,text/plain"})
    opener = build_opener(SafeRedirectHandler())
    with opener.open(request, timeout=12) as response:
        content_type = response.headers.get("Content-Type", "").lower()
        raw = response.read(1_500_000)
        final_url = response.geturl()
    if not is_public_url(final_url):
        raise ValueError("The final URL is not a public address and was blocked.")
    if "text" not in content_type and "html" not in content_type and "xml" not in content_type:
        return raw.decode("utf-8", errors="ignore")[:12000]
    parser = VisibleTextParser()
    parser.feed(raw.decode("utf-8", errors="ignore"))
    text = parser.text() or raw.decode("utf-8", errors="ignore")
    return text[:30000]


def extract_pdf_text(uploaded_file):
    reader = PdfReader(uploaded_file)
    pages = []
    for page in reader.pages[:30]:
        try:
            text = page.extract_text() or ""
            if text.strip(): pages.append(text)
        except Exception:
            pass
    text = "\n\n".join(pages).strip()
    if not text:
        raise ValueError("No readable text was found in this PDF. It may be scanned/image-only. Please use a screenshot/image of the relevant page for vision analysis.")
    return text[:50000]


def image_to_data_url(uploaded_file):
    """Convert one uploaded image to a compact JPEG data URL.

    Kept modest in size (max_side=900, moderate JPEG quality) so a small
    number of images stays well under Groq's on-demand tokens-per-minute
    budget for vision models — full-resolution uploads were previously
    large enough on their own to trip the TPM rate limit."""
    from io import BytesIO
    try:
        uploaded_file.seek(0)
    except Exception:
        pass
    image = Image.open(uploaded_file).convert("RGB")
    max_side = 900
    if max(image.size) > max_side:
        scale = max_side / max(image.size)
        image = image.resize((max(1, int(image.width * scale)), max(1, int(image.height * scale))))
    for quality in (75, 62, 50, 40):
        buffer = BytesIO()
        image.save(buffer, format="JPEG", quality=quality, optimize=True)
        encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")
        if len(encoded) <= 900_000 or quality == 40:
            return f"data:image/jpeg;base64,{encoded}"
    return f"data:image/jpeg;base64,{encoded}"


def images_to_data_urls(uploaded_files, max_images=5):
    """Convert multiple uploaded images while keeping the request manageable."""
    if not uploaded_files:
        return []
    urls = []
    for uploaded_file in list(uploaded_files)[:max_images]:
        urls.append(image_to_data_url(uploaded_file))
    return urls


def uploaded_fingerprint(uploaded_files):
    """Return a content fingerprint so a new scan cannot reuse stale image state."""
    if not uploaded_files:
        return ""
    digest = hashlib.sha256()
    for uploaded_file in uploaded_files:
        try:
            data = uploaded_file.getvalue()
        except Exception:
            data = b""
        digest.update(safe_text(getattr(uploaded_file, "name", "")).encode("utf-8", errors="ignore"))
        digest.update(str(len(data)).encode("ascii"))
        digest.update(hashlib.sha256(data).digest())
    return digest.hexdigest()


def single_file_fingerprint(uploaded_file):
    """Fingerprint a single uploaded file (used for video scanning)."""
    if not uploaded_file:
        return ""
    try:
        data = uploaded_file.getvalue()
    except Exception:
        data = b""
    digest = hashlib.sha256()
    digest.update(safe_text(getattr(uploaded_file, "name", "")).encode("utf-8", errors="ignore"))
    digest.update(str(len(data)).encode("ascii"))
    digest.update(hashlib.sha256(data).digest())
    return digest.hexdigest()


# ------------------- Video: frame + audio extraction -------------------
# Videos are not sent to the vision model directly. Instead SATARK pulls a
# handful of representative frames (evenly spaced through the clip) with
# OpenCV and treats them exactly like an "Image" scan. If OpenCV or an
# audio-transcription path is unavailable in this environment, SATARK
# degrades gracefully and explains what could not be analyzed rather than
# crashing the whole scan.
MAX_VIDEO_FRAMES = 2  # kept minimal — every extra frame competes with the
# transcript and system prompt for the same tight tokens-per-minute budget
MAX_VIDEO_BYTES = 200 * 1024 * 1024  # 200 MB safety cap for in-memory handling


def _video_dependencies_available():
    try:
        import cv2  # noqa: F401
        return True
    except Exception:
        return False


def extract_video_frames(uploaded_file, max_frames=MAX_VIDEO_FRAMES):
    """Extract up to `max_frames` evenly spaced frames from an uploaded video
    as PIL Images. Returns (frames, duration_seconds, warnings)."""
    import tempfile

    try:
        import cv2
    except Exception as exc:
        raise RuntimeError(
            "Video frame extraction requires OpenCV (opencv-python-headless), "
            "which is not installed in this environment. Run "
            "`pip install opencv-python-headless --break-system-packages` and restart the app."
        ) from exc

    warnings = []
    try:
        uploaded_file.seek(0)
    except Exception:
        pass
    data = uploaded_file.read()
    if len(data) > MAX_VIDEO_BYTES:
        raise ValueError("This video is larger than the 200 MB limit SATARK can safely process in-session.")
    if not data:
        raise ValueError("The uploaded video appears to be empty or unreadable.")

    suffix = os.path.splitext(safe_text(getattr(uploaded_file, "name", "")))[1] or ".mp4"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(data)
        tmp_path = tmp.name

    frames = []
    duration = 0.0
    try:
        capture = cv2.VideoCapture(tmp_path)
        if not capture.isOpened():
            raise ValueError("SATARK could not open this video file. It may be corrupted or in an unsupported codec.")

        fps = capture.get(cv2.CAP_PROP_FPS) or 0
        frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        duration = (frame_count / fps) if fps > 0 else 0.0

        if frame_count <= 0:
            # Fall back to sequential reads if metadata is unreliable.
            count = 0
            while True:
                ok, frame_bgr = capture.read()
                if not ok:
                    break
                count += 1
                if count % 30 == 0 and len(frames) < max_frames:
                    frames.append(_bgr_to_pil(frame_bgr))
                if len(frames) >= max_frames:
                    break
            if not frames:
                raise ValueError("SATARK could not read any frames from this video.")
        else:
            target_frames = min(max_frames, frame_count)
            indices = [int(i * (frame_count - 1) / max(1, target_frames - 1)) for i in range(target_frames)] if target_frames > 1 else [0]
            for idx in indices:
                capture.set(cv2.CAP_PROP_POS_FRAMES, idx)
                ok, frame_bgr = capture.read()
                if ok:
                    frames.append(_bgr_to_pil(frame_bgr))
            if not frames:
                raise ValueError("SATARK could not extract readable frames from this video.")

        capture.release()
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass

    return frames, duration, warnings


def _bgr_to_pil(frame_bgr):
    import cv2
    frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    return Image.fromarray(frame_rgb)


def pil_frames_to_data_urls(frames, max_side=512):
    """Convert extracted PIL frames into compact JPEG data URLs for the vision
    model. Kept small (512px, low JPEG quality) because Groq's on-demand tier
    has a tight tokens-per-minute budget shared across every frame AND the
    audio transcript AND the system prompt in the same request."""
    from io import BytesIO
    urls = []
    for image in frames:
        image = image.convert("RGB")
        if max(image.size) > max_side:
            scale = max_side / max(image.size)
            image = image.resize((max(1, int(image.width * scale)), max(1, int(image.height * scale))))
        for quality in (55, 42, 30):
            buffer = BytesIO()
            image.save(buffer, format="JPEG", quality=quality, optimize=True)
            encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")
            if len(encoded) <= 400_000 or quality == 30:
                urls.append(f"data:image/jpeg;base64,{encoded}")
                break
    return urls


def transcribe_video_audio(uploaded_file, client):
    """Best-effort audio transcription via Groq Whisper. Returns "" if audio
    extraction isn't available in this environment rather than failing the
    whole video scan — frame analysis can still proceed without it."""
    import tempfile

    try:
        import cv2  # noqa: F401
    except Exception:
        return ""

    try:
        uploaded_file.seek(0)
        data = uploaded_file.read()
    except Exception:
        return ""

    suffix = os.path.splitext(safe_text(getattr(uploaded_file, "name", "")))[1] or ".mp4"
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(data)
            tmp_path = tmp.name

        with open(tmp_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                file=(os.path.basename(tmp_path), audio_file.read()),
                model="whisper-large-v3",
                response_format="text",
            )
        text = transcript if isinstance(transcript, str) else safe_text(getattr(transcript, "text", ""))
        # Kept short: on Groq's on-demand tier the tokens-per-minute budget is
        # shared across the transcript, the system prompt, and every video
        # frame in the same request, so a long transcript alone can blow the
        # limit even with small images.
        return text.strip()[:3000]
    except Exception:
        # Audio may be silent, absent, or the account may lack Whisper access.
        # Frame-only analysis is still useful, so don't raise here.
        return ""
    finally:
        if tmp_path:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass


def get_client(api_key):
    key = safe_text(api_key)
    return Groq(api_key=key) if key else None


# ---------------------- Model discovery ------------------------
TEXT_MODEL_PREFERENCES = [
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
]
# Vision model fallback chain. Previously this was a single hardcoded model
# (qwen/qwen3.6-27b), which meant image/QR analysis broke entirely the moment
# that one model became unavailable or the API key lost access to it.
# analyze_with_groq now tries each of these in order and only reports failure
# once every candidate has been exhausted.
VISION_MODEL_PREFERENCES = [
    "qwen/qwen3.6-27b",
]

# Some vision models cap how many images can be sent in one request (e.g. Qwen
# allows only 3). Keyed by model id; models not listed here use the default
# cap applied in analyze_with_groq.
VISION_MODEL_IMAGE_LIMITS = {
    "qwen/qwen3.6-27b": 3,
}


def discover_models(client):
    """Ask Groq which models this exact API key can access."""
    try:
        listing = client.models.list()
        items = getattr(listing, "data", listing)
        ids = set()
        for item in items or []:
            mid = getattr(item, "id", None)
            if mid:
                ids.add(str(mid))
            elif isinstance(item, dict) and item.get("id"):
                ids.add(str(item["id"]))
        return ids
    except Exception:
        return set()


def choose_model(available, preferences):
    if not available:
        return preferences[0]
    for model in preferences:
        if model in available:
            return model
    return None


def model_status(client):
    available = discover_models(client)
    text_model = choose_model(available, TEXT_MODEL_PREFERENCES)
    vision_model = choose_model(available, VISION_MODEL_PREFERENCES)
    return available, text_model, vision_model


# ------------------------- AI analysis --------------------------
SYSTEM_PROMPT = """
You are SATARK, a careful digital-threat and content-authenticity analysis assistant.

Analyze the content for scams, phishing, social engineering, malware, impersonation,
suspicious links, credential theft, fraud, payment fraud, account takeover, malicious
QR codes, deepfakes, AI-generated/manipulated media, and fabricated or misleading claims.

Rules:
- Never claim certainty when evidence is weak. Distinguish evidence from inference.
- Confidence must reflect evidence strength: weak/ambiguous evidence → below 50; only
  strong, unambiguous evidence → above 85. Do not default high.
- Do not invent URLs, organizations, sender details, or facts not visible in the input.
- CRITICAL: Professional visual quality (clean logo, good typography, polished layout)
  is NOT evidence of truthfulness. A fabricated or AI-generated endorsement can look just
  as polished as a real one. Never let visual/production quality lower your Fake
  Information, Impersonation, or Deepfake Risk scores — judge those on the plausibility
  of the underlying claim, not the graphic design.
- For any image that asserts a specific named real person did/said/endorsed something,
  treat this as an unverified factual claim requiring scrutiny, not just a design
  element. Explicitly reason about real-world plausibility given who the person is and
  what role or position they are commonly known for (e.g. a person widely known to hold
  a government office, judicial role, regulatory position, or similar public-trust role
  making a commercial product endorsement is unusual and often against normal conduct
  norms — flag this tension). This applies generally to any named real person, not only
  political figures — also apply it to claimed celebrity, executive, or institutional
  endorsements that seem inconsistent with what is publicly known about that person or
  organization. Raise Fake Information / Impersonation to at least Medium when such a
  claim cannot be corroborated from the image alone.
- For images/video frames: inspect visible text, URLs, QR content, logos, layout,
  instructions, and whether content may be AI-generated, manipulated, or a deepfake.
  Identify factual claims (quotes, endorsements, identities, affiliations) that may need
  verification. Do NOT classify as Safe merely because it looks like a normal/professional
  graphic — cybersecurity safety and content authenticity are separate axes, and a "Safe"
  cybersecurity verdict must not imply the claims shown are true.
- If the image depicts a real, named person making an endorsement/claim that you cannot
  verify from the image alone, the verdict and summary MUST state plainly that this
  cannot be confirmed as genuine and should be independently verified before belief or
  sharing — do not phrase this as an optional suggestion buried only in recommendations.
- For URLs: consider domain mismatch, redirects, credential requests, urgency, impersonation.

Return ONLY valid JSON, no markdown, no code fences. Required schema:
{
  "risk_score": 0,
  "confidence": 0,
  "threat_category": "Safe / Phishing / Scam / Malware / Impersonation / Suspicious Link / Payment Fraud / Account Takeover / Unverified Claim / Other",
  "verdict": "one short sentence",
  "summary": "2-4 sentence plain-English explanation",
  "key_indicators": ["indicator 1", "indicator 2"],
  "recommendations": ["action 1", "action 2"],
  "scam_pattern": "one short pattern name",
  "threat_analysis": {
    "Scam Indicators": "Detected / Not detected / Low / Medium / High",
    "Phishing Signs": "Detected / Not detected / Low / Medium / High",
    "Deepfake Risk": "Detected / Not detected / Low / Medium / High",
    "Fake Information": "Detected / Not detected / Low / Medium / High",
    "Suspicious Links": "Detected / Not detected / Low / Medium / High",
    "Impersonation": "Detected / Not detected / Low / Medium / High",
    "Malware Indicators": "Detected / Not detected / Low / Medium / High",
    "Social Engineering": "Detected / Not detected / Low / Medium / High"
  },
  "final_conclusion": "2-4 sentence final conclusion explaining why the assessment was reached"
}
"""


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
            errors.append(f"{model}: {exc}")
            # Move on to the next candidate model instead of giving up
            # immediately — this applies to text, image and video requests now.
            continue

    detail = "\n".join(errors[-4:])
    kind = "image/QR/video" if image_data_urls else "text"
    rate_limited = any("rate_limit_exceeded" in e or "Request too large" in e for e in errors)

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

SC_CSS = """
<style>
:root {
  --bg:#0a0b10;
  --surface:#15161d;
  --surface2:#1c1e28;
  --line:rgba(255,255,255,.10);
  --line2:rgba(255,255,255,.18);
  --text:#f7f8fb;
  --soft:#e4e5ee;
  --muted:#9ea1b4;
  --violet:#a48bff;
  --violet2:rgba(164,139,255,.16);
  --cyan:#5eead4;
  --gold:#f2c879;
  --safe:#3ee08a;
  --warn:#ffbe4d;
  --danger:#ff5c5c;
}
*{box-sizing:border-box}
html,body,[class*="css"]{font-family:"Manrope","Segoe UI",sans-serif;}
body{background:var(--bg);color:var(--text);}
h1,h2,h3,h4,h5,h6{color:#f7f7fb!important;}
.stApp{
  min-height:100vh;
  background:
    radial-gradient(circle at 12% -8%, rgba(164,139,255,.16), transparent 32rem),
    radial-gradient(circle at 90% 10%, rgba(94,234,212,.10), transparent 28rem),
    radial-gradient(circle at 50% 110%, rgba(242,200,121,.07), transparent 34rem),
    linear-gradient(180deg,#0a0b10 0%,#0d0e15 55%,#0a0b10 100%);
}
.block-container{max-width:1200px;padding:1.2rem clamp(1rem,3vw,3rem) 4rem;}
.section-title{
  margin:1.4rem 0 .35rem;font-family:"Sora",sans-serif;font-size:1.35rem;
  font-weight:800;color:#f5f5f9;
}
.section-copy{margin:0 0 .8rem;color:#c7c9d6;font-size:.9rem;}
div[data-testid="stButton"]>button{
  min-height:46px;border-radius:13px;border:1px solid var(--line2);
  background:rgba(255,255,255,.055);color:var(--text);font-weight:700;
  transition:.18s ease;
}
div[data-testid="stButton"]>button:hover{
  transform:translateY(-2px);border-color:rgba(164,139,255,.6);
  background:rgba(164,139,255,.12);box-shadow:0 15px 35px rgba(0,0,0,.32);
}
div[data-testid="stButton"]>button[kind="primary"]{
  border-color:rgba(164,139,255,.7);
  background:linear-gradient(135deg,#40376b,#1b1c27);
}
/* ============================================================
   SCAM CHALLENGE — game system
   ============================================================ */
.pill{
  display:inline-block;
  padding:6px 14px;
  border-radius:999px;
  border:1px solid var(--line2);
  background:rgba(164,139,255,.10);
  color:#d6cfff;
  font-size:.64rem;
  font-weight:800;
  letter-spacing:.16em;
  text-transform:uppercase;
}
.sc-dash{
  position:relative;
  overflow:hidden;
  padding:26px;
  border:1px solid var(--line2);
  border-radius:20px;
  background:
    radial-gradient(circle at 12% 0%, rgba(164,139,255,.16), transparent 55%),
    radial-gradient(circle at 92% 105%, rgba(94,234,212,.10), transparent 50%),
    linear-gradient(145deg,rgba(28,30,40,.94),rgba(13,14,20,.97));
  box-shadow:0 20px 55px rgba(0,0,0,.4), inset 0 1px 0 rgba(255,255,255,.05);
}
.sc-dash:before{
  content:"";
  position:absolute;inset:0;
  background-image:radial-gradient(rgba(255,255,255,.055) 1px, transparent 1px);
  background-size:24px 24px;
  -webkit-mask-image:radial-gradient(circle at 20% 10%, #000 0%, transparent 70%);
          mask-image:radial-gradient(circle at 20% 10%, #000 0%, transparent 70%);
  pointer-events:none;
}
.sc-dash-badge{flex-shrink:0;}
.sc-dash-rankinfo{flex:1;min-width:220px;}
 
/* ---- HEADER + POINTS BADGE (top-right, all views) ---- */
.sc-header-row{
  display:flex;
  align-items:flex-start;
  justify-content:space-between;
  gap:16px;
  flex-wrap:wrap;
}
.sc-header-row .section-title{margin-top:0;}
.sc-points-badge{
  display:flex;
  align-items:center;
  gap:10px;
  padding:9px 18px;
  border-radius:14px;
  border:1px solid rgba(242,200,121,.45);
  background:linear-gradient(135deg, rgba(242,200,121,.18), rgba(164,139,255,.12));
  box-shadow:0 10px 24px rgba(0,0,0,.32), inset 0 1px 0 rgba(255,255,255,.08);
  flex-shrink:0;
  margin-top:2px;
}
.sc-points-icon{
  font-size:1.15rem;
  filter:drop-shadow(0 0 6px rgba(242,200,121,.65));
}
.sc-points-text{display:flex;flex-direction:column;line-height:1.1;}
.sc-points-v{font-family:Sora,sans-serif;font-size:1.1rem;font-weight:800;color:#f7f7fb;}
.sc-points-l{font-size:.58rem;font-weight:800;letter-spacing:.12em;text-transform:uppercase;color:#e8d5a7;margin-top:2px;}
.sc-tagline{
  color:#d6cfff;
  font-size:.7rem;
  font-weight:800;
  letter-spacing:.16em;
  text-transform:uppercase;
  margin-bottom:8px;
}
.sc-row{display:flex;align-items:center;gap:18px;flex-wrap:wrap;}
.sc-rankname{font-family:Sora,sans-serif;font-size:1.2rem;font-weight:800;color:#f7f7fb;}
.sc-ranknum{color:#d6cfff;font-size:.74rem;font-weight:800;letter-spacing:.14em;}
.sc-progresswrap{margin-top:16px;}
.sc-progresslabel{display:flex;justify-content:space-between;font-size:.74rem;color:#d3d4e0;font-weight:700;margin-bottom:6px;}
.sc-bar{height:12px;border-radius:999px;background:#23252f;overflow:hidden;border:1px solid var(--line);}
.sc-bar>div{height:100%;border-radius:inherit;background:linear-gradient(90deg,#a48bff,#5eead4);transition:width .4s ease;}
.sc-stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(110px,1fr));gap:10px;margin-top:18px;}
.sc-stat{padding:12px;border:1px solid var(--line);border-radius:13px;background:rgba(255,255,255,.045);text-align:center;}
.sc-stat-v{font-family:Sora,sans-serif;font-size:1.3rem;font-weight:800;color:#f7f7fb;}
.sc-stat-l{margin-top:3px;font-size:.63rem;font-weight:800;letter-spacing:.1em;text-transform:uppercase;color:#a7aabb;}
 
/* ---- BADGES (game-rank style emblem) ---- */
.sc-badge-wrap{position:relative;width:92px;height:92px;display:flex;align-items:center;justify-content:center;flex-shrink:0;}
.sc-badge-wrap.sc-lg{width:128px;height:128px;}
.sc-badge-wrap.sc-sm{width:56px;height:56px;}
.sc-badge-outer{
  position:absolute;inset:0;border-radius:50%;
  background:conic-gradient(from 180deg, var(--rc), #ffffff33, var(--rc), #00000055, var(--rc));
  padding:3px;
  -webkit-mask:radial-gradient(farthest-side,#000 calc(100% - 3px),transparent calc(100% - 3px));
          mask:radial-gradient(farthest-side,#000 calc(100% - 3px),transparent calc(100% - 3px));
}
.sc-badge-ring{
  position:absolute;inset:8px;border-radius:50%;
  border:1.5px dashed color-mix(in srgb, var(--rc) 70%, transparent);
  opacity:.8;
}
.sc-badge-core{
  position:absolute;inset:14px;border-radius:50%;
  display:grid;place-items:center;
  font-size:1.9rem;line-height:1;text-align:center;
  background:radial-gradient(circle at 32% 26%, color-mix(in srgb, var(--rc) 35%, transparent), #0d0e15 72%);
  border:2px solid color-mix(in srgb, var(--rc) 55%, transparent);
  box-shadow:inset 0 0 18px rgba(0,0,0,.5), 0 0 22px color-mix(in srgb, var(--rc) 35%, transparent);
}
.sc-badge-core span{display:block;transform:translateY(-0.04em);}
.sc-badge-wrap.sc-sm .sc-badge-core{font-size:1.1rem;inset:9px;}
.sc-badge-wrap.sc-sm .sc-badge-ring{inset:6px;}
.sc-badge-wrap.sc-lg .sc-badge-core{font-size:2.5rem;inset:18px;}
.sc-badge-tier{
  position:absolute;left:50%;bottom:-9px;transform:translateX(-50%);
  padding:2px 9px;border-radius:999px;
  background:linear-gradient(135deg, var(--rc), #0d0e15);
  border:1px solid rgba(255,255,255,.35);
  color:#fff;font-family:Sora,sans-serif;font-size:.62rem;font-weight:800;
  letter-spacing:.04em;white-space:nowrap;box-shadow:0 4px 10px rgba(0,0,0,.4);
}
.sc-badge-wrap.sc-sm .sc-badge-tier{display:none;}
.sc-anim-pulse{animation:sc-pulse 2.4s ease-in-out infinite;}
.sc-anim-rotate .sc-badge-ring{animation:sc-rotatering 7s linear infinite;}
.sc-anim-shimmer .sc-badge-core{position:relative;overflow:hidden;}
.sc-anim-shimmer .sc-badge-core:after{
  content:"";position:absolute;inset:0;
  background:linear-gradient(120deg,transparent 30%,rgba(255,255,255,.4) 50%,transparent 70%);
  background-size:220% 220%;animation:sc-shimmer 2.6s ease-in-out infinite;
}
.sc-anim-legend{animation:sc-pulse 1.7s ease-in-out infinite;}
.sc-anim-legend .sc-badge-ring{animation:sc-rotatering 4.2s linear infinite;}
.sc-anim-legend .sc-badge-core:after{
  content:"";position:absolute;inset:0;
  background:linear-gradient(120deg,transparent 30%,rgba(255,255,255,.5) 50%,transparent 70%);
  background-size:220% 220%;animation:sc-shimmer 1.8s ease-in-out infinite;
}
@keyframes sc-pulse{
  0%,100%{filter:drop-shadow(0 0 4px color-mix(in srgb, var(--rc) 45%, transparent));transform:scale(1);}
  50%{filter:drop-shadow(0 0 16px var(--rc));transform:scale(1.045);}
}
@keyframes sc-rotatering{0%{transform:rotate(0deg);}100%{transform:rotate(360deg);}}
@keyframes sc-shimmer{0%{background-position:-120% -120%;}100%{background-position:120% 120%;}}
 
/* ---- LEVEL MAP ---- */
.sc-rankblock{margin:22px 0 6px;padding:14px 16px;border:1px solid var(--line2);border-radius:16px;background:rgba(255,255,255,.035);}
.sc-rankblock-head{display:flex;align-items:center;gap:14px;margin-bottom:2px;}
.sc-rankblock-head>div{display:flex;flex-direction:column;justify-content:center;}
.sc-rankblock-title{font-family:Sora,sans-serif;font-weight:800;font-size:.95rem;color:#f5f5f9;}
.sc-rankblock-sub{font-size:.68rem;color:#a7aabb;font-weight:700;letter-spacing:.06em;margin-top:2px;}
.sc-cell{min-height:52px;border-radius:12px;border:1px solid var(--line);display:flex;flex-direction:column;align-items:center;justify-content:center;font-size:.72rem;font-weight:800;text-align:center;padding:4px;}
.sc-cell-locked{background:rgba(255,255,255,.02);color:#5f6273;opacity:.65;}
.sc-cell-completed{background:rgba(62,224,138,.12);border-color:rgba(62,224,138,.45);color:#a4f5c4;}
.sc-cell-current{background:rgba(164,139,255,.18);border-color:rgba(164,139,255,.8);color:#ece7ff;animation:sc-pulse 2.2s ease-in-out infinite;--rc:#a48bff;}
div[data-testid="stButton"]>button.sc-levelbtn-locked, div[data-testid="stButton"] button:disabled{opacity:.45;cursor:not-allowed;}
 
/* ---- HUD ---- */
.sc-hud{display:grid;grid-template-columns:repeat(auto-fit,minmax(100px,1fr));gap:10px;padding:14px;margin-bottom:14px;border:1px solid var(--line2);border-radius:15px;background:rgba(255,255,255,.04);}
.sc-hud-item{text-align:center;}
.sc-hud-v{font-family:Sora,sans-serif;font-size:1.15rem;font-weight:800;color:#f7f7fb;}
.sc-hud-l{font-size:.6rem;font-weight:800;letter-spacing:.1em;text-transform:uppercase;color:#a7aabb;margin-top:2px;}
.sc-qcard{padding:22px;border:1px solid var(--line2);border-radius:18px;background:rgba(255,255,255,.045);margin-bottom:14px;}
.sc-qcat{display:inline-block;padding:4px 11px;border-radius:999px;background:rgba(242,200,121,.13);border:1px solid rgba(242,200,121,.4);color:#f2c879;font-size:.62rem;font-weight:800;letter-spacing:.1em;text-transform:uppercase;margin-bottom:12px;}
.sc-qtext{font-size:1.06rem;line-height:1.55;color:#f5f5f9;font-weight:650;}
.sc-feedback{padding:16px 18px;border-radius:14px;margin:14px 0;font-weight:700;border:1px solid var(--line2);}
.sc-feedback-correct{background:rgba(62,224,138,.13);border-color:rgba(62,224,138,.45);color:#a4f5c4;}
.sc-feedback-wrong{background:rgba(255,92,92,.13);border-color:rgba(255,92,92,.45);color:#ffb3b3;}
.sc-feedback-pts{font-family:Sora,sans-serif;font-size:1.5rem;margin-top:2px;}
.sc-explain{padding:14px 16px;border-left:3px solid var(--violet);border-radius:12px;background:var(--violet2);color:#eceefb;line-height:1.6;font-size:.89rem;}
 
/* ---- RESULTS / RANKUP ---- */
.sc-results{padding:26px;border-radius:20px;border:1px solid var(--line2);text-align:center;background:linear-gradient(160deg,rgba(28,30,40,.94),rgba(13,14,20,.97));box-shadow:0 20px 55px rgba(0,0,0,.4);}
.sc-results-level{color:#a7aabb;font-size:.72rem;font-weight:800;letter-spacing:.14em;text-transform:uppercase;}
.sc-results-title{font-family:Sora,sans-serif;font-size:1.75rem;font-weight:800;color:#f7f7fb;margin:6px 0 18px;}
.sc-bigscore{font-family:Sora,sans-serif;font-size:2.7rem;font-weight:800;background:linear-gradient(90deg,#a48bff,#f2c879);-webkit-background-clip:text;background-clip:text;color:transparent;}
.sc-rankup-wrap{text-align:center;padding:34px 22px;border-radius:22px;border:1px solid rgba(242,200,121,.45);background:radial-gradient(circle at 50% 0%,rgba(242,200,121,.16),transparent 60%),linear-gradient(160deg,rgba(28,30,40,.95),rgba(13,14,20,.97));box-shadow:0 25px 65px rgba(0,0,0,.45);}
.sc-rankup-label{color:#f2c879;font-size:.8rem;font-weight:800;letter-spacing:.24em;text-transform:uppercase;margin-bottom:18px;}
.sc-rankup-newbadge{color:#a4f5c4;font-size:.72rem;font-weight:800;letter-spacing:.1em;text-transform:uppercase;margin-top:16px;}
@media (max-width:640px){
  .sc-badge-wrap.sc-lg{width:96px;height:96px;}
  .sc-badge-wrap.sc-lg .sc-badge-core{font-size:1.9rem;}
  .sc-bigscore{font-size:2rem;}
}
</style>
"""

# ----------------------- SC-LOGIC-START ------------------------
# ==============================================================
# SCAM CHALLENGE — game engine (100 levels x 10 questions)
# ==============================================================
SC_RANKS = [
    {"num": "I", "roman": "I", "name": "DIGITAL ROOKIE", "lo": 1, "hi": 10,
     "icon": "🛡️", "anim": "sc-anim-pulse", "color": "#7fd68f"},
    {"num": "II", "roman": "II", "name": "SCAM SCOUT", "lo": 11, "hi": 20,
     "icon": "🔎", "anim": "sc-anim-pulse", "color": "#5eead4"},
    {"num": "III", "roman": "III", "name": "THREAT TRACKER", "lo": 21, "hi": 30,
     "icon": "📡", "anim": "sc-anim-rotate", "color": "#7fb6ff"},
    {"num": "IV", "roman": "IV", "name": "CYBER SENTINEL", "lo": 31, "hi": 40,
     "icon": "🛰️", "anim": "sc-anim-pulse", "color": "#a48bff"},
    {"num": "V", "roman": "V", "name": "FRAUD HUNTER", "lo": 41, "hi": 50,
     "icon": "🎯", "anim": "sc-anim-rotate", "color": "#ff9f6e"},
    {"num": "VI", "roman": "VI", "name": "SECURITY OPERATIVE", "lo": 51, "hi": 60,
     "icon": "⚙️", "anim": "sc-anim-shimmer", "color": "#ffd166"},
    {"num": "VII", "roman": "VII", "name": "CYBER GUARDIAN", "lo": 61, "hi": 70,
     "icon": "🔰", "anim": "sc-anim-pulse", "color": "#57e5c4"},
    {"num": "VIII", "roman": "VIII", "name": "THREAT COMMANDER", "lo": 71, "hi": 80,
     "icon": "📶", "anim": "sc-anim-rotate", "color": "#ff8fc9"},
    {"num": "IX", "roman": "IX", "name": "CYBER MASTER", "lo": 81, "hi": 90,
     "icon": "💠", "anim": "sc-anim-shimmer", "color": "#c9a9ff"},
    {"num": "X", "roman": "X", "name": "SATARK LEGEND", "lo": 91, "hi": 100,
     "icon": "👁️", "anim": "sc-anim-legend", "color": "#f2c879"},
]
 
 
def sc_rank_for_level(level):
    level = max(1, min(100, level))
    for r in SC_RANKS:
        if r["lo"] <= level <= r["hi"]:
            return r
    return SC_RANKS[-1]
 
 
def sc_badge_html(rank, size="lg"):
    """Game-style rank emblem. Built flush-left / single-line to avoid
    Markdown treating indented HTML as a code block."""
    size_cls = {"lg": "sc-lg", "sm": "sc-sm", "md": ""}.get(size, "")
    return ('<div class="sc-badge-wrap ' + size_cls + ' ' + rank["anim"] + '" style="--rc:' + rank["color"] + '">'
            '<div class="sc-badge-outer"></div>'
            '<div class="sc-badge-ring"></div>'
            '<div class="sc-badge-core"><span>' + rank["icon"] + '</span></div>'
            '<div class="sc-badge-tier">RANK ' + rank["roman"] + '</div>'
            '</div>')
 
 
# ---------------- Shared vocabulary pools ----------------
SC_BANKS = ["HDFC Bank", "ICICI Bank", "SBI", "Axis Bank", "Kotak Mahindra", "Punjab National Bank", "Yes Bank", "IDFC First Bank"]
SC_UPI = ["PhonePe", "Google Pay", "Paytm", "BHIM UPI", "Amazon Pay"]
SC_COURIERS = ["Delhivery", "Blue Dart", "India Post", "DTDC", "Ekart", "Xpressbees"]
SC_NAMES = ["Rohan", "Priya", "Arjun", "Sneha", "Vikram", "Ananya", "Karan", "Meera", "Farhan", "Ishita", "Nikhil", "Divya", "Aditya", "Pooja"]
SC_COMPANIES = ["Infosys", "TCS", "Wipro", "a fast-growing startup", "a multinational retail chain", "a logistics firm", "an EdTech company"]
SC_BROKERS = ["a SEBI-sounding advisory group", "a private trading Telegram channel", "an unlisted 'wealth partner' app", "a 'VIP signals' WhatsApp group"]
SC_PLATFORMS = ["Instagram", "Facebook", "WhatsApp", "LinkedIn", "Telegram", "X (Twitter)"]
SC_CITIES = ["Lagos", "Kyiv", "a city you've never visited", "a foreign IP address", "Dubai", "an unfamiliar location abroad"]
SC_DEPTS = ["Head Office IT", "the Fraud Prevention cell", "Corporate Compliance", "the Risk Management team", "Network Security"]
SC_ITEMS = ["a used bike", "a gaming console", "furniture", "a smartphone", "a laptop", "a camera"]
SC_DOMAINS_REAL = ["amazon.in", "flipkart.com", "irctc.co.in", "paytm.com", "myntra.com", "zomato.com"]
SC_APPS = ["a food delivery app", "a bank app", "an e-commerce app", "a UPI app", "a ride-hailing app", "a streaming app"]
SC_DOC_TYPES = ["a shared invoice", "a payroll spreadsheet", "a project proposal", "a scanned contract", "a shared photo album"]
SC_REASONS = ["a medical emergency", "a car accident abroad", "being stranded at an airport", "an urgent visa fee", "a hospital deposit"]
SC_RELATIONS = ["a close relative", "your father", "your sister", "your best friend", "your spouse", "your son"]
 
 
def _mk(rng, category, question, correct, distractors, explanation, qtype="identify"):
    opts = [correct] + list(distractors)
    rng.shuffle(opts)
    return {
        "category": category,
        "qtype": qtype,
        "question": question,
        "options": opts,
        "answer": opts.index(correct),
        "explanation": explanation,
    }
 
 
def g_phishing(rng, tier):
    bank = rng.choice(SC_BANKS)
    mins = rng.choice([5, 10, 15, 20, 30, 45])
    code = rng.randint(100, 999)
    if tier <= 2:
        q = (f'An SMS says: "{bank}: Your account will be suspended in {mins} minutes. '
             f'Verify now: bit.ly/verify-{code}". What is the strongest warning sign?')
        correct = "Urgency + an unofficial shortened link asking you to 'verify'"
    else:
        domain = f"{bank.split()[0].lower()}-secure{code}.com"
        q = (f'You get an email that looks pixel-perfect like {bank}, includes your first name, '
             f'and links to "{domain}" to "re-confirm KYC" within {mins} minutes. What should worry you most?')
        correct = f"The domain '{domain}' is not the bank's real domain, despite the email looking authentic"
    return _mk(rng, "Phishing", q, correct, [
        "The email/SMS uses your first name",
        "The message is written in formal English",
        "The message arrived during business hours",
    ], "Legitimate banks never create artificial time pressure and never send verification "
       "links to look-alike domains. Always type the bank's known URL directly instead of "
       "clicking a link in an unsolicited message.")
 
 
def g_otp(rng, tier):
    who = rng.choice(["your bank's fraud department", "a 'customer care executive'", "a courier agent", "a delivery partner", "a 'RBI compliance officer'"])
    amt = rng.randint(2000, 60000)
    if tier <= 2:
        q = f'Someone calling from {who} asks you to read out the OTP you just received to "cancel a fraudulent transaction" of ₹{amt}. What should you do?'
        correct = "Refuse and hang up — never share an OTP with anyone who calls you"
    else:
        q = (f'{who.capitalize()} calls, already knows your last 4 card digits and full name, and asks you '
             f'to read an OTP to "reverse" a ₹{amt} transaction that never happened. What is the real purpose of the OTP?')
        correct = "The OTP would actually authorize a payment or login the caller is trying to complete"
    return _mk(rng, "OTP Scam", q, correct, [
        "It is needed to confirm your identity to the bank",
        "It is safe since they already know your card details",
        "Reading it out loud does not share it electronically",
    ], "An OTP is a one-time authorization code. No legitimate process ever requires you to "
       "read it to someone else — doing so approves whatever transaction the scammer initiated.")
 
 
def g_suspicious_link(rng, tier):
    topic = rng.choice(["a parcel customs fee", "a subscription renewal", "a KYC update", "a refund", "an electricity bill", "a SIM deactivation notice"])
    tag = rng.choice(['pay', 'kyc', 'verify', 'refund', 'update', 'confirm'])
    short = f"{rng.choice(['tiny.cc', 'bit.ly', 'cutt.ly'])}/{tag}{rng.randint(10, 999)}"
    channel = rng.choice(["WhatsApp", "SMS", "email"])
    q = f'A {channel} message about {topic} includes the link "{short}". Before tapping it, what should you check first?'
    correct = "Where the shortened link actually redirects to, using a link-preview/expander tool"
    return _mk(rng, "Suspicious Link", q, correct, [
        "Whether the message has correct spelling",
        "How many people the message was forwarded to",
        "Whether the sender has a profile photo",
    ], "Shortened links hide the real destination. Expanding or hovering over a link before "
       "clicking reveals the true domain, which is the single most reliable signal.")
 
 
def g_fake_prize(rng, tier):
    amt = rng.choice([15000, 25000, 35000, 50000, 75000, 100000, 150000])
    fee = rng.choice([299, 499, 999, 1499, 1999])
    platform = rng.choice(["a lucky draw you never entered", "a festival giveaway you don't remember joining", "a mobile-recharge lottery"])
    q = (f'A message says you have won ₹{amt:,} in {platform}, and asks for a '
         f'₹{fee} "processing fee" to release it. What is the biggest red flag?')
    correct = "Genuine prizes are never released by first collecting a fee from the winner"
    return _mk(rng, "Fake Prize", q, correct, [
        "The amount is too large to be real",
        "The message uses the word 'lucky draw'",
        "The fee is a round number",
    ], "Legitimate lotteries or rewards deduct tax/fees from the winnings itself — they never "
       "ask winners to pay money upfront to 'unlock' a prize.")
 
 
def g_impersonation(rng, tier):
    name = rng.choice(SC_NAMES)
    role = rng.choice(["your manager", "a close relative", "your company's HR head", "an old college friend", "your landlord"])
    amt = rng.choice([1000, 2000, 5000, 10000])
    q = (f'You get a message that looks exactly like it is from {role} ("{name}"), asking you to urgently '
         f'buy ₹{amt} in gift cards and send the codes because they are "in a meeting and can\'t call." What should you do?')
    correct = "Verify through a separate channel (a phone call) before taking any action"
    return _mk(rng, "Impersonation", q, correct, [
        "Comply quickly since it sounds urgent",
        "Reply asking for more details over the same chat",
        "Ignore it completely without checking",
    ], "Impersonation scams rely on urgency and an inability to verify in the moment. A quick "
       "call to the real person on a known number instantly exposes the scam.")
 
 
def g_fake_support(rng, tier):
    app = rng.choice(SC_APPS)
    issue = rng.choice(["a failed refund", "a login issue", "a stuck payment", "an app crash", "a missing order"])
    wait = rng.choice([2, 5, 10, 15])
    q = (f'You search online for {app} customer care about {issue}, wait {wait} minutes, and call a number '
         f'from the results. The agent asks you to install a remote-access app "to fix the issue faster." '
         f'What is the danger here?')
    correct = "Remote-access tools give the caller full control of your device, including banking apps"
    return _mk(rng, "Fake Support", q, correct, [
        "Remote apps use too much data",
        "It will slow down your phone",
        "Support calls are always free anyway",
    ], "Fake customer-care numbers are frequently seeded on the open web. Once a scammer has "
       "remote access, they can open your banking apps directly — never install remote-access "
       "software at the request of an unsolicited 'support' call.")
 
 
def g_delivery(rng, tier):
    courier = rng.choice(SC_COURIERS)
    fee = rng.choice([2, 5, 10, 19, 25, 49])
    reason = rng.choice(["customs fee", "address correction fee", "storage fee", "re-delivery fee"])
    tracking = rng.randint(100000000, 999999999)
    q = (f'An SMS claims to be from {courier} (tracking #{tracking}): "Your parcel is on hold, pay ₹{fee} '
         f'{reason} to release it: {courier.lower().replace(" ", "")}-track.info/pay". What should you do first?')
    correct = "Track the order directly on the courier's official app/site instead of the SMS link"
    return _mk(rng, "Delivery Scam", q, correct, [
        "Pay the small fee since it is inexpensive",
        "Forward the SMS to friends to warn them first",
        "Reply STOP to the SMS",
    ], "The tiny fee is deliberate — designed to feel too small to question. The link domain "
       "is not the courier's real domain, and real customs charges are never collected via SMS links.")
 
 
def g_fake_bank_msg(rng, tier):
    bank = rng.choice(SC_BANKS)
    amt = rng.randint(8000, 95000)
    phone = rng.randint(70000, 99999)
    q = (f'An SMS reads: "{bank}: ₹{amt} debited from your a/c. If not done by you, call {phone}'
         f'{rng.randint(10000, 99999)} immediately." Calling this number connects you to a scammer. '
         f'What is the actual pattern here?')
    correct = "A fake debit alert designed to make you call a scammer-controlled 'helpline' in a panic"
    return _mk(rng, "Fake Bank Message", q, correct, [
        "A normal fraud-alert SMS from the bank",
        "A system-generated OTP message",
        "A promotional offer from the bank",
    ], "Fabricated debit alerts create panic so the victim calls a number controlled by the "
       "scammer, who then asks for card/OTP details to 'reverse' a transaction that never happened.")
 
 
def g_upi(rng, tier):
    app = rng.choice(SC_UPI)
    amt = rng.randint(500, 25000)
    item = rng.choice(SC_ITEMS)
    if tier <= 2:
        q = (f'You receive a {app} notification: "You have a payment request for ₹{amt}. Approve to receive money." '
             f'What should you know about UPI collect requests?')
        correct = "Approving a 'collect request' sends money OUT of your account, it never receives money"
    else:
        q = (f'A seller offering {item} on a resale marketplace insists on sending you a {app} "collect request" '
             f'instead of a normal transfer, to pay you ₹{amt} for the item. Why is this suspicious?')
        correct = "Collect requests only debit money from the person who approves them — the buyer wants you to pay, not get paid"
    return _mk(rng, "UPI Scam", q, correct, [
        "Collect requests are just a faster way to receive money",
        "It only works if you also enter your UPI PIN twice",
        "It is safe as long as the request is under ₹2,000",
    ], "A UPI 'collect' request always deducts money from whoever approves it. Anyone asking "
       "you to approve a collect request to 'receive' a payment is trying to debit your account.")
 
 
def g_qr(rng, tier):
    amt = rng.randint(800, 30000)
    reason = rng.choice(["a refund for a returned item", "a cashback offer", "a prize claim", "a security deposit return"])
    q = (f'To process {reason} of ₹{amt}, someone asks you to scan a QR code and enter your UPI PIN. '
         f'What is wrong with this request?')
    correct = "Scanning a QR code and entering a PIN is always used to SEND money, never to receive it"
    return _mk(rng, "QR Scam", q, correct, [
        "QR codes can only be used once",
        "They should have used a bank transfer instead",
        "QR refunds take longer than UPI IDs",
    ], "Receiving money never requires scanning a QR code or entering your PIN. Any process "
       "that asks for a PIN after a QR scan is a payment being pulled from your account.")
 
 
def g_job(rng, tier):
    company = rng.choice(SC_COMPANIES)
    pay = rng.randint(25, 95) * 1000
    task = rng.choice(["liking videos", "reviewing hotels online", "data entry", "typing captchas", "forwarding messages"])
    fee = rng.choice([500, 999, 1500, 2500])
    q = (f'A recruiter messages you a "work-from-home" job at {company} paying ₹{pay:,}/month for {task}, '
         f'but asks for a refundable ₹{fee} "registration fee" first. What should you suspect?')
    correct = "A job scam — legitimate employers never charge candidates to be hired"
    return _mk(rng, "Job Scam", q, correct, [
        "The pay is fair for the work described",
        "Refundable fees are always safe to pay",
        "This is normal for remote jobs",
    ], "Any job that asks the candidate to pay money upfront — registration, training kits, "
       "or 'refundable' deposits — is a strong indicator of a job scam, regardless of the brand name used.")
 
 
def g_social_impersonation(rng, tier):
    platform = rng.choice(SC_PLATFORMS)
    name = rng.choice(SC_NAMES)
    amt = rng.choice([2000, 5000, 8000, 15000])
    q = (f'A {platform} account using {name}\'s name and real photos messages your friends asking to borrow '
         f'₹{amt}, but the real {name} says they never sent it. What happened?')
    correct = f"The account (or {name}'s real account) was cloned or compromised to scam their contacts"
    return _mk(rng, "Social Media Impersonation", q, correct, [
        f"{name} is lying to avoid repaying a real loan",
        "It is a coincidence and unrelated accounts",
        "Social platforms cannot be impersonated",
    ], "Cloned or hacked profiles are commonly used to message a real person's existing contacts, "
       "who are more likely to trust a request that appears to come from someone they know.")
 
 
def g_advanced_phishing(rng, tier):
    bank = rng.choice(SC_BANKS)
    tail = rng.choice(["alerts", "secure-kyc", "netbanking", "verify", "support"])
    code = rng.randint(10, 99)
    q = (f'An email from "{bank.lower().replace(" ", "")}-{tail}{code}.com" has correct grammar, the real logo, '
         f'a real customer-support footer, and a login page that looks identical to {bank}\'s real site. '
         f'What is the one detail that reliably exposes it?')
    correct = "The sending domain does not match the bank's official domain, even though everything else looks right"
    return _mk(rng, "Advanced Phishing", q, correct, [
        "The email contains the bank's logo",
        "The email has no spelling mistakes",
        "The page asks for a login and password",
    ], "Sophisticated phishing kits can copy visual design perfectly. The domain in the address "
       "bar (not the page's appearance) is the one element attackers cannot fake convincingly.")
 
 
def g_url_manipulation(rng, tier):
    real = rng.choice(SC_DOMAINS_REAL)
    style = rng.choice(["hyphen-insert", "char-swap", "subdomain-trick", "extra-word"])
    order_id = rng.randint(100000, 999999)
    channel = rng.choice(["a tracking SMS", "an order-confirmation email", "a WhatsApp forward", "a push notification"])
    base, tld = real.split(".", 1)
    if style == "hyphen-insert":
        fake = f"{base}-secure.{tld}"
    elif style == "char-swap":
        fake = real.replace("o", "0", 1) if "o" in real else real.replace("i", "1", 1)
    elif style == "subdomain-trick":
        fake = f"{base}.{tld}.login-verify.com"
    else:
        fake = f"{base}account.{tld}"
    q = (f'{channel.capitalize()} about order #{order_id} links to "https://{fake}", claiming to be {real}. '
         f'Which of these URLs is most likely a manipulated look-alike of "{real}"?')
    correct = fake
    distract = [real, f"www.{real}", f"{real}/account"]
    return _mk(rng, "URL Manipulation", q, correct, distract,
               f"'{fake}' subtly alters the real domain '{real}' — extra words, character swaps, or "
               f"fake subdomains are invisible at a glance but resolve to an entirely different, "
               f"attacker-controlled server.")
 
 
def g_domain_spoofing(rng, tier):
    real = rng.choice(["hdfcbank.com", "icicibank.com", "sbi.co.in", "axisbank.com", "kotak.com", "yesbank.in", "idfcfirstbank.com"])
    tail = rng.choice(["verify", "secure-login", "kyc-update", "account-check", "reactivate", "confirm-id"])
    ref = rng.randint(10000, 99999)
    spoof = real.split(".")[0] + f"-{tail}.net"
    q = (f'A login page URL reads "https://{spoof}/login?ref={ref}" '
         f'and displays a padlock icon (HTTPS). Does the padlock mean the site is safe?')
    correct = "No — HTTPS only means the connection is encrypted, not that the site is genuine"
    return _mk(rng, "Domain Spoofing", q, correct, [
        "Yes, the padlock guarantees it is the real bank",
        "Yes, because scam sites cannot get HTTPS certificates",
        "It depends on the browser being used",
    ], "Attackers can obtain valid HTTPS certificates for spoofed domains just as easily as "
       "legitimate sites. Encryption protects data in transit, it says nothing about who owns the site.")
 
 
def g_social_engineering(rng, tier):
    dept = rng.choice(SC_DEPTS)
    mgr = rng.choice(SC_NAMES)
    channel = rng.choice(["a code sent to your phone", "your email verification code", "your login PIN"])
    ticket = rng.randint(1000, 9999)
    q = (f'A caller claiming to be from "{dept}" (case #INC-{ticket}) says your system was flagged for a '
         f'security breach, creates urgency, name-drops your actual manager "{mgr}", and asks you to read '
         f'back {channel} to "confirm your identity." What technique is being used?')
    correct = "Pretexting — building a believable false scenario using real details to lower your guard"
    return _mk(rng, "Social Engineering", q, correct, [
        "Standard IT security verification",
        "A phishing email, not a phone technique",
        "Two-factor authentication working correctly",
    ], "Social engineers research real names, roles and jargon in advance so the pretext feels "
       "credible. The actual goal is almost always to extract a one-time code or credential from you directly.")
 
 
def g_fake_support_interaction(rng, tier):
    app = rng.choice(SC_APPS)
    minutes = rng.choice([3, 5, 8, 10, 12, 15])
    ticket = rng.randint(100000, 999999)
    issue = rng.choice(["a failed refund", "a duplicate charge", "an OTP that never arrived", "a login lockout"])
    q = (f'While troubleshooting {issue} on {app} via a chat with "support" (ticket #{ticket}), the agent '
         f'insists on screen-sharing and asks you to open your banking app "just to check the balance shown," '
         f'without ever asking for a password. The session lasts {minutes} minutes. Why is this still risky?')
    correct = "A screen-share alone lets the agent see OTPs, balances, and account numbers as you type them"
    return _mk(rng, "Fake Support Interaction", q, correct, [
        "It is safe since they never asked for a password",
        "Screen sharing cannot capture banking apps",
        "It is fine as long as the session stays short",
    ], "Never entering a password doesn't make screen-sharing safe — everything visible on "
       "screen, including OTP pop-ups and account details, is captured by the person watching.")
 
 
def g_marketplace(rng, tier):
    item = rng.choice(SC_ITEMS)
    pay = rng.choice(["a courier company's 'advance payment protection'", "a 'buyer protection escrow' link", "a 'marketplace insurance' form"])
    price = rng.randint(3, 90) * 1000
    q = (f'A buyer offers ₹{price:,} for your {item} on an online marketplace, then insists on paying via '
         f'{pay} and sends a fake link to "verify" your bank details before shipping. What should you do?')
    correct = "Refuse — never enter bank details on a link sent by a buyer; use the marketplace's own payment flow"
    return _mk(rng, "Marketplace Scam", q, correct, [
        "Proceed since the name sounds official",
        "Share only the last 4 digits of your account",
        "Ask the buyer for ID proof first",
    ], "'Payment protection' links from buyers are a classic marketplace scam — the link is a "
       "credential-harvesting page, not a real courier or payment provider.")
 
 
def g_account_takeover(rng, tier):
    service = rng.choice(["email", "social media", "banking app", "cloud storage"])
    city = rng.choice(SC_CITIES)
    device = rng.choice(["an unrecognised Android device", "an unrecognised Windows PC", "an unknown browser session", "a device you've never used"])
    mins = rng.choice([2, 4, 6, 9, 12])
    q = (f'You get a "New login detected" alert for your {service} account from {city} on {device}, followed '
         f'{mins} minutes later by a password-reset email you did not request. What is the correct immediate action?')
    correct = "Change the password immediately from a trusted device and enable/verify two-factor authentication"
    return _mk(rng, "Account Takeover", q, correct, [
        "Ignore it since the login may have failed",
        "Wait 24 hours to see if it happens again",
        "Reply to the alert email asking who logged in",
    ], "A login alert followed by an unrequested reset email indicates an active takeover attempt. "
       "Acting immediately — before the attacker completes the reset — is what limits the damage.")
 
 
def g_bec(rng, tier):
    role = rng.choice(["CEO", "CFO", "Managing Director", "VP Finance"])
    dept = rng.choice(["finance team", "accounts payable team", "procurement desk"])
    amt = rng.randint(2, 25)
    decimal = rng.choice([0, 25, 5, 75])
    invoice = rng.randint(1000, 9999)
    q = (f'An email (re: invoice #{invoice}) that appears to be from your {role}, sent from a domain differing '
         f'by one letter from your company\'s real domain, urgently asks the {dept} to wire ₹{amt}.{decimal:02d} '
         f'lakh to a "new vendor account" and says not to call because they are "in back-to-back meetings." '
         f'What is this?')
    correct = "Business Email Compromise (BEC) — impersonating an executive to bypass normal payment checks"
    return _mk(rng, "Business Email Compromise", q, correct, [
        "A normal, time-sensitive vendor payment",
        "An internal IT test of the finance workflow",
        "A phishing attempt aimed at employees' personal accounts",
    ], "BEC attacks specifically target finance/payment approval steps by impersonating "
       "executives and discouraging verification. The 'don't call me' instruction is itself a red flag.")
 
 
def g_credential_harvesting(rng, tier):
    doc = rng.choice(SC_DOC_TYPES)
    host = rng.choice(["a generic cloud-storage-lookalike domain", "a link-shortener redirect", "a domain with no company branding at all"])
    sender = rng.choice(SC_NAMES)
    ref = rng.randint(1000, 9999)
    q = (f'"{sender}" shares a link (doc ref #{ref}) to {doc} that requires you to "sign in with your work '
         f'email and password" on a page hosted on {host} before you can view it. What is actually happening?')
    correct = "The login form is a fake page designed only to capture your email and password"
    return _mk(rng, "Credential Harvesting", q, correct, [
        "The document is protected for legitimate privacy reasons",
        "This is standard for all shared documents",
        "It only matters if you reuse the same password elsewhere",
    ], "Fake 'sign in to view' pages exist purely to capture credentials. Reusing the same "
       "password elsewhere is what turns one leaked login into access to many other accounts.")
 
 
def g_investment(rng, tier):
    source = rng.choice(SC_BROKERS)
    pct = rng.choice([12, 15, 20, 25, 30, 40])
    window = rng.choice(["monthly", "weekly", "in 10 days"])
    minimum = rng.randint(3, 150) * 1000
    members = rng.randint(200, 9000)
    q = (f'{source.capitalize()} ({members:,} members) asks for a minimum ₹{minimum:,} deposit and promises '
         f'guaranteed {pct}% {window} returns on a "pre-IPO" investment, showing screenshots of other members\' '
         f'profits. What is the strongest warning sign?')
    correct = "A 'guaranteed' high fixed return — genuine investments always carry risk and no fixed guarantee"
    return _mk(rng, "Investment Scam", q, correct, [
        "The group has many active members",
        "The screenshots look professionally made",
        "It focuses on pre-IPO companies",
    ], "No legitimate investment can guarantee fixed high returns — markets carry risk by "
       "definition. Guaranteed-return promises are one of the most consistent signals of an investment scam.")
 
 
def g_multistage(rng, tier):
    days = rng.choice([3, 5, 7, 10, 14, 21])
    mentor = rng.choice(["trading mentor", "crypto guru", "forex expert", "'senior analyst'", "portfolio coach"])
    app = rng.choice(["a special trading app", "a 'partner exchange' website", "a private investment portal", "an exclusive members-only platform"])
    seed_profit = rng.randint(500, 9000)
    platform = rng.choice(SC_PLATFORMS)
    q = (f'Over {days} days on {platform}, a new online contact builds rapport, then mentions a "{mentor}," '
         f'then shows a real ₹{seed_profit} profit on a small trade to build trust, then asks you to move '
         f'larger funds to {app}. What is this multi-stage pattern designed to do?')
    correct = "Slowly build trust before introducing the actual financial ask, making the final request feel earned"
    return _mk(rng, "Multi-Stage Social Engineering", q, correct, [
        "Test your knowledge of trading before offering real advice",
        "Standard onboarding for legitimate trading platforms",
        "A random coincidence with no coordinated goal",
    ], "Multi-stage scams (often called 'pig butchering' scams) deliberately spread the "
       "manipulation over days or weeks so the final financial request doesn't feel sudden or risky.")
 
 
def g_deepfake(rng, tier):
    relation = rng.choice(SC_RELATIONS)
    reason = rng.choice(SC_REASONS)
    amt = rng.randint(10, 80) * 1000
    q = (f'You receive a video call that looks and sounds exactly like {relation}, asking you to urgently '
         f'transfer ₹{amt:,} for {reason}, but the call keeps freezing at odd moments and cuts off '
         f'before you can ask a personal verification question. What should you do?')
    correct = "Hang up and call the relative back directly on their known number before sending anything"
    return _mk(rng, "Deepfake Scam", q, correct, [
        "Trust it since the face and voice matched",
        "Ask them to repeat themselves on the same call",
        "Transfer a smaller amount to be safe",
    ], "Real-time deepfake audio/video can convincingly mimic appearance and voice but often "
       "glitches under unexpected questions. A callback on an independently known number defeats "
       "the scam because the attacker cannot intercept it.")
 
 
def g_romance(rng, tier):
    platform = rng.choice(SC_PLATFORMS + ["a dating app"])
    weeks = rng.choice([2, 3, 4, 6, 8])
    amt = rng.randint(15, 60) * 1000
    excuse = rng.choice(["a customs fee to fly and meet you", "a hospital bill after an accident", "releasing a 'seized' gift package"])
    q = (f'An online partner on {platform} you have never met in person, after {weeks} weeks of daily messages, '
         f'says they need ₹{amt:,} for {excuse}, promising to repay double. What pattern is this?')
    correct = "A romance scam — emotional investment is used to justify an urgent money request"
    return _mk(rng, "Romance Scam", q, correct, [
        "A genuine emergency that should be trusted given the relationship",
        "A normal travel delay unrelated to money",
        "Proof that the relationship is serious",
    ], "Romance scams invest weeks in emotional connection specifically so a later money "
       "request feels like helping someone you care about, rather than a stranger's demand.")
 
 
SC_GENERATORS = {
    "Phishing": g_phishing, "OTP Scam": g_otp, "Suspicious Link": g_suspicious_link,
    "Fake Prize": g_fake_prize, "Impersonation": g_impersonation, "Fake Support": g_fake_support,
    "Delivery Scam": g_delivery, "Fake Bank Message": g_fake_bank_msg, "UPI Scam": g_upi,
    "QR Scam": g_qr, "Job Scam": g_job, "Social Media Impersonation": g_social_impersonation,
    "Advanced Phishing": g_advanced_phishing, "URL Manipulation": g_url_manipulation,
    "Domain Spoofing": g_domain_spoofing, "Social Engineering": g_social_engineering,
    "Fake Support Interaction": g_fake_support_interaction, "Marketplace Scam": g_marketplace,
    "Account Takeover": g_account_takeover, "Business Email Compromise": g_bec,
    "Credential Harvesting": g_credential_harvesting, "Investment Scam": g_investment,
    "Multi-Stage Social Engineering": g_multistage, "Deepfake Scam": g_deepfake,
    "Romance Scam": g_romance,
}
 
SC_TIER_CATEGORIES = {
    1: ["Phishing", "OTP Scam", "Suspicious Link", "Fake Prize", "Impersonation", "Fake Support"],
    2: ["Delivery Scam", "Fake Bank Message", "UPI Scam", "QR Scam", "Job Scam", "Social Media Impersonation"],
    3: ["Advanced Phishing", "URL Manipulation", "Domain Spoofing", "Social Engineering",
        "Fake Support Interaction", "Marketplace Scam"],
    4: ["Account Takeover", "Business Email Compromise", "Credential Harvesting", "Investment Scam",
        "Multi-Stage Social Engineering", "Deepfake Scam", "Romance Scam"],
}
SC_TIER_CATEGORIES[5] = SC_TIER_CATEGORIES[3] + SC_TIER_CATEGORIES[4]
SC_TIER_CATEGORIES[6] = SC_TIER_CATEGORIES[4] + ["Advanced Phishing", "Domain Spoofing", "Social Engineering"]
SC_TIER_CATEGORIES[7] = SC_TIER_CATEGORIES[4] + ["Multi-Stage Social Engineering", "Deepfake Scam", "Business Email Compromise"]
 
 
def sc_tier_for_level(level):
    if level <= 10:
        return 1
    if level <= 20:
        return 2
    if level <= 40:
        return 3
    if level <= 60:
        return 4
    if level <= 80:
        return 5
    if level <= 90:
        return 6
    return 7
 
 
# Max points per question (was 1000, now 2000 -> 20,000 max per level)
SC_MAX_POINTS = 2000
 
 
@st.cache_data(show_spinner=False)
def sc_build_bank():
    bank = {}
    for level in range(1, 101):
        tier = sc_tier_for_level(level)
        cats = SC_TIER_CATEGORIES[tier]
        offset = (level * 3) % len(cats)
        questions = []
        for qi in range(10):
            category = cats[(qi + offset) % len(cats)]
            rng = random.Random(level * 1000 + qi * 7 + 13)
            qd = SC_GENERATORS[category](rng, tier)
            qd["id"] = f"L{level}Q{qi+1}"
            qd["level"] = level
            qd["difficulty"] = tier
            qd["maxPoints"] = SC_MAX_POINTS
            questions.append(qd)
        bank[level] = questions
    return bank
 
 
def sc_compute_points(correct, elapsed):
    if not correct:
        return 0
    t = max(0.0, elapsed)
    raw = SC_MAX_POINTS * math.exp(-t / 18.0)
    floor_pts = int(SC_MAX_POINTS * 0.08)  # 160 at 2000 max
    return int(max(floor_pts, min(SC_MAX_POINTS, round(raw))))
 
 
# ------------------------ SC-LOGIC-END -------------------------

# ------------------------ SC-UI-START ---------------------------
# ---------------- Scam Challenge — UI / state helpers ----------------
def sc_start_level(level):
    """Server-side guarded entry point — never trust a button existing as the only gate."""
    if level < 1 or level > 100:
        return
    if level > st.session_state.sc_highest_unlocked:
        st.warning("That level is still locked. Complete the earlier levels first.")
        return
    st.session_state.sc_playing_level = level
    st.session_state.sc_q_idx = 0
    st.session_state.sc_answered = False
    st.session_state.sc_selected_idx = None
    st.session_state.sc_level_correct = 0
    st.session_state.sc_level_incorrect = 0
    st.session_state.sc_level_times = []
    st.session_state.sc_level_points = 0
    st.session_state.sc_q_start = time.time()
    st.session_state.sc_view = "play"
 
 
def sc_progress_pct():
    return round(((st.session_state.sc_highest_unlocked - 1) / 100) * 100)
 
 
def render_sc_dashboard():
    rank = sc_rank_for_level(st.session_state.sc_highest_unlocked)
    pct = sc_progress_pct()
    completed_n = len(st.session_state.sc_completed_levels)
    lvl_label = str(min(st.session_state.sc_highest_unlocked, 100))
    # NOTE: the whole card is rendered in ONE st.markdown call. Splitting an
    # opening <div> and its closing </div> across separate st.markdown calls
    # does not nest them in Streamlit — each call is its own isolated DOM
    # node, so the browser auto-closes the stray tag and you get an empty
    # styled box with the real content floating outside it underneath.
    st.markdown(
        '<div class="sc-dash">'
        '<div class="sc-tagline">THINK FAST. SPOT THE SCAM. STAY SATARK.</div>'
        '<div class="sc-row">'
        '<div class="sc-dash-badge">' + sc_badge_html(rank, "lg") + '</div>'
        '<div class="sc-dash-rankinfo">'
        '<div class="sc-ranknum">RANK ' + rank["roman"] + '</div>'
        '<div class="sc-rankname">' + rank["name"] + '</div>'
        '<div class="sc-progresswrap">'
        '<div class="sc-progresslabel"><span>LEVEL ' + lvl_label + ' / 100</span><span>' + str(pct) + '%</span></div>'
        '<div class="sc-bar"><div style="width:' + str(pct) + '%"></div></div>'
        '</div>'
        '</div>'
        '</div>'
        '<div class="sc-stats">'
        '<div class="sc-stat"><div class="sc-stat-v">' + f'{st.session_state.sc_total_score:,}' + '</div><div class="sc-stat-l">Total Score</div></div>'
        '<div class="sc-stat"><div class="sc-stat-v">' + str(completed_n) + '</div><div class="sc-stat-l">Completed</div></div>'
        '<div class="sc-stat"><div class="sc-stat-v">' + str(100 - completed_n) + '</div><div class="sc-stat-l">Remaining</div></div>'
        '</div>'
        '</div>',
        unsafe_allow_html=True
    )
    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        if st.session_state.sc_highest_unlocked > 100:
            label = "🏆 Replay Level Map"
        else:
            label = f"Continue Challenge → Level {st.session_state.sc_highest_unlocked}"
        if st.button(label, key="sc_continue", type="primary", use_container_width=True):
            sc_start_level(min(st.session_state.sc_highest_unlocked, 100))
            st.rerun()
    with c2:
        if st.button("🗺️ View Level Map", key="sc_view_map", use_container_width=True):
            st.session_state.sc_view = "levelmap"
            st.rerun()
 
 
def render_sc_levelmap():
    if st.button("← Back to Dashboard", key="sc_map_back"):
        st.session_state.sc_view = "dashboard"
        st.rerun()
    for rank in SC_RANKS:
        completed_in_block = sum(
            1 for lv in range(rank["lo"], rank["hi"] + 1)
            if lv in st.session_state.sc_completed_levels
        )
        perfect_in_block = sum(
            1 for lv in range(rank["lo"], rank["hi"] + 1)
            if lv in st.session_state.sc_perfect_levels
        )
        st.markdown(
            '<div class="sc-rankblock">'
            '<div class="sc-rankblock-head">'
            + sc_badge_html(rank, "sm") +
            '<div>'
            '<div class="sc-rankblock-title">RANK ' + rank["roman"] + ' • ' + rank["name"] + '</div>'
            '<div class="sc-rankblock-sub">LEVELS ' + str(rank["lo"]) + '–' + str(rank["hi"]) + ' • '
            + str(completed_in_block) + '/10 COMPLETE • ' + str(perfect_in_block)
            + '/10 PERFECT (needed to rank up)</div>'
            '</div>'
            '</div>'
            '</div>',
            unsafe_allow_html=True
        )
        levels = list(range(rank["lo"], rank["hi"] + 1))
        for row_start in (0, 5):
            cols = st.columns(5)
            for i, lv in enumerate(levels[row_start:row_start + 5]):
                with cols[i]:
                    if lv in st.session_state.sc_completed_levels:
                        mark = "★" if lv in st.session_state.sc_perfect_levels else "✓"
                        if st.button(f"{mark} {lv:02d}", key=f"sc_lvl_{lv}", use_container_width=True):
                            sc_start_level(lv)
                            st.rerun()
                    elif lv == st.session_state.sc_highest_unlocked:
                        if st.button(f"▶ {lv:02d}", key=f"sc_lvl_{lv}", type="primary", use_container_width=True):
                            sc_start_level(lv)
                            st.rerun()
                    elif lv <= st.session_state.sc_highest_unlocked:
                        if st.button(f"{lv:02d}", key=f"sc_lvl_{lv}", use_container_width=True):
                            sc_start_level(lv)
                            st.rerun()
                    else:
                        st.markdown(
                            '<div class="sc-cell sc-cell-locked">🔒<br>' + f'{lv:02d}' + '</div>',
                            unsafe_allow_html=True
                        )
 
 
def render_sc_play():
    level = st.session_state.sc_playing_level
    bank = sc_build_bank()
    questions = bank[level]
    qi = st.session_state.sc_q_idx
    q = questions[qi]
    rank = sc_rank_for_level(level)
 
    top_l, top_r = st.columns([1, 5])
    with top_l:
        if st.button("← Exit", key="sc_play_exit"):
            st.session_state.sc_playing_level = None
            st.session_state.sc_view = "levelmap"
            st.rerun()
 
    acc_txt = f"{st.session_state.sc_level_correct}/{qi + (1 if st.session_state.sc_answered else 0)}"
    st.markdown(
        '<div class="sc-hud">'
        '<div class="sc-hud-item"><div class="sc-hud-v">' + f'{level:02d}' + '</div><div class="sc-hud-l">Level</div></div>'
        '<div class="sc-hud-item"><div class="sc-hud-v">' + f'{qi+1}/10' + '</div><div class="sc-hud-l">Question</div></div>'
        '<div class="sc-hud-item"><div class="sc-hud-v">' + f'{st.session_state.sc_level_points:,}' + '</div><div class="sc-hud-l">Score</div></div>'
        '<div class="sc-hud-item"><div class="sc-hud-v">' + acc_txt + '</div><div class="sc-hud-l">Accuracy</div></div>'
        '<div class="sc-hud-item"><div class="sc-hud-v">' + rank["roman"] + '</div><div class="sc-hud-l">Rank</div></div>'
        '</div>',
        unsafe_allow_html=True
    )
    st.markdown(
        '<div class="sc-qcard">'
        '<div class="sc-qcat">' + q["category"] + '</div>'
        '<div class="sc-qtext">' + q["question"] + '</div>'
        '</div>',
        unsafe_allow_html=True
    )
    if not st.session_state.sc_answered:
        cols = st.columns(2)
        for idx, opt in enumerate(q["options"]):
            with cols[idx % 2]:
                if st.button(opt, key=f"sc_opt_{level}_{qi}_{idx}", use_container_width=True):
                    elapsed = time.time() - (st.session_state.sc_q_start or time.time())
                    correct = (idx == q["answer"])
                    points = sc_compute_points(correct, elapsed)
                    st.session_state.sc_selected_idx = idx
                    st.session_state.sc_answered = True
                    st.session_state.sc_last_points = points
                    st.session_state.sc_last_correct = correct
                    st.session_state.sc_last_elapsed = elapsed
                    st.session_state.sc_level_points += points
                    st.session_state.sc_level_times.append(elapsed)
                    if correct:
                        st.session_state.sc_level_correct += 1
                    else:
                        st.session_state.sc_level_incorrect += 1
                    st.rerun()
    else:
        correct = st.session_state.sc_last_correct
        pts = st.session_state.sc_last_points
        elapsed = st.session_state.sc_last_elapsed
        if correct:
            st.markdown(
                '<div class="sc-feedback sc-feedback-correct">✓ CORRECT — answered in ' + f'{elapsed:.1f}s'
                + '<div class="sc-feedback-pts">+' + str(pts) + ' POINTS</div></div>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                '<div class="sc-feedback sc-feedback-wrong">✕ INCORRECT<div class="sc-feedback-pts">0 POINTS</div></div>',
                unsafe_allow_html=True
            )
        st.markdown(
            '<div class="sc-explain"><strong>Correct answer:</strong> ' + q["options"][q["answer"]] + '<br><br>'
            '<strong>Why:</strong> ' + q["explanation"] + '</div>',
            unsafe_allow_html=True
        )
        is_last = (qi == 9)
        btn_label = "Finish Level →" if is_last else "Next Question →"
        if st.button(btn_label, key=f"sc_next_{level}_{qi}", type="primary", use_container_width=True):
            if is_last:
                sc_finish_level(level)
            else:
                st.session_state.sc_q_idx += 1
                st.session_state.sc_answered = False
                st.session_state.sc_selected_idx = None
                st.session_state.sc_q_start = time.time()
            st.rerun()
 
 
def sc_rank_levels_all_perfect(rank):
    """True only if every one of the rank's 10 levels has been aced (10/10) at least once."""
    return all(
        lv in st.session_state.sc_perfect_levels
        for lv in range(rank["lo"], rank["hi"] + 1)
    )


def sc_finish_level(level):
    n = 10
    correct_n = st.session_state.sc_level_correct
    avg_time = (
        sum(st.session_state.sc_level_times) / len(st.session_state.sc_level_times)
        if st.session_state.sc_level_times else 0
    )
    score = st.session_state.sc_level_points

    # Best score / best correct-count ever achieved on this level (replays count).
    prev_best = st.session_state.sc_level_scores.get(level, 0)
    st.session_state.sc_level_scores[level] = max(prev_best, score)
    prev_best_correct = st.session_state.sc_level_best_correct.get(level, 0)
    best_correct = max(prev_best_correct, correct_n)
    st.session_state.sc_level_best_correct[level] = best_correct
    if best_correct >= n:
        st.session_state.sc_perfect_levels.add(level)

    st.session_state.sc_level_stats[level] = {
        "correct": correct_n, "incorrect": n - correct_n,
        "avg_time": avg_time, "score": score,
    }
    # A level is "completed" (shows a checkmark, replayable) once finished at all,
    # regardless of score.
    st.session_state.sc_completed_levels.add(level)
    st.session_state.sc_total_score = sum(st.session_state.sc_level_scores.values())

    passed = correct_n >= (n // 2)  # need >=50% correct to advance
    rankup_target = None

    # Only the level currently at the frontier can push progress forward —
    # replaying an already-cleared earlier level never unlocks anything new,
    # it only banks a better score / moves it toward "perfect".
    if passed and level == st.session_state.sc_highest_unlocked and level < 100:
        rank = sc_rank_for_level(level)
        is_rank_boundary = (level == rank["hi"])
        if is_rank_boundary:
            # Crossing into a new rank/badge requires every level in the
            # current rank to have been aced (10/10) at some point.
            if sc_rank_levels_all_perfect(rank):
                st.session_state.sc_highest_unlocked = level + 1
                rankup_target = sc_rank_for_level(level + 1)
            # else: level itself still "passes" (unlocked/replayable), but
            # the next level and the badge stay locked until it's perfected.
        else:
            st.session_state.sc_highest_unlocked = level + 1

    st.session_state.sc_last_level_result = {
        "level": level, "score": score, "correct": correct_n,
        "incorrect": n - correct_n, "avg_time": avg_time,
        "is_legend": (level == 100),
        "passed": passed,
    }
    if rankup_target:
        st.session_state.sc_pending_rankup = rankup_target
        st.session_state.sc_view = "rankup"
    else:
        st.session_state.sc_view = "results"
 
 
def render_sc_rankup():
    rank = st.session_state.sc_pending_rankup
    st.markdown(
        '<div class="sc-rankup-wrap">'
        '<div class="sc-rankup-label">RANK UP</div>'
        + sc_badge_html(rank, "lg") +
        '<div class="sc-ranknum" style="margin-top:14px">RANK ' + rank["roman"] + '</div>'
        '<div class="sc-rankname">' + rank["name"] + '</div>'
        '<div class="sc-rankup-newbadge">✦ NEW BADGE UNLOCKED ✦</div>'
        '</div>',
        unsafe_allow_html=True
    )
    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
    if st.button("Continue →", key="sc_rankup_continue", type="primary", use_container_width=True):
        st.session_state.sc_pending_rankup = None
        st.session_state.sc_view = "results"
        st.rerun()
 
 
def render_sc_results():
    r = st.session_state.sc_last_level_result
    level = r["level"]
    accuracy = f'{r["correct"]}/10'
    if r["is_legend"]:
        header = ('<div class="sc-results-level">FINAL CHALLENGE COMPLETE</div>'
                   '<div class="sc-results-title">🏆 SATARK LEGEND</div>')
    else:
        header = ('<div class="sc-results-level">LEVEL ' + f'{level:02d}' + ' COMPLETE</div>'
                   '<div class="sc-results-title">Great work!</div>')
    unlock_html = ""
    if level < 100:
        nxt = level + 1
        rank = sc_rank_for_level(level)
        is_boundary = (level == rank["hi"])
        if nxt <= st.session_state.sc_highest_unlocked:
            msg, color = f"Level {nxt:02d} unlocked!", "#a4f5c4"
        elif not r["passed"]:
            msg, color = "Score at least 5/10 to unlock the next level — try again!", "#ffb3b3"
        elif is_boundary:
            missing = [lv for lv in range(rank["lo"], rank["hi"] + 1)
                       if lv not in st.session_state.sc_perfect_levels]
            missing_txt = ", ".join(f"{lv:02d}" for lv in missing)
            msg = (f"Rank up locked — get a perfect 10/10 on level(s) {missing_txt} "
                   f"to unlock Level {nxt:02d} and the next badge.")
            color = "#ffbe4d"
        else:
            msg, color = f"Level {nxt:02d} status unchanged.", "#a7aabb"
        unlock_html = "<p style='margin-top:16px;color:" + color + ";font-weight:700'>" + msg + "</p>"
    st.markdown(
        header +
        '<div class="sc-results">'
        '<div class="sc-bigscore">' + f'{r["score"]:,}' + ' / ' + f'{SC_MAX_POINTS*10:,}' + '</div>'
        '<div class="sc-stats" style="margin-top:20px">'
        '<div class="sc-stat"><div class="sc-stat-v">' + accuracy + '</div><div class="sc-stat-l">Accuracy</div></div>'
        '<div class="sc-stat"><div class="sc-stat-v">' + f'{r["avg_time"]:.1f}s' + '</div><div class="sc-stat-l">Avg Response</div></div>'
        '<div class="sc-stat"><div class="sc-stat-v">' + str(r["incorrect"]) + '</div><div class="sc-stat-l">Missed</div></div>'
        '</div>'
        + unlock_html +
        '</div>',
        unsafe_allow_html=True
    )
    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🗺️ Level Map", key="sc_res_map", use_container_width=True):
            st.session_state.sc_view = "levelmap"
            st.rerun()
    with c2:
        next_unlocked = level < 100 and (level + 1) <= st.session_state.sc_highest_unlocked
        if next_unlocked:
            btn_label, target = "Next Level →", level + 1
        else:
            btn_label, target = "🔁 Retry Level", level
        if level < 100 and st.button(btn_label, key="sc_res_next", type="primary", use_container_width=True):
            sc_start_level(target)
            st.rerun()
 
 
def sc_live_points():
    """Total points banked from completed levels, plus whatever has been
    earned so far in the level currently being played (updates the moment
    each question is answered correctly, before the level is finished)."""
    live = st.session_state.sc_total_score
    if st.session_state.sc_view == "play":
        live += st.session_state.sc_level_points
    return live
 
 
def render_scam_challenge():
    points = sc_live_points()
    st.markdown(
        '<div class="sc-header-row">'
        '<div>'
        '<div class="section-title">🎯 Scam Challenge</div>'
        '<div class="section-copy">A 100-level cybersecurity game. Spot the scam, beat the clock, rank up.</div>'
        '</div>'
        '<div class="sc-points-badge">'
        '<div class="sc-points-icon">✦</div>'
        '<div class="sc-points-text"><div class="sc-points-v">' + f'{points:,}' + '</div><div class="sc-points-l">Points</div></div>'
        '</div>'
        '</div>',
        unsafe_allow_html=True
    )
    view = st.session_state.sc_view
    if view == "levelmap":
        render_sc_levelmap()
    elif view == "play":
        render_sc_play()
    elif view == "rankup":
        render_sc_rankup()
    elif view == "results":
        render_sc_results()
    else:
        render_sc_dashboard()
 
 
# ------------------------- SC-UI-END ------------------------------

SC_DEFAULTS = {
    "sc_view": "dashboard",
    "sc_highest_unlocked": 1,
    "sc_completed_levels": set(),
    "sc_level_best_correct": {},
    "sc_perfect_levels": set(),
    "sc_level_scores": {},
    "sc_level_stats": {},
    "sc_total_score": 0,
    "sc_playing_level": None,
    "sc_q_idx": 0,
    "sc_q_start": None,
    "sc_answered": False,
    "sc_selected_idx": None,
    "sc_level_correct": 0,
    "sc_level_incorrect": 0,
    "sc_level_times": [],
    "sc_level_points": 0,
    "sc_last_points": 0,
    "sc_last_correct": None,
    "sc_last_elapsed": 0.0,
    "sc_pending_rankup": None,
    "sc_last_level_result": None,
}
 
 
def sc_init_state():
    for k, v in SC_DEFAULTS.items():
        if k not in st.session_state:
            st.session_state[k] = v
 
 


# ----------------------- Session state -------------------------
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
            except Exception as exc: st.error(f"Could not check Groq: {exc}")
    st.markdown('<div class="side-label">Personalization</div>',unsafe_allow_html=True)
    role=st.selectbox("👤 Who are you?",["Student","Teacher","Working professional","Parent / Guardian","Senior user","Security learner"],index=0)
    st.markdown('<div class="privacy"><strong>🔒 Privacy first</strong><br>SATARK keeps history only in this Streamlit session. Submitted content is not intentionally saved to disk by this app. Content is sent to Groq only when you analyze it. Avoid passwords, private keys and secrets.</div>',unsafe_allow_html=True)

# ---------------------------- Hero -----------------------------
st.markdown('<section class="hero"><div class="pill">AI SECURITY • EXPLAIN • LEARN • PROTECT</div><h1><span class="hero-primary">Think it’s a scam?</span><br><span class="hero-secondary">Let <span class="hero-brand">SATARK</span> check it.</span></h1><p><strong>Paste a message, inspect a link, upload a screenshot, video, or analyze a PDF.</strong><br>SATARK explains the risk in simple language and shows the evidence behind its assessment.</p></section>',unsafe_allow_html=True)

# --------------------------- Pages -----------------------------
# --------------------------- Pages -----------------------------

if st.session_state.page == "Home":

    st.markdown('<div class="analyze">', unsafe_allow_html=True)

    if st.button(
        "Let SATARK Check It",
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
            help="Best results come from text-based PDFs.",
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
                f"⚠️ Could not fetch that URL safely: {exc}"
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