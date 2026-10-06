"""Deterministic, UI-neutral finding model for SATARK results."""

_SEVERITY = {
    "high": 3,
    "medium": 2,
    "low": 1,
    "clear": 0,
    "unknown": 0,
}


def finding_severity(value):
    text = str(value or "").strip().lower()
    if "high" in text or "detected" in text:
        return "high"
    if "medium" in text:
        return "medium"
    if "low" in text:
        return "low"
    if "not detected" in text or "clear" in text:
        return "clear"
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
                if severity in {"high", "medium", "unknown"}
                else "No meaningful indicator was detected by this check."
            ),
        })
    findings.sort(key=lambda item: _SEVERITY.get(item["severity"], 0), reverse=True)
    return findings
