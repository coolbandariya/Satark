"""Navigation and session controls for SATARK."""
import os
import streamlit as st

def render_sidebar(get_client, discover_models, choose_model, text_preferences, vision_preferences):
    with st.sidebar:
        st.markdown('<div class="brand"><div class="brand-logo">SATARK <span class="brand-dot">◦</span></div><div class="brand-tag">Smart threat analysis · clear decisions</div></div>', unsafe_allow_html=True)
        st.markdown('<div class="side-label">Workspace</div>', unsafe_allow_html=True)
        pages=[("Home","🏠 Overview"),("Analyze","🔎 Analyze"),("History","🕘 History"),("Challenge","🎯 Scam Challenge"),("Academy","🎓 Academy"),("Classroom","👨‍🏫 Classroom")]
        for page,label in pages:
            if st.button(
                label,
                key=f"nav_{page}",
                use_container_width=True,
                type="primary" if st.session_state.get("page") == page else "secondary",
            ):
                st.session_state.page=page
                st.rerun()
        st.markdown('<div class="side-label">AI connection</div>', unsafe_allow_html=True)
        env_key=os.getenv("GROQ_API_KEY","")
        api_key=st.text_input("🔑 Groq API key",value=env_key,type="password",placeholder="Paste your Groq API key",help="Used only for the current Streamlit session; SATARK does not intentionally write it to disk.")
        if api_key and st.button("Check AI connection",key="check_ai",use_container_width=True):
            try:
                client=get_client(api_key); available=discover_models(client)
                st.session_state.available_models=available
                st.session_state.text_model=choose_model(available,text_preferences)
                st.session_state.vision_model=choose_model(available,vision_preferences)
                if st.session_state.text_model and st.session_state.vision_model: st.success("Connected · text + vision ready")
                elif st.session_state.text_model: st.warning("Connected · text ready, vision unavailable for this key")
                else: st.error("Key accepted, but no supported SATARK text model is available.")
            except Exception as exc: st.error(f"Connection check failed ({type(exc).__name__}). Verify the key, network, and provider status.")
        st.markdown('<div class="side-label">Audience</div>', unsafe_allow_html=True)
        role=st.selectbox("👤 Your context",["Student","Teacher","Working professional","Parent / Guardian","Senior user","Security learner"],index=0)
        st.markdown('<div class="privacy"><strong>🔒 Privacy boundary</strong><br>History stays in this browser session. Submitted content is not intentionally written to disk by SATARK. Content is sent to Groq only when you start an analysis. Never submit passwords, OTPs, private keys, or other secrets.</div>',unsafe_allow_html=True)
    return api_key, role
