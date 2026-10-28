#!/usr/bin/env python3
"""
opencode_submit.py -- read Claude's notes, watch flags/pending/, submit to CTFd.

Role: OPENCODE does NOT solve challenges. It only:
  1. reads Claude's notes (--read-notes) to build the solved/in-progress/unsolved state
  2. watches flags/pending/ for flag files (filename = "<id>_<name>.flag")
  3. submits each flag via the CTFd API (session cookie loaded from an env file,
     never hardcoded in this script)
  4. logs every attempt to logs/opencode_submit_YYYYMMDD.log
     and moves accepted flags into flags/submitted/

Guardrails:
  - never submits a flag for a challenge Claude marks as in_progress UNLESS the flag
    file is physically present in pending/ (an actual flag beats an in-progress note)
  - never re-submits a flag already accepted (submitted/ or logs)
  - never touches Claude's own files (read-only on --notes-path)
  - refreshes the solved set from the API every ~60s (Resync loop)

Platform/CTF-specific values (base URL, session cookie, flag format, notes path)
are no longer hardcoded -- pass them per-CTF via CLI flags or an env file, so this
one script works across CTFs instead of being wired to a single event.

Usage:
    python3 src/tools/platform/opencode_submit.py \
        --base-url https://ctf.example.com \
        --env-file workspaces/<id>/.env \
        --notes-path workspaces/<id>/notes.md \
        --flag-regex 'ctf\\{[^}]+\\}' \
        --read-notes --watch

Env file (KEY=VALUE lines, same convention as ctf_platform_client.py):
    CTF_SESSION_COOKIE=<cookie value>
    CTF_BASE_URL=https://ctf.example.com        # optional, overridden by --base-url
    CTF_FLAG_REGEX=ctf\\{[^}]+\\}                 # optional, overridden by --flag-regex
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

try:
    import requests
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
except ImportError:
    print("pip3 install requests")
    sys.exit(1)

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_FLAG_DIR = REPO_ROOT / "flags"
DEFAULT_LOG_DIR = REPO_ROOT / "logs"

# Generic fallback: matches TAG{...}-style flags of any CTF ("ctf{...}", "kBxAc{...}", ...).
DEFAULT_FLAG_REGEX = r"[A-Za-z0-9_]{2,30}\{[^}]{1,300}\}"
ID_PREFIX_RE = re.compile(r"^(\d+)")


def load_env_file(path: Path) -> dict:
    """Same KEY=VALUE convention as ctf_platform_client.py's load_env_file."""
    env: dict[str, str] = {}
    if not path or not path.exists():
        return env
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        env[key.strip()] = value.strip()
    return env


def log(msg: str) -> None:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    print(f"[{ts}] {msg}", flush=True)


def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


