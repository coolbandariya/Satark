"""Browser smoke and layout regression checks for the local Streamlit app."""
from pathlib import Path
from io import BytesIO
import os
from playwright.sync_api import sync_playwright
from pypdf import PdfReader

URL=os.getenv("SATARK_E2E_URL","http://127.0.0.1:8501")
ARTIFACTS=Path(os.getenv("SATARK_E2E_ARTIFACTS","artifacts"))
ARTIFACTS.mkdir(parents=True,exist_ok=True)


def assert_layout(page, name):
    page.wait_for_timeout(3300)
    body=page.locator("body").inner_text()
    assert "Pause the panic." in body, f"{name}: home copy missing"
    assert page.locator("#satark-intro-overlay").count() == 0, f"{name}: intro overlay did not dismiss"
    metrics=page.evaluate("""() => ({
        viewport: window.innerWidth,
        scrollWidth: document.documentElement.scrollWidth,
        key: [...document.querySelectorAll('.ih-hero,.ih-capability-grid,.st-key-home-actions,.ih-method')].map(el => {
            const r=el.getBoundingClientRect();
            return {left:r.left,right:r.right,top:r.top,bottom:r.bottom,width:r.width,height:r.height};
        }),
        workflowSteps: document.querySelectorAll(".ih-method-step").length,
        scanners: document.querySelectorAll(".scanner").length
    })""")
    assert metrics["scrollWidth"] <= metrics["viewport"] + 2, f"{name}: horizontal overflow {metrics}"
    assert len(metrics["key"]) >= 3, f"{name}: primary home layout selectors were not found: {metrics}"
    assert metrics["workflowSteps"] == 4, f"{name}: onboarding workflow is incomplete"
    assert page.locator(".ih-hero h1").count() == 1, f"{name}: hero heading missing"
    assert page.locator(".ih-capability-grid article").count() >= 4, f"{name}: capability cards missing"
    for rect in metrics["key"]:
        assert rect["left"] >= -2, f"{name}: element extends left of viewport: {rect}"
        assert rect["right"] <= metrics["viewport"] + 2, f"{name}: element extends right of viewport: {rect}"
    if name == "desktop":
        assert metrics["scanners"] == 0, f"{name}: scanners unexpectedly rendered on home"
    page.screenshot(path=str(ARTIFACTS / f"{name}.png"),full_page=True)


def assert_no_overlap(page, selector, name):
    rects=page.locator(selector).evaluate_all("""els => els.map(el => { const r=el.getBoundingClientRect(); return {left:r.left,right:r.right,top:r.top,bottom:r.bottom}; })""")
    for i,left in enumerate(rects):
        for j,right in enumerate(rects):
            if j <= i:
                continue
            horizontal=max(0,min(left["right"],right["right"])-max(left["left"],right["left"]))
            vertical=max(0,min(left["bottom"],right["bottom"])-max(left["top"],right["top"]))
            assert horizontal == 0 or vertical == 0, f"{name}: {selector} elements overlap: {left} vs {right}"


def choose_workspace(page, steps_down):
    """Select a FIRSTLIGHT workspace using keyboard input to avoid flaky popover clicks."""
    workspace = page.get_by_role("combobox", name="Investigation workspace")
    workspace.click()
    for _ in range(steps_down):
        workspace.press("ArrowDown")
    workspace.press("Enter")


