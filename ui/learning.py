"""Learning surfaces for SATARK Academy and Classroom Mode."""
import streamlit as st

def render_academy():
    st.markdown('<div class="section-title">🎓 SATARK Academy</div><div class="section-copy">Learn the patterns behind common scams so you can spot them before you need an AI check.</div>',unsafe_allow_html=True)
    lessons=[("🎣","Phishing","Fake messages and pages designed to steal credentials or information."),("⏰","Urgency manipulation","Pressure tactics that make you act before you verify."),("👤","Impersonation","Attackers pretending to be banks, schools, companies, friends or officials."),("🔗","Suspicious links","Look-alike domains, strange paths, redirects and unexpected login pages."),("💳","Payment fraud","Fake fees, refunds, prizes, QR payments and requests for money."),("🔐","Account takeover","Attempts to obtain passwords, OTPs, recovery codes or session access.")]
    cols=st.columns(3)
    for i,(icon,title,copy) in enumerate(lessons):
        with cols[i%3]: st.markdown(f'<div class="feature-card"><div class="feature-icon">{icon}</div><div class="feature-title">{title}</div><div class="feature-copy">{copy}</div></div>',unsafe_allow_html=True)
    st.markdown("### One rule to remember"); st.info("STOP → VERIFY → ACT. Pressure, secrecy, urgency, or money requests are reasons to pause and verify through an independent official channel.")

def render_classroom(history):
    st.markdown('<div class="section-title">👨‍🏫 Classroom Mode</div><div class="section-copy">A lightweight view for using SATARK as a cyber-safety learning tool.</div>',unsafe_allow_html=True)
    total=len(history); avg=round(sum(x["score"] for x in history)/total) if total else 0; high=sum(1 for x in history if x["score"]>=70)
    a,b,c=st.columns(3)
    with a: st.markdown(f'<div class="metric"><div class="metric-label">Analyses this session</div><div class="metric-value">{total}</div></div>',unsafe_allow_html=True)
    with b: st.markdown(f'<div class="metric"><div class="metric-label">Average risk score</div><div class="metric-value">{avg}/100</div></div>',unsafe_allow_html=True)
    with c: st.markdown(f'<div class="metric"><div class="metric-label">High-risk findings</div><div class="metric-value critical">{high}</div></div>',unsafe_allow_html=True)
    st.markdown("### A simple classroom flow"); st.markdown("**1.** Give students a suspicious message. **2.** Ask them to identify warning signs. **3.** Run it through SATARK. **4.** Compare the evidence. **5.** Use Scam Challenge to reinforce the lesson.")
    counts={}
    for item in history: counts[item["category"]]=counts.get(item["category"],0)+1
    st.markdown("### Patterns seen in this session")
    if counts:
        for key,value in sorted(counts.items(),key=lambda x:x[1],reverse=True): st.write(f"• **{key}** — {value} analysis(es)")
    else: st.info("Run a few example analyses to populate these session statistics.")
