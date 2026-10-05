# 🧰 CORE PYTHON / SYSTEM
import os
from pathlib import Path
import re
import random
import time
import math
import json
import base64
import hashlib
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
from satark_utils import safe_text, clean_json_text, normalize_check_value, check_class
from ui.results import render_threat_analysis, render_verification_sources
from ui.navigation import render_sidebar
from ui.demo import get_demo_result
from ui.learning import render_academy, render_classroom
from ui.history import render_history


# ============================================================
# SATARK — Smart threat analysis · clear decisions
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

# --------------------------- Helpers --------------------------

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


from url_security import VisibleTextParser, is_public_url, fetch_url_text

MAX_PDF_BYTES = 25 * 1024 * 1024
MAX_IMAGE_BYTES = 10 * 1024 * 1024

def _uploaded_size(uploaded_file):
    try:
        return int(getattr(uploaded_file, "size"))
    except (TypeError, ValueError):
        pass
    try:
        return len(uploaded_file.getvalue())
    except Exception:
        return None

def extract_pdf_text(uploaded_file):
    size = _uploaded_size(uploaded_file)
    if size is not None and size > MAX_PDF_BYTES:
        raise ValueError("This PDF is larger than SATARK's 25 MB processing limit.")
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
    size = _uploaded_size(uploaded_file)
    if size is not None and size > MAX_IMAGE_BYTES:
        raise ValueError("This image is larger than SATARK's 10 MB processing limit.")
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


from video_processing import (
    MAX_VIDEO_FRAMES,
    MAX_VIDEO_BYTES,
    _video_dependencies_available,
    extract_video_frames,
    pil_frames_to_data_urls,
    transcribe_video_audio,
)


from ai_provider import (
    get_client,
    TEXT_MODEL_PREFERENCES,
    VISION_MODEL_PREFERENCES,
    VISION_MODEL_IMAGE_LIMITS,
    discover_models,
    choose_model,
    model_status,
)


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
def confidence_css_class(confidence):
    """Color-code the confidence metric so low-confidence results are visually
    distinct instead of looking identical to high-confidence ones."""
    if confidence >= 85:
        return "safe"
    if confidence >= 50:
        return "caution"
    return "critical"


def render_result(result):
    score = clamp_score(result.get("risk_score", 50))
    label, css = risk_label(score, result.get("threat_category", ""))
    indicators = result.get("key_indicators", [])
    recs = result.get("recommendations", [])
    if not isinstance(indicators, list):
        indicators = []
    if not isinstance(recs, list):
        recs = []

    try:
        confidence = max(0.0, min(100.0, float(result.get("confidence", 70.0))))
    except (TypeError, ValueError):
        confidence = 70.0

    conf_css = confidence_css_class(confidence)
    category = html.escape(safe_text(result.get("threat_category", "Needs review"), "Needs review"))
    verdict = html.escape(safe_text(result.get("verdict", "Manual review recommended.")))
    pattern = html.escape(safe_text(result.get("scam_pattern", category), category))
    summary = html.escape(safe_text(result.get("summary", "")))
    primary_action = html.escape(
        safe_text(recs[0], "Review the content manually before acting.")
    )

    if confidence >= 85:
        confidence_label = "High confidence"
        confidence_note = "The available evidence is relatively consistent."
    elif confidence >= 50:
        confidence_label = "Moderate confidence"
        confidence_note = "Some evidence is useful, but important uncertainty remains."
    else:
        confidence_label = "Low confidence"
        confidence_note = "Evidence is limited or ambiguous; verify before acting."

    st.markdown('<div class="result">', unsafe_allow_html=True)
    st.markdown(
        '<div class="result-head">🛡️ SATARK analysis</div>'
        '<div class="eyebrow">Evidence-first assessment · AI-assisted · verify important findings independently</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        f'<div class="result-hero result-{css}">'
        f'<div class="result-hero-label">Current assessment</div>'
        f'<div class="result-hero-value">{label}</div>'
        f'<div class="result-hero-copy">{verdict}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    a, b, c = st.columns(3)
    with a:
        st.markdown(
            f'<div class="metric"><div class="metric-label">Risk score</div>'
            f'<div class="metric-value">{score}<span class="metric-suffix">/100</span></div></div>',
            unsafe_allow_html=True,
        )
    with b:
        st.markdown(
            f'<div class="metric"><div class="metric-label">Threat pattern</div>'
            f'<div class="metric-value metric-value-small">{pattern}</div></div>',
            unsafe_allow_html=True,
        )
    with c:
        st.markdown(
            f'<div class="metric"><div class="metric-label">AI confidence</div>'
            f'<div class="metric-value {conf_css}">{confidence:.0f}%</div></div>',
            unsafe_allow_html=True,
        )

    st.markdown(f'<div class="bar" role="progressbar" aria-label="Risk score" aria-valuemin="0" aria-valuemax="100" aria-valuenow="{score}"><div style="width:{score}%"></div></div>', unsafe_allow_html=True)

    st.markdown(
        f'<div class="confidence-note">'
        f'<strong>{confidence_label}</strong> · {confidence_note}'
        f'</div>',
        unsafe_allow_html=True,
    )

    if summary:
        st.markdown(
            f'<section class="result-section"><div class="result-section-kicker">WHY</div>'
            f'<h3>Why this result</h3><p>{summary}</p></section>',
            unsafe_allow_html=True,
        )

    st.markdown(
        f'<section class="action-banner"><div class="result-section-kicker">DO THIS NEXT</div>'
        f'<strong>{primary_action}</strong>'
        f'<span>Verify through an independent official channel before sharing money, credentials, OTPs or sensitive information.</span>'
        f'</section>',
        unsafe_allow_html=True,
    )

    left, right = st.columns(2)
    with left:
        st.markdown('<div class="evidence"><strong>🧩 Evidence</strong>', unsafe_allow_html=True)
        if indicators:
            for item in indicators:
                st.markdown(
                    f'<div class="evidence-item">⚠️ {html.escape(safe_text(item))}</div>',
                    unsafe_allow_html=True,
                )
        else:
            st.markdown(
                '<div class="evidence-item">No specific indicators were returned.</div>',
                unsafe_allow_html=True,
            )
        st.markdown('</div>', unsafe_allow_html=True)

    with right:
        st.markdown('<div class="evidence"><strong>🧭 Recommended next steps</strong>', unsafe_allow_html=True)
        if recs:
            for item in recs:
                st.markdown(
                    f'<div class="action-item"><span>✓</span><span>{html.escape(safe_text(item))}</span></div>',
                    unsafe_allow_html=True,
                )
        else:
            st.markdown(
                '<div class="action-item">Review the content manually before acting.</div>',
                unsafe_allow_html=True,
            )
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    render_threat_analysis(result, THREAT_CHECKS)
    render_verification_sources(result, OFFICIAL_VERIFICATION_SOURCES)

    conclusion = html.escape(build_final_conclusion(result))
    st.markdown(
        f'<section class="report-section"><h3>💡 Bottom line</h3>'
        f'<div class="conclusion-card">{conclusion}</div></section>',
        unsafe_allow_html=True,
    )


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
        "last_input_fingerprint":"","analysis_request_id":"","demo_mode":False,
    }
    for k,v in defaults.items():
        if k not in st.session_state: st.session_state[k]=v
