"""Session history UI."""
import html
import streamlit as st

def render_history(history, make_pdf_report, risk_label):
    st.markdown('<div class="section-title">🕘 Analysis history</div><div class="section-copy">Temporary session history. Original submitted content is not stored here; only analysis results and metadata are retained.</div>',unsafe_allow_html=True)
    if not history:
        st.info("No analyses yet. Run a check and the result will appear here for this session."); return
    if st.button("Clear session history",key="clear_history"):
        st.session_state.history=[]; st.session_state.result=None; st.rerun()
    for i,entry in enumerate(history):
        score=entry["score"]; label,_=risk_label(score,entry.get("category",""))
        with st.expander(f'{entry["mode"]} · {entry["category"]} · {score}/100 · {entry["time"]}'):
            st.markdown(f'<span class="badge">{html.escape(label)}</span> <span class="badge">{html.escape(entry["category"])}</span>',unsafe_allow_html=True); st.write(entry["verdict"])
            c1,c2=st.columns(2)
            with c1:
                if st.button("Open result",key=f"history_open_{i}"):
                    st.session_state.result=entry["result"]; st.session_state.mode=entry["mode"]; st.session_state.demo_mode=False; st.session_state.page="Analyze"; st.rerun()
            with c2:
                st.download_button("📄 Export PDF",make_pdf_report(entry["result"],entry["mode"]),file_name=f"SATARK_report_{i+1}.pdf",mime="application/pdf",key=f"history_dl_{i}")
