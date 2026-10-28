#!/usr/bin/env python3
"""
Watch the kbxac CTFd countdown and trigger recon as soon as challenges open.

Does NOT poll in a tight 2s loop -- that is unnecessary load on the
platform. Instead it sleeps until shortly before the known start time
(read from the countdown page's data-cd-start attribute), then checks
more frequently only in the final window.

Usage:
    python3 workspaces/kbxac/watch.py
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WS = Path(__file__).resolve().parent
CLIENT = ROOT / "src" / "tools" / "platform" / "ctf_platform_client.py"

# Known event start, read from the countdown page's data-cd-start
# attribute on 2026-10-09 (2026-10-09 18:30:00 UTC = 00:00 IST). Hardcoded
# as a fallback because once any challenge (even a pre-event "out context"
# bonus one) is visible, list-challenges succeeds via the CTFd API and no
# longer dumps the countdown HTML we'd otherwise re-parse this from.
KNOWN_START_EPOCH = 1791570600.0

# Categories already open before the real start (pre-event bonus/social
# challenges, e.g. "out context" on this platform). Their presence must
# NOT be mistaken for the main event opening.
PRE_EVENT_CATEGORIES = {"out context"}

COMMON = [
    sys.executable, str(CLIENT),
    "--env-file", str(WS / ".env"),
    "--session-file", str(WS / "session" / "storage_state.json"),
    "--artifact-dir", str(WS / "artifacts"),
    "--log-dir", str(WS / "logs"),
]


def log(msg: str) -> None:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    print(f"[{ts}] {msg}", flush=True)


def run_client(*args: str) -> dict:
    out = subprocess.run(COMMON + list(args), capture_output=True, text=True, timeout=60)
    try:
        return json.loads(out.stdout)
    except json.JSONDecodeError:
        return {"ok": False, "raw_stdout": out.stdout, "raw_stderr": out.stderr}


def get_start_epoch() -> float | None:
    """Fetch the countdown page fresh and extract data-cd-start, if present."""
    res = run_client("list-challenges")
    dump = res.get("raw_dump")
    if not dump:
        return None
    path = ROOT / dump
    if not path.exists():
        return None
    html = path.read_text(errors="ignore")
    m = re.search(r'data-cd-start="(\d+)"', html)
    if m:
        return float(m.group(1))
    return None


def real_categories_open() -> bool:
    """True once a challenge outside the known pre-event categories shows up."""
    res = run_client("list-challenges")
    chals = res.get("challenges") or []
    if not res.get("ok") or not chals:
        return False
    real = [c for c in chals if (c.get("category") or "").strip().lower() not in PRE_EVENT_CATEGORIES]
    if real:
        log(f"Detected {len(real)} challenge(s) outside pre-event categories: "
            + ", ".join(f"{c.get('category')}/{c.get('name')}" for c in real[:5]))
        return True
    return False


def main() -> int:
    log("watch.py starting - resolving CTF start time from countdown page")
    start_epoch = get_start_epoch() or KNOWN_START_EPOCH
    when = datetime.fromtimestamp(start_epoch, tz=timezone.utc)
    log(f"Countdown target: {when.isoformat()} (epoch {start_epoch})")

    # Phase A: coarse sleep until ~20 minutes before start (or immediately
    # if we couldn't resolve a start time). 20 min gives margin to catch
    # an early open / clock drift without hammering the server for hours.
    FINE_WINDOW_SECONDS = 20 * 60
    while True:
        remaining = start_epoch - time.time()
        if remaining <= FINE_WINDOW_SECONDS:
            break
        sleep_for = min(remaining - FINE_WINDOW_SECONDS, 600)  # re-check at least every 10 min
        log(f"T-{remaining:.0f}s to start. Sleeping {sleep_for:.0f}s.")
        time.sleep(sleep_for)

    # Phase B: fine polling in the final window (every ~5s, not 2s).
    log("Entering fine-polling window (last ~20 min before start).")
    while True:
        if real_categories_open():
            log("Real-category challenges are OPEN. Triggering recon.")
            break
        remaining = start_epoch - time.time()
        log(f"Still pre-event. T-{remaining:.0f}s.")
        time.sleep(5)

    # Hand off to recon.
    recon = WS / "recon.py"
    log(f"Launching {recon}")
    subprocess.run([sys.executable, str(recon)])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
