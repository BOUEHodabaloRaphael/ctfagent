#!/bin/sh
# Static analysis of an untrusted sample inside a locked-down container.
# Usage: sandbox/run.sh <sample> [REKit args...]     (run from workspaces/rekit-lab/)
# The sample is NEVER executed: REKit only reads it. Container has no network,
# a read-only root fs, no capabilities and tight resource limits.
set -eu
SAMPLE=$(realpath "$1"); shift
HERE=$(cd "$(dirname "$0")/.." && pwd)
exec docker run --rm \
  --network none \
  --read-only --tmpfs /tmp:rw,noexec,nosuid,size=64m \
  --cap-drop ALL --security-opt no-new-privileges \
  --pids-limit 128 --memory 512m --cpus 1 \
  --user 10001:10001 \
  -v "$HERE/vendor/REKITV2.py:/opt/REKITV2.py:ro" \
  -v "$SAMPLE:/sample/target:ro" \
  rekit-sandbox python3 -I /opt/REKITV2.py /sample/target "$@"
