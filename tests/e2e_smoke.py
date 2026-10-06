"""Browser smoke and layout regression checks for the local Streamlit app."""
from pathlib import Path
import os
from playwright.sync_api import sync_playwright

URL=os.getenv("SATARK_E2E_URL","http://127.0.0.1:8501")
ARTIFACTS=Path(os.getenv("SATARK_E2E_ARTIFACTS","artifacts"))
ARTIFACTS.mkdir(parents=True,exist_ok=True)


def assert_layout(page, name):
    page.wait_for_timeout(1500)
    body=page.locator("body").inner_text()
    assert "Pause. Investigate. Then act." in body, f"{name}: home copy missing"
    metrics=page.evaluate("""() => ({
        viewport: window.innerWidth,
        scrollWidth: document.documentElement.scrollWidth,
        key: [...document.querySelectorAll('.hero,.home-grid,.st-key-home-actions,.home-how-title')].map(el => {
            const r=el.getBoundingClientRect();
            return {left:r.left,right:r.right,top:r.top,bottom:r.bottom,width:r.width,height:r.height};
        }),
        radar: [...document.querySelectorAll('iframe[aria-hidden="true"]')].map(el => ({
            position:getComputedStyle(el).position,
            zIndex:getComputedStyle(el).zIndex,
            pointerEvents:getComputedStyle(el).pointerEvents,
        }))
    })""")
    assert metrics["scrollWidth"] <= metrics["viewport"] + 2, f"{name}: horizontal overflow {metrics}"
    for rect in metrics["key"]:
        assert rect["left"] >= -2, f"{name}: element extends left of viewport: {rect}"
        assert rect["right"] <= metrics["viewport"] + 2, f"{name}: element extends right of viewport: {rect}"
    for radar in metrics["radar"]:
        assert radar["position"] == "fixed", f"{name}: radar iframe is not fixed"
        assert radar["pointerEvents"] == "none", f"{name}: radar intercepts pointer events"
    page.screenshot(path=str(ARTIFACTS / f"{name}.png"),full_page=True)


def main():
    with sync_playwright() as p:
        browser=p.chromium.launch()
        for name,width,height in (("desktop",1440,900),("mobile",390,844)):
            page=browser.new_page(viewport={"width":width,"height":height},reduced_motion="reduce")
            page.goto(URL,wait_until="domcontentloaded",timeout=60_000)
            assert_layout(page,name)
            if name=="desktop":
                page.get_by_role("button",name="Start an investigation →").click()
                page.get_by_text("What do you want to check?").wait_for(timeout=30_000)
            page.close()
        browser.close()

if __name__=="__main__":
    main()
