"""React Bits-inspired Stepper integration for the Streamlit UI.

SATARK is a Streamlit application, so the React component is mounted inside a
self-contained Streamlit HTML component. The browser loads React, ReactDOM,
and Motion from esm.sh; no Python package or unused npm workspace is added.
"""

from __future__ import annotations

import streamlit.components.v1 as components


_STEPPER_HTML = r"""
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<style>
:root{color-scheme:dark}
html,body,#root{margin:0;width:100%;min-height:100%;background:transparent}
body{font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;color:#f5f5f4}
*{box-sizing:border-box}
.stepper{width:100%;max-width:760px;margin:0 auto;border:1px solid rgba(255,255,255,.12);border-radius:28px;background:rgba(8,8,8,.78);box-shadow:0 20px 50px rgba(0,0,0,.22);overflow:hidden;backdrop-filter:blur(12px)}
.indicators{display:flex;align-items:center;padding:24px 28px 18px}
.indicator{width:34px;height:34px;border-radius:999px;display:grid;place-items:center;flex:0 0 auto;font-size:13px;font-weight:700;cursor:pointer;border:0}
.indicator:focus-visible{outline:2px solid #d6b36a;outline-offset:3px}
.connector{height:3px;flex:1;margin:0 9px;border-radius:999px;background:rgba(255,255,255,.13);overflow:hidden}
.connector>div{height:100%;background:#d6b36a;transform-origin:left center}
.content{position:relative;overflow:hidden;padding:0 28px;min-height:185px}
.content-inner{padding:12px 0 6px}
.eyebrow{font-size:11px;letter-spacing:.16em;text-transform:uppercase;color:#d6b36a;font-weight:700}
h2{font-size:clamp(1.35rem,3vw,1.9rem);line-height:1.15;margin:9px 0 10px;letter-spacing:-.035em}
p{margin:0;color:#b8b6af;line-height:1.65;font-size:14px;max-width:620px}
.step-list{margin:16px 0 0;padding-left:18px;color:#c8c5bc;font-size:13px;line-height:1.8}
.footer{display:flex;justify-content:flex-end;gap:10px;padding:16px 28px 26px}
button.nav{border:0;font:inherit;font-weight:600;cursor:pointer;padding:9px 15px;border-radius:999px}
button.back{background:transparent;color:#aaa7a0}
button.next{background:#d6b36a;color:#10100f}
button.nav:focus-visible{outline:2px solid #d6b36a;outline-offset:3px}
button.nav:hover{filter:brightness(1.08)}
.complete{padding:28px;text-align:center;min-height:185px;display:grid;place-items:center}
@media(max-width:600px){.indicators{padding:18px 16px 12px}.content{padding:0 18px}.footer{padding:12px 18px 20px}.stepper{border-radius:22px}.indicator{width:30px;height:30px}.connector{margin:0 5px}}
@media(prefers-reduced-motion:reduce){*{scroll-behavior:auto!important}}
</style>
</head>
<body><div id="root"></div>
<script type="module">
import React,{useState,useLayoutEffect,useRef} from "https://esm.sh/react@18.3.1";
import {createRoot} from "https://esm.sh/react-dom@18.3.1/client";
import {motion,AnimatePresence} from "https://esm.sh/motion@12.23.24/react";

const h=React.createElement;
const steps=[
 {title:"Start with the evidence",body:"Choose the suspicious message, link, image, PDF, or video you want SATARK to examine.",items:["Keep the original context","Do not open suspicious links just to test them"]},
 {title:"Let SATARK inspect it",body:"SATARK extracts the relevant signals and sends supported analysis to your configured AI provider.",items:["URL checks stay limited to eligible public pages","Uploads are processed within the app limits"]},
 {title:"Review the risk",body:"Read the threat category, evidence, confidence, and recommended actions together.",items:["A high score is not proof","A low score is not a guarantee of safety"]},
 {title:"Verify before acting",body:"Use the result as a triage aid, then independently verify consequential claims or requests.",items:["Never share passwords, OTPs, or private keys","Report confirmed abuse through the appropriate channel"]}
];

function Stepper(){
 const [current,setCurrent]=useState(1),[direction,setDirection]=useState(1),[done,setDone]=useState(false);
 const reduced=matchMedia("(prefers-reduced-motion: reduce)").matches;
 const go=n=>{setDirection(n>current?1:-1);setCurrent(n)};
 const next=()=>current<steps.length?go(current+1):setDone(true);
 const back=()=>current>1&&go(current-1);
 if(done)return h("div",{className:"stepper"},h("div",{className:"complete"},h("div",null,
   h("div",{className:"eyebrow"},"SATARK • READY"),
   h("h2",null,"You’re ready to run a security check."),
   h("p",null,"Use the Check something page to start with the content you received.")
 ));
 return h("div",{className:"stepper"},
   h("div",{className:"indicators"},steps.map((s,i)=>{
     const n=i+1,status=current===n?"active":current>n?"complete":"inactive";
     return h(React.Fragment,{key:n},
       h(motion.button,{className:"indicator",type:"button","aria-label":`Go to step ${n}`,onClick:()=>go(n),animate:{scale:status==="active"?1.06:1,backgroundColor:status==="inactive"?"#262626":"#d6b36a",color:status==="inactive"?"#aaa7a0":"#11100d"},transition:{duration:reduced?0:.25}},status==="complete"?"✓":n),
       i<steps.length-1&&h("div",{className:"connector"},h(motion.div,{animate:{scaleX:current>n?1:0},transition:{duration:reduced?0:.35}}))
     );
   })),
   h("div",{className:"content"},
     h(AnimatePresence,{initial:false,mode:"sync",custom:direction},
       h(motion.div,{key:current,custom:direction,initial:{x:direction>0?"100%":"-100%",opacity:0},animate:{x:0,opacity:1},exit:{x:direction>0?"-35%":"35%",opacity:0},transition:{duration:reduced?0:.35},className:"content-inner"},
         h("div",{className:"eyebrow"},`STEP ${current} / ${steps.length}`),
         h("h2",null,steps[current-1].title),
         h("p",null,steps[current-1].body),
         h("ul",{className:"step-list"},steps[current-1].items.map((x,i)=>h("li",{key:i},x)))
       )
     )
   ),
   h("div",{className:"footer"},
     current>1&&h("button",{className:"nav back",type:"button",onClick:back},"Previous"),
     h("button",{className:"nav next",type:"button",onClick:next},current===steps.length?"Complete":"Next")
   )
 );
}
createRoot(document.getElementById("root")).render(h(Stepper));
</script></body></html>
"""


def render_stepper() -> None:
    """Render the SATARK onboarding stepper."""
    components.html(_STEPPER_HTML, height=390, scrolling=False)
