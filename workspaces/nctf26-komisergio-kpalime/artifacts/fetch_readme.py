from pathlib import Path
from playwright.sync_api import sync_playwright

STATE_FILE = Path("/home/kali/ctfagent/src/tools/ctf/nctf26_storage_state.json")
BASE_URL = "https://arena.ctf.tg"
URL_PATH = "/files/18a6285af20ba8798cb76306192221d3/README.txt?token=eyJ1c2VyX2lkIjo1OSwidGVhbV9pZCI6MjMsImZpbGVfaWQiOjQyNn0.au554w.oz6-E622WE4wLXtMnVjNWaAIwLg"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(storage_state=str(STATE_FILE))
    page = context.new_page()
    page.goto(f"{BASE_URL}/challenges", wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(500)
    resp = page.request.get(f"{BASE_URL}{URL_PATH}")
    print("status:", resp.status)
    print(resp.text())
    browser.close()
