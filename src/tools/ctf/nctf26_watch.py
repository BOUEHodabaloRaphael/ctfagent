#!/usr/bin/env python3
"""Poll /challenges headlessly (Playwright, saved session) and report any
challenge names not seen in the last snapshot, plus the 'next challenge'
countdown. Never touches the user's real Chrome -- separate headless
Chromium instance via the existing nctf26 Playwright session.

Usage:
    python3 nctf26_watch.py          # one-shot check, prints new challenges
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE_URL = "https://arena.ctf.tg"
STATE_FILE = Path(__file__).parent / "nctf26_storage_state.json"
SNAPSHOT_FILE = Path(__file__).parent / "nctf26_challenge_snapshot.json"


def main() -> None:
    if not STATE_FILE.exists():
        print("Pas de session sauvegardee -- lancer 'login' d'abord.", file=sys.stderr)
        sys.exit(1)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(storage_state=str(STATE_FILE))
        page = context.new_page()
        page.goto(f"{BASE_URL}/challenges", wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(2000)

        names = set()
        for btn in page.query_selector_all("main button"):
            txt = (btn.inner_text() or "").strip()
            if not txt:
                continue
            # strip trailing point value lines if present (button text can be
            # "name\npoints" -- keep first line only as the name)
            name = txt.splitlines()[0].strip()
            if name and name not in ("Catégorie", "Auteur"):
                names.add(name)

        body_text = page.inner_text("main")
        countdown_match = re.search(r"Prochain challenge dans\s*([0-9]+ min [0-9]+ s)", body_text)
        countdown = countdown_match.group(1) if countdown_match else None
        open_match = re.search(r"(\d+)\s*/\s*(\d+)\s*challenges ouverts", body_text)
        open_count = open_match.group(0) if open_match else None

        browser.close()

    prev = set()
    if SNAPSHOT_FILE.exists():
        prev = set(json.loads(SNAPSHOT_FILE.read_text()).get("names", []))

    new_names = sorted(names - prev)

    SNAPSHOT_FILE.write_text(json.dumps({"names": sorted(names)}, indent=2))

    print(f"Countdown prochain challenge: {countdown}")
    print(f"Ouverts: {open_count}")
    print(f"Total challenges vus: {len(names)}")
    if new_names:
        print("NOUVEAUX:")
        for n in new_names:
            print(f"  - {n}")
    else:
        print("(aucun nouveau depuis le dernier snapshot)")


if __name__ == "__main__":
    main()
