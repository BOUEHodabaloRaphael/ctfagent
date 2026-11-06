#!/usr/bin/env bash
# Ghidra headless (image rekit-ghidra11) without a local Ghidra install.
#
#   ./src/tools/rev/ghidra_headless.sh <binary> [outdir]
#
# Imports <binary> into a throwaway project, runs auto-analysis, and leaves the
# project in <outdir> (default: ./ghidra_<basename>) so it can be reopened with
#   analyzeHeadless <projdir> <projname> -process <basename> -postScript ...
# or exported with the plugin script
#   .claude/skills/reverse-engineering/scripts/ghidra/export_decompiled.py
#
# Why the flags: the image runs as uid 10001 (user "analyst"); mounting the
# project dir with --user $(id -u) keeps the output owned by you, and HOME=/tmp
# gives Ghidra a writable config dir.  Do not remove them.
set -euo pipefail

BIN="${1:?usage: ghidra_headless.sh <binary> [outdir]}"
[[ -f "$BIN" ]] || { echo "no such file: $BIN" >&2; exit 1; }
BIN="$(realpath "$BIN")"

NAME="$(basename "$BIN")"
OUT="${2:-./ghidra_${NAME//[^A-Za-z0-9_.-]/_}}"
mkdir -p "$OUT"
OUT="$(realpath "$OUT")"

IMAGE="${GHIDRA_IMAGE:-rekit-ghidra11}"
docker image inspect "$IMAGE" >/dev/null 2>&1 || {
  echo "docker image '$IMAGE' missing; build it with workspaces/rekit-lab/sandbox-ghidra11/Dockerfile" >&2
  exit 1
}

docker run --rm \
  --user "$(id -u):$(id -g)" -e HOME=/tmp \
  -v "$(dirname "$BIN"):/in:ro" \
  -v "$OUT:/proj" \
  "$IMAGE" \
  /opt/ghidra/support/analyzeHeadless /proj proj1 -import "/in/$NAME"

echo "project: $OUT  (open: analyzeHeadless $OUT proj1 -process $NAME)"
