"""Session history UI with searchable, animated result cards."""
import html
import streamlit as st


def _safe_score(value):
    try:
        score = int(float(value))
    except (TypeError, ValueError, OverflowError):
        return 0
    return max(0, min(100, score))


def _safe_entry(entry):
    if not isinstance(entry, dict):
        return {"mode": "Unknown", "category": "Needs review", "score": 0, "time": "", "verdict": "Manual review recommended.", "result": {}}
    result = entry.get("result")
    return {
        **entry,
        "mode": str(entry.get("mode") or "Unknown"),
        "category": str(entry.get("category") or "Needs review"),
        "score": _safe_score(entry.get("score", 0)),
        "time": str(entry.get("time") or ""),
        "verdict": str(entry.get("verdict") or "Manual review recommended."),
        "result": result if isinstance(result, dict) else {},
    }


def render_history(history, make_pdf_report, risk_label):
    st.markdown(
        '<div class="section-title">🕘 Analysis history</div>'
        '<div class="section-copy">Temporary session history. Only analysis results and metadata are retained in this browser session.</div>',
        unsafe_allow_html=True,
    )

    history = [_safe_entry(entry) for entry in history if isinstance(entry, dict)]
    if not history:
        st.info("No analyses yet. Run a check and the result will appear here for this session.")
        if st.button("🔎 Start an investigation", key="history_to_analyze", type="primary", use_container_width=True):
            st.session_state.page = "Analyze"
            st.rerun()
        return

    top_left, top_mid, top_right = st.columns([2, 1, 1])
    with top_left:
        query = st.text_input(
            "Search history",
            placeholder="Search category, verdict, scanner or time…",
            key="history_query",
            label_visibility="collapsed",
        )
    with top_mid:
        modes = ["All"] + sorted({str(item.get("mode", "Unknown")) for item in history})
        mode_filter = st.selectbox("Scanner", modes, key="history_mode_filter", label_visibility="collapsed")
    with top_right:
        risk_filter = st.selectbox("Risk", ["All", "Safe", "Caution", "Critical"], key="history_risk_filter", label_visibility="collapsed")

    if st.button("Clear session history", key="clear_history"):
        st.session_state.history = []
        st.session_state.result = None
        st.rerun()

    query_lower = str(query or "").strip().lower()

    def matches(entry):
        if mode_filter != "All" and str(entry.get("mode")) != mode_filter:
            return False
        score = _safe_score(entry.get("score", 0))
        if risk_filter == "Safe" and score >= 35:
            return False
        if risk_filter == "Caution" and not (35 <= score < 70):
            return False
        if risk_filter == "Critical" and score < 70:
            return False
        if query_lower:
            haystack = " ".join(
                str(entry.get(key, "")) for key in ("mode", "category", "verdict", "time")
            ).lower()
            if query_lower not in haystack:
                return False
        return True

    filtered = [entry for entry in history if matches(entry)]
    st.caption(f"Showing {len(filtered)} of {len(history)} session result(s).")

    if not filtered:
        st.warning("No history entries match those filters.")
        return

    for visible_index, entry in enumerate(filtered):
        score = int(entry.get("score", 0))
        label, _ = risk_label(score, entry.get("category", ""))
        mode = html.escape(str(entry.get("mode", "Unknown")))
        category = html.escape(str(entry.get("category", "Needs review")))
        timestamp = html.escape(str(entry.get("time", "")))
        with st.expander(f"{mode} · {category} · {score}/100 · {timestamp}"):
            st.markdown(
                f'<div class="history-card">'
                f'<span class="badge">{html.escape(label)}</span> '
                f'<span class="badge">{category}</span>'
                f'<div class="history-verdict">{html.escape(str(entry.get("verdict", "Manual review recommended.")))}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Open result", key=f"history_open_{visible_index}"):
                    st.session_state.result = entry.get("result") or None
                    st.session_state.mode = entry.get("mode", "Unknown")
                    st.session_state.demo_mode = False
                    st.session_state.page = "Analyze"
                    st.rerun()
            with c2:
                st.download_button(
                    "📄 Export PDF",
                    make_pdf_report(entry["result"], entry["mode"]),
                    file_name=f"SATARK_report_{visible_index + 1}.pdf",
                    mime="application/pdf",
                    key=f"history_dl_{visible_index}",
                )
