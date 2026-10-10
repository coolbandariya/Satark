"""Accessible result-table presentation components."""
import html
import streamlit as st
from satark_utils import safe_text, safe_url, check_class, THREAT_CHECKS, OFFICIAL_VERIFICATION_SOURCES

def render_threat_analysis(result, threat_checks=None):
    """Render threat checks with the canonical SATARK defaults when omitted."""
    threat_checks = threat_checks or THREAT_CHECKS
    rows=[]; checks=result.get("threat_analysis",{})
    if not isinstance(checks,dict): checks={}
    for check in threat_checks:
        value=safe_text(checks.get(check,"Needs review"),"Needs review"); cls=check_class(value); icon="✖" if cls=="check-clear" else "✓" if cls=="check-detected" else "•"
        rows.append(f'<tr><td>{html.escape(check)}</td><td class="{cls}">{icon} {html.escape(value)}</td></tr>')
    table='<table class="report-table"><caption class="sr-only">Security checks and their current results</caption><thead><tr><th scope="col">Security Check</th><th scope="col">Result</th></tr></thead><tbody>'+''.join(rows)+'</tbody></table>'
    legend='<div class="status-legend"><div class="status-legend-title">How to read the results</div><span class="status-item"><span class="status-detected">✓ Detected</span> — sufficient evidence that the indicator is present.</span><span class="status-item"><span class="status-review">• Needs review</span> — evidence is ambiguous or insufficient; verify it manually.</span><span class="status-item"><span class="status-clear">✖ Not detected</span> — no meaningful evidence of that indicator was found.</span></div>'
    st.markdown(f'<section class="report-section"><h3>🔎 Threat signals</h3>{table}{legend}</section>',unsafe_allow_html=True)

def render_verification_sources(result, default_sources=None):
    """Render verification sources with the canonical SATARK defaults when omitted."""
    default_sources = default_sources or OFFICIAL_VERIFICATION_SOURCES
    rows=[]; sources=result.get("verification_sources",default_sources)
    if not isinstance(sources,list): sources=default_sources
    for item in sources:
        if not isinstance(item,dict): continue
        source=html.escape(safe_text(item.get("source"))); purpose=html.escape(safe_text(item.get("purpose"))); website=safe_url(item.get("website"))
        if not website: continue
        safe_href=html.escape(website,quote=True)
        rows.append(f'<tr><td>{source}</td><td>{purpose}</td><td><a class="source-link" href="{safe_href}" target="_blank" rel="noopener noreferrer">{html.escape(website)}</a></td></tr>')
    table='<table class="report-table"><caption class="sr-only">Official sources for independently verifying high-impact findings</caption><thead><tr><th scope="col">Source</th><th scope="col">Purpose</th><th scope="col">Official Website</th></tr></thead><tbody>'+''.join(rows)+'</tbody></table>'
    st.markdown(f'<section class="report-section"><h3>📚 Verify independently</h3>{table}</section>',unsafe_allow_html=True)

def render_evidence_ledger(evidence, mode=""):
    """Show deterministic observations separately from the model's assessment."""
    evidence = (
        [
            item for item in evidence
            if isinstance(item, dict)
            and any(
                safe_text(item.get(field))
                for field in ("title", "observation", "evidence")
            )
        ]
        if isinstance(evidence, list)
        else []
    )
    st.markdown(
        '<section class="report-section evidence-ledger">'
        '<h3>🧾 Evidence ledger</h3>'
        '<p class="ledger-intro">These observations were extracted by local, deterministic rules '
        'from the supplied text. They are separate from the AI assessment; a signal is not proof '
        'of fraud, and no signal does not prove content is safe.</p>'
        '</section>',
        unsafe_allow_html=True,
    )

    if not evidence:
        if str(mode).lower() in {"image", "qr"}:
            message = "This image-based workflow did not produce a text-only evidence ledger. Review the visual analysis and verify important claims independently."
        else:
            message = "No supported text signals were extracted by the current rule set. This is not a safety clearance."
        st.info(message)
        return

    rows = []
    for item in evidence[:20]:
        if not isinstance(item, dict):
            continue
        title = html.escape(safe_text(item.get("title"), "Observation"))
        observation = html.escape(safe_text(item.get("observation")))
        excerpt = html.escape(safe_text(item.get("evidence")))
        method = html.escape(safe_text(item.get("method"), "Deterministic pattern"))
        source = html.escape(safe_text(item.get("source"), "Submitted text"))
        rows.append(
            '<article class="ledger-item">'
            '<div class="ledger-item-top">'
            f'<span class="ledger-tag">{title}</span>'
            f'<span class="ledger-method">{method}</span>'
            '</div>'
            f'<p class="ledger-observation">{observation}</p>'
            f'<blockquote class="ledger-quote">{excerpt}</blockquote>'
            f'<div class="ledger-source">Source: {source}</div>'
            '</article>'
        )

    if rows:
        st.markdown(
            '<div class="ledger-grid">' + "".join(rows) + '</div>',
            unsafe_allow_html=True,
        )
    st.caption(
        f"{len(rows)} rule-based observation(s). Rules are intentionally conservative and may miss or misinterpret context."
    )


def render_evidence_review(result):
    """Render the deterministic evidence-coverage check beside the report."""
    from review_engine import build_evidence_review

    review = build_evidence_review(result)
    level = html.escape(safe_text(review.get("level", "review"), "review"))
    status = html.escape(safe_text(review.get("status", "Needs review")))
    message = html.escape(safe_text(review.get("message", "")))
    evidence_count = int(review.get("evidence_count", 0))
    indicator_count = int(review.get("indicator_count", 0))
    st.markdown(
        '<section class="evidence-review evidence-review--' + level + '" role="status">'
        '<div class="evidence-review-head"><div>'
        '<div class="evidence-review-kicker">INDEPENDENT COVERAGE CHECK</div>'
        '<h3>' + status + '</h3></div>'
        '<span class="evidence-review-count">' + str(evidence_count) + ' local signal(s)</span></div>'
        '<p>' + message + '</p>'
        '<div class="evidence-review-foot">Rule signals: ' + str(evidence_count)
        + ' · AI-reported indicators: ' + str(indicator_count)
        + ' · This is a coverage check, not a verdict or a claim-by-claim verifier.</div>'
        '</section>',
        unsafe_allow_html=True,
    )
