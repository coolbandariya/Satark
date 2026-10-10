"""Deterministic, explainable signal extraction for SATARK.

These rules identify observable patterns in supplied text. They do not prove
that content is malicious and must never be treated as a calibrated risk score.
No network requests are made by this module.
"""

import ipaddress
import re
from urllib.parse import urlparse

_MAX_FINDINGS = 20
_MAX_EXCERPT = 180

_URL_RE = re.compile(r"(?i)\b(?:https?://|www\.)[^\s<>'\"()]+")
_PHONE_RE = re.compile(r"(?<!\w)(?:\+91[\s.-]?)?[6-9]\d{9}(?!\w)")
_UPI_RE = re.compile(r"(?i)\b[a-z0-9._-]{2,}@(okaxis|okhdfcbank|okicici|oksbi|ybl|ibl|axl|upi|paytm|apl|fbl|barodampay|kotak|indus|yesbank|axisbank|hdfcbank|icici|sbi|pnb|freecharge|jio)\b")
_URGENCY = (
    "act now", "immediately", "urgent", "within 24 hours", "within 24 hrs",
    "account will be blocked", "account will be suspended", "final warning",
    "last chance", "expires today", "verify now", "limited time",
)
_CREDENTIAL_RE = re.compile(
    r"(?i)\b(?:share|send|enter|provide|confirm|submit|tell us|reply with)\b"
    r"[^.!?\n]{0,55}\b(?:otp|one[- ]time password|password|passcode|upi pin|pin|cvv|cvc|card number|bank details)\b"
)
_PAYMENT_RE = re.compile(
    r"(?i)\b(?:pay|transfer|deposit|send)\b[^.!?\n]{0,45}"
    r"\b(?:fee|money|payment|deposit|registration|processing|advance|₹|rs\.?|inr)\b"
)
_SHORTENERS = {
    "bit.ly", "tinyurl.com", "t.co", "is.gd", "cutt.ly", "rb.gy",
    "shorturl.at", "rebrand.ly", "tiny.cc",
}


def _excerpt(text: str, start: int, end: int) -> str:
    left = max(0, start - 55)
    right = min(len(text), max(end, start + 1) + 75)
    value = " ".join(text[left:right].split())
    if left:
        value = "…" + value
    if right < len(text):
        value += "…"
    return value[:_MAX_EXCERPT]


def _finding(kind: str, title: str, explanation: str, evidence: str, start: int, end: int):
    return {
        "id": kind,
        "title": title,
        "observation": explanation,
        "evidence": evidence[:_MAX_EXCERPT],
        "source": "Submitted text",
        "method": "Deterministic pattern",
        "interpretation": "Review signal — not a verdict",
        "position": start,
    }


def extract_deterministic_evidence(value, *, max_findings=_MAX_FINDINGS):
    """Return explainable observations from text without classifying it as safe/scam."""
    text = str(value or "")
    if not text.strip():
        return []

    findings = []

    for match in _URL_RE.finditer(text):
        raw = match.group(0).rstrip(".,;:!?]")
        candidate = raw if raw.lower().startswith(("http://", "https://")) else "https://" + raw
        try:
            parsed = urlparse(candidate)
            host = (parsed.hostname or "").lower().rstrip(".")
        except ValueError:
            host = ""
        if not host:
            continue

        findings.append(_finding(
            "url-present", "URL present",
            "A web address is present. Its presence alone does not establish maliciousness.",
            raw, match.start(), match.end(),
        ))

        try:
            ipaddress.ip_address(host)
            is_ip = True
        except ValueError:
            is_ip = False

        if is_ip:
            findings.append(_finding(
                "url-ip-host", "URL uses an IP address",
                "The hostname is a literal IP address; verify the destination independently.",
                raw, match.start(), match.end(),
            ))
        if host in _SHORTENERS:
            findings.append(_finding(
                "url-shortener", "URL shortener detected",
                "The destination is obscured by a known URL-shortening domain.",
                raw, match.start(), match.end(),
            ))
        if host.startswith("xn--") or ".xn--" in host:
            findings.append(_finding(
                "url-punycode", "Punycode hostname",
                "The hostname contains an internationalized-domain encoding; inspect the displayed domain carefully.",
                raw, match.start(), match.end(),
            ))
        if parsed.username is not None or parsed.password is not None:
            findings.append(_finding(
                "url-credentials", "Credentials embedded in URL",
                "The URL contains a user-info component that can disguise the apparent destination.",
                raw, match.start(), match.end(),
            ))

    for match in _PHONE_RE.finditer(text):
        findings.append(_finding(
            "phone-present", "Phone number present",
            "A phone-like number is present. This does not indicate fraud by itself.",
            match.group(0), match.start(), match.end(),
        ))

    for match in _UPI_RE.finditer(text):
        findings.append(_finding(
            "upi-present", "UPI-style ID present",
            "A UPI-style payment identifier is present. Verify the recipient before paying.",
            match.group(0), match.start(), match.end(),
        ))

    lowered = text.lower()
    for phrase in _URGENCY:
        match = re.search(r"(?i)" + re.escape(phrase), text)
        if match:
            findings.append(_finding(
                "urgency-language", "Urgency language",
                "Pressure to act quickly can reduce careful verification; check the request through an independent channel.",
                match.group(0), match.start(), match.end(),
            ))

    for pattern, kind, title, explanation in (
        (_CREDENTIAL_RE, "credential-request", "Sensitive credential request",
         "The text appears to pair an instruction with a request for a credential or authentication secret."),
        (_PAYMENT_RE, "payment-request", "Payment-related request",
         "The text appears to pair an action with a payment or fee term; context is needed to judge legitimacy."),
    ):
        for match in pattern.finditer(text):
            findings.append(_finding(
                kind, title, explanation, match.group(0), match.start(), match.end(),
            ))

    # Keep the earliest evidence first and remove repeated observations.
    unique = []
    seen = set()
    for item in sorted(findings, key=lambda entry: (entry["position"], entry["id"])):
        signature = (item["id"], item["evidence"].casefold())
        if signature in seen:
            continue
        seen.add(signature)
        unique.append(item)
        if len(unique) >= max(1, min(int(max_findings), 100)):
            break

    for item in unique:
        item.pop("position", None)
    return unique
