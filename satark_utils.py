"""Small, side-effect-free text and result normalization helpers."""
import re

def safe_text(value, default=""):  # cleans the text
    if value is None:
        return default
    return str(value).strip()

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

def safe_url(value):
    """Allow only explicit web URLs for user-visible verification links."""
    from urllib.parse import urlparse
    url = safe_text(value)
    try:
        parsed = urlparse(url)
    except ValueError:
        return ""
    if parsed.scheme not in {"https", "http"} or not parsed.netloc:
        return ""
    if parsed.username is not None or parsed.password is not None:
        return ""
    return url


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

