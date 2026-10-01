"""Step 5 checks: headless Chromium against a local http.server; screenshots to screenshots/."""
import subprocess, sys, time
from playwright.sync_api import sync_playwright

srv = subprocess.Popen([sys.executable, "-m", "http.server", "8765"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(1)
errors, ok = [], True
def check(cond, msg):
    global ok
    print(("PASS " if cond else "FAIL ") + msg); ok &= bool(cond)

def setup(page, equipment, indoor, project, fuel=None, tons=None, cost=None):
    page.select_option("#equipment", equipment); page.select_option("#indoor", indoor)
    page.check(f'input[name="project"][value="{project}"]')
    if fuel: page.select_option("#fuel", fuel)
    page.fill("#tons", "" if tons is None else str(tons)); page.fill("#cost", "" if cost is None else str(cost))

try:
    with sync_playwright() as p:
        b = p.chromium.launch()
        page = b.new_page(viewport={"width": 1280, "height": 900})
        page.on("console", lambda m: m.type == "error" and errors.append(m.text))
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto("http://localhost:8765/index.html"); page.wait_for_load_state("networkidle")
        r = page.locator("#result")

        setup(page, "vrf", "mixed", "replacement", "gas", 20, 50000)
        t = r.inner_text()
        check("Commercial VRF" in t, "1 VRF rule matched")
        check("20 tons × $2,250 = $45,000" in t, "1 math line")
        check("Capped at 75% of installed cost" in t and "$37,500" in t, "1 75% cap note ($50k cost → $37,500)")
        check("Pre-approval required" in t, "1 pre-approval badge")
        check("Showing 50 of" in t and any(k in t for k in ("REYQ", "RELQ", "RXYQ")), "1 Daikin VRV models listed")
        check(page.locator("#draft-banner").is_hidden(), "1 no DRAFT banner (all verified)")
        page.screenshot(path="screenshots/1_vrf_mixed_gas_20t.png", full_page=True)

        setup(page, "ashp", "ducted", "new")
        t = r.inner_text()
        check("No Energize CT incentive found for this combination." in t, "2 residential new construction → no incentive")
        check(page.locator("#fuel-wrap").is_hidden(), "2 Replacing hidden for new construction")
        page.screenshot(path="screenshots/2_res_ashp_new.png", full_page=True)

        setup(page, "gshp", "ducted", "replacement", "oil", 10)
        t = r.inner_text()
        check("Commercial ground source" in t and "10 tons × $4,000 = $40,000" in t, "3 GSHP commercial rule, $40,000")
        check("WSLH120" in t and "Showing 50 of" not in t, "3 GSHP 10-ton models listed (no untonned rows)")
        page.screenshot(path="screenshots/3_gshp_oil_10t.png", full_page=True)

        setup(page, "vrf", "mixed", "replacement", "heat_pump", 20)
        check("No Energize CT incentive" in r.inner_text(), "extra: commercial heat pump replacement → no incentive")
        setup(page, "wshp", "ducted", "replacement", "oil", 10)
        check("No Energize CT incentive" in r.inner_text(), "extra: WSHP → no incentive")
        setup(page, "vrf", "mixed", "replacement", "gas")
        check("Enter system size for an estimate" in r.inner_text(), "extra: no tons → prompt, program still shown")

        m = b.new_page(viewport={"width": 390, "height": 844})
        m.on("console", lambda msg: msg.type == "error" and errors.append(msg.text))
        m.goto("http://localhost:8765/index.html"); m.wait_for_load_state("networkidle")
        setup(m, "vrf", "mixed", "replacement", "gas", 20, 50000)
        sw, cw = m.evaluate("[document.documentElement.scrollWidth, document.documentElement.clientWidth]")
        fb, rt = m.locator("#form").bounding_box(), m.locator("#result").bounding_box()
        check(sw <= cw, f"4 mobile no horizontal scroll ({sw} <= {cw})")
        check(rt["y"] > fb["y"] + fb["height"] - 1, "4 mobile stacked (result below form)")
        m.screenshot(path="screenshots/4_mobile_390.png", full_page=True)
        b.close()
    check(not errors, f"5 zero console errors {errors}")
finally:
    srv.terminate()
sys.exit(0 if ok else 1)
