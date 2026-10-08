"""Interactive learning surfaces for SATARK Academy and Classroom Mode."""
import json
import streamlit as st

LESSONS = [
    ("🎣", "Phishing", "Fake messages and pages designed to steal credentials or information.",
     ["Check the sender and domain independently.", "Never use a login link supplied by an unexpected message.", "Treat urgency + credential requests as a high-risk combination."]),
    ("⏰", "Urgency manipulation", "Pressure tactics that make you act before you verify.",
     ["Pause when a message says 'act now' or threatens immediate consequences.", "Verify through an official app, website or known phone number.", "A deadline does not make an unverified instruction trustworthy."]),
    ("👤", "Impersonation", "Attackers pretending to be banks, schools, companies, friends or officials.",
     ["Compare the identity with an independent source.", "Do not trust logos, caller ID or polished graphics alone.", "Ask the real organisation through a channel you found yourself."]),
    ("🔗", "Suspicious links", "Look-alike domains, strange paths, redirects and unexpected login pages.",
     ["Read the actual hostname, not just the page title.", "Avoid shortened or unexpected links when the stakes are high.", "Use SATARK's URL scanner before interacting with a suspicious public page."]),
    ("💳", "Payment fraud", "Fake fees, refunds, prizes, QR payments and requests for money.",
     ["Never pay a 'release fee' just to receive a prize/refund.", "Do not scan a QR code merely because a message says it is for receiving money.", "Confirm payment requests with the recipient independently."]),
    ("🔐", "Account takeover", "Attempts to obtain passwords, OTPs, recovery codes or session access.",
     ["Never share OTPs or recovery codes with a caller or chat contact.", "Use the official app/site instead of a supplied login link.", "If credentials were exposed, change them through the official service immediately."]),
]

def render_academy():
    st.markdown('<div class="section-title">🎓 SATARK Academy</div><div class="section-copy">Interactive lessons for recognizing the signals behind common digital threats.</div>', unsafe_allow_html=True)

    cols = st.columns(3)
    for i, (icon, title, copy, steps) in enumerate(LESSONS):
        with cols[i % 3]:
            st.markdown(
                f'<div class="feature-card"><div class="feature-icon">{icon}</div>'
                f'<div class="feature-title">{title}</div><div class="feature-copy">{copy}</div></div>',
                unsafe_allow_html=True,
            )
            with st.expander(f"Study {title}", expanded=False):
                for step in steps:
                    st.markdown(f"**•** {step}")

    st.markdown("### The SATARK rule")
    st.info("STOP → VERIFY → ACT. Pressure, secrecy, urgency, money requests, credential requests, and unexpected links are reasons to pause and verify independently.")

    if st.button("🎯 Practice these signals in Scam Challenge", key="academy_to_challenge", type="primary", use_container_width=True):
        st.session_state.page = "Challenge"
        st.rerun()


def render_classroom(history):
    st.markdown('<div class="section-title">👨‍🏫 Classroom Mode</div><div class="section-copy">A session-level teaching dashboard. Nothing here is persisted as a student record.</div>', unsafe_allow_html=True)
    total = len(history)
    avg = round(sum(x.get("score", 0) for x in history) / total) if total else 0
    high = sum(1 for x in history if x.get("score", 0) >= 70)

    a, b, c = st.columns(3)
    with a:
        st.markdown(f'<div class="metric"><div class="metric-label">Analyses this session</div><div class="metric-value">{total}</div></div>', unsafe_allow_html=True)
    with b:
        st.markdown(f'<div class="metric"><div class="metric-label">Average risk score</div><div class="metric-value">{avg}/100</div></div>', unsafe_allow_html=True)
    with c:
        st.markdown(f'<div class="metric"><div class="metric-label">High-risk findings</div><div class="metric-value critical">{high}</div></div>', unsafe_allow_html=True)

    counts = {}
    for item in history:
        category = str(item.get("category", "Needs review"))
        counts[category] = counts.get(category, 0) + 1

    st.markdown("### Session patterns")
    if counts:
        for key, value in sorted(counts.items(), key=lambda x: x[1], reverse=True):
            st.markdown(f"- **{key}** — {value} analysis(es)")
    else:
        st.info("Run a few analyses to populate classroom statistics.")

    st.markdown("### Teaching flow")
    st.markdown("**1.** Present suspicious content.  **2.** Ask learners to identify evidence.  **3.** Run SATARK.  **4.** Compare reasoning.  **5.** Practice the pattern in Scam Challenge.")

    report_lines = [
        "SATARK Classroom Session Summary",
        "",
        f"Analyses: {total}",
        f"Average risk score: {avg}/100",
        f"High-risk findings: {high}",
        "",
        "Patterns:",
    ] + [f"- {k}: {v}" for k, v in sorted(counts.items(), key=lambda x: x[1], reverse=True)]
    st.download_button(
        "↓ Export session summary",
        data="\n".join(report_lines),
        file_name="SATARK_classroom_session.txt",
        mime="text/plain",
        disabled=not bool(history),
        use_container_width=True,
        key="classroom_export",
    )

    if st.button("🔎 Open analyzer", key="classroom_to_analyze", use_container_width=True):
        st.session_state.page = "Analyze"
        st.rerun()
