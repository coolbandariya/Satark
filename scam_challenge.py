"""Scam Challenge game content, state helpers, and Streamlit rendering."""
import html
import random
import math
import time

import streamlit as st

SC_CSS = """
<style>
:root {
  --bg:#070808;
  --surface:#0d0f0f;
  --surface2:#121514;
  --line:rgba(239,232,213,.10);
  --line2:rgba(239,232,213,.18);
  --text:#f5f2e9;
  --soft:#d9d6cd;
  --muted:#aaa79e;
  --violet:#d7b56f;
  --violet2:rgba(215,181,111,.08);
  --cyan:#55d98a;
  --gold:#d7b56f;
  --safe:#55d98a;
  --warn:#e9b85f;
  --danger:#ff6b61;
}
*{box-sizing:border-box}
html,body,[class*="css"]{font-family:"Manrope","Segoe UI",sans-serif;}
body{background:var(--bg);color:var(--text);}
h1,h2,h3,h4,h5,h6{color:#f7f7fb!important;}
.stApp{
  min-height:100vh;
  background:
    radial-gradient(circle at 12% -8%, rgba(215,181,111,.08), transparent 32rem),
    radial-gradient(circle at 90% 10%, rgba(85,217,138,.05), transparent 28rem),
    radial-gradient(circle at 50% 110%, rgba(215,181,111,.05), transparent 34rem),
    linear-gradient(180deg,#070808 0%,#0c0f0e 55%,#070808 100%);
}
.block-container{max-width:1200px;padding:1.2rem clamp(1rem,3vw,3rem) 4rem;}
.section-title{
  margin:1.4rem 0 .35rem;font-family:"Sora",sans-serif;font-size:1.35rem;
  font-weight:800;color:#f5f5f9;
}
.section-copy{margin:0 0 .8rem;color:#c7c9d6;font-size:.9rem;}
div[data-testid="stButton"]>button{
  min-height:46px;border-radius:13px;border:1px solid var(--line2);
  background:rgba(255,255,255,.055);color:var(--text);font-weight:700;
  transition:.18s ease;
}
div[data-testid="stButton"]>button:hover{
  transform:translateY(-2px);border-color:rgba(164,139,255,.6);
  background:rgba(164,139,255,.12);box-shadow:0 15px 35px rgba(0,0,0,.32);
}
div[data-testid="stButton"]>button[kind="primary"]{
  border-color:rgba(164,139,255,.7);
  background:linear-gradient(135deg,#7b6439,#171914);
}
/* ============================================================
   SCAM CHALLENGE — game system
   ============================================================ */
.pill{
  display:inline-block;
  padding:6px 14px;
  border-radius:999px;
  border:1px solid var(--line2);
  background:rgba(164,139,255,.10);
  color:#d6cfff;
  font-size:.64rem;
  font-weight:800;
  letter-spacing:.16em;
  text-transform:uppercase;
}
.sc-dash{
  position:relative;
  overflow:hidden;
  padding:26px;
  border:1px solid var(--line2);
  border-radius:20px;
  background:
    radial-gradient(circle at 12% 0%, rgba(215,181,111,.08), transparent 55%),
    radial-gradient(circle at 92% 105%, rgba(85,217,138,.05), transparent 50%),
    linear-gradient(145deg,rgba(28,30,40,.94),rgba(13,14,20,.97));
  box-shadow:0 20px 55px rgba(0,0,0,.4), inset 0 1px 0 rgba(255,255,255,.05);
}
.sc-dash:before{
  content:"";
  position:absolute;inset:0;
  background-image:radial-gradient(rgba(255,255,255,.055) 1px, transparent 1px);
  background-size:24px 24px;
  -webkit-mask-image:radial-gradient(circle at 20% 10%, #000 0%, transparent 70%);
          mask-image:radial-gradient(circle at 20% 10%, #000 0%, transparent 70%);
  pointer-events:none;
}
.sc-dash-badge{flex-shrink:0;}
.sc-dash-rankinfo{flex:1;min-width:220px;}

/* ---- HEADER + POINTS BADGE (top-right, all views) ---- */
.sc-header-row{
  display:flex;
  align-items:flex-start;
  justify-content:space-between;
  gap:16px;
  flex-wrap:wrap;
}
.sc-header-row .section-title{margin-top:0;}
.sc-points-badge{
  display:flex;
  align-items:center;
  gap:10px;
  padding:9px 18px;
  border-radius:14px;
  border:1px solid rgba(242,200,121,.45);
  background:linear-gradient(135deg, rgba(242,200,121,.18), rgba(164,139,255,.12));
  box-shadow:0 10px 24px rgba(0,0,0,.32), inset 0 1px 0 rgba(255,255,255,.08);
  flex-shrink:0;
  margin-top:2px;
}
.sc-points-icon{
  font-size:1.15rem;
  filter:drop-shadow(0 0 6px rgba(242,200,121,.65));
}
.sc-points-text{display:flex;flex-direction:column;line-height:1.1;}
.sc-points-v{font-family:Sora,sans-serif;font-size:1.1rem;font-weight:800;color:#f7f7fb;}
.sc-points-l{font-size:.58rem;font-weight:800;letter-spacing:.12em;text-transform:uppercase;color:#e8d5a7;margin-top:2px;}
.sc-tagline{
  color:#d6cfff;
  font-size:.7rem;
  font-weight:800;
  letter-spacing:.16em;
  text-transform:uppercase;
  margin-bottom:8px;
}
.sc-row{display:flex;align-items:center;gap:18px;flex-wrap:wrap;}
.sc-rankname{font-family:Sora,sans-serif;font-size:1.2rem;font-weight:800;color:#f7f7fb;}
.sc-ranknum{color:#d6cfff;font-size:.74rem;font-weight:800;letter-spacing:.14em;}
.sc-progresswrap{margin-top:16px;}
.sc-progresslabel{display:flex;justify-content:space-between;font-size:.74rem;color:#d3d4e0;font-weight:700;margin-bottom:6px;}
.sc-bar{height:12px;border-radius:999px;background:#23252f;overflow:hidden;border:1px solid var(--line);}
.sc-bar>div{height:100%;border-radius:inherit;background:linear-gradient(90deg,#d7b56f,#55d98a);transition:width .4s ease;}
.sc-stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(110px,1fr));gap:10px;margin-top:18px;}
.sc-stat{padding:12px;border:1px solid var(--line);border-radius:13px;background:rgba(255,255,255,.045);text-align:center;}
.sc-stat-v{font-family:Sora,sans-serif;font-size:1.3rem;font-weight:800;color:#f7f7fb;}
.sc-stat-l{margin-top:3px;font-size:.63rem;font-weight:800;letter-spacing:.1em;text-transform:uppercase;color:#a7aabb;}

/* ---- BADGES (game-rank style emblem) ---- */
.sc-badge-wrap{position:relative;width:92px;height:92px;display:flex;align-items:center;justify-content:center;flex-shrink:0;}
.sc-badge-wrap.sc-lg{width:128px;height:128px;}
.sc-badge-wrap.sc-sm{width:56px;height:56px;}
.sc-badge-outer{
  position:absolute;inset:0;border-radius:50%;
  background:conic-gradient(from 180deg, var(--rc), #ffffff33, var(--rc), #00000055, var(--rc));
  padding:3px;
  -webkit-mask:radial-gradient(farthest-side,#000 calc(100% - 3px),transparent calc(100% - 3px));
          mask:radial-gradient(farthest-side,#000 calc(100% - 3px),transparent calc(100% - 3px));
}
.sc-badge-ring{
  position:absolute;inset:8px;border-radius:50%;
  border:1.5px dashed color-mix(in srgb, var(--rc) 70%, transparent);
  opacity:.8;
}
.sc-badge-core{
  position:absolute;inset:14px;border-radius:50%;
  display:grid;place-items:center;
  font-size:1.9rem;line-height:1;text-align:center;
  background:radial-gradient(circle at 32% 26%, color-mix(in srgb, var(--rc) 35%, transparent), #0d0e15 72%);
  border:2px solid color-mix(in srgb, var(--rc) 55%, transparent);
  box-shadow:inset 0 0 18px rgba(0,0,0,.5), 0 0 22px color-mix(in srgb, var(--rc) 35%, transparent);
}
.sc-badge-core span{display:block;transform:translateY(-0.04em);}
.sc-badge-wrap.sc-sm .sc-badge-core{font-size:1.1rem;inset:9px;}
.sc-badge-wrap.sc-sm .sc-badge-ring{inset:6px;}
.sc-badge-wrap.sc-lg .sc-badge-core{font-size:2.5rem;inset:18px;}
.sc-badge-tier{
  position:absolute;left:50%;bottom:-9px;transform:translateX(-50%);
  padding:2px 9px;border-radius:999px;
  background:linear-gradient(135deg, var(--rc), #0d0e15);
  border:1px solid rgba(255,255,255,.35);
  color:#fff;font-family:Sora,sans-serif;font-size:.62rem;font-weight:800;
  letter-spacing:.04em;white-space:nowrap;box-shadow:0 4px 10px rgba(0,0,0,.4);
}
.sc-badge-wrap.sc-sm .sc-badge-tier{display:none;}
.sc-anim-pulse{animation:sc-pulse 2.4s ease-in-out infinite;}
.sc-anim-rotate .sc-badge-ring{animation:sc-rotatering 7s linear infinite;}
.sc-anim-shimmer .sc-badge-core{position:relative;overflow:hidden;}
.sc-anim-shimmer .sc-badge-core:after{
  content:"";position:absolute;inset:0;
  background:linear-gradient(120deg,transparent 30%,rgba(255,255,255,.4) 50%,transparent 70%);
  background-size:220% 220%;animation:sc-shimmer 2.6s ease-in-out infinite;
}
.sc-anim-legend{animation:sc-pulse 1.7s ease-in-out infinite;}
.sc-anim-legend .sc-badge-ring{animation:sc-rotatering 4.2s linear infinite;}
.sc-anim-legend .sc-badge-core:after{
  content:"";position:absolute;inset:0;
  background:linear-gradient(120deg,transparent 30%,rgba(255,255,255,.5) 50%,transparent 70%);
  background-size:220% 220%;animation:sc-shimmer 1.8s ease-in-out infinite;
}
@keyframes sc-pulse{
  0%,100%{filter:drop-shadow(0 0 4px color-mix(in srgb, var(--rc) 45%, transparent));transform:scale(1);}
  50%{filter:drop-shadow(0 0 16px var(--rc));transform:scale(1.045);}
}
@keyframes sc-rotatering{0%{transform:rotate(0deg);}100%{transform:rotate(360deg);}}
@keyframes sc-shimmer{0%{background-position:-120% -120%;}100%{background-position:120% 120%;}}

/* ---- LEVEL MAP ---- */
.sc-rankblock{margin:22px 0 6px;padding:14px 16px;border:1px solid var(--line2);border-radius:16px;background:rgba(255,255,255,.035);}
.sc-rankblock-head{display:flex;align-items:center;gap:14px;margin-bottom:2px;}
.sc-rankblock-head>div{display:flex;flex-direction:column;justify-content:center;}
.sc-rankblock-title{font-family:Sora,sans-serif;font-weight:800;font-size:.95rem;color:#f5f5f9;}
.sc-rankblock-sub{font-size:.68rem;color:#a7aabb;font-weight:700;letter-spacing:.06em;margin-top:2px;}
.sc-cell{min-height:52px;border-radius:12px;border:1px solid var(--line);display:flex;flex-direction:column;align-items:center;justify-content:center;font-size:.72rem;font-weight:800;text-align:center;padding:4px;}
.sc-cell-locked{background:rgba(255,255,255,.02);color:#5f6273;opacity:.65;}
.sc-cell-completed{background:rgba(62,224,138,.12);border-color:rgba(62,224,138,.45);color:#a4f5c4;}
.sc-cell-current{background:rgba(164,139,255,.18);border-color:rgba(164,139,255,.8);color:#ece7ff;animation:sc-pulse 2.2s ease-in-out infinite;--rc:#a48bff;}
div[data-testid="stButton"]>button.sc-levelbtn-locked, div[data-testid="stButton"] button:disabled{opacity:.45;cursor:not-allowed;}

/* ---- HUD ---- */
.sc-hud{display:grid;grid-template-columns:repeat(auto-fit,minmax(100px,1fr));gap:10px;padding:14px;margin-bottom:14px;border:1px solid var(--line2);border-radius:15px;background:rgba(255,255,255,.04);}
.sc-hud-item{text-align:center;}
.sc-hud-v{font-family:Sora,sans-serif;font-size:1.15rem;font-weight:800;color:#f7f7fb;}
.sc-hud-l{font-size:.6rem;font-weight:800;letter-spacing:.1em;text-transform:uppercase;color:#a7aabb;margin-top:2px;}
.sc-qcard{padding:22px;border:1px solid var(--line2);border-radius:18px;background:rgba(255,255,255,.045);margin-bottom:14px;}
.sc-qcat{display:inline-block;padding:4px 11px;border-radius:999px;background:rgba(242,200,121,.13);border:1px solid rgba(242,200,121,.4);color:#f2c879;font-size:.62rem;font-weight:800;letter-spacing:.1em;text-transform:uppercase;margin-bottom:12px;}
.sc-qtext{font-size:1.06rem;line-height:1.55;color:#f5f5f9;font-weight:650;}
.sc-feedback{padding:16px 18px;border-radius:14px;margin:14px 0;font-weight:700;border:1px solid var(--line2);}
.sc-feedback-correct{background:rgba(62,224,138,.13);border-color:rgba(62,224,138,.45);color:#a4f5c4;}
.sc-feedback-wrong{background:rgba(255,92,92,.13);border-color:rgba(255,92,92,.45);color:#ffb3b3;}
.sc-feedback-pts{font-family:Sora,sans-serif;font-size:1.5rem;margin-top:2px;}
.sc-explain{padding:14px 16px;border-left:3px solid var(--violet);border-radius:12px;background:var(--violet2);color:#eceefb;line-height:1.6;font-size:.89rem;}

/* ---- RESULTS / RANKUP ---- */
.sc-results{padding:26px;border-radius:20px;border:1px solid var(--line2);text-align:center;background:linear-gradient(160deg,rgba(28,30,40,.94),rgba(13,14,20,.97));box-shadow:0 20px 55px rgba(0,0,0,.4);}
.sc-results-level{color:#a7aabb;font-size:.72rem;font-weight:800;letter-spacing:.14em;text-transform:uppercase;}
.sc-results-title{font-family:Sora,sans-serif;font-size:1.75rem;font-weight:800;color:#f7f7fb;margin:6px 0 18px;}
.sc-bigscore{font-family:Sora,sans-serif;font-size:2.7rem;font-weight:800;background:linear-gradient(90deg,#a48bff,#f2c879);-webkit-background-clip:text;background-clip:text;color:transparent;}
.sc-rankup-wrap{text-align:center;padding:34px 22px;border-radius:22px;border:1px solid rgba(242,200,121,.45);background:radial-gradient(circle at 50% 0%,rgba(242,200,121,.16),transparent 60%),linear-gradient(160deg,rgba(28,30,40,.95),rgba(13,14,20,.97));box-shadow:0 25px 65px rgba(0,0,0,.45);}
.sc-rankup-label{color:#f2c879;font-size:.8rem;font-weight:800;letter-spacing:.24em;text-transform:uppercase;margin-bottom:18px;}
.sc-rankup-newbadge{color:#a4f5c4;font-size:.72rem;font-weight:800;letter-spacing:.1em;text-transform:uppercase;margin-top:16px;}
@media (max-width:640px){
  .sc-badge-wrap.sc-lg{width:96px;height:96px;}
  .sc-badge-wrap.sc-lg .sc-badge-core{font-size:1.9rem;}
  .sc-bigscore{font-size:2rem;}
}
</style>
"""

