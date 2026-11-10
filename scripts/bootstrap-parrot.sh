#!/usr/bin/env bash
# bootstrap-parrot.sh — one-shot CTFAgent setup for a fresh Parrot OS (or any
# Debian/Kali-based) machine: Claude Code CLI + the full CTF toolchain used by
# this repo's skills. Idempotent — safe to re-run.
#
# Two ways to use it:
#
#   A) Repo already present (USB copy, already cloned):
#      cd ctfagent && ./scripts/bootstrap-parrot.sh
#
#   B) Fresh machine, repo only on GitHub (needs the repo to be public, or
#      CTFAGENT_REPO_URL set to an https://user:TOKEN@github.com/... URL for
#      a private repo):
#      curl -fsSL https://raw.githubusercontent.com/huanghuoguoguo/ctfagent/main/scripts/bootstrap-parrot.sh | bash
#
# What it does NOT do (on purpose — see workspaces/nctf26/machine-migration-runbook.md):
#   - never touches any secret (.env, session/, storage_state.json,
#     .claude/settings*.json) — those are gitignored and must be copied back
#     by hand from the old machine, never through this script or git.
#   - does not build the Ghidra docker image by default (slow, needs docker);
#     pass --with-ghidra-image to also build it.
set -euo pipefail

REPO_URL="${CTFAGENT_REPO_URL:-https://github.com/huanghuoguoguo/ctfagent.git}"
TARGET_DIR="${CTFAGENT_DIR:-$HOME/ctfagent}"
WITH_GHIDRA_IMAGE=0

for arg in "$@"; do
  case "$arg" in
    --with-ghidra-image) WITH_GHIDRA_IMAGE=1 ;;
    *) echo "unknown argument: $arg" >&2; exit 1 ;;
  esac
done

log() { echo -e "\n[*] $*"; }

log "CTFAgent bootstrap starting"

# ---------------------------------------------------------------------------
# 1. Get the repo: reuse current dir if it already looks like ctfagent,
#    reuse TARGET_DIR if already cloned there, otherwise clone fresh.
# ---------------------------------------------------------------------------
if [ -f "./CLAUDE.md" ] && [ -d "./.claude/skills" ]; then
  TARGET_DIR="$(pwd)"
  log "Running from inside an existing repo copy: $TARGET_DIR"
elif [ -d "$TARGET_DIR/.git" ]; then
  log "Repo already present at $TARGET_DIR"
else
  log "Cloning $REPO_URL into $TARGET_DIR"
  git clone "$REPO_URL" "$TARGET_DIR"
fi
cd "$TARGET_DIR"

# ---------------------------------------------------------------------------
# 2. Node.js + Claude Code CLI
# ---------------------------------------------------------------------------
if ! command -v node >/dev/null 2>&1; then
  log "Installing Node.js LTS"
  curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
  sudo apt-get install -y nodejs
else
  log "Node.js already present ($(node --version))"
fi

if ! command -v claude >/dev/null 2>&1; then
  log "Installing Claude Code CLI"
  npm install -g @anthropic-ai/claude-code
else
  log "Claude Code CLI already present"
fi

# ---------------------------------------------------------------------------
# 3. apt packages (see workspaces/nctf26/prep-arsenal-2026-11-06.md section 3)
# ---------------------------------------------------------------------------
log "Installing apt packages (CTF toolchain)"
sudo apt-get update
sudo apt-get install -y \
  binwalk foremost libimage-exiftool-perl tshark sleuthkit \
  ffmpeg steghide testdisk john pcapfix \
  apktool jq qemu-user-static ltrace unblob \
  bruteshark \
  nmap curl socat netcat-traditional \
  docker.io \
  gdb gdb-multiarch radare2

# ---------------------------------------------------------------------------
# 4. Python packages (user install, --break-system-packages for PEP 668)
# ---------------------------------------------------------------------------
log "Installing Python packages"
pip3 install --user --break-system-packages \
  volatility3 Pillow numpy matplotlib scipy librosa scikit-learn \
  opencv-python-headless pymongo impacket brotli exrex stegano heatshrink2 \
  lief frida-tools flare-capa flare-floss requests pwntools \
  capstone unicorn angr z3-solver pyelftools pefile yara-python \
  checksec.py ROPgadget

# ---------------------------------------------------------------------------
# 5. CFR (Java decompiler)
# ---------------------------------------------------------------------------
log "Installing CFR (Java decompiler)"
mkdir -p ~/.local/opt/cfr
curl -sSL -o ~/.local/opt/cfr/cfr.jar \
  https://repo1.maven.org/maven2/org/benf/cfr/0.152/cfr-0.152.jar

# ---------------------------------------------------------------------------
# 6. Optional: build the Ghidra headless docker image (slow)
# ---------------------------------------------------------------------------
if [ "$WITH_GHIDRA_IMAGE" -eq 1 ]; then
  if command -v docker >/dev/null 2>&1; then
    log "Building rekit-ghidra11 docker image (this takes a while)"
    sudo docker build -t rekit-ghidra11 workspaces/rekit-lab/sandbox-ghidra11/
  else
    echo "WARNING: docker not available, skipping Ghidra image build" >&2
  fi
else
  log "Skipping Ghidra docker image build (pass --with-ghidra-image to include it)"
fi

# ---------------------------------------------------------------------------
# 7. Verify
# ---------------------------------------------------------------------------
log "Running test suite"
python3 -m pytest tests/ -q || echo "WARNING: some tests failed, check manually" >&2

log "Checking skill inventory"
python3 src/tools/common/check_skill_inventory.py --root . || true

cat <<EOF

==============================================================
CTFAgent bootstrap done. Repo at: $TARGET_DIR

MANUAL STEPS STILL NEEDED (never automated — secrets never touch git):
  1. Copy back the secret files listed in
     workspaces/nctf26/machine-migration-runbook.md (section 0):
       .claude/settings.json, .claude/settings.local.json
       src/tools/ctf/.env, src/tools/ctf/nctf26_storage_state.json
       workspaces/bugpwn/.env, workspaces/bugpwn/session/
       workspaces/kbxac/.env,  workspaces/kbxac/session/
  2. Run 'claude login' inside $TARGET_DIR if not already authenticated.
  3. Once finale infra is announced on site, fill
     src/tools/ctf/attack_defense_toolkit/config.py (team IPs, FLAG_REGEX,
     submission endpoint).
  4. If you skipped the Ghidra image, re-run with --with-ghidra-image
     once docker is confirmed working, or build it manually:
       docker build -t rekit-ghidra11 workspaces/rekit-lab/sandbox-ghidra11/
==============================================================
EOF
