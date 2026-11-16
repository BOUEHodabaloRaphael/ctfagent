import json, time
from pathlib import Path
from playwright.sync_api import sync_playwright

STATE_FILE = Path("/home/kali/ctfagent/src/tools/ctf/nctf26_storage_state.json")
BASE_URL = "https://arena.ctf.tg"

ids = [486, 453, 265, 433, 371, 372, 373, 374, 384, 385, 386, 487, 509, 522, 267, 504]

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(storage_state=str(STATE_FILE))
    page = context.new_page()
    page.goto(f"{BASE_URL}/challenges", wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(500)

    for cid in ids:
        resp = page.request.get(f"{BASE_URL}/plugins/team_instancer/status?challenge_id={cid}",
                                 headers={"Accept": "application/json"})
        try:
            d = resp.json()
        except Exception:
            d = {"raw": resp.text()[:200]}
        print(cid, d)
        time.sleep(0.3)

    browser.close()