# ----------------------- SC-LOGIC-START ------------------------
# ==============================================================
# SCAM CHALLENGE — game engine (100 levels x 10 questions)
# ==============================================================
SC_RANKS = [
    {"num": "I", "roman": "I", "name": "DIGITAL ROOKIE", "lo": 1, "hi": 10,
     "icon": "🛡️", "anim": "sc-anim-pulse", "color": "#7fd68f"},
    {"num": "II", "roman": "II", "name": "SCAM SCOUT", "lo": 11, "hi": 20,
     "icon": "🔎", "anim": "sc-anim-pulse", "color": "#5eead4"},
    {"num": "III", "roman": "III", "name": "THREAT TRACKER", "lo": 21, "hi": 30,
     "icon": "📡", "anim": "sc-anim-rotate", "color": "#7fb6ff"},
    {"num": "IV", "roman": "IV", "name": "CYBER SENTINEL", "lo": 31, "hi": 40,
     "icon": "🛰️", "anim": "sc-anim-pulse", "color": "#a48bff"},
    {"num": "V", "roman": "V", "name": "FRAUD HUNTER", "lo": 41, "hi": 50,
     "icon": "🎯", "anim": "sc-anim-rotate", "color": "#ff9f6e"},
    {"num": "VI", "roman": "VI", "name": "SECURITY OPERATIVE", "lo": 51, "hi": 60,
     "icon": "⚙️", "anim": "sc-anim-shimmer", "color": "#ffd166"},
    {"num": "VII", "roman": "VII", "name": "CYBER GUARDIAN", "lo": 61, "hi": 70,
     "icon": "🔰", "anim": "sc-anim-pulse", "color": "#57e5c4"},
    {"num": "VIII", "roman": "VIII", "name": "THREAT COMMANDER", "lo": 71, "hi": 80,
     "icon": "📶", "anim": "sc-anim-rotate", "color": "#ff8fc9"},
    {"num": "IX", "roman": "IX", "name": "CYBER MASTER", "lo": 81, "hi": 90,
     "icon": "💠", "anim": "sc-anim-shimmer", "color": "#c9a9ff"},
    {"num": "X", "roman": "X", "name": "SATARK LEGEND", "lo": 91, "hi": 100,
     "icon": "👁️", "anim": "sc-anim-legend", "color": "#f2c879"},
]


