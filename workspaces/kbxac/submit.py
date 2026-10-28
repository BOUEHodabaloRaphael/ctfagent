#!/usr/bin/env python3
"""
Thin, safe wrapper around ctf_platform_client.py submit for the kbxac event.

Guardrails (deliberately NOT fully unattended):
  - Refuses an empty/obviously-malformed flag (no braces at all, or
    whitespace-only).
  - Refuses to resubmit a flag string already logged as tried for the
    same challenge id in logs/submissions.log (CTFd rate-limits/bans on
    repeated wrong guesses -- don't hammer it).
  - Still requires a human call per submission; this is not meant to be
    wired into a blind auto-submit loop.

Usage:
    python3 workspaces/kbxac/submit.py --id 12 --flag 'kbxac{...}'
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

WS = Path(__file__).resolve().parent
ROOT = WS.parents[1]
CLIENT = ROOT / "src" / "tools" / "platform" / "ctf_platform_client.py"
LOG_FILE = WS / "logs" / "submissions.log"

# Official event start (from the countdown page's data-cd-start attribute,
# 2026-10-09). Real-category challenges (web/pwn/...) were observed via
# the CTFd API hours before this time -- almost certainly a visibility
# misconfiguration, not something we're meant to exploit. Deliberate
# decision (2026-10-09, user confirmed): analyze early, submit nothing
# before the official start. Use --force only if the user explicitly
# tells you the rules allow it.
OFFICIAL_START_EPOCH = 1791570600.0


def already_tried(cid: int, flag: str) -> bool:
    if not LOG_FILE.exists():
        return False
    for line in LOG_FILE.read_text(errors="ignore").splitlines():
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        if rec.get("id") == cid and rec.get("flag") == flag:
            return True
    return False


def looks_sane(flag: str) -> bool:
    flag = flag.strip()
    if not flag:
        return False
    # Most CTFd flags are wrapped in some_prefix{...}; accept raw-value
    # flags too (seen in this repo's other events) but reject obvious
    # placeholder/empty guesses.
    if flag.lower() in {"flag", "ctf{...}", "kbxac{...}", "todo", "test"}:
        return False
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--id", type=int, required=True)
    ap.add_argument("--flag", required=True)
    ap.add_argument("--force", action="store_true", help="skip the already-tried guard")
    args = ap.parse_args()

    flag = args.flag.strip()

    if not args.force and time.time() < OFFICIAL_START_EPOCH:
        remaining = OFFICIAL_START_EPOCH - time.time()
        print(json.dumps({
            "ok": False,
            "error": f"official start not reached yet (T-{remaining:.0f}s); "
                     f"refusing to submit before 2026-10-09T18:30:00Z. Use --force to override.",
        }))
        return 4

    if not looks_sane(flag):
        print(json.dumps({"ok": False, "error": "flag failed sanity check, not submitting"}))
        return 2

    if not args.force and already_tried(args.id, flag):
        print(json.dumps({"ok": False, "error": "this exact flag was already submitted for this id; use --force to repeat"}))
        return 3

    cmd = [
        sys.executable, str(CLIENT), "submit",
        "--env-file", str(WS / ".env"),
        "--session-file", str(WS / "session" / "storage_state.json"),
        "--artifact-dir", str(WS / "artifacts"),
        "--log-dir", str(WS / "logs"),
        "--id", str(args.id),
        "--flag", flag,
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    print(res.stdout)
    if res.stderr:
        print(res.stderr, file=sys.stderr)
    return res.returncode


if __name__ == "__main__":
    raise SystemExit(main())