init_state()
sc_init_state()  # Scam Challenge v2 session-state defaults

api_key = render_sidebar(get_client, discover_models, choose_model, TEXT_MODEL_PREFERENCES, VISION_MODEL_PREFERENCES)

# ---------------------------- Hero -----------------------------
st.markdown('<section class="hero"><div class="pill">AI SECURITY • EXPLAIN • LEARN • PROTECT</div><h1><span class="hero-primary">Not sure if it’s safe?</span><br><span class="hero-secondary">Let <span class="hero-brand">SATARK</span> investigate.</span></h1><p><strong>Paste a message, check a link, or upload an image, PDF, or video.</strong><br>SATARK highlights evidence, explains uncertainty, and gives you the safest next step.</p><div class="hero-note">Advisory only · Verify important findings independently</div></section>',unsafe_allow_html=True)

# --------------------------- Pages -----------------------------
# --------------------------- Pages -----------------------------

if st.session_state.page == "Home":

    st.markdown(
        '<div class="home-intro">'
        '<div class="home-intro-title">Clear answers for suspicious content.</div>'
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

    st.markdown('<div class="analyze">', unsafe_allow_html=True)

    if st.button(
        "Start checking  →",
        use_container_width=True,
        type="primary",
        key="goto_analyze"
    ):
        st.session_state.page = "Analyze"
        st.session_state.scroll_to_scanners = True
        st.rerun()
    if st.button(
        "See a sample result",
        use_container_width=True,
        key="demo_result"
    ):
        st.session_state.result = get_demo_result()
        st.session_state.mode = "Text"
        st.session_state.demo_mode = True
        st.session_state.page = "Analyze"
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
        '<div class="section-title">Choose what you want SATARK to inspect</div>'
        '<div class="section-copy">'
        'Choose a scanner. Seven scanners cover text, links, images, documents, QR codes and video.'
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
                    f"Select {name}",
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
    if st.session_state.get("demo_mode"):
        st.info("🧪 Sample result · this is an offline example. Run a real analysis to replace it.")


    st.markdown(
        f'<div class="section-title">🔎 Analyze {mode.lower()}</div>'
        f'<div class="section-copy">Selected scanner: <strong>{mode}</strong> · Results are advisory; verify important findings independently.</div>',
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
            "Message or content",
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
            "Website or link",
            placeholder="https://example.com/path",
            key="url_input"
        )


    # ==========================================================
    # PDF
    # ==========================================================

    elif mode == "PDF":

        uploaded = st.file_uploader(
            "Upload a PDF document",
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
            "Upload image(s)",
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
        "🔍 Run SATARK analysis",
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

        st.session_state.demo_mode = False

        if not safe_text(api_key):

            st.error(
                "🔑 Add your Groq API key in the sidebar before running an analysis."
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
                "Analysis complete · review the evidence below."
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

    render_history(st.session_state.history, make_pdf_report, risk_label)


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

    render_academy()


elif st.session_state.page == "Classroom":

    render_classroom(st.session_state.history)


# ==============================================================
# FOOTER
# ==============================================================

st.markdown(
    '<div class="footer">'
    'SATARK • Smart threat analysis · clear decisions<br>'
    'AI analysis is advisory. Always verify high-impact security '
    'decisions independently.<br>'
    'Session history is temporary and does not intentionally '
    'preserve submitted source content.'
    '</div>',
    unsafe_allow_html=True
)