def sc_rank_for_level(level):
    level = max(1, min(100, level))
    for r in SC_RANKS:
        if r["lo"] <= level <= r["hi"]:
            return r
    return SC_RANKS[-1]


def sc_badge_html(rank, size="lg"):
    """Game-style rank emblem. Built flush-left / single-line to avoid
    Markdown treating indented HTML as a code block."""
    size_cls = {"lg": "sc-lg", "sm": "sc-sm", "md": ""}.get(size, "")
    return ('<div class="sc-badge-wrap ' + size_cls + ' ' + rank["anim"] + '" style="--rc:' + rank["color"] + '">'
            '<div class="sc-badge-outer"></div>'
            '<div class="sc-badge-ring"></div>'
            '<div class="sc-badge-core"><span>' + rank["icon"] + '</span></div>'
            '<div class="sc-badge-tier">RANK ' + rank["roman"] + '</div>'
            '</div>')


# ---------------- Shared vocabulary pools ----------------
SC_BANKS = ["HDFC Bank", "ICICI Bank", "SBI", "Axis Bank", "Kotak Mahindra", "Punjab National Bank", "Yes Bank", "IDFC First Bank"]
SC_UPI = ["PhonePe", "Google Pay", "Paytm", "BHIM UPI", "Amazon Pay"]
SC_COURIERS = ["Delhivery", "Blue Dart", "India Post", "DTDC", "Ekart", "Xpressbees"]
SC_NAMES = ["Rohan", "Priya", "Arjun", "Sneha", "Vikram", "Ananya", "Karan", "Meera", "Farhan", "Ishita", "Nikhil", "Divya", "Aditya", "Pooja"]
SC_COMPANIES = ["Infosys", "TCS", "Wipro", "a fast-growing startup", "a multinational retail chain", "a logistics firm", "an EdTech company"]
SC_BROKERS = ["a SEBI-sounding advisory group", "a private trading Telegram channel", "an unlisted 'wealth partner' app", "a 'VIP signals' WhatsApp group"]
SC_PLATFORMS = ["Instagram", "Facebook", "WhatsApp", "LinkedIn", "Telegram", "X (Twitter)"]
SC_CITIES = ["Lagos", "Kyiv", "a city you've never visited", "a foreign IP address", "Dubai", "an unfamiliar location abroad"]
SC_DEPTS = ["Head Office IT", "the Fraud Prevention cell", "Corporate Compliance", "the Risk Management team", "Network Security"]
SC_ITEMS = ["a used bike", "a gaming console", "furniture", "a smartphone", "a laptop", "a camera"]
SC_DOMAINS_REAL = ["amazon.in", "flipkart.com", "irctc.co.in", "paytm.com", "myntra.com", "zomato.com"]
SC_APPS = ["a food delivery app", "a bank app", "an e-commerce app", "a UPI app", "a ride-hailing app", "a streaming app"]
SC_DOC_TYPES = ["a shared invoice", "a payroll spreadsheet", "a project proposal", "a scanned contract", "a shared photo album"]
SC_REASONS = ["a medical emergency", "a car accident abroad", "being stranded at an airport", "an urgent visa fee", "a hospital deposit"]
SC_RELATIONS = ["a close relative", "your father", "your sister", "your best friend", "your spouse", "your son"]


def _mk(rng, category, question, correct, distractors, explanation, qtype="identify"):
    opts = [correct] + list(distractors)
    rng.shuffle(opts)
    return {
        "category": category,
        "qtype": qtype,
        "question": question,
        "options": opts,
        "answer": opts.index(correct),
        "explanation": explanation,
    }


def g_phishing(rng, tier):
    bank = rng.choice(SC_BANKS)
    mins = rng.choice([5, 10, 15, 20, 30, 45])
    code = rng.randint(100, 999)
    if tier <= 2:
        q = (f'An SMS says: "{bank}: Your account will be suspended in {mins} minutes. '
             f'Verify now: bit.ly/verify-{code}". What is the strongest warning sign?')
        correct = "Urgency + an unofficial shortened link asking you to 'verify'"
    else:
        domain = f"{bank.split()[0].lower()}-secure{code}.com"
        q = (f'You get an email that looks pixel-perfect like {bank}, includes your first name, '
             f'and links to "{domain}" to "re-confirm KYC" within {mins} minutes. What should worry you most?')
        correct = f"The domain '{domain}' is not the bank's real domain, despite the email looking authentic"
    return _mk(rng, "Phishing", q, correct, [
        "The email/SMS uses your first name",
        "The message is written in formal English",
        "The message arrived during business hours",
    ], "Legitimate banks never create artificial time pressure and never send verification "
       "links to look-alike domains. Always type the bank's known URL directly instead of "
       "clicking a link in an unsolicited message.")


def g_otp(rng, tier):
    who = rng.choice(["your bank's fraud department", "a 'customer care executive'", "a courier agent", "a delivery partner", "a 'RBI compliance officer'"])
    amt = rng.randint(2000, 60000)
    if tier <= 2:
        q = f'Someone calling from {who} asks you to read out the OTP you just received to "cancel a fraudulent transaction" of ₹{amt}. What should you do?'
        correct = "Refuse and hang up — never share an OTP with anyone who calls you"
    else:
        q = (f'{who.capitalize()} calls, already knows your last 4 card digits and full name, and asks you '
             f'to read an OTP to "reverse" a ₹{amt} transaction that never happened. What is the real purpose of the OTP?')
        correct = "The OTP would actually authorize a payment or login the caller is trying to complete"
    return _mk(rng, "OTP Scam", q, correct, [
        "It is needed to confirm your identity to the bank",
        "It is safe since they already know your card details",
        "Reading it out loud does not share it electronically",
    ], "An OTP is a one-time authorization code. No legitimate process ever requires you to "
       "read it to someone else — doing so approves whatever transaction the scammer initiated.")


def g_suspicious_link(rng, tier):
    topic = rng.choice(["a parcel customs fee", "a subscription renewal", "a KYC update", "a refund", "an electricity bill", "a SIM deactivation notice"])
    tag = rng.choice(['pay', 'kyc', 'verify', 'refund', 'update', 'confirm'])
    short = f"{rng.choice(['tiny.cc', 'bit.ly', 'cutt.ly'])}/{tag}{rng.randint(10, 999)}"
    channel = rng.choice(["WhatsApp", "SMS", "email"])
    q = f'A {channel} message about {topic} includes the link "{short}". Before tapping it, what should you check first?'
    correct = "Where the shortened link actually redirects to, using a link-preview/expander tool"
    return _mk(rng, "Suspicious Link", q, correct, [
        "Whether the message has correct spelling",
        "How many people the message was forwarded to",
        "Whether the sender has a profile photo",
    ], "Shortened links hide the real destination. Expanding or hovering over a link before "
       "clicking reveals the true domain, which is the single most reliable signal.")


def g_fake_prize(rng, tier):
    amt = rng.choice([15000, 25000, 35000, 50000, 75000, 100000, 150000])
    fee = rng.choice([299, 499, 999, 1499, 1999])
    platform = rng.choice(["a lucky draw you never entered", "a festival giveaway you don't remember joining", "a mobile-recharge lottery"])
    q = (f'A message says you have won ₹{amt:,} in {platform}, and asks for a '
         f'₹{fee} "processing fee" to release it. What is the biggest red flag?')
    correct = "Genuine prizes are never released by first collecting a fee from the winner"
    return _mk(rng, "Fake Prize", q, correct, [
        "The amount is too large to be real",
        "The message uses the word 'lucky draw'",
        "The fee is a round number",
    ], "Legitimate lotteries or rewards deduct tax/fees from the winnings itself — they never "
       "ask winners to pay money upfront to 'unlock' a prize.")


