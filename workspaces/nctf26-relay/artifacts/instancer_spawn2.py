import sys, json, re
from pathlib import Path
from playwright.sync_api import sync_playwright

STATE_FILE = Path("/home/kali/ctfagent/src/tools/ctf/nctf26_storage_state.json")
BASE_URL = "https://arena.ctf.tg"
cid = sys.argv[1] if len(sys.argv) > 1 else "267"
action = sys.argv[2] if len(sys.argv) > 2 else "spawn"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(storage_state=str(STATE_FILE))
    page = context.new_page()
    page.goto(f"{BASE_URL}/challenges", wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(500)

    nonce = page.evaluate("() => window.init && window.init.csrfNonce")
    print("csrf nonce:", nonce, file=sys.stderr)

    resp = page.request.post(f"{BASE_URL}/plugins/team_instancer/{action}",
                              headers={"Accept": "application/json", "Content-Type": "application/json", "CSRF-Token": nonce or ""},
                              data=json.dumps({"challenge_id": int(cid)}))
    print(f"status_code={resp.status}")
    try:
        print(json.dumps(resp.json(), indent=2, ensure_ascii=False))
    except Exception as e:
        print("parse error", e, resp.text()[:500])
    browser.close()
