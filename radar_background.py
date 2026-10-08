"""Lightweight background hook for SATARK.

The app used to mount a full-screen WebGL radar from an external CDN. That
made the UI dependent on a third-party browser module and could produce a
blank/slow layer on restricted networks. The visual treatment now lives in
styles.css, so this hook intentionally does nothing.
"""

def render_radar_background() -> None:
    """Keep the call site stable while using the CSS-only background."""
    return None
