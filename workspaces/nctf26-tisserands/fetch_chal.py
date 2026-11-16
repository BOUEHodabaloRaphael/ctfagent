from pathlib import Path
from playwright.sync_api import sync_playwright
import json

STATE_FILE = Path("/home/kali/ctfagent/src/tools/ctf/nctf26_storage_state.json")
BASE_URL = "https://arena.ctf.tg"
OUT_DIR = Path("/home/kali/ctfagent/workspaces/nctf26-tisserands/artifacts")
OUT_DIR.mkdir(parents=True, exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(storage_state=str(STATE_FILE))
    page = context.new_page()
    page.goto(f"{BASE_URL}/challenges", wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(1000)
    resp = page.request.get(f"{BASE_URL}/api/v1/challenges/447")
    data = resp.json()
    print(json.dumps(data, indent=2, ensure_ascii=False))

    (OUT_DIR / "challenge_447.json").write_text(json.dumps(data, indent=2, ensure_ascii=False))

    files = data.get("data", {}).get("files", [])
    for f in files:
        url = f if f.startswith("http") else f"{BASE_URL}{f}"
        fname = url.split("/")[-1].split("?")[0]
        r = page.request.get(url)
        out_path = OUT_DIR / fname
        out_path.write_bytes(r.body())
        print(f"Downloaded {url} -> {out_path} ({len(r.body())} bytes)")

    browser.close()
