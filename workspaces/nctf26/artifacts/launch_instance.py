#!/usr/bin/env python3
"""Open a challenge modal, click the instance-launch button, and dump the
resulting HTML (to find host:port) -- read-only reconnaissance of the UI,
no exploitation yet."""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE_URL = "https://arena.ctf.tg"
STATE_FILE = Path("/home/kali/ctfagent/src/tools/ctf/nctf26_storage_state.json")

challenge_name = sys.argv[1]

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=["--host-resolver-rules=MAP arena.ctf.tg 104.21.67.127"])
    context = browser.new_context(storage_state=str(STATE_FILE))
    page = context.new_page()
    page.goto(f"{BASE_URL}/challenges", wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(2000)

    btn = page.get_by_role("button", name=challenge_name, exact=False).first
    btn.wait_for(state="visible", timeout=15000)
    btn.click()
    page.wait_for_timeout(1500)

    # Look for a launch/start/demarrer button inside the modal
    for label in ["Démarrer mon instance", "Démarrer", "Demarrer", "Launch", "Start", "Lancer"]:
        try:
            launch_btn = page.get_by_role("button", name=label, exact=False).first
            if launch_btn.is_visible(timeout=1000):
                print(f"[found launch button: {label}]")
                launch_btn.click()
                page.wait_for_timeout(8000)
                break
        except Exception:
            continue

    # Dump modal text content
    modal = page.query_selector(".modal.show, .modal-dialog, [role=dialog]")
    if modal:
        print(modal.inner_text())
    else:
        print("[no modal found, dumping body text snippet]")
        print(page.inner_text("body")[:3000])

    browser.close()
