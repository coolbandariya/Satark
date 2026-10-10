"""CSS-only visual layers for SATARK.

The app intentionally avoids a CDN/WebGL background so the UI remains fast,
predictable, and usable on restricted networks. The base design system and
small finishing layer are loaded locally.
"""
from pathlib import Path

import streamlit as st


def render_radar_background() -> None:
    """Load the local finishing layer after the main design-system stylesheet."""
    polish_path = Path(__file__).with_name("ui-polish.css")
    try:
        polish_css = polish_path.read_text(encoding="utf-8")
    except OSError:
        # A missing optional polish layer must never prevent an investigation.
        return
    if polish_css.strip():
        st.markdown(f"<style>{polish_css}</style>", unsafe_allow_html=True)
