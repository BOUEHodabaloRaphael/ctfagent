#!/bin/sh
# Extract an encrypted malware zip INSIDE the sandbox (tmpfs, noexec) and run REKit on it.
# Usage: sandbox/run_zip.sh <sample.zip> <password> [REKit args...]
set -eu
ZIP=$(realpath "$1"); PASS=$2; shift 2
HERE=$(cd "$(dirname "$0")/.." && pwd)
exec docker run --rm \
  --network none \
  --read-only --tmpfs /tmp:rw,noexec,nosuid,size=256m \
  --cap-drop ALL --security-opt no-new-privileges \
  --pids-limit 128 --memory 512m --cpus 1 \
  --user 10001:10001 \
  -v "$HERE/vendor/REKITV2.py:/opt/REKITV2.py:ro" \
  -v "$ZIP:/sample/s.zip:ro" \
  rekit-sandbox sh -c '
    7z x -y -p"$0" -o/tmp/x /sample/s.zip >/dev/null
    for f in $(find /tmp/x -type f); do
      file -b "$f" | grep -q "^ELF\|^PE32" || continue
      echo "[sandbox] $(basename "$f" | cut -c1-12)... $(stat -c %s "$f") bytes: $(file -b "$f" | cut -c1-55)"
      python3 -I /opt/REKITV2.py "$f" "$@"
    done' "$PASS" "$@"