def g_impersonation(rng, tier):
    name = rng.choice(SC_NAMES)
    role = rng.choice(["your manager", "a close relative", "your company's HR head", "an old college friend", "your landlord"])
    amt = rng.choice([1000, 2000, 5000, 10000])
    q = (f'You get a message that looks exactly like it is from {role} ("{name}"), asking you to urgently '
         f'buy ₹{amt} in gift cards and send the codes because they are "in a meeting and can\'t call." What should you do?')
    correct = "Verify through a separate channel (a phone call) before taking any action"
    return _mk(rng, "Impersonation", q, correct, [
        "Comply quickly since it sounds urgent",
        "Reply asking for more details over the same chat",
        "Ignore it completely without checking",
    ], "Impersonation scams rely on urgency and an inability to verify in the moment. A quick "
       "call to the real person on a known number instantly exposes the scam.")


def g_fake_support(rng, tier):
    app = rng.choice(SC_APPS)
    issue = rng.choice(["a failed refund", "a login issue", "a stuck payment", "an app crash", "a missing order"])
    wait = rng.choice([2, 5, 10, 15])
    q = (f'You search online for {app} customer care about {issue}, wait {wait} minutes, and call a number '
         f'from the results. The agent asks you to install a remote-access app "to fix the issue faster." '
         f'What is the danger here?')
    correct = "Remote-access tools give the caller full control of your device, including banking apps"
    return _mk(rng, "Fake Support", q, correct, [
        "Remote apps use too much data",
        "It will slow down your phone",
        "Support calls are always free anyway",
    ], "Fake customer-care numbers are frequently seeded on the open web. Once a scammer has "
       "remote access, they can open your banking apps directly — never install remote-access "
       "software at the request of an unsolicited 'support' call.")


def g_delivery(rng, tier):
    courier = rng.choice(SC_COURIERS)
    fee = rng.choice([2, 5, 10, 19, 25, 49])
    reason = rng.choice(["customs fee", "address correction fee", "storage fee", "re-delivery fee"])
    tracking = rng.randint(100000000, 999999999)
    q = (f'An SMS claims to be from {courier} (tracking #{tracking}): "Your parcel is on hold, pay ₹{fee} '
         f'{reason} to release it: {courier.lower().replace(" ", "")}-track.info/pay". What should you do first?')
    correct = "Track the order directly on the courier's official app/site instead of the SMS link"
    return _mk(rng, "Delivery Scam", q, correct, [
        "Pay the small fee since it is inexpensive",
        "Forward the SMS to friends to warn them first",
        "Reply STOP to the SMS",
    ], "The tiny fee is deliberate — designed to feel too small to question. The link domain "
       "is not the courier's real domain, and real customs charges are never collected via SMS links.")


def g_fake_bank_msg(rng, tier):
    bank = rng.choice(SC_BANKS)
    amt = rng.randint(8000, 95000)
    phone = rng.randint(70000, 99999)
    q = (f'An SMS reads: "{bank}: ₹{amt} debited from your a/c. If not done by you, call {phone}'
         f'{rng.randint(10000, 99999)} immediately." Calling this number connects you to a scammer. '
         f'What is the actual pattern here?')
    correct = "A fake debit alert designed to make you call a scammer-controlled 'helpline' in a panic"
    return _mk(rng, "Fake Bank Message", q, correct, [
        "A normal fraud-alert SMS from the bank",
        "A system-generated OTP message",
        "A promotional offer from the bank",
    ], "Fabricated debit alerts create panic so the victim calls a number controlled by the "
       "scammer, who then asks for card/OTP details to 'reverse' a transaction that never happened.")


def g_upi(rng, tier):
    app = rng.choice(SC_UPI)
    amt = rng.randint(500, 25000)
    item = rng.choice(SC_ITEMS)
    if tier <= 2:
        q = (f'You receive a {app} notification: "You have a payment request for ₹{amt}. Approve to receive money." '
             f'What should you know about UPI collect requests?')
        correct = "Approving a 'collect request' sends money OUT of your account, it never receives money"
    else:
        q = (f'A seller offering {item} on a resale marketplace insists on sending you a {app} "collect request" '
             f'instead of a normal transfer, to pay you ₹{amt} for the item. Why is this suspicious?')
        correct = "Collect requests only debit money from the person who approves them — the buyer wants you to pay, not get paid"
    return _mk(rng, "UPI Scam", q, correct, [
        "Collect requests are just a faster way to receive money",
        "It only works if you also enter your UPI PIN twice",
        "It is safe as long as the request is under ₹2,000",
    ], "A UPI 'collect' request always deducts money from whoever approves it. Anyone asking "
       "you to approve a collect request to 'receive' a payment is trying to debit your account.")


def g_qr(rng, tier):
    amt = rng.randint(800, 30000)
    reason = rng.choice(["a refund for a returned item", "a cashback offer", "a prize claim", "a security deposit return"])
    q = (f'To process {reason} of ₹{amt}, someone asks you to scan a QR code and enter your UPI PIN. '
         f'What is wrong with this request?')
    correct = "Scanning a QR code and entering a PIN is always used to SEND money, never to receive it"
    return _mk(rng, "QR Scam", q, correct, [
        "QR codes can only be used once",
        "They should have used a bank transfer instead",
        "QR refunds take longer than UPI IDs",
    ], "Receiving money never requires scanning a QR code or entering your PIN. Any process "
       "that asks for a PIN after a QR scan is a payment being pulled from your account.")


def g_job(rng, tier):
    company = rng.choice(SC_COMPANIES)
    pay = rng.randint(25, 95) * 1000
    task = rng.choice(["liking videos", "reviewing hotels online", "data entry", "typing captchas", "forwarding messages"])
    fee = rng.choice([500, 999, 1500, 2500])
    q = (f'A recruiter messages you a "work-from-home" job at {company} paying ₹{pay:,}/month for {task}, '
         f'but asks for a refundable ₹{fee} "registration fee" first. What should you suspect?')
    correct = "A job scam — legitimate employers never charge candidates to be hired"
    return _mk(rng, "Job Scam", q, correct, [
        "The pay is fair for the work described",
        "Refundable fees are always safe to pay",
        "This is normal for remote jobs",
    ], "Any job that asks the candidate to pay money upfront — registration, training kits, "
       "or 'refundable' deposits — is a strong indicator of a job scam, regardless of the brand name used.")


def g_social_impersonation(rng, tier):
    platform = rng.choice(SC_PLATFORMS)
    name = rng.choice(SC_NAMES)
    amt = rng.choice([2000, 5000, 8000, 15000])
    q = (f'A {platform} account using {name}\'s name and real photos messages your friends asking to borrow '
         f'₹{amt}, but the real {name} says they never sent it. What happened?')
    correct = f"The account (or {name}'s real account) was cloned or compromised to scam their contacts"
    return _mk(rng, "Social Media Impersonation", q, correct, [
        f"{name} is lying to avoid repaying a real loan",
        "It is a coincidence and unrelated accounts",
        "Social platforms cannot be impersonated",
    ], "Cloned or hacked profiles are commonly used to message a real person's existing contacts, "
       "who are more likely to trust a request that appears to come from someone they know.")


def g_advanced_phishing(rng, tier):
    bank = rng.choice(SC_BANKS)
    tail = rng.choice(["alerts", "secure-kyc", "netbanking", "verify", "support"])
    code = rng.randint(10, 99)
    q = (f'An email from "{bank.lower().replace(" ", "")}-{tail}{code}.com" has correct grammar, the real logo, '
         f'a real customer-support footer, and a login page that looks identical to {bank}\'s real site. '
         f'What is the one detail that reliably exposes it?')
    correct = "The sending domain does not match the bank's official domain, even though everything else looks right"
    return _mk(rng, "Advanced Phishing", q, correct, [
        "The email contains the bank's logo",
        "The email has no spelling mistakes",
        "The page asks for a login and password",
    ], "Sophisticated phishing kits can copy visual design perfectly. The domain in the address "
       "bar (not the page's appearance) is the one element attackers cannot fake convincingly.")


