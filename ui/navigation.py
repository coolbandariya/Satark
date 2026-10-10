"""Focused navigation and session controls for SATARK."""
import os
import streamlit as st


def render_sidebar(get_client, discover_models, choose_model, text_preferences, vision_preferences):
    with st.sidebar:
        st.markdown(
            '<div class="brand"><div class="brand-mark">S<span>·</span></div>'
            '<div><div class="brand-logo">SATARK</div>'
            '<div class="brand-tag">Evidence-first threat investigation</div></div></div>',
            unsafe_allow_html=True,
        )
        st.markdown('<div class="side-label">Workspace</div>', unsafe_allow_html=True)
        pages = [
            ("Home", "Overview"),
            ("Analyze", "Investigate"),
            ("History", "Session history"),
        ]
        for page, label in pages:
            if st.button(
                label,
                key=f"nav_{page}",
                use_container_width=True,
                type="primary" if st.session_state.get("page") == page else "secondary",
            ):
                st.session_state.page = page
                st.rerun()

        env_key = os.getenv("GROQ_API_KEY", "")
        api_key = env_key
        with st.expander("AI provider", expanded=not bool(env_key)):
            st.caption("Connect a provider to run live analysis. The offline sample works without a key.")
            api_key = st.text_input(
                "Groq API key",
                value=env_key,
                type="password",
                placeholder="Paste your Groq API key",
                help="Used for the current Streamlit session. Never commit keys to source control.",
                key="groq_api_key_input",
            )
            if api_key and st.button("Test connection", key="check_ai", use_container_width=True):
                try:
                    client = get_client(api_key)
                    available = discover_models(client)
                    st.session_state.available_models = available
                    st.session_state.text_model = choose_model(available, text_preferences)
                    st.session_state.vision_model = choose_model(available, vision_preferences)
                    if st.session_state.text_model and st.session_state.vision_model:
                        st.success("Connected · text and vision ready")
                    elif st.session_state.text_model:
                        st.warning("Connected · text ready; vision model unavailable")
                    else:
                        st.error("No supported text model is available for this key.")
                except Exception as exc:
                    st.error(
                        f"Connection check failed ({type(exc).__name__}). "
                        "Verify the key, network and provider status."
                    )

        with st.expander("Analysis context", expanded=False):
            role = st.selectbox(
                "Who is this for?",
                [
                    "Student",
                    "Teacher",
                    "Working professional",
                    "Parent / Guardian",
                    "Senior user",
                    "Security learner",
                ],
                index=0,
                key="analysis_audience",
            )

        st.markdown(
            '<div class="privacy"><span class="privacy-icon">↳</span>'
            '<div><strong>Privacy boundary</strong><p>History stays in this session. Content is sent to the AI provider only when you start an analysis. Do not submit passwords, OTPs, private keys or unnecessary personal data.</p></div></div>',
            unsafe_allow_html=True,
        )
    return api_key, role
