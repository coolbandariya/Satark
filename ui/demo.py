"""Safe, offline demo result used to explain SATARK before API setup."""
import copy

DEMO_RESULT = {
    "risk_score": 88,
    "confidence": 78,
    "threat_category": "Scam",
    "scam_pattern": "Urgency + credential request",
    "verdict": "Do not click the link or share credentials. Verify the sender through an independent official channel.",
    "summary": "The example combines urgency with a request to act through a link. Those signals are commonly used to push people into acting before they can verify the source.",
    "key_indicators": [
        "Creates urgency and discourages careful verification.",
        "Requests sensitive account information through a link.",
        "Uses a generic sender identity instead of a verifiable official channel.",
    ],
    "recommendations": [
        "Do not click the link or reply with credentials.",
        "Open the organisation's official website or app yourself.",
        "Report or block the sender if the message is unsolicited.",
    ],
    "threat_analysis": {
        "Scam Indicators": "Detected",
        "Phishing Signs": "Detected",
        "Deepfake Risk": "Low",
        "Fake Information": "Needs review",
        "Suspicious Links": "Detected",
        "Impersonation": "Detected",
        "Malware Indicators": "Not detected",
        "Social Engineering": "Detected",
    },
}


def get_demo_result():
    return copy.deepcopy(DEMO_RESULT)
