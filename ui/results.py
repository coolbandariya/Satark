"""Accessible result-table presentation components."""
import html
import streamlit as st
from satark_utils import safe_text, check_class

def render_threat_analysis(result, threat_checks):
    rows=[]; checks=result.get("threat_analysis",{})
    if not isinstance(checks,dict): checks={}
    for check in threat_checks:
        value=safe_text(checks.get(check,"Needs review"),"Needs review"); cls=check_class(value); icon="✖" if cls=="check-clear" else "✓" if cls=="check-detected" else "•"
        rows.append(f'<tr><td>{html.escape(check)}</td><td class="{cls}">{icon} {html.escape(value)}</td></tr>')
    table='<table class="report-table"><caption class="sr-only">Security checks and their current results</caption><thead><tr><th scope="col">Security Check</th><th scope="col">Result</th></tr></thead><tbody>'+''.join(rows)+'</tbody></table>'
    legend='<div class="status-legend"><div class="status-legend-title">How to read the results</div><span class="status-item"><span class="status-detected">✓ Detected</span> — sufficient evidence that the indicator is present.</span><span class="status-item"><span class="status-review">• Needs review</span> — evidence is ambiguous or insufficient; verify it manually.</span><span class="status-item"><span class="status-clear">✖ Not detected</span> — no meaningful evidence of that indicator was found.</span></div>'
    st.markdown(f'<section class="report-section"><h3>🔎 Threat signals</h3>{table}{legend}</section>',unsafe_allow_html=True)

def render_verification_sources(result, default_sources):
    rows=[]; sources=result.get("verification_sources",default_sources)
    if not isinstance(sources,list): sources=default_sources
    for item in sources:
        if not isinstance(item,dict): continue
        source=html.escape(safe_text(item.get("source"))); purpose=html.escape(safe_text(item.get("purpose"))); website=safe_text(item.get("website"))
        if not website.startswith(("https://","http://")): continue
        safe_href=html.escape(website,quote=True)
        rows.append(f'<tr><td>{source}</td><td>{purpose}</td><td><a class="source-link" href="{safe_href}" target="_blank" rel="noopener noreferrer">{html.escape(website)}</a></td></tr>')
    table='<table class="report-table"><caption class="sr-only">Official sources for independently verifying high-impact findings</caption><thead><tr><th scope="col">Source</th><th scope="col">Purpose</th><th scope="col">Official Website</th></tr></thead><tbody>'+''.join(rows)+'</tbody></table>'
    st.markdown(f'<section class="report-section"><h3>📚 Verify independently</h3>{table}</section>',unsafe_allow_html=True)
