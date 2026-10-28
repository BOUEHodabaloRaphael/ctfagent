#!/usr/bin/env python3
"""
Suggest (and optionally create) git worktrees for the workspaces that look
most active, so several challenges can be worked in parallel sessions
instead of one session context-switching between all of them.

Read-only by default (just prints suggestions). With --apply it only ever
ADDS new worktrees via `git worktree add`; it never removes a workspace,
an existing worktree, or any file.

Usage:
    python3 parallel_dispatch.py --repo-root .
    python3 parallel_dispatch.py --repo-root . --top 3 --apply
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

SOLVED_MARKERS = ("solved", "flag captured", "flag confirmed")


def is_likely_solved(workspace: Path) -> bool:
    """Best-effort heuristic: treat a workspace as settled (skip it) if its
    own notes mention a solved status. Never relies on metadata.json alone,
    since many workspaces in this repo were set up by hand without one."""
    for name in ("HANDOFF.md", "notes.md", "metadata.json"):
        candidate = workspace / name
        if not candidate.exists():
            continue
        try:
            text = candidate.read_text(encoding="utf-8", errors="ignore").lower()
        except OSError:
            continue
        if name == "metadata.json" and '"status": "solved"' in text:
            return True
        if any(marker in text for marker in SOLVED_MARKERS):
            return True
    return False


def most_recent_mtime(workspace: Path) -> float:
    best = workspace.stat().st_mtime
    for path in workspace.rglob("*"):
        try:
            best = max(best, path.stat().st_mtime)
        except OSError:
            continue
    return best


def existing_worktrees(repo_root: Path) -> set[str]:
    try:
        out = subprocess.run(
            ["git", "worktree", "list", "--porcelain"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            check=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError):
        return set()
    paths = set()
    for line in out.splitlines():
        if line.startswith("worktree "):
            paths.add(line.split(" ", 1)[1].strip())
    return paths


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--top", type=int, default=3, help="How many active workspaces to suggest")
    parser.add_argument(
        "--apply", action="store_true", help="Actually create the suggested git worktrees"
    )
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    workspaces_dir = repo_root / "workspaces"
    if not workspaces_dir.is_dir():
        print(json.dumps({"ok": False, "error": f"no workspaces/ under {repo_root}"}))
        return 1

    active: list[tuple[float, Path]] = []
    for workspace in sorted(workspaces_dir.iterdir()):
        if not workspace.is_dir():
            continue
        if is_likely_solved(workspace):
            continue
        active.append((most_recent_mtime(workspace), workspace))

    active.sort(key=lambda pair: pair[0], reverse=True)
    top = active[: args.top]

    worktree_root = repo_root / ".claude" / "worktrees"
    existing = existing_worktrees(repo_root)

    suggestions = []
    for _, workspace in top:
        slug = workspace.name
        target = worktree_root / f"parallel-{slug}"
        branch = f"parallel/{slug}"
        already = str(target) in existing or target.exists()
        suggestions.append(
            {
                "workspace": slug,
                "worktree_path": str(target),
                "branch": branch,
                "already_exists": already,
            }
        )

    applied = None
    if args.apply:
        applied = []
        for suggestion in suggestions:
            if suggestion["already_exists"]:
                applied.append({"workspace": suggestion["workspace"], "ok": True, "skipped": "already exists"})
                continue
            cmd = ["git", "worktree", "add", "-b", suggestion["branch"], suggestion["worktree_path"]]
            proc = subprocess.run(cmd, cwd=str(repo_root), capture_output=True, text=True)
            applied.append(
                {
                    "workspace": suggestion["workspace"],
                    "ok": proc.returncode == 0,
                    "stdout": proc.stdout.strip(),
                    "stderr": proc.stderr.strip(),
                }
            )

    result = {
        "ok": True,
        "active_workspaces_considered": len(active),
        "suggestions": suggestions,
        "applied": applied,
        "note": (
            "Open a separate Claude Code session rooted at each worktree_path "
            "for true parallel work on that challenge."
        ),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
