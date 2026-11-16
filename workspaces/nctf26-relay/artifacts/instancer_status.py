import sys, json
from pathlib import Path
from playwright.sync_api import sync_playwright

STATE_FILE = Path("/home/kali/ctfagent/src/tools/ctf/nctf26_storage_state.json")
BASE_URL = "https://arena.ctf.tg"
cid = sys.argv[1] if len(sys.argv) > 1 else "267"
action = sys.argv[2] if len(sys.argv) > 2 else "status"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(storage_state=str(STATE_FILE))
    page = context.new_page()
    # need a page load first so CSRF cookie/session is attached properly
    page.goto(f"{BASE_URL}/challenges", wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(500)

    if action == "status":
        resp = page.request.get(f"{BASE_URL}/plugins/team_instancer/status?challenge_id={cid}",
                                 headers={"Accept": "application/json"})
    elif action == "spawn":
        resp = page.request.post(f"{BASE_URL}/plugins/team_instancer/spawn",
                                  headers={"Accept": "application/json", "Content-Type": "application/json"},
                                  data=json.dumps({"challenge_id": int(cid)}))
    else:
        print("unknown action"); sys.exit(1)

    print(f"status_code={resp.status}")
    try:
        print(json.dumps(resp.json(), indent=2, ensure_ascii=False))
    except Exception as e:
        print("parse error", e, resp.text()[:1000])
    browser.close()
