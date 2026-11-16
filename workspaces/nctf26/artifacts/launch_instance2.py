#!/usr/bin/env python3
import sys, json
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE_URL = "https://arena.ctf.tg"
STATE_FILE = Path("/home/kali/ctfagent/src/tools/ctf/nctf26_storage_state.json")
challenge_name = sys.argv[1]

responses = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=["--host-resolver-rules=MAP arena.ctf.tg 104.21.67.127"])
    context = browser.new_context(storage_state=str(STATE_FILE))
    page = context.new_page()

    def on_response(resp):
        url = resp.url
        if "arena.ctf.tg" in url and ("instance" in url or "launch" in url or "docker" in url or "deploy" in url or "container" in url):
            try:
                body = resp.text()
            except Exception:
                body = "<binary or unavailable>"
            responses.append((resp.status, url, body[:2000]))

    page.on("response", on_response)

    page.goto(f"{BASE_URL}/challenges", wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(2000)

    btn = page.get_by_role("button", name=challenge_name, exact=False).first
    btn.wait_for(state="visible", timeout=15000)
    btn.click()
    page.wait_for_timeout(1500)

    launch_btn = page.get_by_role("button", name="Démarrer mon instance", exact=False).first
    launch_btn.click()
    page.wait_for_timeout(6000)

    print("=== captured responses ===")
    for status, url, body in responses:
        print(status, url)
        print(body)
        print("---")

    print("=== modal text ===")
    modal = page.query_selector(".modal.show, .modal-dialog, [role=dialog]")
    if modal:
        print(modal.inner_text())

    browser.close()
