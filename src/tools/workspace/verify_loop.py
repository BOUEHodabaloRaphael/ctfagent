#!/usr/bin/env python3
"""
Generic exploit verification loop for a challenge workspace.

Closes the "exploit -> verify -> log (-> submit)" gap: instead of eyeballing
exploit output by hand after every tweak, this runs one or more candidate
exploit scripts inside a workspace, scans their combined stdout/stderr for a
flag pattern, and writes a structured result so the next decision (try the
next script, or submit) does not require re-reading raw terminal scrollback.

Purely additive: it never deletes or overwrites existing workspace files. It
only appends to <workspace>/verify_log.jsonl and, on a match, writes a new
file under flags/pending/.

Usage:
    python3 verify_loop.py --workspace workspaces/pwn001
    python3 verify_loop.py --workspace workspaces/pwn001 --cmd "python3 exp_flag.py"
    python3 verify_loop.py --workspace workspaces/pwn001 --submit \
        --base-url https://ctf.example.com --id 12 --env-file workspaces/pwn001/.env
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

FLAG_PATTERN = re.compile(r"[A-Za-z0-9_]{2,24}\{[^{}\s]{2,200}\}")

# Checked in this order; every match is still a *candidate*, not a guarantee.
CANDIDATE_GLOBS = [
    "solve.py",
    "exploit.py",
    "poc.py",
    "exp_flag.py",
    "exp.py",
    "exp_*.py",
    "exploit_*.py",
    "exploit*.py",
]


def now_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def discover_candidates(workspace: Path) -> list[Path]:
    seen: set[Path] = set()
    ordered: list[Path] = []
    for pattern in CANDIDATE_GLOBS:
        for match in sorted(workspace.glob(pattern)):
            if match.is_file() and match not in seen:
                seen.add(match)
                ordered.append(match)
    return ordered


def run_one(cmd: list[str], cwd: Path, timeout: int) -> dict:
    started = time.time()
    timed_out = False
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        stdout, stderr, returncode = proc.stdout, proc.stderr, proc.returncode
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or ""
        stderr = exc.stderr or ""
        returncode = None
        timed_out = True
    except OSError as exc:
        stdout, stderr, returncode = "", str(exc), None

    elapsed = time.time() - started
    combined = f"{stdout}\n{stderr}"
    matches = sorted(set(FLAG_PATTERN.findall(combined)))

    return {
        "cmd": cmd,
        "returncode": returncode,
        "timed_out": timed_out,
        "elapsed_sec": round(elapsed, 2),
        "flags_found": matches,
        "tail": "\n".join(combined.strip().splitlines()[-30:]),
    }


def append_jsonl(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")


def save_pending_flag(repo_root: Path, workspace_id: str, flag: str) -> Path:
    pending_dir = repo_root / "flags" / "pending"
    pending_dir.mkdir(parents=True, exist_ok=True)
    dest = pending_dir / f"{workspace_id}_{now_stamp()}.flag"
    dest.write_text(flag, encoding="utf-8")
    return dest


def submit_flag(repo_root: Path, flag: str, args: argparse.Namespace) -> dict:
    client = repo_root / "src" / "tools" / "platform" / "ctf_platform_client.py"
    cmd = [sys.executable, str(client), "submit", "--flag", flag]
    if args.base_url:
        cmd += ["--base-url", args.base_url]
    if args.chal_id is not None:
        cmd += ["--id", str(args.chal_id)]
    if args.env_file:
        cmd += ["--env-file", args.env_file]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    lines = [line for line in proc.stdout.strip().splitlines() if line.strip()]
    if not lines:
        return {"ok": False, "error": "ctf_platform_client produced no output", "stderr": proc.stderr}
    try:
        return json.loads(lines[-1])
    except json.JSONDecodeError:
        return {"ok": False, "error": "could not parse ctf_platform_client output", "raw": proc.stdout}


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--workspace", required=True, help="Path to workspaces/<id>")
    parser.add_argument(
        "--cmd",
        action="append",
        help="Explicit shell-splittable command to run instead of auto-discovery (repeatable)",
    )
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument(
        "--submit", action="store_true", help="Submit the first flag found via ctf_platform_client.py"
    )
    parser.add_argument("--base-url")
    parser.add_argument("--id", dest="chal_id", type=int)
    parser.add_argument("--env-file")
    parser.add_argument("--repo-root", default=".")
    args = parser.parse_args()

    workspace = Path(args.workspace).resolve()
    repo_root = Path(args.repo_root).resolve()
    if not workspace.is_dir():
        print(json.dumps({"ok": False, "error": f"workspace not found: {workspace}"}))
        return 1

    if args.cmd:
        commands = [c.split() for c in args.cmd]
    else:
        candidates = discover_candidates(workspace)
        if not candidates:
            print(
                json.dumps(
                    {
                        "ok": False,
                        "error": (
                            "no candidate exploit script found "
                            "(solve.py/exploit.py/exp_*.py/...) and --cmd not given"
                        ),
                    }
                )
            )
            return 1
        commands = [[sys.executable, str(c)] for c in candidates]

    log_path = workspace / "verify_log.jsonl"
    results = []
    found_flag = None

    for cmd in commands:
        record = run_one(cmd, cwd=workspace, timeout=args.timeout)
        record["ts"] = now_stamp()
        append_jsonl(log_path, record)
        results.append(record)
        if record["flags_found"] and found_flag is None:
            found_flag = record["flags_found"][0]

    summary = {
        "ok": found_flag is not None,
        "workspace": str(workspace),
        "tried": len(commands),
        "flag": found_flag,
        "log": str(log_path),
        "results": results,
    }

    if found_flag:
        pending_path = save_pending_flag(repo_root, workspace.name, found_flag)
        summary["pending_flag_file"] = str(pending_path)
        if args.submit:
            summary["submit_result"] = submit_flag(repo_root, found_flag, args)

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