def g_url_manipulation(rng, tier):
    real = rng.choice(SC_DOMAINS_REAL)
    style = rng.choice(["hyphen-insert", "char-swap", "subdomain-trick", "extra-word"])
    order_id = rng.randint(100000, 999999)
    channel = rng.choice(["a tracking SMS", "an order-confirmation email", "a WhatsApp forward", "a push notification"])
    base, tld = real.split(".", 1)
    if style == "hyphen-insert":
        fake = f"{base}-secure.{tld}"
    elif style == "char-swap":
        fake = real.replace("o", "0", 1) if "o" in real else real.replace("i", "1", 1)
    elif style == "subdomain-trick":
        fake = f"{base}.{tld}.login-verify.com"
    else:
        fake = f"{base}account.{tld}"
    q = (f'{channel.capitalize()} about order #{order_id} links to "https://{fake}", claiming to be {real}. '
         f'Which of these URLs is most likely a manipulated look-alike of "{real}"?')
    correct = fake
    distract = [real, f"www.{real}", f"{real}/account"]
    return _mk(rng, "URL Manipulation", q, correct, distract,
               f"'{fake}' subtly alters the real domain '{real}' — extra words, character swaps, or "
               f"fake subdomains are invisible at a glance but resolve to an entirely different, "
               f"attacker-controlled server.")


def g_domain_spoofing(rng, tier):
    real = rng.choice(["hdfcbank.com", "icicibank.com", "sbi.co.in", "axisbank.com", "kotak.com", "yesbank.in", "idfcfirstbank.com"])
    tail = rng.choice(["verify", "secure-login", "kyc-update", "account-check", "reactivate", "confirm-id"])
    ref = rng.randint(10000, 99999)
    spoof = real.split(".")[0] + f"-{tail}.net"
    q = (f'A login page URL reads "https://{spoof}/login?ref={ref}" '
         f'and displays a padlock icon (HTTPS). Does the padlock mean the site is safe?')
    correct = "No — HTTPS only means the connection is encrypted, not that the site is genuine"
    return _mk(rng, "Domain Spoofing", q, correct, [
        "Yes, the padlock guarantees it is the real bank",
        "Yes, because scam sites cannot get HTTPS certificates",
        "It depends on the browser being used",
    ], "Attackers can obtain valid HTTPS certificates for spoofed domains just as easily as "
       "legitimate sites. Encryption protects data in transit, it says nothing about who owns the site.")


def g_social_engineering(rng, tier):
    dept = rng.choice(SC_DEPTS)
    mgr = rng.choice(SC_NAMES)
    channel = rng.choice(["a code sent to your phone", "your email verification code", "your login PIN"])
    ticket = rng.randint(1000, 9999)
    q = (f'A caller claiming to be from "{dept}" (case #INC-{ticket}) says your system was flagged for a '
         f'security breach, creates urgency, name-drops your actual manager "{mgr}", and asks you to read '
         f'back {channel} to "confirm your identity." What technique is being used?')
    correct = "Pretexting — building a believable false scenario using real details to lower your guard"
    return _mk(rng, "Social Engineering", q, correct, [
        "Standard IT security verification",
        "A phishing email, not a phone technique",
        "Two-factor authentication working correctly",
    ], "Social engineers research real names, roles and jargon in advance so the pretext feels "
       "credible. The actual goal is almost always to extract a one-time code or credential from you directly.")


def g_fake_support_interaction(rng, tier):
    app = rng.choice(SC_APPS)
    minutes = rng.choice([3, 5, 8, 10, 12, 15])
    ticket = rng.randint(100000, 999999)
    issue = rng.choice(["a failed refund", "a duplicate charge", "an OTP that never arrived", "a login lockout"])
    q = (f'While troubleshooting {issue} on {app} via a chat with "support" (ticket #{ticket}), the agent '
         f'insists on screen-sharing and asks you to open your banking app "just to check the balance shown," '
         f'without ever asking for a password. The session lasts {minutes} minutes. Why is this still risky?')
    correct = "A screen-share alone lets the agent see OTPs, balances, and account numbers as you type them"
    return _mk(rng, "Fake Support Interaction", q, correct, [
        "It is safe since they never asked for a password",
        "Screen sharing cannot capture banking apps",
        "It is fine as long as the session stays short",
    ], "Never entering a password doesn't make screen-sharing safe — everything visible on "
       "screen, including OTP pop-ups and account details, is captured by the person watching.")


def g_marketplace(rng, tier):
    item = rng.choice(SC_ITEMS)
    pay = rng.choice(["a courier company's 'advance payment protection'", "a 'buyer protection escrow' link", "a 'marketplace insurance' form"])
    price = rng.randint(3, 90) * 1000
    q = (f'A buyer offers ₹{price:,} for your {item} on an online marketplace, then insists on paying via '
         f'{pay} and sends a fake link to "verify" your bank details before shipping. What should you do?')
    correct = "Refuse — never enter bank details on a link sent by a buyer; use the marketplace's own payment flow"
    return _mk(rng, "Marketplace Scam", q, correct, [
        "Proceed since the name sounds official",
        "Share only the last 4 digits of your account",
        "Ask the buyer for ID proof first",
    ], "'Payment protection' links from buyers are a classic marketplace scam — the link is a "
       "credential-harvesting page, not a real courier or payment provider.")


def g_account_takeover(rng, tier):
    service = rng.choice(["email", "social media", "banking app", "cloud storage"])
    city = rng.choice(SC_CITIES)
    device = rng.choice(["an unrecognised Android device", "an unrecognised Windows PC", "an unknown browser session", "a device you've never used"])
    mins = rng.choice([2, 4, 6, 9, 12])
    q = (f'You get a "New login detected" alert for your {service} account from {city} on {device}, followed '
         f'{mins} minutes later by a password-reset email you did not request. What is the correct immediate action?')
    correct = "Change the password immediately from a trusted device and enable/verify two-factor authentication"
    return _mk(rng, "Account Takeover", q, correct, [
        "Ignore it since the login may have failed",
        "Wait 24 hours to see if it happens again",
        "Reply to the alert email asking who logged in",
    ], "A login alert followed by an unrequested reset email indicates an active takeover attempt. "
       "Acting immediately — before the attacker completes the reset — is what limits the damage.")


def g_bec(rng, tier):
    role = rng.choice(["CEO", "CFO", "Managing Director", "VP Finance"])
    dept = rng.choice(["finance team", "accounts payable team", "procurement desk"])
    amt = rng.randint(2, 25)
    decimal = rng.choice([0, 25, 5, 75])
    invoice = rng.randint(1000, 9999)
    q = (f'An email (re: invoice #{invoice}) that appears to be from your {role}, sent from a domain differing '
         f'by one letter from your company\'s real domain, urgently asks the {dept} to wire ₹{amt}.{decimal:02d} '
         f'lakh to a "new vendor account" and says not to call because they are "in back-to-back meetings." '
         f'What is this?')
    correct = "Business Email Compromise (BEC) — impersonating an executive to bypass normal payment checks"
    return _mk(rng, "Business Email Compromise", q, correct, [
        "A normal, time-sensitive vendor payment",
        "An internal IT test of the finance workflow",
        "A phishing attempt aimed at employees' personal accounts",
    ], "BEC attacks specifically target finance/payment approval steps by impersonating "
       "executives and discouraging verification. The 'don't call me' instruction is itself a red flag.")


def g_credential_harvesting(rng, tier):
    doc = rng.choice(SC_DOC_TYPES)
    host = rng.choice(["a generic cloud-storage-lookalike domain", "a link-shortener redirect", "a domain with no company branding at all"])
    sender = rng.choice(SC_NAMES)
    ref = rng.randint(1000, 9999)
    q = (f'"{sender}" shares a link (doc ref #{ref}) to {doc} that requires you to "sign in with your work '
         f'email and password" on a page hosted on {host} before you can view it. What is actually happening?')
    correct = "The login form is a fake page designed only to capture your email and password"
    return _mk(rng, "Credential Harvesting", q, correct, [
        "The document is protected for legitimate privacy reasons",
        "This is standard for all shared documents",
        "It only matters if you reuse the same password elsewhere",
    ], "Fake 'sign in to view' pages exist purely to capture credentials. Reusing the same "
       "password elsewhere is what turns one leaked login into access to many other accounts.")


def g_investment(rng, tier):
    source = rng.choice(SC_BROKERS)
    pct = rng.choice([12, 15, 20, 25, 30, 40])
    window = rng.choice(["monthly", "weekly", "in 10 days"])
    minimum = rng.randint(3, 150) * 1000
    members = rng.randint(200, 9000)
    q = (f'{source.capitalize()} ({members:,} members) asks for a minimum ₹{minimum:,} deposit and promises '
         f'guaranteed {pct}% {window} returns on a "pre-IPO" investment, showing screenshots of other members\' '
         f'profits. What is the strongest warning sign?')
    correct = "A 'guaranteed' high fixed return — genuine investments always carry risk and no fixed guarantee"
    return _mk(rng, "Investment Scam", q, correct, [
        "The group has many active members",
        "The screenshots look professionally made",
        "It focuses on pre-IPO companies",
    ], "No legitimate investment can guarantee fixed high returns — markets carry risk by "
       "definition. Guaranteed-return promises are one of the most consistent signals of an investment scam.")


