#!/usr/bin/env python3
"""
Fast flag submission for kbxac CTFd — plain HTTP (requests), NO Playwright.
Playwright's full page load (networkidle) takes 20-30s+ under server load;
this does a single lightweight GET (to grab/refresh the CSRF nonce, cached
after the first call) + one POST to /api/v1/challenges/attempt. Typically
sub-second to a couple seconds.

Guardrails kept from submit.py: rejects empty/placeholder flags, refuses to
resubmit an identical flag already logged for that id (use --force to
override), still logs every attempt to logs/submissions.log.

Usage:
    python3 workspaces/kbxac/fast_submit.py --id 25 --flag 'kBxAc{...}'
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

try:
    import requests
except ImportError:
    print(json.dumps({"ok": False, "error": "pip3 install requests"}))
    sys.exit(1)

WS = Path(__file__).resolve().parent
LOG_FILE = WS / "logs" / "submissions.log"
BASE_URL = "https://ctf.kbxac.xyz"
SESSION_COOKIE = "23b7edf9-bc19-4091-987c-e3cd9ddeb65c.1_r3VMuxcr0MbsbQMkOBGnUBigA"

_NONCE_CACHE_FILE = WS / "logs" / ".csrf_nonce_cache"


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
    if flag.lower() in {"flag", "kbxac{...}", "todo", "test"}:
        return False
    return True


def append_log(record: dict) -> None:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(record) + "\n")


def get_nonce(sess: "requests.Session", force_refresh: bool = False) -> str:
    if not force_refresh and _NONCE_CACHE_FILE.exists():
        cached = _NONCE_CACHE_FILE.read_text().strip()
        if cached:
            return cached
    r = sess.get(f"{BASE_URL}/challenges", timeout=15)
    m = re.search(r"'csrfNonce':\s*\"([a-f0-9]+)\"", r.text)
    if not m:
        m = re.search(r'csrfNonce["\']?\s*[:=]\s*["\']([a-f0-9]+)["\']', r.text)
    if not m:
        raise RuntimeError("could not extract csrf nonce from /challenges")
    nonce = m.group(1)
    _NONCE_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    _NONCE_CACHE_FILE.write_text(nonce)
    return nonce


def submit(cid: int, flag: str) -> dict:
    sess = requests.Session()
    sess.cookies.set("session", SESSION_COOKIE, domain="ctf.kbxac.xyz")
    sess.verify = False
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    nonce = get_nonce(sess)
    resp = sess.post(
        f"{BASE_URL}/api/v1/challenges/attempt",
        json={"challenge_id": cid, "submission": flag},
        headers={"CSRF-Token": nonce, "Content-Type": "application/json"},
        timeout=15,
    )
    if resp.status_code == 403:
        # nonce likely stale/rotated -- refresh once and retry
        nonce = get_nonce(sess, force_refresh=True)
        resp = sess.post(
            f"{BASE_URL}/api/v1/challenges/attempt",
            json={"challenge_id": cid, "submission": flag},
            headers={"CSRF-Token": nonce, "Content-Type": "application/json"},
            timeout=15,
        )
    try:
        data = resp.json()
    except ValueError:
        return {"ok": False, "error": f"non-JSON response (status {resp.status_code})", "raw": resp.text[:500]}

    inner = data.get("data", {})
    return {
        "ok": True,
        "status_code": resp.status_code,
        "status": inner.get("status"),
        "message": inner.get("message"),
        "correct": inner.get("status") in ("correct", "already_solved"),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--id", type=int, required=True)
    ap.add_argument("--flag", required=True)
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    flag = args.flag.strip()
    if not looks_sane(flag):
        print(json.dumps({"ok": False, "error": "flag failed sanity check"}))
        return 2
    if not args.force and already_tried(args.id, flag):
        print(json.dumps({"ok": False, "error": "already submitted identical flag for this id; use --force"}))
        return 3

    t0 = time.time()
    try:
        result = submit(args.id, flag)
    except Exception as e:
        result = {"ok": False, "error": str(e)}
    result["elapsed_s"] = round(time.time() - t0, 2)

    append_log({
        "ts": time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()),
        "id": args.id, "flag": flag,
        "ok": result.get("ok", False), "correct": result.get("correct"),
        "message": result.get("message"),
    })
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result.get("correct") else 1


if __name__ == "__main__":
    raise SystemExit(main())
