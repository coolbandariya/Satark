"""One-time, accessible SATARK intro overlay for the Streamlit shell."""
from __future__ import annotations

import streamlit as st


def render_intro_loader() -> None:
    """Show a brief branded intro once per browser session, without blocking app work."""
    if st.session_state.get("_satark_intro_seen", False):
        return
    st.session_state["_satark_intro_seen"] = True

    st.iframe(
        r"""<!doctype html><html><head><meta charset="utf-8"></head><body><script>
        (() => {
          try {
            const hostWindow = window.parent;
            const doc = hostWindow.document;
            if (doc.getElementById("satark-intro-overlay")) return;

            const style = doc.createElement("style");
            style.id = "satark-intro-style";
            style.textContent = `
              #satark-intro-overlay {
                position: fixed; inset: 0; z-index: 2147483000;
                display: grid; place-items: center; overflow: hidden;
                background:
                  radial-gradient(ellipse at 50% 42%, rgba(70, 112, 145, .17), transparent 38%),
                  radial-gradient(ellipse at 50% 100%, rgba(70, 160, 135, .07), transparent 42%),
                  #070a0f;
                color: #eef5ff; font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
                opacity: 1; visibility: visible;
                transition: opacity .42s ease, visibility .42s ease;
              }
              #satark-intro-overlay::before {
                content: ""; position: absolute; inset: 0; pointer-events: none; opacity: .22;
                background-image: linear-gradient(rgba(160,190,220,.055) 1px, transparent 1px),
                  linear-gradient(90deg, rgba(160,190,220,.055) 1px, transparent 1px);
                background-size: 42px 42px;
                mask-image: radial-gradient(ellipse at center, #000 0%, transparent 75%);
              }
              #satark-intro-overlay .satark-intro-inner {
                position: relative; z-index: 1; width: min(460px, calc(100vw - 40px));
                display: flex; flex-direction: column; align-items: center; text-align: center;
                animation: satark-intro-rise .65s cubic-bezier(.2,.75,.2,1) both;
              }
              #satark-intro-overlay .satark-mark {
                width: 66px; height: 66px; display: grid; place-items: center; position: relative;
                border: 1px solid rgba(157,205,224,.34); border-radius: 20px;
                background: linear-gradient(145deg, rgba(123,181,204,.13), rgba(255,255,255,.025));
                box-shadow: 0 0 54px rgba(83,172,190,.12), inset 0 1px rgba(255,255,255,.09);
                font-size: 31px; font-weight: 800; letter-spacing: -.09em; color: #effbff;
              }
              #satark-intro-overlay .satark-mark::after {
                content: ""; position: absolute; width: 7px; height: 7px; right: 11px; bottom: 12px;
                border-radius: 50%; background: #81e2c0; box-shadow: 0 0 12px rgba(129,226,192,.75);
              }
              #satark-intro-overlay .satark-wordmark {
                margin-top: 23px; font-size: clamp(27px, 6vw, 36px); font-weight: 820;
                letter-spacing: .17em; padding-left: .17em; line-height: 1;
              }
              #satark-intro-overlay .satark-subbrand {
                margin-top: 11px; color: #8ea4b8; font-size: 10px; font-weight: 750;
                letter-spacing: .2em; text-transform: uppercase;
              }
              #satark-intro-overlay .satark-loader-orbit {
                position: relative; width: 114px; height: 114px; margin: 28px 0 24px;
                display: grid; place-items: center;
              }
              #satark-intro-overlay .satark-loader-orbit::before,
              #satark-intro-overlay .satark-loader-orbit::after {
                content: ""; position: absolute; inset: 0; border: 1px solid rgba(133,183,205,.16); border-radius: 50%;
              }
              #satark-intro-overlay .satark-loader-orbit::after {
                inset: 12px; border-style: dashed; border-color: rgba(133,183,205,.24);
                animation: satark-intro-spin 9s linear infinite;
              }
              #satark-intro-overlay .satark-radar {
                width: 70px; height: 70px; position: relative; overflow: hidden; border-radius: 50%;
                border: 1px solid rgba(129,226,192,.36);
                background: radial-gradient(circle, rgba(129,226,192,.09) 0 2px, transparent 3px),
                  linear-gradient(0deg, transparent 49.5%, rgba(129,226,192,.2) 50%, transparent 50.5%),
                  linear-gradient(90deg, transparent 49.5%, rgba(129,226,192,.2) 50%, transparent 50.5%),
                  radial-gradient(circle, rgba(129,226,192,.08), rgba(129,226,192,.015) 68%, transparent 70%);
              }
              #satark-intro-overlay .satark-radar::before {
                content: ""; position: absolute; inset: 0; border-radius: 50%;
                background: conic-gradient(from 0deg, transparent 0 72%, rgba(129,226,192,.23) 92%, transparent 100%);
                animation: satark-intro-spin 2.8s linear infinite;
              }
              #satark-intro-overlay .satark-radar::after {
                content: ""; position: absolute; width: 4px; height: 4px; left: 51%; top: 28%;
                border-radius: 50%; background: #81e2c0; box-shadow: 0 0 9px #81e2c0;
              }
              #satark-intro-overlay .satark-status {
                color: #d8e5ef; font-size: 11px; font-weight: 750; letter-spacing: .17em; text-transform: uppercase;
              }
              #satark-intro-overlay .satark-description {
                margin-top: 9px; color: #7e90a4; font-size: 12px; line-height: 1.65; max-width: 340px;
              }
              #satark-intro-overlay .satark-progress {
                margin-top: 24px; width: min(250px, 72vw); height: 2px; overflow: hidden;
                background: rgba(154,185,206,.15); border-radius: 10px;
              }
              #satark-intro-overlay .satark-progress span {
                display: block; width: 36%; height: 100%; border-radius: inherit;
                background: linear-gradient(90deg, transparent, #81e2c0, #a8e8ef, transparent);
                animation: satark-intro-progress .95s ease-in-out infinite;
              }
              #satark-intro-overlay .satark-foot {
                margin-top: 23px; color: #536477; font-size: 9px; font-weight: 700;
                letter-spacing: .15em; text-transform: uppercase;
              }
              #satark-intro-overlay .satark-skip {
                margin-top: 18px; border: 1px solid rgba(154,185,206,.18); border-radius: 999px;
                padding: 7px 13px; color: #9cb0c2; background: rgba(255,255,255,.025);
                font: inherit; font-size: 11px; cursor: pointer;
              }
              #satark-intro-overlay .satark-skip:focus-visible { outline: 2px solid #81e2c0; outline-offset: 3px; }
              #satark-intro-overlay.satark-intro-leaving { opacity: 0; visibility: hidden; pointer-events: none; }
              @keyframes satark-intro-spin { to { transform: rotate(360deg); } }
              @keyframes satark-intro-progress { from { transform: translateX(-120%); } to { transform: translateX(360%); } }
              @keyframes satark-intro-rise { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
              @media (max-width: 480px) {
                #satark-intro-overlay .satark-mark { width: 58px; height: 58px; border-radius: 17px; }
                #satark-intro-overlay .satark-loader-orbit { margin: 23px 0 20px; }
              }
              @media (prefers-reduced-motion: reduce) {
                #satark-intro-overlay *, #satark-intro-overlay *::before, #satark-intro-overlay *::after {
                  animation: none !important; transition: none !important;
                }
              }
            `;
            doc.head.appendChild(style);

            const overlay = doc.createElement("div");
            overlay.id = "satark-intro-overlay";
            overlay.setAttribute("role", "dialog");
            overlay.setAttribute("aria-modal", "true");
            overlay.setAttribute("aria-label", "SATARK intro");
            const previousFocus = doc.activeElement;
            overlay.innerHTML = `
              <div class="satark-intro-inner">
                <div class="satark-mark" aria-hidden="true">S<span style="color:#81e2c0">·</span></div>
                <div class="satark-wordmark">SATARK</div>
                <div class="satark-subbrand">Digital threat intelligence</div>
                <div class="satark-loader-orbit" aria-hidden="true"><div class="satark-radar"></div></div>
                <div class="satark-status" role="status" aria-live="polite">Preparing your workspace</div>
                <div class="satark-description">Bringing your investigation tools into focus.<br>Evidence first. Decisions with context.</div>
                <div class="satark-progress" aria-hidden="true"><span></span></div>
                <div class="satark-foot">FIRSTLIGHT · THREAT ANALYSIS · DIGITAL SAFETY</div>
                <button class="satark-skip" type="button">Skip intro</button>
              </div>`;
            doc.body.appendChild(overlay);

            let dismissed = false;
            const skipButton = overlay.querySelector(".satark-skip");
            const onKeydown = (event) => {
              if (event.key === "Escape") {
                event.preventDefault();
                dismiss();
              } else if (event.key === "Tab") {
                // The splash is a short-lived modal; keep keyboard focus on its only control.
                event.preventDefault();
                skipButton.focus();
              }
            };
            const dismiss = () => {
              if (dismissed) return;
              dismissed = true;
              doc.removeEventListener("keydown", onKeydown);
              overlay.classList.add("satark-intro-leaving");
              hostWindow.setTimeout(() => {
                overlay.remove();
                const css = doc.getElementById("satark-intro-style");
                if (css) css.remove();
                if (previousFocus && previousFocus.isConnected && typeof previousFocus.focus === "function") {
                  previousFocus.focus({preventScroll: true});
                }
              }, 450);
            };
            skipButton.addEventListener("click", dismiss);
            doc.addEventListener("keydown", onKeydown);
            skipButton.focus({preventScroll: true});
            const reduceMotion = hostWindow.matchMedia && hostWindow.matchMedia("(prefers-reduced-motion: reduce)").matches;
            hostWindow.setTimeout(dismiss, reduceMotion ? 650 : 1300);
          } catch (error) {
            // The intro is decorative: a blocked embed must never prevent use of SATARK.
          }
        })();
        </script></body></html>""",
        height=1,
        width=1,
        tab_index=-1,
    )
