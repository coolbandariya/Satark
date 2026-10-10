"""Evidence-coverage review that keeps deterministic observations separate from AI claims."""
from math import isfinite


def _safe_score(value):
    try:
        score = float(value)
        if not isfinite(score):
            return 50
        return max(0, min(100, int(score)))
    except (TypeError, ValueError, OverflowError):
        return 50


def _items(value):
    if isinstance(value, (list, tuple)):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def build_evidence_review(result):
    """Summarize whether the assessment has independent text-rule corroboration.

    This is a coverage check, not a claim verifier and not a replacement for
    human review. Image/QR findings are intentionally handled separately.
    """
    result = result if isinstance(result, dict) else {}
    mode = str(result.get("analysis_mode", "")).strip().lower()
    evidence = result.get("deterministic_evidence", [])
    evidence = (
        [
            item for item in evidence
            if isinstance(item, dict)
            and any(
                str(item.get(field, "")).strip()
                for field in ("title", "observation", "evidence")
            )
        ]
        if isinstance(evidence, list)
        else []
    )
    indicators = _items(result.get("key_indicators", []))
    score = _safe_score(result.get("risk_score", 50))
    category = str(result.get("threat_category", "")).strip().lower()
    high_risk = score >= 70 or category in {"scam", "phishing", "malware"}

    if mode in {"image", "qr"}:
        return {
            "status": "Visual workflow",
            "level": "info",
            "evidence_count": 0,
            "indicator_count": len(indicators),
            "message": (
                "The local text-rule layer does not independently verify visual findings. "
                "Review the image analysis and verify important claims through an independent source."
            ),
        }

    if mode == "video":
        return {
            "status": "Multimodal workflow",
            "level": "info",
            "evidence_count": 0,
            "indicator_count": len(indicators),
            "message": (
                "Sampled video frames and any available transcript are not exhaustively verified by "
                "the local text-rule layer. Review the supplied findings and verify important claims independently."
            ),
        }

    if evidence:
        return {
            "status": "Independent text signals found",
            "level": "supported",
            "evidence_count": len(evidence),
            "indicator_count": len(indicators),
            "message": (
                f"{len(evidence)} local rule-based observation(s) were extracted separately "
                "from the AI interpretation. These observations are heuristics, not proof of fraud, "
                "and may not support every part of the overall verdict."
            ),
        }

    if high_risk:
        return {
            "status": "High-risk assessment needs corroboration",
            "level": "review",
            "evidence_count": 0,
            "indicator_count": len(indicators),
            "message": (
                "The model returned a high-risk assessment, but the local text-rule layer found "
                "no supporting text signals. Treat the conclusion as uncorroborated and verify it manually."
            ),
        }

    if indicators:
        return {
            "status": "No independent text corroboration",
            "level": "review",
            "evidence_count": 0,
            "indicator_count": len(indicators),
            "message": (
                "The AI reported indicator(s), but the local text-rule layer extracted no observations. "
                "This does not prove the AI is wrong; inspect the source and verify independently."
            ),
        }

    return {
        "status": "Limited evidence",
        "level": "review",
        "evidence_count": 0,
        "indicator_count": 0,
        "message": (
            "No supported local text signals were extracted. A lack of detected signals is not a safety clearance."
        ),
    }