def g_multistage(rng, tier):
    days = rng.choice([3, 5, 7, 10, 14, 21])
    mentor = rng.choice(["trading mentor", "crypto guru", "forex expert", "'senior analyst'", "portfolio coach"])
    app = rng.choice(["a special trading app", "a 'partner exchange' website", "a private investment portal", "an exclusive members-only platform"])
    seed_profit = rng.randint(500, 9000)
    platform = rng.choice(SC_PLATFORMS)
    q = (f'Over {days} days on {platform}, a new online contact builds rapport, then mentions a "{mentor}," '
         f'then shows a real ₹{seed_profit} profit on a small trade to build trust, then asks you to move '
         f'larger funds to {app}. What is this multi-stage pattern designed to do?')
    correct = "Slowly build trust before introducing the actual financial ask, making the final request feel earned"
    return _mk(rng, "Multi-Stage Social Engineering", q, correct, [
        "Test your knowledge of trading before offering real advice",
        "Standard onboarding for legitimate trading platforms",
        "A random coincidence with no coordinated goal",
    ], "Multi-stage scams (often called 'pig butchering' scams) deliberately spread the "
       "manipulation over days or weeks so the final financial request doesn't feel sudden or risky.")


def g_deepfake(rng, tier):
    relation = rng.choice(SC_RELATIONS)
    reason = rng.choice(SC_REASONS)
    amt = rng.randint(10, 80) * 1000
    q = (f'You receive a video call that looks and sounds exactly like {relation}, asking you to urgently '
         f'transfer ₹{amt:,} for {reason}, but the call keeps freezing at odd moments and cuts off '
         f'before you can ask a personal verification question. What should you do?')
    correct = "Hang up and call the relative back directly on their known number before sending anything"
    return _mk(rng, "Deepfake Scam", q, correct, [
        "Trust it since the face and voice matched",
        "Ask them to repeat themselves on the same call",
        "Transfer a smaller amount to be safe",
    ], "Real-time deepfake audio/video can convincingly mimic appearance and voice but often "
       "glitches under unexpected questions. A callback on an independently known number defeats "
       "the scam because the attacker cannot intercept it.")


def g_romance(rng, tier):
    platform = rng.choice(SC_PLATFORMS + ["a dating app"])
    weeks = rng.choice([2, 3, 4, 6, 8])
    amt = rng.randint(15, 60) * 1000
    excuse = rng.choice(["a customs fee to fly and meet you", "a hospital bill after an accident", "releasing a 'seized' gift package"])
    q = (f'An online partner on {platform} you have never met in person, after {weeks} weeks of daily messages, '
         f'says they need ₹{amt:,} for {excuse}, promising to repay double. What pattern is this?')
    correct = "A romance scam — emotional investment is used to justify an urgent money request"
    return _mk(rng, "Romance Scam", q, correct, [
        "A genuine emergency that should be trusted given the relationship",
        "A normal travel delay unrelated to money",
        "Proof that the relationship is serious",
    ], "Romance scams invest weeks in emotional connection specifically so a later money "
       "request feels like helping someone you care about, rather than a stranger's demand.")


SC_GENERATORS = {
    "Phishing": g_phishing, "OTP Scam": g_otp, "Suspicious Link": g_suspicious_link,
    "Fake Prize": g_fake_prize, "Impersonation": g_impersonation, "Fake Support": g_fake_support,
    "Delivery Scam": g_delivery, "Fake Bank Message": g_fake_bank_msg, "UPI Scam": g_upi,
    "QR Scam": g_qr, "Job Scam": g_job, "Social Media Impersonation": g_social_impersonation,
    "Advanced Phishing": g_advanced_phishing, "URL Manipulation": g_url_manipulation,
    "Domain Spoofing": g_domain_spoofing, "Social Engineering": g_social_engineering,
    "Fake Support Interaction": g_fake_support_interaction, "Marketplace Scam": g_marketplace,
    "Account Takeover": g_account_takeover, "Business Email Compromise": g_bec,
    "Credential Harvesting": g_credential_harvesting, "Investment Scam": g_investment,
    "Multi-Stage Social Engineering": g_multistage, "Deepfake Scam": g_deepfake,
    "Romance Scam": g_romance,
}

SC_TIER_CATEGORIES = {
    1: ["Phishing", "OTP Scam", "Suspicious Link", "Fake Prize", "Impersonation", "Fake Support"],
    2: ["Delivery Scam", "Fake Bank Message", "UPI Scam", "QR Scam", "Job Scam", "Social Media Impersonation"],
    3: ["Advanced Phishing", "URL Manipulation", "Domain Spoofing", "Social Engineering",
        "Fake Support Interaction", "Marketplace Scam"],
    4: ["Account Takeover", "Business Email Compromise", "Credential Harvesting", "Investment Scam",
        "Multi-Stage Social Engineering", "Deepfake Scam", "Romance Scam"],
}
SC_TIER_CATEGORIES[5] = SC_TIER_CATEGORIES[3] + SC_TIER_CATEGORIES[4]
SC_TIER_CATEGORIES[6] = SC_TIER_CATEGORIES[4] + ["Advanced Phishing", "Domain Spoofing", "Social Engineering"]
SC_TIER_CATEGORIES[7] = SC_TIER_CATEGORIES[4] + ["Multi-Stage Social Engineering", "Deepfake Scam", "Business Email Compromise"]


def sc_tier_for_level(level):
    if level <= 10:
        return 1
    if level <= 20:
        return 2
    if level <= 40:
        return 3
    if level <= 60:
        return 4
    if level <= 80:
        return 5
    if level <= 90:
        return 6
    return 7


# Max points per question (was 1000, now 2000 -> 20,000 max per level)
SC_MAX_POINTS = 2000


@st.cache_data(show_spinner=False)
def sc_build_bank():
    bank = {}
    for level in range(1, 101):
        tier = sc_tier_for_level(level)
        cats = SC_TIER_CATEGORIES[tier]
        offset = (level * 3) % len(cats)
        questions = []
        for qi in range(10):
            category = cats[(qi + offset) % len(cats)]
            rng = random.Random(level * 1000 + qi * 7 + 13)
            qd = SC_GENERATORS[category](rng, tier)
            qd["id"] = f"L{level}Q{qi+1}"
            qd["level"] = level
            qd["difficulty"] = tier
            qd["maxPoints"] = SC_MAX_POINTS
            questions.append(qd)
        bank[level] = questions
    return bank


def sc_compute_points(correct, elapsed):
    if not correct:
        return 0
    t = max(0.0, elapsed)
    raw = SC_MAX_POINTS * math.exp(-t / 18.0)
    floor_pts = int(SC_MAX_POINTS * 0.08)  # 160 at 2000 max
    return int(max(floor_pts, min(SC_MAX_POINTS, round(raw))))


# ------------------------ SC-LOGIC-END -------------------------

# ------------------------ SC-UI-START ---------------------------
# ---------------- Scam Challenge — UI / state helpers ----------------
def sc_start_level(level):
    """Server-side guarded entry point — never trust a button existing as the only gate."""
    if level < 1 or level > 100:
        return
    if level > st.session_state.sc_highest_unlocked:
        st.warning("That level is still locked. Complete the earlier levels first.")
        return
    st.session_state.sc_playing_level = level
    st.session_state.sc_q_idx = 0
    st.session_state.sc_answered = False
    st.session_state.sc_selected_idx = None
    st.session_state.sc_level_correct = 0
    st.session_state.sc_level_incorrect = 0
    st.session_state.sc_level_times = []
    st.session_state.sc_level_points = 0
    st.session_state.sc_q_start = time.time()
    st.session_state.sc_view = "play"


def sc_progress_pct():
    return round(((st.session_state.sc_highest_unlocked - 1) / 100) * 100)


