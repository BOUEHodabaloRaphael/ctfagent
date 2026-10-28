#!/usr/bin/env python3
"""
watch_scheduled.py -- read-only watcher for ctf.bugpwn.com (battleCTF).

STRICT SCOPE: detection only. No exploitation, no flag submission, no scanning.
Reuses the existing authenticated session (workspaces/bugpwn/session/storage_state.json)
via Playwright's APIRequestContext (cookies loaded from storage_state, no UI automation
needed for the read-only checks themselves).

Schedule (Europe/Paris-style UTC+1, no DST handling -- fixed offset as specified):
  09:00-20:45  LIGHT watch      : every 30 min  -- just confirms the session is alive.
  20:45-21:00  APPROACHING      : every 2 min   -- ramping up before the release window.
  21:00-00:00  INTENSIVE watch  : every 2 min    -- the actual challenge-release window.
  00:00-00:30  FINAL checks     : every 2 min    -- catches a late release.
  00:30-09:00  LIGHT watch      : every 30 min  -- default/quiet hours (not explicitly
                                                    specified by the user; treated as LIGHT).

Behavior:
  - Detects NEW challenges only (diffs against a persisted known-ids file so restarts
    don't re-alert on already-seen challenges).
  - Prints name/category/points/URL for each new challenge, with a loud visual block
    and a terminal bell.
  - Logs every check (mode, challenge count, session status) to
    workspaces/bugpwn/session/watcher_log.txt with UTC timestamps.
  - If the session looks expired: logs a warning. If CTF_PASS is set in the environment
    (never hardcoded in this file), attempts one fresh login via a real Playwright page
    and persists the refreshed storage_state.json; otherwise just keeps retrying on the
    light interval and tells the user to refresh the session manually.
  - Auto-recovers from connection resets / timeouts with exponential backoff -- the loop
    itself never crashes on a single failed check.

Usage:
    python3 watch_scheduled.py
    (CTF_PASS=... python3 watch_scheduled.py   # optional, enables auto-relogin)
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
import traceback
from datetime import datetime, timedelta, timezone

from playwright.sync_api import sync_playwright

BASE = "https://ctf.bugpwn.com"
HERE = os.path.dirname(os.path.abspath(__file__))
STATE_PATH = os.path.join(HERE, "session", "storage_state.json")
KNOWN_PATH = os.path.join(HERE, "session", "watcher_known_ids.json")
LOG_PATH = os.path.join(HERE, "session", "watcher_log.txt")
USER = os.environ.get("CTF_USER", "L&_M@z4rt")
PASS = os.environ.get("CTF_PASS", "")  # optional: export CTF_PASS=... for auto-relogin

TZ_UTC1 = timezone(timedelta(hours=1))

LIGHT_INTERVAL = 10 * 60
TIGHT_INTERVAL = 2 * 60


def now_utc1() -> datetime:
    return datetime.now(TZ_UTC1)


def log(msg: str) -> None:
    line = f"[{datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}] {msg}"
    print(line, flush=True)
    try:
        with open(LOG_PATH, "a") as f:
            f.write(line + "\n")
    except OSError:
        pass


def get_mode(t: datetime) -> tuple[str, str, int]:
    """Returns (mode_name, icon_label, interval_seconds) for the given UTC+1 time."""
    tod = t.time()
    h, m = tod.hour, tod.minute
    minutes = h * 60 + m

    def between(a_h, a_m, b_h, b_m):
        return a_h * 60 + a_m <= minutes < b_h * 60 + b_m

    if between(20, 45, 21, 0) or between(21, 0, 24, 0):
        return ("INTENSIVE" if minutes >= 21 * 60 else "APPROACHING",
                "🌙 VEILLE INTENSIVE" if minutes >= 21 * 60 else "🌙 VEILLE RAPPROCHEE",
                TIGHT_INTERVAL)
    if between(0, 0, 0, 30):
        return ("FINAL", "🌙 DERNIERS CHECKS", TIGHT_INTERVAL)
    return ("LIGHT", "☀ VEILLE LEGERE", LIGHT_INTERVAL)


def next_window_eta(t: datetime) -> str:
    """Human-readable countdown to the next 21:00 UTC+1 window, if currently outside it."""
    today_2100 = t.replace(hour=21, minute=0, second=0, microsecond=0)
    target = today_2100 if t < today_2100 else today_2100 + timedelta(days=1)
    delta = target - t
    total_s = int(delta.total_seconds())
    hh, rem = divmod(total_s, 3600)
    mm, ss = divmod(rem, 60)
    return f"{hh:02d}h{mm:02d}m{ss:02d}s avant 21:00 UTC+1 ({target.strftime('%Y-%m-%d %H:%M')})"


def load_known() -> set[int]:
    if os.path.exists(KNOWN_PATH):
        try:
            return set(json.load(open(KNOWN_PATH)))
        except Exception:
            return set()
    return set()


def save_known(ids: set[int]) -> None:
    os.makedirs(os.path.dirname(KNOWN_PATH), exist_ok=True)
    json.dump(sorted(ids), open(KNOWN_PATH, "w"))


def alert_new_challenge(c: dict) -> None:
    url = f"{BASE}/challenges#{c.get('id')}"
    block = (
        "\n" + "#" * 64 + "\n"
        f"### NOUVEAU CHALLENGE DETECTE !\n"
        f"### Nom      : {c.get('name')}\n"
        f"### Categorie: {c.get('category')}\n"
        f"### Points   : {c.get('value')}\n"
        f"### ID       : {c.get('id')}\n"
        f"### URL      : {url}\n"
        + "#" * 64 + "\n"
    )
    sys.stdout.write("\a")  # terminal bell
    print(block, flush=True)
    log(f"NEW CHALLENGE #{c.get('id')} {c.get('name')!r} [{c.get('category')}] "
        f"{c.get('value')}pts -> {url}")


def try_relogin(pw_context) -> bool:
    """Attempts one fresh login via a real page if CTF_PASS is set. Persists storage_state
    on success. Returns True if the session is valid afterward."""
    if not PASS:
        log("Session semble expiree et CTF_PASS n'est pas defini -> pas de relogin auto. "
            "Rafraichis workspaces/bugpwn/session/storage_state.json manuellement.")
        return False
    page = pw_context.new_page()
    try:
        page.goto(f"{BASE}/login", timeout=20000)
        page.wait_for_selector('input[name="name"]', timeout=10000)
        page.fill('input[name="name"]', USER)
        page.fill('input[name="password"]', PASS)
        page.click('button[type="submit"], input[type="submit"]')
        page.wait_for_load_state("networkidle", timeout=15000)
        pw_context.storage_state(path=STATE_PATH)
        log("Relogin automatique reussi, storage_state.json rafraichi.")
        return True
    except Exception as e:
        log(f"Relogin automatique echoue: {e}")
        return False
    finally:
        page.close()


def check_once(pw_context, known: set[int]) -> set[int]:
    """Does one read-only check. Returns the (possibly updated) known-ids set."""
    r = pw_context.request.get(f"{BASE}/api/v1/users/me", timeout=15000)
    me_ok = False
    try:
        me_ok = bool(r.ok and r.json().get("success"))
    except Exception:
        me_ok = False

    if not me_ok:
        log(f"Session INVALIDE (HTTP {r.status}) -- tentative de relogin...")
        if try_relogin(pw_context):
            r = pw_context.request.get(f"{BASE}/api/v1/users/me", timeout=15000)
            me_ok = r.ok and r.json().get("success")
        if not me_ok:
            log("Session toujours invalide apres tentative. Check suivant en mode leger.")
            return known

    r = pw_context.request.get(f"{BASE}/api/v1/challenges", timeout=15000)
    if not r.ok:
        log(f"Appel /api/v1/challenges en echec: HTTP {r.status}")
        return known
    data = r.json()
    if not data.get("success"):
        log(f"API challenges success=False: {json.dumps(data)[:200]}")
        return known

    chals = data.get("data", [])
    current_ids = {c["id"] for c in chals}
    new_ids = current_ids - known
    if new_ids:
        for c in sorted(chals, key=lambda c: c["id"]):
            if c["id"] in new_ids:
                alert_new_challenge(c)
    else:
        log(f"Check OK -- session valide, {len(chals)} challenges publies, aucun nouveau.")
    return known | current_ids


def main() -> int:
    log("=== watcher demarre ===")
    if not os.path.exists(STATE_PATH):
        log(f"ERREUR: {STATE_PATH} introuvable. Lance une session authentifiee d'abord.")
        return 1

    known = load_known()
    log(f"{len(known)} challenge(s) deja connus charges depuis {KNOWN_PATH}")

    backoff = 5
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context(storage_state=STATE_PATH)

        try:
            while True:
                t = now_utc1()
                mode, label, interval = get_mode(t)
                print(f"[{label}] {t.strftime('%Y-%m-%d %H:%M:%S')} UTC+1", flush=True)
                if mode == "LIGHT":
                    print(f"  -> {next_window_eta(t)}", flush=True)

                try:
                    known = check_once(context, known)
                    save_known(known)
                    backoff = 5  # reset backoff after a clean check
                except Exception as e:
                    # Covers ConnectionResetError / timeouts / any transient network issue.
                    log(f"Erreur pendant le check ({type(e).__name__}: {e}) -- "
                        f"nouvelle tentative dans {backoff}s.")
                    log(traceback.format_exc(limit=2))
                    time.sleep(backoff)
                    backoff = min(backoff * 2, 300)
                    continue

                time.sleep(interval)
        except KeyboardInterrupt:
            log("=== watcher arrete (Ctrl+C) ===")
        finally:
            context.close()
            browser.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
