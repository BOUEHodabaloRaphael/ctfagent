#!/usr/bin/env python3
"""Poll /api/v1/challenges every ~1s using Playwright's lightweight
`request` context (no browser launch per call -- a single persistent
APIRequestContext reusing the saved session cookie). Prints NEW challenge
names as they appear vs the last run's snapshot (same snapshot file as
nctf26_watch.py, so both stay in sync).

This is a single sustained ~1 req/s loop against the platform's own
challenge-list API -- NOT a flood (no parallelism, no sub-second rate,
one connection reused). Exits cleanly on Ctrl-C / SIGTERM.
"""
import json
import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE_URL = "https://arena.ctf.tg"
STATE_FILE = Path(__file__).parent / "nctf26_storage_state.json"
SNAPSHOT_FILE = Path(__file__).parent / "nctf26_challenge_snapshot.json"
POLL_INTERVAL_S = 1.0


def main():
    if not STATE_FILE.exists():
        print("Pas de session sauvegardee -- lancer 'login' d'abord.", file=sys.stderr)
        sys.exit(1)

    prev = set()
    if SNAPSHOT_FILE.exists():
        prev = set(json.loads(SNAPSHOT_FILE.read_text()).get("names", []))

    with sync_playwright() as p:
        ctx = p.request.new_context(storage_state=str(STATE_FILE))
        n = 0
        while True:
            n += 1
            try:
                resp = ctx.get(f"{BASE_URL}/api/v1/challenges", timeout=8000)
                if resp.status == 429:
                    print(f"[{n}] HTTP 429 -- backing off 30s", flush=True)
                    time.sleep(30)
                    continue
                data = resp.json().get("data", [])
                names = {c["name"] for c in data}
                new_names = sorted(names - prev)
                if new_names:
                    print("NOUVEAUX:", flush=True)
                    for nm in new_names:
                        c = next(x for x in data if x["name"] == nm)
                        print(f"  - {nm} (id={c['id']}, cat={c['category']}, {c['value']}pts)", flush=True)
                    prev = names
                    SNAPSHOT_FILE.write_text(json.dumps({"names": sorted(names)}, indent=2))
            except Exception as e:
                print(f"[{n}] erreur transitoire: {e}", file=sys.stderr, flush=True)
            time.sleep(POLL_INTERVAL_S)


if __name__ == "__main__":
    main()
