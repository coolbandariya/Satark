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
            style.textContent = "\n#satark-intro-overlay {\n  position:fixed; inset:0; z-index:2147483000; display:grid; place-items:center; overflow:hidden;\n  background:radial-gradient(ellipse at 50% 38%,rgba(126,61,177,.25),transparent 42%),\n    radial-gradient(ellipse at 50% 100%,rgba(255,128,37,.13),transparent 45%),#10091e;\n  color:#fff4df; font-family:\"Courier New\",ui-monospace,monospace; opacity:1; visibility:visible;\n  transition:opacity .42s ease,visibility .42s ease;\n}\n#satark-intro-overlay::before {\n  content:\"\";position:absolute;inset:0;pointer-events:none;opacity:.25;\n  background-image:linear-gradient(rgba(255,255,255,.035) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.035) 1px,transparent 1px);\n  background-size:4px 4px;\n}\n#satark-intro-overlay::after {\n  content:\"\";position:absolute;inset:0;pointer-events:none;\n  background:linear-gradient(transparent 50%,rgba(0,0,0,.2) 50%);background-size:100% 4px;opacity:.3;\n}\n#satark-intro-overlay .satark-arcade-shell {\n  position:relative;z-index:2;width:min(560px,calc(100vw - 32px));min-height:540px;\n  display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;\n  padding:32px 22px 126px;box-sizing:border-box;animation:satark-arcade-enter .55s steps(5,end) both;\n}\n#satark-intro-overlay .satark-pixel-label {\n  color:#b8a1d4;font-size:9px;font-weight:700;letter-spacing:.23em;text-transform:uppercase;\n}\n#satark-intro-overlay .satark-pixel-mascot {\n  position:relative;display:grid;place-items:center;width:124px;height:138px;margin:4px 0 12px;\n  filter:drop-shadow(0 0 15px rgba(255,173,62,.28));animation:satark-pizza-float 2.4s ease-in-out infinite;\n}\n#satark-intro-overlay .satark-mascot-shadow {\n  position:absolute;bottom:1px;width:52px;height:9px;border-radius:50%;background:rgba(0,0,0,.48);\n  filter:blur(4px);animation:satark-shadow-pulse 2.4s ease-in-out infinite;\n}\n#satark-intro-overlay .satark-wordmark {\n  margin-top:8px;font-size:clamp(26px,6vw,36px);font-weight:900;letter-spacing:.18em;padding-left:.18em;line-height:1;\n  color:#fff4d8;text-shadow:3px 3px 0 #6e36a0,0 0 22px rgba(186,118,255,.28);\n}\n#satark-intro-overlay .satark-subbrand {\n  margin-top:11px;color:#ffb24c;font-size:9px;font-weight:800;letter-spacing:.2em;text-transform:uppercase;\n}\n#satark-intro-overlay .satark-boot-label {\n  margin-top:29px;color:#ffe18a;font-size:clamp(11px,2.8vw,14px);font-weight:900;letter-spacing:.19em;\n  text-shadow:0 0 12px rgba(255,189,64,.35);\n}\n#satark-intro-overlay .satark-progress-row {display:flex;align-items:center;justify-content:center;width:min(360px,100%);margin-top:17px}\n#satark-intro-overlay .satark-progress-track {\n  display:grid;grid-template-columns:repeat(10,minmax(0,1fr));gap:4px;width:100%;padding:7px;\n  border:1px solid rgba(255,204,89,.45);background:rgba(8,4,18,.82);border-radius:3px;\n  box-shadow:0 0 18px rgba(255,130,44,.12),inset 0 0 12px rgba(116,63,171,.16);\n}\n#satark-intro-overlay .satark-progress-segment {\n  height:19px;border:1px solid rgba(255,204,89,.15);background:rgba(255,204,89,.055);border-radius:1px;\n  transition:background .16s steps(2,end),box-shadow .16s steps(2,end);\n}\n#satark-intro-overlay .satark-progress-segment.is-lit {\n  background:#ffc94e;border-color:#ffe08a;box-shadow:0 0 9px rgba(255,170,47,.45);\n}\n#satark-intro-overlay .satark-status {\n  min-height:20px;margin-top:14px;color:#ffb15a;font-size:9px;font-weight:800;letter-spacing:.12em;text-transform:uppercase;\n}\n#satark-intro-overlay .satark-description {\n  margin-top:5px;max-width:380px;color:#b9accb;font-size:11px;line-height:1.7;\n}\n#satark-intro-overlay .satark-arcade-footer {\n  position:absolute;bottom:98px;color:#77688c;font-size:8px;letter-spacing:.15em;text-transform:uppercase;\n}\n#satark-intro-overlay .satark-tip-card {\n  position:absolute;z-index:3;left:50%;bottom:20px;transform:translateX(-50%);width:min(510px,calc(100vw - 32px));\n  display:flex;align-items:center;gap:13px;padding:14px 16px;box-sizing:border-box;text-align:left;\n  border:1px solid rgba(255,202,84,.32);border-radius:5px;background:rgba(16,8,28,.91);\n  box-shadow:0 8px 28px rgba(0,0,0,.28),inset 0 0 16px rgba(151,84,197,.08);backdrop-filter:blur(5px);\n}\n#satark-intro-overlay .satark-tip-icon {\n  flex-shrink:0;width:30px;height:30px;display:grid;place-items:center;border:1px solid rgba(255,202,84,.3);\n  color:#ffd36a;font-size:19px;box-shadow:0 0 12px rgba(255,191,62,.12);\n}\n#satark-intro-overlay .satark-tip-heading {color:#ffd36a;font-size:9px;font-weight:900;letter-spacing:.16em;text-transform:uppercase}\n#satark-intro-overlay .satark-tip-text {margin-top:6px;color:#e7dff0;font-size:10px;line-height:1.55}\n#satark-intro-overlay .satark-skip {\n  position:absolute;right:16px;top:16px;z-index:4;border:1px solid rgba(210,188,235,.28);border-radius:3px;\n  padding:8px 10px;color:#d9c9e9;background:rgba(20,10,34,.76);font:inherit;font-size:9px;letter-spacing:.08em;\n  text-transform:uppercase;cursor:pointer;\n}\n#satark-intro-overlay .satark-skip:focus-visible {outline:2px solid #ffd36a;outline-offset:3px}\n#satark-intro-overlay.satark-intro-leaving {opacity:0;visibility:hidden;pointer-events:none}\n@keyframes satark-arcade-enter {from{opacity:0;transform:translateY(9px)}to{opacity:1;transform:translateY(0)}}\n@keyframes satark-pizza-float {0%,100%{transform:translateY(0)}50%{transform:translateY(-9px)}}\n@keyframes satark-shadow-pulse {0%,100%{transform:scale(1);opacity:.5}50%{transform:scale(.72);opacity:.25}}\n@media(max-width:480px) {\n  #satark-intro-overlay .satark-arcade-shell {min-height:100dvh;padding:45px 12px 140px}\n  #satark-intro-overlay .satark-pixel-mascot {width:104px;height:118px}\n  #satark-intro-overlay .satark-progress-segment {height:15px}\n  #satark-intro-overlay .satark-tip-card {bottom:12px;padding:11px 12px}\n  #satark-intro-overlay .satark-arcade-footer {bottom:100px;font-size:7px}\n}\n@media(prefers-reduced-motion:reduce) {\n  #satark-intro-overlay *,#satark-intro-overlay *::before,#satark-intro-overlay *::after {animation:none!important;transition:none!important}\n}\n";
            doc.head.appendChild(style);

            const overlay = doc.createElement("div");
            overlay.id = "satark-intro-overlay";
            overlay.setAttribute("role", "dialog");
            overlay.setAttribute("aria-modal", "true");
            overlay.setAttribute("aria-label", "SATARK intro");
            const previousFocus = doc.activeElement;
            overlay.innerHTML = "\n<div class=\"satark-arcade-shell\">\n  <button class=\"satark-skip\" type=\"button\">Skip intro ↗</button>\n  <div class=\"satark-pixel-label\">FIRSTLIGHT // SECURITY ARCADE</div>\n  <div class=\"satark-pixel-mascot\" aria-hidden=\"true\">\n    <svg xmlns=\"http://www.w3.org/2000/svg\" width=\"112\" height=\"112\" viewBox=\"0 0 48 48\" style=\"shape-rendering:crispEdges\">\n      <path d=\"M24 3 L42 12 V24 C42 34 34 41 24 46 C14 41 6 34 6 24 V12 Z\" fill=\"#6f3ca2\" stroke=\"#c6a4ee\" stroke-width=\"2\"/>\n      <path d=\"M24 7 L37 14 V24 C37 31 31 36 24 40 C17 36 11 31 11 24 V14 Z\" fill=\"#241334\" stroke=\"#9d6dc7\" stroke-width=\"1.5\"/>\n      <path d=\"M24 12 L35 33 H13 Z\" fill=\"#ffd15b\" stroke=\"#e79b30\" stroke-width=\"1.5\"/>\n      <path d=\"M24 16 L31 30 H17 Z\" fill=\"#f7a93a\"/>\n      <rect x=\"19\" y=\"21\" width=\"4\" height=\"4\" fill=\"#c33d43\"/><rect x=\"26\" y=\"25\" width=\"4\" height=\"4\" fill=\"#c33d43\"/>\n      <rect x=\"23\" y=\"27\" width=\"3\" height=\"3\" fill=\"#c33d43\"/>\n      <path d=\"M17 32 L19 35 M24 32 L24 37 M30 32 L29 35\" stroke=\"#ffe18a\" stroke-width=\"2\"/>\n      <path d=\"M17 12 L19 10 M30 10 L32 12\" stroke=\"#fff0c0\" stroke-width=\"1.5\"/>\n    </svg>\n    <div class=\"satark-mascot-shadow\"></div>\n  </div>\n  <div class=\"satark-wordmark\">SATARK</div>\n  <div class=\"satark-subbrand\">Pause · Inspect · Verify</div>\n  <div class=\"satark-boot-label\">SYSTEM BOOTING...</div>\n  <div class=\"satark-progress-row\" aria-hidden=\"true\">\n    <div class=\"satark-progress-track\"><span class=\"satark-progress-segment\" data-segment=\"0\"></span><span class=\"satark-progress-segment\" data-segment=\"1\"></span><span class=\"satark-progress-segment\" data-segment=\"2\"></span><span class=\"satark-progress-segment\" data-segment=\"3\"></span><span class=\"satark-progress-segment\" data-segment=\"4\"></span><span class=\"satark-progress-segment\" data-segment=\"5\"></span><span class=\"satark-progress-segment\" data-segment=\"6\"></span><span class=\"satark-progress-segment\" data-segment=\"7\"></span><span class=\"satark-progress-segment\" data-segment=\"8\"></span><span class=\"satark-progress-segment\" data-segment=\"9\"></span></div>\n  </div>\n  <div class=\"satark-status\" role=\"status\" aria-live=\"polite\">Waking up the threat radar...</div>\n  <div class=\"satark-description\">Preparing your investigation workspace.<br>Evidence first. Confidence with context.</div>\n  <div class=\"satark-arcade-footer\">FIRSTLIGHT • THREAT ANALYSIS • DIGITAL SAFETY</div>\n</div>\n<div class=\"satark-tip-card\">\n  <div class=\"satark-tip-icon\" aria-hidden=\"true\">!</div>\n  <div><div class=\"satark-tip-heading\">Security checkpoint</div><div class=\"satark-tip-text\">Pause before you click. Verify the sender and destination first.</div></div>\n</div>";
            doc.body.appendChild(overlay);

            const statusMessages = [
              "Waking up the threat radar...",
              "Calibrating evidence checks...",
              "Securing the investigation workspace...",
              "Getting your signals in order..."
            ];
            const securityTips = [
              "Pause before you click. Verify the sender and destination first.",
              "A familiar logo is not proof a message is genuine.",
              "Never share passwords, OTPs, or recovery codes.",
              "Treat AI findings as signals. Check the evidence before acting."
            ];
            const segments = [...overlay.querySelectorAll(".satark-progress-segment")];
            const status = overlay.querySelector(".satark-status");
            const tipText = overlay.querySelector(".satark-tip-text");
            let progress = 0;
            let statusIndex = 0;
            let tipIndex = 0;
            const reducedMotion = hostWindow.matchMedia && hostWindow.matchMedia("(prefers-reduced-motion: reduce)").matches;
            const progressTimer = hostWindow.setInterval(() => {
              progress = (progress + 1) % (segments.length + 1);
              segments.forEach((segment, index) => segment.classList.toggle("is-lit", index < progress));
            }, reducedMotion ? 120 : 170);
            const statusTimer = hostWindow.setInterval(() => {
              statusIndex = (statusIndex + 1) % statusMessages.length;
              if (status) status.textContent = statusMessages[statusIndex];
            }, 650);
            const tipTimer = hostWindow.setInterval(() => {
              tipIndex = (tipIndex + 1) % securityTips.length;
              if (tipText) tipText.textContent = securityTips[tipIndex];
            }, 1050);
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
              hostWindow.clearInterval(progressTimer);
              hostWindow.clearInterval(statusTimer);
              hostWindow.clearInterval(tipTimer);
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
            hostWindow.setTimeout(dismiss, reducedMotion ? 900 : 2600);
          } catch (error) {
            // The intro is decorative: a blocked embed must never prevent use of SATARK.
          }
        })();
        </script></body></html>""",
        height=1,
        width=1,
        tab_index=-1,
    )
