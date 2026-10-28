#!/usr/bin/env python3
"""
SessionStart hook: prints a short sync summary for ctfagent so a new Claude
Code session opened in this repo starts already aware of (1) the latest
project memory, (2) which workspaces are still active, and (3) the two
verification/parallelism helper scripts.

Read-only. Never deletes or modifies anything; only reads MEMORY.md and
shells out to parallel_dispatch.py (also read-only without --apply).

Emits the hookSpecificOutput.additionalContext shape SessionStart hooks use
to inject text into the new session's context.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
MEMORY_DIR = Path.home() / ".claude" / "projects" / "-home-kali-ctfagent" / "memory"
DISPATCH_SCRIPT = REPO_ROOT / "src" / "tools" / "workspace" / "parallel_dispatch.py"


def read_memory_index(limit: int = 6) -> list[str]:
    index = MEMORY_DIR / "MEMORY.md"
    if not index.exists():
        return []
    lines = [line.strip() for line in index.read_text(encoding="utf-8").splitlines() if line.strip()]
    return lines[:limit]


def active_workspaces(top: int = 5) -> list[str]:
    if not DISPATCH_SCRIPT.exists():
        return []
    try:
        proc = subprocess.run(
            [sys.executable, str(DISPATCH_SCRIPT), "--repo-root", str(REPO_ROOT), "--top", str(top)],
            capture_output=True,
            text=True,
            timeout=15,
        )
        data = json.loads(proc.stdout)
    except Exception:
        return []
    return [s["workspace"] for s in data.get("suggestions", [])]


def build_summary() -> str:
    parts = ["## ctfagent session sync"]

    memory_lines = read_memory_index()
    if memory_lines:
        parts.append("**Memoire recente (MEMORY.md):**")
        parts.extend(f"- {line.lstrip('- ')}" for line in memory_lines)
    else:
        parts.append("**Memoire:** aucune entree trouvee dans MEMORY.md.")

    workspaces = active_workspaces()
    if workspaces:
        parts.append("\n**Workspaces actifs (les plus recents):** " + ", ".join(workspaces))
    else:
        parts.append("\n**Workspaces actifs:** aucun detecte (ou parallel_dispatch.py indisponible).")

    parts.append(
        "\n**Outils disponibles:**\n"
        "- `src/tools/workspace/verify_loop.py --workspace workspaces/<id>` : lance les scripts "
        "d'exploit du workspace, detecte le flag, log dans verify_log.jsonl, ecrit flags/pending/.\n"
        "- `src/tools/workspace/parallel_dispatch.py --top N [--apply]` : suggere/cree des "
        "git worktrees pour travailler plusieurs workspaces en parallele."
    )

    return "\n".join(parts)


def main() -> int:
    summary = build_summary()
    output = {
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": summary,
        }
    }
    print(json.dumps(output, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
