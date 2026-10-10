"""PDF report rendering for SATARK."""

import html
import math
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from satark_utils import OFFICIAL_VERIFICATION_SOURCES, check_class
from review_engine import build_evidence_review

from datetime import datetime
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")
THREAT_CHECKS = [
    "Scam Indicators", "Phishing Signs", "Deepfake Risk", "Fake Information",
    "Suspicious Links", "Impersonation", "Malware Indicators", "Social Engineering",
]


def now_ist():
    return datetime.now(IST)


def clamp_score(value):
    try:
        return max(0, min(100, int(float(value))))
    except (TypeError, ValueError, OverflowError):
        return 50


def risk_label(score, category=""):
    score = clamp_score(score)
    if _safe_text(category).lower() == "scam":
        return "SCAM", "critical"
    if score < 35:
        return "LOWER SIGNAL", "safe"
    if score < 70:
        return "CAUTION", "caution"
    return "CRITICAL THREAT", "critical"


def build_final_conclusion(result):
    existing = _safe_text(result.get("final_conclusion", ""))
    if existing:
        return existing
    label, _ = risk_label(result.get("risk_score", 50), result.get("threat_category", ""))
    summary = _safe_text(result.get("summary", ""))
    verdict = _safe_text(result.get("verdict", "Manual review recommended."))
    if summary:
        return f"SATARK assessed this item as {label.lower()} based on the evidence identified during analysis. {summary} {verdict} Verify the source independently before taking any high-impact action."
    return f"SATARK assessed this item as {label.lower()}. {verdict} Verify the source independently before taking any high-impact action."
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle


def _safe_text(value, default=""):
    if value is None:
        return default
    return str(value).strip()


def pdf_escape(text):
    return html.escape(_safe_text(text)).replace("\n", "<br/>")


