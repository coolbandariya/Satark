"""Groq client and model-selection helpers for SATARK."""

from groq import Groq

from satark_utils import safe_text


def get_client(api_key):
    key = safe_text(api_key)
    return Groq(api_key=key) if key else None


# ---------------------- Model discovery ------------------------
TEXT_MODEL_PREFERENCES = [
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
]
# Vision model fallback chain. Previously this was a single hardcoded model
# (qwen/qwen3.8-27b), which meant image/QR analysis broke entirely the moment
# that one model became unavailable or the API key lost access to it.
# analyze_with_groq now tries each of these in order and only reports failure
# once every candidate has been exhausted.
VISION_MODEL_PREFERENCES = [
    "qwen/qwen3.8-27b",
]

# Some vision models cap how many images can be sent in one request (e.g. Qwen
# allows only 3). Keyed by model id; models not listed here use the default
# cap applied in analyze_with_groq.
VISION_MODEL_IMAGE_LIMITS = {
    "qwen/qwen3.8-27b": 3,
}


def discover_models(client):
    """Ask Groq which models this exact API key can access."""
    try:
        listing = client.models.list()
        items = getattr(listing, "data", listing)
        ids = set()
        for item in items or []:
            mid = getattr(item, "id", None)
            if mid:
                ids.add(str(mid))
            elif isinstance(item, dict) and item.get("id"):
                ids.add(str(item["id"]))
        return ids
    except Exception:
        return set()


def choose_model(available, preferences):
    if not available:
        return preferences[0]
    for model in preferences:
        if model in available:
            return model
    return None


def model_status(client):
    available = discover_models(client)
    text_model = choose_model(available, TEXT_MODEL_PREFERENCES)
    vision_model = choose_model(available, VISION_MODEL_PREFERENCES)
    return available, text_model, vision_model