class Submitter:
    def __init__(self, base_url: str, session_cookie: str, flag_regex: str,
                 notes_path: Path | None, flags_dir: Path, log_dir: Path):
        self.base_url = base_url.rstrip("/")
        self.session_cookie = session_cookie
        self.flag_re = re.compile(flag_regex)
        self.notes_path = notes_path
        self.pending = flags_dir / "pending"
        self.submitted = flags_dir / "submitted"
        self.log_dir = log_dir
        self.solved: set[int] = set()
        self.challenge_map: dict[int, dict] = {}
        self._nonce_cache: str | None = None

    # -- http -------------------------------------------------------------
    def sess(self) -> "requests.Session":
        s = requests.Session()
        s.verify = False
        domain = self.base_url.split("//", 1)[-1].split("/", 1)[0]
        s.cookies.set("session", self.session_cookie, domain=domain)
        return s

    def get_nonce(self, s: "requests.Session", force: bool = False) -> str:
        if self._nonce_cache and not force:
            return self._nonce_cache
        r = s.get(f"{self.base_url}/challenges", timeout=20)
        m = re.search(r"'csrfNonce':\s*\"([a-f0-9]+)\"", r.text) or \
            re.search(r'csrfNonce["\']?\s*[:=]\s*["\']([a-f0-9]+)["\']', r.text)
        if not m:
            raise RuntimeError("could not extract csrf nonce")
        self._nonce_cache = m.group(1)
        return self._nonce_cache

    def api_challenges(self) -> list:
        s = self.sess()
        r = s.get(f"{self.base_url}/api/v1/challenges", timeout=20)
        return r.json().get("data", [])

    def refresh_state(self) -> None:
        try:
            chals = self.api_challenges()
        except Exception as e:
            log(f"refresh_state: API error, keeping previous state ({e})")
            return
        self.solved = {c["id"] for c in chals if c.get("solved_by_me")}
        self.challenge_map = {
            c["id"]: {"name": c.get("name"), "category": c.get("category"), "solves": c.get("solves")}
            for c in chals
        }

    def submit_flag(self, cid: int, flag: str) -> dict:
        s = self.sess()
        try:
            n = self.get_nonce(s)
            r = s.post(
                f"{self.base_url}/api/v1/challenges/attempt",
                json={"challenge_id": cid, "submission": flag},
                headers={"CSRF-Token": n, "Content-Type": "application/json"},
                timeout=20,
            )
            if r.status_code == 403:
                n = self.get_nonce(s, force=True)
                r = s.post(
                    f"{self.base_url}/api/v1/challenges/attempt",
                    json={"challenge_id": cid, "submission": flag},
                    headers={"CSRF-Token": n, "Content-Type": "application/json"},
                    timeout=20,
                )
        except Exception as e:
            return {"ok": False, "error": str(e)}
        try:
            data = r.json().get("data", {})
        except ValueError:
            return {"ok": False, "error": f"non-JSON (HTTP {r.status_code})", "raw": r.text[:300]}
        status = data.get("status")
        return {
            "ok": True,
            "status_code": r.status_code,
            "status": status,
            "message": data.get("message"),
            "correct": status in ("correct", "already_solved"),
        }

    # -- notes --------------------------------------------------------------
    def read_notes(self) -> dict:
        """Parse Claude's notes.md for a rough solved/in-progress signal.

        Generic heuristic (no challenge names hardcoded): a line mentioning a
        title followed by "IN PROGRESS" or "solved" (case-insensitive).
        """
        state = {"solved": set(), "in_progress": set()}
        if not self.notes_path or not self.notes_path.exists():
            return state
        txt = self.notes_path.read_text(errors="ignore")
        for line in txt.splitlines():
            m = re.match(r"^\s*[-*]?\s*([A-Za-z0-9 _'\-\*]{2,60})\s*[—-].*\bIN PROGRESS\b", line)
            if m:
                state["in_progress"].add(m.group(1).strip())
            m = re.match(r"^\s*[-*]?\s*([A-Za-z0-9 _'\-\*]{2,60})\s*[—-].*\bsolved\b", line, re.IGNORECASE)
            if m:
                state["solved"].add(m.group(1).strip())
        return state

    # -- flag file handling ---------------------------------------------
    def append_log(self, rec: dict) -> None:
        self.log_dir.mkdir(parents=True, exist_ok=True)
        day = datetime.now(timezone.utc).strftime("%Y%m%d")
        path = self.log_dir / f"opencode_submit_{day}.log"
        with open(path, "a") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    def already_accepted(self, cid: int) -> bool:
        for _ in self.submitted.glob(f"{cid}_*"):
            return True
        return False

    @staticmethod
    def looks_sane(flag: str) -> bool:
        flag = flag.strip()
        low = flag.lower()
        if not flag or low in {"flag", "ctf{...}", "todo", "test"}:
            return False
        if "{" not in flag:
            return False
        return True

    def resolve_id(self, name: str) -> int | None:
        m = ID_PREFIX_RE.match(name)
        if m:
            return int(m.group(1))
        base = name.removesuffix(".flag").lower()
        for cid, info in self.challenge_map.items():
            if base in (info.get("name") or "").lower():
                return cid
        return None

    def handle(self, filepath: Path) -> None:
        name = filepath.name
        cid = self.resolve_id(name)
        payload = filepath.read_text(errors="ignore").strip()
        fm = self.flag_re.search(payload)
        flag = fm.group(0) if fm else payload

        log(f"HANDLE {name} -> cid={cid}, flag={flag!r}")

        if cid is None:
            self.append_log({"ts": _ts(), "file": name, "action": "skip",
                              "reason": "cannot resolve challenge id from filename"})
            log("  SKIP: cannot resolve challenge id (filename must start with <id>_)")
            return

        info = self.challenge_map.get(cid, {})
        if cid in self.solved or self.already_accepted(cid):
            self.submitted.mkdir(parents=True, exist_ok=True)
            filepath.rename(self.submitted / name)
            self.append_log({"ts": _ts(), "file": name, "id": cid, "action": "moved_submitted",
                              "reason": "already_solved_known", "flag": flag})
            log("  ALREADY SOLVED -> moved to submitted/ (no submission)")
            return

        if not self.looks_sane(flag):
            log("  SKIP: flag failed sanity check, leaving in pending/")
            self.append_log({"ts": _ts(), "file": name, "id": cid, "action": "skip",
                              "reason": "sanity_failed", "flag": flag})
            return

        log(f"  SUBMIT id={cid} {info.get('name')} flag={flag}")
        res = self.submit_flag(cid, flag)
        res["file"] = name
        res["id"] = cid
        res["flag"] = flag
        self.append_log(res)
        log(f"  RESULT: {res}")

        if res.get("correct"):
            self.submitted.mkdir(parents=True, exist_ok=True)
            filepath.rename(self.submitted / name)
            log(f"  ACCEPTED -> moved to submitted/: {name}")
            self.solved.add(cid)
        else:
            log(f"  WRONG/PENDING -> kept in pending/: {name}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--base-url", help="CTFd base URL, e.g. https://ctf.example.com "
                                        "(overrides CTF_BASE_URL from --env-file)")
    ap.add_argument("--env-file", type=Path,
                     help="KEY=VALUE file holding CTF_SESSION_COOKIE "
                          "(and optionally CTF_BASE_URL / CTF_FLAG_REGEX). "
                          "Never commit this file.")
    ap.add_argument("--flag-regex", help="Regex matching this CTF's flag format "
                                          f"(default: generic '{DEFAULT_FLAG_REGEX}')")
    ap.add_argument("--notes-path", type=Path, help="Path to Claude's notes.md for this CTF "
                                                      "(optional; used only by --read-notes)")
    ap.add_argument("--flags-dir", type=Path, default=DEFAULT_FLAG_DIR)
    ap.add_argument("--log-dir", type=Path, default=DEFAULT_LOG_DIR)
    ap.add_argument("--read-notes", action="store_true")
    ap.add_argument("--watch", action="store_true")
    ap.add_argument("--once", action="store_true", help="single scan of pending/, then exit")
    ap.add_argument("--id", type=int)
    ap.add_argument("--flag")
    args = ap.parse_args()

    env = load_env_file(args.env_file) if args.env_file else {}
    base_url = args.base_url or env.get("CTF_BASE_URL")
    session_cookie = env.get("CTF_SESSION_COOKIE")
    flag_regex = args.flag_regex or env.get("CTF_FLAG_REGEX") or DEFAULT_FLAG_REGEX

    if not base_url:
        ap.error("--base-url is required (or set CTF_BASE_URL in --env-file)")
    if not session_cookie:
        ap.error("CTF_SESSION_COOKIE missing: put it in --env-file, never on the CLI "
                  "(shell history / process listing would leak it)")

    sub = Submitter(
        base_url=base_url,
        session_cookie=session_cookie,
        flag_regex=flag_regex,
        notes_path=args.notes_path,
        flags_dir=args.flags_dir,
        log_dir=args.log_dir,
    )

    sub.pending.mkdir(parents=True, exist_ok=True)
    sub.submitted.mkdir(parents=True, exist_ok=True)
    sub.log_dir.mkdir(parents=True, exist_ok=True)

    if args.id and args.flag:  # direct one-shot submission
        sub.refresh_state()
        payload_path = sub.pending / f"{args.id}_manual.flag"
        payload_path.write_text(args.flag)
        sub.handle(payload_path)
        return 0

    if args.read_notes:
        sub.refresh_state()
        notes = sub.read_notes()
        unsolved_ids = [i for i in sub.challenge_map if i not in sub.solved]
        print(json.dumps({
            "claude_solved": sorted(sub.solved),
            "claude_in_progress_from_notes": sorted(notes["in_progress"]),
            "unsolved": unsolved_ids,
            "challenge_map": {str(k): v["name"] for k, v in sorted(sub.challenge_map.items())},
            "flag_regex": flag_regex,
        }, indent=2))

    if args.once:
        for f in sorted(sub.pending.iterdir()):
            if f.is_file():
                sub.handle(f)
        return 0

    if args.watch:
        log(f"Watching {sub.pending} (poll 2s). Ctrl-C to stop.")
        last_refresh = 0.0
        while True:
            try:
                files = sorted(sub.pending.glob("*.flag")) + sorted(sub.pending.iterdir())
                seen = set()
                for f in files:
                    if not f.is_file() or f in seen:
                        continue
                    seen.add(f)
                    sub.handle(f)
                now = time.time()
                if now - last_refresh >= 60:
                    sub.refresh_state()
                    last_refresh = now
            except KeyboardInterrupt:
                log("Stopped.")
                return 0
            except Exception as e:
                log(f"watch loop error: {e}")
            time.sleep(2)

    ap.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