def render_sc_dashboard():
    rank = sc_rank_for_level(st.session_state.sc_highest_unlocked)
    pct = sc_progress_pct()
    completed_n = len(st.session_state.sc_completed_levels)
    lvl_label = str(min(st.session_state.sc_highest_unlocked, 100))
    # NOTE: the whole card is rendered in ONE st.markdown call. Splitting an
    # opening <div> and its closing </div> across separate st.markdown calls
    # does not nest them in Streamlit — each call is its own isolated DOM
    # node, so the browser auto-closes the stray tag and you get an empty
    # styled box with the real content floating outside it underneath.
    st.markdown(
        '<div class="sc-dash">'
        '<div class="sc-tagline">THINK FAST. SPOT THE SCAM. STAY SATARK.</div>'
        '<div class="sc-row">'
        '<div class="sc-dash-badge">' + sc_badge_html(rank, "lg") + '</div>'
        '<div class="sc-dash-rankinfo">'
        '<div class="sc-ranknum">RANK ' + rank["roman"] + '</div>'
        '<div class="sc-rankname">' + rank["name"] + '</div>'
        '<div class="sc-progresswrap">'
        '<div class="sc-progresslabel"><span>LEVEL ' + lvl_label + ' / 100</span><span>' + str(pct) + '%</span></div>'
        '<div class="sc-bar"><div style="width:' + str(pct) + '%"></div></div>'
        '</div>'
        '</div>'
        '</div>'
        '<div class="sc-stats">'
        '<div class="sc-stat"><div class="sc-stat-v">' + f'{st.session_state.sc_total_score:,}' + '</div><div class="sc-stat-l">Total Score</div></div>'
        '<div class="sc-stat"><div class="sc-stat-v">' + str(completed_n) + '</div><div class="sc-stat-l">Completed</div></div>'
        '<div class="sc-stat"><div class="sc-stat-v">' + str(100 - completed_n) + '</div><div class="sc-stat-l">Remaining</div></div>'
        '</div>'
        '</div>',
        unsafe_allow_html=True
    )
    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        if st.session_state.sc_highest_unlocked > 100:
            label = "🏆 Replay Level Map"
        else:
            label = f"Continue Challenge → Level {st.session_state.sc_highest_unlocked}"
        if st.button(label, key="sc_continue", type="primary", use_container_width=True):
            sc_start_level(min(st.session_state.sc_highest_unlocked, 100))
            st.rerun()
    with c2:
        if st.button("🗺️ View Level Map", key="sc_view_map", use_container_width=True):
            st.session_state.sc_view = "levelmap"
            st.rerun()


def render_sc_levelmap():
    if st.button("← Back to Dashboard", key="sc_map_back"):
        st.session_state.sc_view = "dashboard"
        st.rerun()
    for rank in SC_RANKS:
        completed_in_block = sum(
            1 for lv in range(rank["lo"], rank["hi"] + 1)
            if lv in st.session_state.sc_completed_levels
        )
        perfect_in_block = sum(
            1 for lv in range(rank["lo"], rank["hi"] + 1)
            if lv in st.session_state.sc_perfect_levels
        )
        st.markdown(
            '<div class="sc-rankblock">'
            '<div class="sc-rankblock-head">'
            + sc_badge_html(rank, "sm") +
            '<div>'
            '<div class="sc-rankblock-title">RANK ' + rank["roman"] + ' • ' + rank["name"] + '</div>'
            '<div class="sc-rankblock-sub">LEVELS ' + str(rank["lo"]) + '–' + str(rank["hi"]) + ' • '
            + str(completed_in_block) + '/10 COMPLETE • ' + str(perfect_in_block)
            + '/10 PERFECT (needed to rank up)</div>'
            '</div>'
            '</div>'
            '</div>',
            unsafe_allow_html=True
        )
        levels = list(range(rank["lo"], rank["hi"] + 1))
        for row_start in (0, 5):
            cols = st.columns(5)
            for i, lv in enumerate(levels[row_start:row_start + 5]):
                with cols[i]:
                    if lv in st.session_state.sc_completed_levels:
                        mark = "★" if lv in st.session_state.sc_perfect_levels else "✓"
                        if st.button(f"{mark} {lv:02d}", key=f"sc_lvl_{lv}", use_container_width=True):
                            sc_start_level(lv)
                            st.rerun()
                    elif lv == st.session_state.sc_highest_unlocked:
                        if st.button(f"▶ {lv:02d}", key=f"sc_lvl_{lv}", type="primary", use_container_width=True):
                            sc_start_level(lv)
                            st.rerun()
                    elif lv <= st.session_state.sc_highest_unlocked:
                        if st.button(f"{lv:02d}", key=f"sc_lvl_{lv}", use_container_width=True):
                            sc_start_level(lv)
                            st.rerun()
                    else:
                        st.markdown(
                            '<div class="sc-cell sc-cell-locked">🔒<br>' + f'{lv:02d}' + '</div>',
                            unsafe_allow_html=True
                        )


def render_sc_play():
    level = st.session_state.sc_playing_level
    bank = sc_build_bank()
    questions = bank[level]
    qi = st.session_state.sc_q_idx
    q = questions[qi]
    rank = sc_rank_for_level(level)

    top_l, top_r = st.columns([1, 5])
    with top_l:
        if st.button("← Exit", key="sc_play_exit"):
            st.session_state.sc_playing_level = None
            st.session_state.sc_view = "levelmap"
            st.rerun()

    acc_txt = f"{st.session_state.sc_level_correct}/{qi + (1 if st.session_state.sc_answered else 0)}"
    st.markdown(
        '<div class="sc-hud">'
        '<div class="sc-hud-item"><div class="sc-hud-v">' + f'{level:02d}' + '</div><div class="sc-hud-l">Level</div></div>'
        '<div class="sc-hud-item"><div class="sc-hud-v">' + f'{qi+1}/10' + '</div><div class="sc-hud-l">Question</div></div>'
        '<div class="sc-hud-item"><div class="sc-hud-v">' + f'{st.session_state.sc_level_points:,}' + '</div><div class="sc-hud-l">Score</div></div>'
        '<div class="sc-hud-item"><div class="sc-hud-v">' + acc_txt + '</div><div class="sc-hud-l">Accuracy</div></div>'
        '<div class="sc-hud-item"><div class="sc-hud-v">' + rank["roman"] + '</div><div class="sc-hud-l">Rank</div></div>'
        '</div>',
        unsafe_allow_html=True
    )
    st.markdown(
        '<div class="sc-qcard">'
        '<div class="sc-qcat">' + q["category"] + '</div>'
        '<div class="sc-qtext">' + q["question"] + '</div>'
        '</div>',
        unsafe_allow_html=True
    )
    if not st.session_state.sc_answered:
        cols = st.columns(2)
        for idx, opt in enumerate(q["options"]):
            with cols[idx % 2]:
                if st.button(opt, key=f"sc_opt_{level}_{qi}_{idx}", use_container_width=True):
                    elapsed = time.time() - (st.session_state.sc_q_start or time.time())
                    correct = (idx == q["answer"])
                    points = sc_compute_points(correct, elapsed)
                    st.session_state.sc_selected_idx = idx
                    st.session_state.sc_answered = True
                    st.session_state.sc_last_points = points
                    st.session_state.sc_last_correct = correct
                    st.session_state.sc_last_elapsed = elapsed
                    st.session_state.sc_level_points += points
                    st.session_state.sc_level_times.append(elapsed)
                    if correct:
                        st.session_state.sc_level_correct += 1
                    else:
                        st.session_state.sc_level_incorrect += 1
                    st.rerun()
    else:
        correct = st.session_state.sc_last_correct
        pts = st.session_state.sc_last_points
        elapsed = st.session_state.sc_last_elapsed
        if correct:
            st.markdown(
                '<div class="sc-feedback sc-feedback-correct">✓ CORRECT — answered in ' + f'{elapsed:.1f}s'
                + '<div class="sc-feedback-pts">+' + str(pts) + ' POINTS</div></div>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                '<div class="sc-feedback sc-feedback-wrong">✕ INCORRECT<div class="sc-feedback-pts">0 POINTS</div></div>',
                unsafe_allow_html=True
            )
        st.markdown(
            '<div class="sc-explain"><strong>Correct answer:</strong> ' + q["options"][q["answer"]] + '<br><br>'
            '<strong>Why:</strong> ' + q["explanation"] + '</div>',
            unsafe_allow_html=True
        )
        is_last = (qi == 9)
        btn_label = "Finish Level →" if is_last else "Next Question →"
        if st.button(btn_label, key=f"sc_next_{level}_{qi}", type="primary", use_container_width=True):
            if is_last:
                sc_finish_level(level)
            else:
                st.session_state.sc_q_idx += 1
                st.session_state.sc_answered = False
                st.session_state.sc_selected_idx = None
                st.session_state.sc_q_start = time.time()
            st.rerun()


def sc_rank_levels_all_perfect(rank):
    """True only if every one of the rank's 10 levels has been aced (10/10) at least once."""
    return all(
        lv in st.session_state.sc_perfect_levels
        for lv in range(rank["lo"], rank["hi"] + 1)
    )