def main():
    with sync_playwright() as p:
        browser=p.chromium.launch()
        for name,width,height in (("desktop",1440,900),("mobile",390,844)):
            page=browser.new_page(viewport={"width":width,"height":height},reduced_motion="reduce")
            page.goto(URL,wait_until="domcontentloaded",timeout=60_000)
            page.locator("#satark-intro-overlay").wait_for(state="attached", timeout=10_000)
            assert_layout(page,name)
            if name=="desktop":
                page.get_by_role("button",name="Start an investigation →").click()
                page.get_by_text("What do you want to check?").wait_for(timeout=30_000)
                assert_no_overlap(page, ".scanner", f"{name}-scanner")
                assert_no_overlap(page, ".capability-card", f"{name}-capability-card")
                assert_no_overlap(page, ".ih-method-step", f"{name}-method-step")
                assert page.get_by_role("button",name="Select Text").is_visible()
                page.get_by_role("button",name="Select Text").click()
                page.get_by_text("Security Analysis").wait_for(timeout=30_000)
                page.get_by_text("Messages & text").wait_for(timeout=30_000)
                page.get_by_text("Ready for input").wait_for(timeout=30_000)

                # Verify that every scanner selection updates the contextual
                # workflow guidance without requiring a provider API key.
                workflow_markers = {
                    "Text": "Messages & text",
                    "URL": "Links & websites",
                    "Image": "Images & screenshots",
                    "PDF": "PDF documents",
                    "QR": "QR code images",
                    "Video": "Video & clips",
                }
                for mode, marker in workflow_markers.items():
                    page.get_by_role("button", name=f"Select {mode}").click()
                    page.get_by_text(f"SELECTED WORKFLOW · {mode.upper()}").wait_for(timeout=30_000)
                    page.get_by_text(marker).wait_for(timeout=30_000)
                # Restore Text so the following navigation/sample checks start
                # from a deterministic state.
                page.get_by_role("button", name="Select Text").click()
                page.get_by_text("SELECTED WORKFLOW · TEXT").wait_for(timeout=30_000)

                # Exercise every top-level navigation surface without requiring
                # an external provider key.
                for label, marker in (
                    ("Session history", "Analysis history"),
                    ("Investigate", "What do you want to check?"),
                    # Return to the home page last; the offline sample action
                    # is intentionally available there, not on the Analyze page.
                    ("Overview", "Pause the panic."),
                ):
                    page.locator('[data-testid="stSidebar"] button').filter(has_text=label).click()
                    page.get_by_text(marker).wait_for(timeout=30_000)

                # FIRSTLIGHT is the flagship workspace; exercise its main
                # synthetic-only investigation path without provider credentials.
                page.locator('[data-testid="stSidebar"] button').filter(has_text="FIRSTLIGHT").click()
                page.get_by_role("button", name="Load / reset synthetic incident").click()
                page.get_by_text("Synthetic case loaded").wait_for(timeout=30_000)
                choose_workspace(page, 2)
                page.get_by_role("button", name="Run investigation workflow").click()
                page.get_by_text("Coordinated investigation").wait_for(timeout=30_000)
                page.get_by_text("Findings", exact=True).wait_for(timeout=30_000)
                page.get_by_text("Evidence gaps", exact=True).wait_for(timeout=30_000)
                page.get_by_role("button", name="Export FIRSTLIGHT incident report (JSON)").wait_for(state="visible", timeout=30_000)
                with page.expect_download(timeout=30_000) as firstlight_download:
                    page.get_by_role("button", name="Export FIRSTLIGHT incident report (JSON)").click()
                firstlight_json = Path(firstlight_download.value.path()).read_text(encoding="utf-8")
                assert '"case_id": "FL-DEMO-2026-001"' in firstlight_json
                assert '"audit_chain_valid": true' in firstlight_json
                assert "Synthetic demonstration only" in firstlight_json

                # Approval remains explicitly simulated; verify the action log
                # and audit trail after one approval.
                choose_workspace(page, 1)
                page.get_by_role("button", name="Approve & simulate").first.click()
                page.get_by_text("Response action log").wait_for(timeout=30_000)
                choose_workspace(page, 1)
                page.get_by_text("Hash-chained audit trail").wait_for(timeout=30_000)
                page.get_by_text("Audit chain verifies against its first entry.").wait_for(timeout=30_000)
                page.locator('[data-testid="stSidebar"] button').filter(has_text="Overview").click()

                # The offline sample must open without a provider key and expose
                # the evidence ledger plus the deterministic coverage check.
                page.get_by_role("button",name="Open the guided sample report").click()
                page.get_by_text("Investigation workflow").wait_for(timeout=30_000)
                page.get_by_text("Evidence ledger").wait_for(timeout=30_000)
                page.get_by_text("INDEPENDENT COVERAGE CHECK").wait_for(timeout=30_000)

                # Validate the real browser download path as well as the PDF
                # generator's unit-level text extraction checks.
                with page.expect_download(timeout=30_000) as download_info:
                    page.get_by_role("button", name="Download PDF report").click()
                download = download_info.value
                downloaded_pdf = Path(download.path()).read_bytes()
                assert downloaded_pdf.startswith(b"%PDF"), "sample report download is not a PDF"
                assert len(downloaded_pdf) > 500, "sample report PDF is unexpectedly small"
                pdf_text = "\n".join(
                    pdf_page.extract_text() or ""
                    for pdf_page in PdfReader(BytesIO(downloaded_pdf)).pages
                )
                assert "Investigation Workflow" in pdf_text, "PDF is missing the investigation workflow"
                assert "Evidence Coverage Review" in pdf_text, "PDF is missing evidence coverage review"
                assert "Rule-Based Evidence Ledger" in pdf_text, "PDF is missing the evidence ledger"
                page.screenshot(path=str(ARTIFACTS / f"{name}-pages.png"),full_page=True)
            else:
                # Exercise the main scan workflow on a narrow viewport too.
                page.get_by_role("button",name="Start an investigation →").click()
                page.get_by_text("What do you want to check?").wait_for(timeout=30_000)
                page.get_by_role("button",name="Select Text").click()
                page.get_by_text("Security Analysis").wait_for(timeout=30_000)
                mobile_metrics=page.evaluate("""() => ({
                    viewport: window.innerWidth,
                    scrollWidth: document.documentElement.scrollWidth,
                    scanners: [...document.querySelectorAll(".scanner")].map(el => {
                        const r=el.getBoundingClientRect();
                        return {left:r.left,right:r.right,width:r.width};
                    })
                })""")
                assert mobile_metrics["scrollWidth"] <= mobile_metrics["viewport"] + 2, (
                    f"mobile-analysis: horizontal overflow {mobile_metrics}"
                )
                for rect in mobile_metrics["scanners"]:
                    assert rect["left"] >= -2 and rect["right"] <= mobile_metrics["viewport"] + 2, (
                        f"mobile-analysis: scanner outside viewport {rect}"
                    )
                page.screenshot(path=str(ARTIFACTS / f"{name}-analysis.png"),full_page=True)
            page.close()
        browser.close()

if __name__=="__main__":
    main()
