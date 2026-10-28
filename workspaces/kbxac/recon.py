#!/usr/bin/env python3
"""
Recon pass for the kbxac CTFd event: list every visible challenge, snapshot
it to artifacts/, and download attachments per challenge.

Reuses src/tools/platform/ctf_platform_client.py rather than re-implementing
HTTP/Playwright logic. Safe to re-run: re-polls current state, does not
submit anything, does not loop tightly.

Usage:
    python3 workspaces/kbxac/recon.py
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WS = Path(__file__).resolve().parent
CLIENT = ROOT / "src" / "tools" / "platform" / "ctf_platform_client.py"

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
    out = subprocess.run(COMMON + list(args), capture_output=True, text=True, timeout=120)
    try:
        return json.loads(out.stdout)
    except json.JSONDecodeError:
        return {"ok": False, "raw_stdout": out.stdout, "raw_stderr": out.stderr}


def main() -> int:
    log("Listing challenges...")
    listing = run_client("list-challenges")
    chals = listing.get("challenges") or []
    if not chals:
        log("No challenges visible yet. Nothing to do (CTF may not have started).")
        print(json.dumps(listing, indent=2, ensure_ascii=False))
        return 1

    log(f"Found {len(chals)} challenges.")

    enriched = []
    for c in chals:
        cid = c.get("id")
        name = c.get("name", f"id{cid}")
        cat = c.get("category", "misc")
        log(f"  [{cat}] {name} (id={cid}, {c.get('value')} pts, {c.get('solves')} solves)")

        detail = run_client("show-challenge", "--id", str(cid))
        data = detail.get("data", {})
        files = data.get("files", [])

        dl_dir = WS / "artifacts" / "files" / f"{cid}_{name}".replace("/", "_")
        if files:
            dl_dir.mkdir(parents=True, exist_ok=True)
            dl = run_client("download", "--id", str(cid), "--out-dir", str(dl_dir))
            log(f"    downloaded: {dl.get('saved', [])}")

        enriched.append({
            "id": cid,
            "name": name,
            "category": cat,
            "value": c.get("value"),
            "solves": c.get("solves"),
            "solved_by_me": c.get("solved_by_me"),
            "description": data.get("description"),
            "files": files,
            "hints": data.get("hints"),
        })

    out_path = WS / "artifacts" / "challenges_enriched.json"
    out_path.write_text(json.dumps(enriched, indent=2, ensure_ascii=False), encoding="utf-8")
    log(f"Saved enriched challenge list -> {out_path}")

    # Quick-win sort: unsolved first, then by points/solves ratio ascending
    # (few points relative to solves = hard; many solves on low points =
    # fast win). We rank by solves descending as a simple "easy first" proxy.
    unsolved = [c for c in enriched if not c.get("solved_by_me")]
    unsolved.sort(key=lambda c: (-(c.get("solves") or 0), c.get("value") or 0))
    log("Suggested solve order (quick wins first):")
    for c in unsolved:
        log(f"  - [{c['category']}] {c['name']} ({c['value']} pts, {c['solves']} solves)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
