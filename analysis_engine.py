"""Pure SATARK result normalization and confidence logic.

This module intentionally has no Streamlit/network/provider side effects so the
core interpretation layer can be unit-tested independently from the UI.
"""

import re

from findings import build_findings

from satark_utils import (
    OFFICIAL_VERIFICATION_SOURCES,
    THREAT_CHECKS,
    check_class,
    normalize_check_value,
    safe_text,
)

def clamp_score(value):
    try:
        return max(0, min(100, int(float(value))))  # limits score to 0–100
    except (TypeError, ValueError):
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
    result["risk_band"] = risk_label(result.get("risk_score", 50), result.get("threat_category", ""))[0]
    result["findings"] = build_findings(result)
    return result


from url_security import VisibleTextParser, is_public_url, fetch_url_text

MAX_PDF_BYTES = 25 * 1024 * 1024
MAX_IMAGE_BYTES = 10 * 1024 * 1024

