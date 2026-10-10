"""Reliable CSS/HTML onboarding stepper for the Streamlit home page.

The previous implementation loaded a second browser runtime inside an iframe.
That was visually fragile on restricted networks and duplicated application
styling. The onboarding path is intentionally static now: it communicates the
workflow clearly without making the home page depend on another frontend runtime.
"""

import streamlit as st

_STEPS = [
    ("01", "Bring the evidence", "Paste a message or URL, or upload the screenshot, PDF or video you are unsure about."),
    ("02", "Inspect the signals", "SATARK extracts the relevant text, media or page signals within bounded processing limits."),
    ("03", "Read the assessment", "Review risk, confidence, evidence and recommended actions together."),
    ("04", "Verify before acting", "Use the result as triage, then independently verify anything consequential."),
]

def render_stepper() -> None:
    """Render the onboarding path without external browser dependencies."""
    cards = "".join(
        f'<article class="workflow-step">'
        f'<div class="workflow-index">{number}</div>'
        f'<h3>{title}</h3>'
        f'<p>{copy}</p>'
        f'</article>'
        for number, title, copy in _STEPS
    )
    st.markdown(f'<div class="workflow-grid">{cards}</div>', unsafe_allow_html=True)