def sc_finish_level(level):
    n = 10
    correct_n = st.session_state.sc_level_correct
    avg_time = (
        sum(st.session_state.sc_level_times) / len(st.session_state.sc_level_times)
        if st.session_state.sc_level_times else 0
    )
    score = st.session_state.sc_level_points

    # Best score / best correct-count ever achieved on this level (replays count).
    prev_best = st.session_state.sc_level_scores.get(level, 0)
    st.session_state.sc_level_scores[level] = max(prev_best, score)
    prev_best_correct = st.session_state.sc_level_best_correct.get(level, 0)
    best_correct = max(prev_best_correct, correct_n)
    st.session_state.sc_level_best_correct[level] = best_correct
    if best_correct >= n:
        st.session_state.sc_perfect_levels.add(level)

    st.session_state.sc_level_stats[level] = {
        "correct": correct_n, "incorrect": n - correct_n,
        "avg_time": avg_time, "score": score,
    }
    # A level is "completed" (shows a checkmark, replayable) once finished at all,
    # regardless of score.
    st.session_state.sc_completed_levels.add(level)
    st.session_state.sc_total_score = sum(st.session_state.sc_level_scores.values())

    passed = correct_n >= (n // 2)  # need >=50% correct to advance
    rankup_target = None

    # Only the level currently at the frontier can push progress forward —
    # replaying an already-cleared earlier level never unlocks anything new,
    # it only banks a better score / moves it toward "perfect".
    if passed and level == st.session_state.sc_highest_unlocked and level < 100:
        rank = sc_rank_for_level(level)
        is_rank_boundary = (level == rank["hi"])
        if is_rank_boundary:
            # Crossing into a new rank/badge requires every level in the
            # current rank to have been aced (10/10) at some point.
            if sc_rank_levels_all_perfect(rank):
                st.session_state.sc_highest_unlocked = level + 1
                rankup_target = sc_rank_for_level(level + 1)
            # else: level itself still "passes" (unlocked/replayable), but
            # the next level and the badge stay locked until it's perfected.
        else:
            st.session_state.sc_highest_unlocked = level + 1

    st.session_state.sc_last_level_result = {
        "level": level, "score": score, "correct": correct_n,
        "incorrect": n - correct_n, "avg_time": avg_time,
        "is_legend": (level == 100),
        "passed": passed,
    }
    if rankup_target:
        st.session_state.sc_pending_rankup = rankup_target
        st.session_state.sc_view = "rankup"
    else:
        st.session_state.sc_view = "results"


def render_sc_rankup():
    rank = st.session_state.sc_pending_rankup
    st.markdown(
        '<div class="sc-rankup-wrap">'
        '<div class="sc-rankup-label">RANK UP</div>'
        + sc_badge_html(rank, "lg") +
        '<div class="sc-ranknum" style="margin-top:14px">RANK ' + rank["roman"] + '</div>'
        '<div class="sc-rankname">' + rank["name"] + '</div>'
        '<div class="sc-rankup-newbadge">✦ NEW BADGE UNLOCKED ✦</div>'
        '</div>',
        unsafe_allow_html=True
    )
    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
    if st.button("Continue →", key="sc_rankup_continue", type="primary", use_container_width=True):
        st.session_state.sc_pending_rankup = None
        st.session_state.sc_view = "results"
        st.rerun()


def render_sc_results():
    r = st.session_state.sc_last_level_result
    level = r["level"]
    accuracy = f'{r["correct"]}/10'
    if r["is_legend"]:
        header = ('<div class="sc-results-level">FINAL CHALLENGE COMPLETE</div>'
                   '<div class="sc-results-title">🏆 SATARK LEGEND</div>')
    else:
        header = ('<div class="sc-results-level">LEVEL ' + f'{level:02d}' + ' COMPLETE</div>'
                   '<div class="sc-results-title">Great work!</div>')
    unlock_html = ""
    if level < 100:
        nxt = level + 1
        rank = sc_rank_for_level(level)
        is_boundary = (level == rank["hi"])
        if nxt <= st.session_state.sc_highest_unlocked:
            msg, color = f"Level {nxt:02d} unlocked!", "#a4f5c4"
        elif not r["passed"]:
            msg, color = "Score at least 5/10 to unlock the next level — try again!", "#ffb3b3"
        elif is_boundary:
            missing = [lv for lv in range(rank["lo"], rank["hi"] + 1)
                       if lv not in st.session_state.sc_perfect_levels]
            missing_txt = ", ".join(f"{lv:02d}" for lv in missing)
            msg = (f"Rank up locked — get a perfect 10/10 on level(s) {missing_txt} "
                   f"to unlock Level {nxt:02d} and the next badge.")
            color = "#ffbe4d"
        else:
            msg, color = f"Level {nxt:02d} status unchanged.", "#a7aabb"
        unlock_html = "<p style='margin-top:16px;color:" + color + ";font-weight:700'>" + msg + "</p>"
    st.markdown(
        header +
        '<div class="sc-results">'
        '<div class="sc-bigscore">' + f'{r["score"]:,}' + ' / ' + f'{SC_MAX_POINTS*10:,}' + '</div>'
        '<div class="sc-stats" style="margin-top:20px">'
        '<div class="sc-stat"><div class="sc-stat-v">' + accuracy + '</div><div class="sc-stat-l">Accuracy</div></div>'
        '<div class="sc-stat"><div class="sc-stat-v">' + f'{r["avg_time"]:.1f}s' + '</div><div class="sc-stat-l">Avg Response</div></div>'
        '<div class="sc-stat"><div class="sc-stat-v">' + str(r["incorrect"]) + '</div><div class="sc-stat-l">Missed</div></div>'
        '</div>'
        + unlock_html +
        '</div>',
        unsafe_allow_html=True
    )
    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🗺️ Level Map", key="sc_res_map", use_container_width=True):
            st.session_state.sc_view = "levelmap"
            st.rerun()
    with c2:
        next_unlocked = level < 100 and (level + 1) <= st.session_state.sc_highest_unlocked
        if next_unlocked:
            btn_label, target = "Next Level →", level + 1
        else:
            btn_label, target = "🔁 Retry Level", level
        if level < 100 and st.button(btn_label, key="sc_res_next", type="primary", use_container_width=True):
            sc_start_level(target)
            st.rerun()


def sc_live_points():
    """Total points banked from completed levels, plus whatever has been
    earned so far in the level currently being played (updates the moment
    each question is answered correctly, before the level is finished)."""
    live = st.session_state.sc_total_score
    if st.session_state.sc_view == "play":
        live += st.session_state.sc_level_points
    return live


def render_scam_challenge():
    points = sc_live_points()
    st.markdown(
        '<div class="sc-header-row">'
        '<div>'
        '<div class="section-title">🎯 Scam Challenge</div>'
        '<div class="section-copy">A 100-level cybersecurity game. Spot the scam, beat the clock, rank up.</div>'
        '</div>'
        '<div class="sc-points-badge">'
        '<div class="sc-points-icon">✦</div>'
        '<div class="sc-points-text"><div class="sc-points-v">' + f'{points:,}' + '</div><div class="sc-points-l">Points</div></div>'
        '</div>'
        '</div>',
        unsafe_allow_html=True
    )
    view = st.session_state.sc_view
    if view == "levelmap":
        render_sc_levelmap()
    elif view == "play":
        render_sc_play()
    elif view == "rankup":
        render_sc_rankup()
    elif view == "results":
        render_sc_results()
    else:
        render_sc_dashboard()


# ------------------------- SC-UI-END ------------------------------

SC_DEFAULTS = {
    "sc_view": "dashboard",
    "sc_highest_unlocked": 1,
    "sc_completed_levels": set(),
    "sc_level_best_correct": {},
    "sc_perfect_levels": set(),
    "sc_level_scores": {},
    "sc_level_stats": {},
    "sc_total_score": 0,
    "sc_playing_level": None,
    "sc_q_idx": 0,
    "sc_q_start": None,
    "sc_answered": False,
    "sc_selected_idx": None,
    "sc_level_correct": 0,
    "sc_level_incorrect": 0,
    "sc_level_times": [],
    "sc_level_points": 0,
    "sc_last_points": 0,
    "sc_last_correct": None,
    "sc_last_elapsed": 0.0,
    "sc_pending_rankup": None,
    "sc_last_level_result": None,
}


def sc_init_state():
    for k, v in SC_DEFAULTS.items():
        if k not in st.session_state:
            st.session_state[k] = v


# ----------------------- Session state -------------------------
