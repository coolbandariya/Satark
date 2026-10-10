"""Deterministic, UI-neutral finding model for SATARK results."""

import re

_SEVERITY = {
    "critical": 4,
    "high": 3,
    "medium": 2,
    "low": 1,
    "clear": 0,
    "unknown": 0,
}


def finding_severity(value):
    """Map a displayed check value to a conservative severity.

    Explicit negative states take precedence, followed by explicit severity
    labels. Generic words such as "detected" are only a fallback; otherwise
    a value like "Low risk — detected" would incorrectly become High.
    """
    text = str(value or "").strip().lower()
    if not text:
        return "unknown"

    # Handle negation before any positive keyword ("not detected" contains
    # the word "detected").
    if re.search(r"\b(?:not detected|none|clear|no sign|absent|false)\b", text):
        return "clear"

    if re.search(r"\b(?:critical|severe)\b", text):
        return "critical"
    if re.search(r"\bhigh\b", text):
        return "high"
    if re.search(r"\bmedium\b|\bmoderate\b", text):
        return "medium"
    if re.search(r"\blow\b", text):
        return "low"
    if re.search(r"\b(?:detected|present|confirmed)\b", text):
        return "high"

    return "unknown"


def build_findings(result):
    """Normalize threat checks into stable finding objects for every UI/export."""
    checks = result.get("threat_analysis", {}) if isinstance(result, dict) else {}
    if not isinstance(checks, dict):
        checks = {}
    findings = []
    for name, value in checks.items():
        severity = finding_severity(value)
        findings.append({
            "id": name.lower().replace(" ", "-"),
            "title": name,
            "status": str(value or "Needs review"),
            "severity": severity,
            "action": (
                "Verify independently before acting."
                if severity in {"critical", "high", "medium", "unknown"}
                else "No meaningful indicator was detected by this check."
            ),
        })
    findings.sort(key=lambda item: _SEVERITY.get(item["severity"], 0), reverse=True)
    return findings
