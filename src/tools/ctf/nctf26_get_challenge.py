#!/usr/bin/env python3
"""Fetch a single challenge's modal text + file links, headlessly (no visible
Chrome). Usage: python3 nctf26_get_challenge.py "<challenge button name>" """
from __future__ import annotations
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE_URL = "https://arena.ctf.tg"
STATE_FILE = Path(__file__).parent / "nctf26_storage_state.json"


def main():
    if len(sys.argv) < 2:
        print("Usage: nctf26_get_challenge.py <challenge name>", file=sys.stderr)
        sys.exit(1)
    name = sys.argv[1]
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(storage_state=str(STATE_FILE))
        page = context.new_page()
        page.goto(f"{BASE_URL}/challenges", wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(2000)
        btn = page.get_by_role("button", name=name, exact=False).first
        btn.wait_for(state="visible", timeout=10000)
        btn.click()
        page.wait_for_timeout(1000)
        dialog = page.query_selector("dialog, [role=dialog]")
        text = dialog.inner_text() if dialog else page.inner_text("main")
        print("=== TEXT ===")
        print(text)
        print("=== FILE LINKS ===")
        for a in page.query_selector_all("a[href*='/files/']"):
            href = a.get_attribute("href")
            print(href)
        browser.close()


if __name__ == "__main__":
    main()
