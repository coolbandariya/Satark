"""Upload and media preprocessing helpers for SATARK.

All helpers enforce bounded input sizes before expensive parsing/encoding.
They do not depend on Streamlit so they can be exercised in isolation.
"""

import base64
import hashlib
from io import BytesIO

from PIL import Image
from pypdf import PdfReader

from satark_utils import safe_text

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


