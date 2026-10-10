"""Safe offline demo result used to explain SATARK before API setup."""
import copy

DEMO_RESULT = {
    "risk_score": 88,
    "confidence": 78,
    "analysis_mode": "Text",
    "threat_category": "Scam",
    "scam_pattern": "Urgency + credential request",
    "verdict": "Do not click the link or share credentials. Verify the sender through an independent official channel.",
    "summary": "The example combines urgency with a request to act through a link. Those signals are commonly used to push people into acting before they can verify the source.",
    "key_indicators": ["Creates urgency and discourages careful verification.", "Requests sensitive account information through a link.", "Uses a generic sender identity instead of a verifiable official channel."],
    "recommendations": ["Do not click the link or reply with credentials.", "Open the organisation's official website or app yourself.", "Report or block the sender if the message is unsolicited."],
    "deterministic_evidence": [
        {"title": "Urgency language", "observation": "The message pressures the recipient to act quickly.", "evidence": "account will be blocked today", "method": "Illustrative sample signal", "source": "Fictional sample message"},
        {"title": "Credential request", "observation": "The message asks for sensitive account information.", "evidence": "confirm your password using the link", "method": "Illustrative sample signal", "source": "Fictional sample message"},
        {"title": "URL present", "observation": "A link is included and should be checked before use.", "evidence": "https://example.invalid/verify", "method": "Illustrative sample signal", "source": "Fictional sample message"},
    ],
    "threat_analysis": {"Scam Indicators":"Detected","Phishing Signs":"Detected","Deepfake Risk":"Low","Fake Information":"Needs review","Suspicious Links":"Detected","Impersonation":"Detected","Malware Indicators":"Not detected","Social Engineering":"Detected"},
}

def get_demo_result():
    return copy.deepcopy(DEMO_RESULT)