def make_pdf_report(result, mode):
    """Create a polished, readable PDF version of the complete SATARK report."""
    if not isinstance(result, dict):
        result = {}
    result = dict(result)
    result.setdefault("analysis_mode", mode)
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4, rightMargin=15*mm, leftMargin=15*mm,
        topMargin=15*mm, bottomMargin=15*mm, title="SATARK Security Report"
    )
    styles = getSampleStyleSheet()
    dark = colors.HexColor("#111113")
    muted = colors.HexColor("#5f6270")
    light_gold = colors.HexColor("#eaf7fc")
    line = colors.HexColor("#d9d9e2")
    green = colors.HexColor("#147d64")
    red = colors.HexColor("#b42345")
    amber = colors.HexColor("#8a5a00")

    title = ParagraphStyle("SATARKTitle", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=22, leading=26, textColor=dark, spaceAfter=5)
    subtitle = ParagraphStyle("SATARKSubtitle", parent=styles["Normal"], fontName="Helvetica", fontSize=9, leading=13, textColor=muted, spaceAfter=12)
    h2 = ParagraphStyle("SATARKH2", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=13, leading=16, textColor=dark, spaceBefore=12, spaceAfter=8)
    body = ParagraphStyle("SATARKBody", parent=styles["BodyText"], fontName="Helvetica", fontSize=9.5, leading=14, textColor=dark, spaceAfter=6)
    small = ParagraphStyle("SATARKSmall", parent=body, fontSize=8, leading=11, textColor=muted)
    verdict_style = ParagraphStyle("SATARKVerdict", parent=body, fontName="Helvetica-Bold", fontSize=10, leading=15, textColor=dark)
    centered = ParagraphStyle("SATARKCentered", parent=body, alignment=TA_CENTER, fontSize=8, textColor=muted)

    score=clamp_score(result.get("risk_score",50)); label,_=risk_label(score,result.get("threat_category",""))
    try:
        confidence_value = float(result.get("confidence", 70.0))
        if not math.isfinite(confidence_value):
            confidence_value = 0.0
    except (TypeError, ValueError, OverflowError):
        confidence_value = 0.0
    confidence_value = max(0.0, min(100.0, confidence_value))
    confidence_color = green if confidence_value >= 85 else (amber if confidence_value >= 50 else red)
    story=[]
    story.append(Paragraph("SATARK", title))
    story.append(Paragraph("Evidence-first digital threat investigation · AI-assisted advisory", subtitle))
    conf_cell_style = ParagraphStyle("SATARKConfCell", parent=body, textColor=confidence_color, fontName="Helvetica-Bold")
    meta=[[Paragraph("Scanner", body), Paragraph(pdf_escape(mode), body), Paragraph("Generated", body), Paragraph(now_ist().strftime('%d %b %Y, %I:%M %p') + ' IST', body)],
          [Paragraph("Assessment signal", body), Paragraph(pdf_escape(label), body), Paragraph("Risk score", body), Paragraph(f"{score}/100", body)],
          [Paragraph("Pattern", body), Paragraph(pdf_escape(result.get('scam_pattern','Needs review')), body), Paragraph("Model-reported confidence", body), Paragraph(f"{confidence_value:.2f}%", conf_cell_style)]]
    meta_table=Table(meta,colWidths=[25*mm,60*mm,30*mm,60*mm],hAlign='LEFT')
    meta_table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),colors.HexColor('#f2f8fc')),('BOX',(0,0),(-1,-1),0.7,line),('INNERGRID',(0,0),(-1,-1),0.4,line),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7)]))
    story.append(meta_table)

    story.append(Paragraph("Final Verdict", h2))
    verdict_data=[[Paragraph(pdf_escape(result.get('verdict','Manual review recommended.')), verdict_style)]]
    vt=Table(verdict_data,colWidths=[175*mm])
    vt.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),light_gold),('BOX',(0,0),(-1,-1),0.7,colors.HexColor('#9bc9dc')),('LEFTPADDING',(0,0),(-1,-1),10),('RIGHTPADDING',(0,0),(-1,-1),10),('TOPPADDING',(0,0),(-1,-1),10),('BOTTOMPADDING',(0,0),(-1,-1),10)]))
    story.append(vt)

    story.append(Paragraph("What SATARK Found", h2))
    story.append(Paragraph(pdf_escape(result.get('summary','No summary was returned.')), body))

    # Explain the workflow that actually ran. This is a static record of the
    # successful report path, not a fabricated real-time progress indicator.
    mode_normalized = _safe_text(result.get("analysis_mode", mode)).lower()
    visual_only = mode_normalized in {"image", "qr"}
    local_evidence = result.get("deterministic_evidence", [])
    if not isinstance(local_evidence, (list, tuple)):
        local_evidence = []
    local_evidence = [
        item for item in local_evidence
        if isinstance(item, dict)
        and any(_safe_text(item.get(field)) for field in ("title", "observation", "evidence"))
    ]
    workflow_rows = [
        [Paragraph("<b>Stage</b>", body), Paragraph("<b>Recorded outcome</b>", body)],
        [Paragraph("Input preparation", body), Paragraph("Completed — input passed preparation and an assessment was returned.", body)],
        [
            Paragraph("Local evidence rules", body),
            Paragraph(
                "Not run for this visual workflow; image findings are handled separately."
                if visual_only else
                f"Completed — {len(local_evidence)} local text observation(s) extracted. No signal is not a safety clearance.",
                body,
            ),
        ],
        [Paragraph("AI interpretation", body), Paragraph("Completed — the configured model returned an assessment.", body)],
        [Paragraph("Evidence coverage review", body), Paragraph("Included below. It checks broad coverage, not every generated claim.", body)],
    ]
    workflow_table = Table(workflow_rows, colWidths=[48*mm, 127*mm], repeatRows=1)
    workflow_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#dff3fa")),
        ("GRID", (0,0), (-1,-1), 0.5, line),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("LEFTPADDING", (0,0), (-1,-1), 7),
        ("RIGHTPADDING", (0,0), (-1,-1), 7),
        ("TOPPADDING", (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
    ]))
    story.append(Paragraph("Investigation Workflow", h2))
    story.append(workflow_table)

    story.append(Paragraph("Evidence Detected", h2))
    evidence = result.get("key_indicators", [])
    if not isinstance(evidence, (list, tuple)):
        evidence = [evidence] if evidence else []
    evidence = [_safe_text(item) for item in evidence if item is not None and _safe_text(item)]
    if not evidence:
        evidence = ["No specific indicators were returned."]
    story.append(Paragraph("<br/>".join("• " + pdf_escape(x) for x in evidence), body))

    story.append(Paragraph("Rule-Based Evidence Ledger (Not a Verdict)", h2))
    ledger = result.get("deterministic_evidence", [])
    if not isinstance(ledger, (list, tuple)):
        ledger = []
    ledger = [
        item for item in ledger
        if isinstance(item, dict)
        and any(_safe_text(item.get(field)) for field in ("title", "observation", "evidence"))
    ]
    if ledger:
        ledger_lines = []
        for item in ledger[:20]:
            if not isinstance(item, dict):
                continue
            title_text = _safe_text(item.get("title"), "Observation")
            observation_text = _safe_text(item.get("observation"))
            excerpt_text = _safe_text(item.get("evidence"))
            ledger_lines.append(
                "<b>" + pdf_escape(title_text) + "</b><br/>"
                + pdf_escape(observation_text)
                + ("<br/><font color='#5f6270'>Observed text: " + pdf_escape(excerpt_text) + "</font>" if excerpt_text else "")
            )
        story.append(Paragraph("<br/><br/>".join(ledger_lines) if ledger_lines else
                               "No supported text observations were extracted. This is not proof that the content is safe.", body))
    else:
        story.append(Paragraph(
            "No supported text observations were extracted. This is not proof that the content is safe.",
            body,
        ))

    # Export the same explicit evidence-coverage boundary shown in the app.
    # This check compares local text-rule observations with the broad AI output;
    # it does not verify each generated claim.
    coverage = build_evidence_review(result)
    coverage_title = _safe_text(coverage.get("status"), "Evidence coverage needs review")
    coverage_message = _safe_text(coverage.get("message"), "Evidence coverage could not be summarized.")
    story.append(Paragraph("Evidence Coverage Review", h2))
    coverage_table = Table(
        [[Paragraph("<b>" + pdf_escape(coverage_title) + "</b><br/>" + pdf_escape(coverage_message), body)]],
        colWidths=[175*mm],
    )
    coverage_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), colors.HexColor("#eaf7fc")),
        ("BOX", (0,0), (-1,-1), 0.7, colors.HexColor("#9bc9dc")),
        ("LEFTPADDING", (0,0), (-1,-1), 10),
        ("RIGHTPADDING", (0,0), (-1,-1), 10),
        ("TOPPADDING", (0,0), (-1,-1), 9),
        ("BOTTOMPADDING", (0,0), (-1,-1), 9),
    ]))
    story.append(coverage_table)
    story.append(Paragraph(
        "Coverage is not claim verification. Local rules can miss signals and may flag benign content; independently verify important findings.",
        small,
    ))

    story.append(Paragraph("What To Do Now", h2))
    recs = result.get("recommendations", [])
    if not isinstance(recs, (list, tuple)):
        recs = [recs] if recs else []
    recs = [_safe_text(item) for item in recs if item is not None and _safe_text(item)]
    if not recs:
        recs = ["Review the content manually before acting."]
    story.append(Paragraph("<br/>".join("• " + pdf_escape(x) for x in recs), body))

    story.append(Paragraph("Threat Analysis", h2))
    threat_analysis = result.get("threat_analysis", {})
    if not isinstance(threat_analysis, dict):
        threat_analysis = {}
    threat_data=[[Paragraph('<b>Security Check</b>',body),Paragraph('<b>Result</b>',body)]]
    for check in THREAT_CHECKS:
        value=_safe_text(threat_analysis.get(check,'Needs review'),'Needs review')
        threat_data.append([Paragraph(pdf_escape(check),body),Paragraph(pdf_escape(value),body)])
    tt=Table(threat_data,colWidths=[95*mm,80*mm],repeatRows=1)
    ts=[('BACKGROUND',(0,0),(-1,0),colors.HexColor('#dff3fa')),('TEXTCOLOR',(0,0),(-1,0),dark),('GRID',(0,0),(-1,-1),0.5,line),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]
    for row_idx in range(1,len(threat_data)):
        value=_safe_text(threat_analysis.get(THREAT_CHECKS[row_idx-1],''))
        cls=check_class(value)
        text_color=green if cls=='check-detected' else red if cls=='check-clear' else amber
        ts.append(('TEXTCOLOR',(1,row_idx),(1,row_idx),text_color))
    tt.setStyle(TableStyle(ts))
    story.append(tt)
    legend_style = ParagraphStyle("SATARKLegend", parent=small, fontSize=8, leading=11, textColor=dark, spaceBefore=5)
    story.append(Paragraph(
        '<b>Status guide:</b> '
        '<font color="#188a4b"><b>Detected</b></font> — sufficient evidence that the indicator is present. '
        '<font color="#b07a00"><b>Needs review</b></font> — evidence is ambiguous or insufficient; verify it manually. '
        '<font color="#c92a4d"><b>Not detected</b></font> — no meaningful evidence of that indicator was found.',
        legend_style
    ))

    story.append(Paragraph("Official Verification Sources", h2))
    source_data=[[Paragraph('<b>Source</b>',body),Paragraph('<b>Purpose</b>',body),Paragraph('<b>Official Website</b>',body)]]
    sources = result.get("verification_sources", OFFICIAL_VERIFICATION_SOURCES)
    if not isinstance(sources, list):
        sources = OFFICIAL_VERIFICATION_SOURCES
    for item in sources:
        if not isinstance(item, dict):
            continue
        website = _safe_text(item.get("website"))
        if not website.startswith(("https://", "http://")):
            website = ""
        source_data.append([Paragraph(pdf_escape(item.get('source')),body),Paragraph(pdf_escape(item.get('purpose')),body),Paragraph(f'<link href="{html.escape(website,quote=True)}" color="#4d3dcc"><u>{pdf_escape(website)}</u></link>',body)])
    stbl=Table(source_data,colWidths=[42*mm,75*mm,58*mm],repeatRows=1)
    stbl.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e7f6f5')),('GRID',(0,0),(-1,-1),0.5,line),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]))
    story.append(stbl)

    story.append(Paragraph("Final Conclusion", h2))
    conclusion=Paragraph(pdf_escape(build_final_conclusion(result)),body)
    ct=Table([[conclusion]],colWidths=[175*mm])
    ct.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),light_gold),('BOX',(0,0),(-1,-1),0.7,colors.HexColor('#d8bb78')),('LEFTPADDING',(0,0),(-1,-1),10),('RIGHTPADDING',(0,0),(-1,-1),10),('TOPPADDING',(0,0),(-1,-1),10),('BOTTOMPADDING',(0,0),(-1,-1),10)]))
    story.append(ct)
    story.append(Spacer(1,8))
    story.append(Paragraph("SATARK is an AI-assisted advisory tool. Verify high-impact security decisions independently.", centered))

    def add_page(canvas, doc):
        canvas.saveState()
        width,height=A4
        canvas.setFillColor(colors.HexColor('#278eac'))
        canvas.rect(0,height-5*mm,width,5*mm,fill=1,stroke=0)
        canvas.setFillColor(muted)
        canvas.setFont('Helvetica',7.5)
        canvas.drawString(15*mm,8*mm,'SATARK • Smart AI Threat Analysis & Risk Knowledge')
        canvas.drawRightString(width-15*mm,8*mm,f'Page {doc.page}')
        canvas.restoreState()

    doc.build(story,onFirstPage=add_page,onLaterPages=add_page)
    return buffer.getvalue()
