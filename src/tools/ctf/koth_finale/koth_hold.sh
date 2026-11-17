#!/usr/bin/env bash
# =============================================================================
# NCTF26 FINALE — KoTH : UNE SEULE COMMANDE, persistante jusqu'a la fin.
#
#   bash koth_hold.sh start      # <- LA commande a lancer (detache, watchdog, log)
#   bash koth_hold.sh status     # suis-je roi ? cadence ? processus vivant ?
#   bash koth_hold.sh stop       # arret propre (fichier STOP + kill du groupe)
#   bash koth_hold.sh selftest   # test complet hors-ligne contre une fausse colline
#   bash koth_hold.sh probe      # 1 claim + 1 status (calibrage a t+0)
#
# Prerequis : hill.env rempli (l'agent le fait a l'ouverture via recon_koth.py).
# Survit a la fermeture du terminal (setsid) ; relance auto si le teneur tombe.
# Pour survivre a un REBOOT de la machine : voir koth-hold.service (README).
#
# Regles : colline in-scope uniquement, pas de DoS, pas d'attaque des autres
# equipes / de l'infra orga.
# =============================================================================
set -u
cd "$(dirname "$0")"

CONF="${KOTH_CONF:-hill.env}"
LOG="koth.log"
STOP="STOP"
SUPPID="supervisor.pid"
PY=python3

say() { printf '[koth_hold] %s\n' "$*"; }

load_conf() {
  if [ -f "$CONF" ]; then
    set -a; . "$CONF"; set +a
  fi
}

need_conf() {
  load_conf
  if [ -z "${KOTH_CLAIM_PATH:-}" ]; then
    say "ERREUR : KOTH_CLAIM_PATH vide dans $CONF."
    say "         -> l'agent doit calibrer la colline d'abord : python3 recon_koth.py"
    say "         -> puis remplir $CONF (modele : hill.env.example)."
    exit 2
  fi
}

alive() {
  [ -f "$SUPPID" ] || return 1
  local p; p=$(cat "$SUPPID" 2>/dev/null) || return 1
  [ -n "$p" ] && kill -0 "$p" 2>/dev/null
}

pgid_of() {
  local p="$1"
  ps -o pgid= -p "$p" 2>/dev/null | tr -d ' '
}

# ---------------------------------------------------------------- supervisor
_supervise() {
  echo $$ > "$SUPPID"
  trap 'say "superviseur: signal recu"; kill 0 2>/dev/null; exit 0' INT TERM
  local restarts=0
  while :; do
    if [ -f "$STOP" ]; then say "STOP present -> fin de la tenue"; break; fi
    "$PY" -u hold_hill.py --run >> "$LOG" 2>&1
    code=$?
    if [ "$code" -eq 0 ]; then say "teneur termine proprement (code 0) -> fin"; break; fi
    restarts=$((restarts + 1))
    say "teneur tombe (code $code) -> relance #$restarts dans 3s"
    sleep 3
  done
  rm -f "$SUPPID"
  say "superviseur arrete"
}

# ------------------------------------------------------------------ commands
cmd_start() {
  need_conf
  if alive; then
    say "deja en cours (pid superviseur $(cat "$SUPPID")) — rien a faire."
    say "suivi : bash koth_hold.sh status"
    exit 0
  fi
  if [ -f "$STOP" ]; then
    say "Un arret a ete demande (fichier STOP). Pour relancer volontairement :"
    say "  rm -f $STOP && bash koth_hold.sh start"
    exit 0
  fi
  mkdir -p "$(dirname "$LOG")"
  say "demarrage detache | conf=$CONF | log=$LOG"
  say "colline : ${KOTH_BASE:-?}${KOTH_CLAIM_PATH} | threads=${KOTH_THREADS:-4}"
  setsid nohup bash "$0" _supervise >> "$LOG" 2>&1 &
  sleep 1
  if alive; then
    say "OK — tenue en cours (superviseur pid $(cat "$SUPPID"))."
    say "Suivi    : bash koth_hold.sh status   (ou tail -f $LOG)"
    say "Arret    : bash koth_hold.sh stop"
  else
    say "ECHEC du demarrage — 20 dernieres lignes du log :"
    tail -n 20 "$LOG"
    exit 1
  fi
}

cmd_stop() {
  touch "$STOP"
  if alive; then
    p=$(cat "$SUPPID"); g=$(pgid_of "$p")
    say "arret : TERM au groupe $g (superviseur pid $p)"
    [ -n "$g" ] && kill -TERM "-$g" 2>/dev/null
    for _ in 1 2 3 4 5 6 7 8 9 10; do alive || break; sleep 0.5; done
    alive && { say "toujours vivant -> KILL"; kill -KILL "-$g" 2>/dev/null; }
  else
    say "aucun superviseur vivant"
  fi
  pkill -f '^python3 .*hold_hill\.py --run' 2>/dev/null || true
  rm -f "$SUPPID"
  say "arrete. Pour repartir : rm -f $STOP && bash koth_hold.sh start"
}

cmd_status() {
  load_conf
  if alive; then say "superviseur : VIVANT (pid $(cat "$SUPPID"))"; else say "superviseur : arrete"; fi
  if [ -f STOP ]; then say "fichier STOP present (arret demande)"; fi
  if [ -f status.json ]; then
    "$PY" - <<'PY'
import json,sys,time
try: d=json.load(open('status.json'))
except Exception as e: print('status.json illisible:',e); sys.exit(0)
up=d.get('uptime_s',0)
print("colline   : %s" % ('ROI=OUI' if d.get('is_king') else 'ROI=NON'))
print("roi actuel: %s (nous: %s)" % (d.get('king'), ','.join(d.get('our_ids') or []) or '?'))
print("claims    : %d (ok=%d err=%d) dernier=%s" % (d.get('claims',0),d.get('ok',0),d.get('err',0),d.get('last_code')))
print("cadence   : %s threads / %ss min / slot=%ss" % (d.get('threads'),d.get('min_interval'),d.get('slot_period')))
print("uptime    : %.0fs (%.1f h)" % (up, up/3600.0))
PY
  else
    say "pas encore de status.json (le teneur n'a pas demarre ?)"
  fi
  echo "--- 6 dernieres lignes de $LOG ---"
  tail -n 6 "$LOG" 2>/dev/null || true
}

cmd_probe() {
  need_conf
  "$PY" -u hold_hill.py --probe 2>&1 | tee -a "$LOG"
}

# --------------------------------------------------------------- self-test
cmd_selftest() {
  say "self-test hors-ligne (fausse colline locale, aucun reseau externe)"
  local port=18777
  local tmp; tmp=$(mktemp -d)
  local fail=0

  "$PY" mock_hill.py --port "$port" --rival --rival-interval 1.5 >"$tmp/mock.log" 2>&1 &
  local mock=$!
  sleep 0.7
  if ! kill -0 "$mock" 2>/dev/null; then
    say "ECHEC: la fausse colline n'a pas demarre"; cat "$tmp/mock.log"; return 1
  fi

  # config de test -> colline locale, etat isole
  export KOTH_BASE="http://127.0.0.1:$port"
  export KOTH_CLAIM_PATH="/claim"
  export KOTH_CLAIM_METHOD="POST"
  export KOTH_CLAIM_BODY='{"team":"TEAM-US","ts":{ts}}'
  export KOTH_STATUS_PATH="/status"
  export KOTH_KING_FIELD="king"
  export KOTH_OUR_ID="TEAM-US"
  export KOTH_THREADS="3"
  export KOTH_MIN_INTERVAL="1.0"
  export KOTH_PERIOD="1"
  export KOTH_TIMEOUT="5"
  export KOTH_STATE_DIR="$tmp"
  export KOTH_STOP_FILE="$tmp/STOP"
  export KOTH_STORAGE="$tmp/none.json"
  unset KOTH_TOKEN KOTH_AUTH KOTH_SLOT_PERIOD KOTH_UNTIL KOTH_SIGN_KEY 2>/dev/null || true

  say "[1/4] probe (1 claim + 1 status)"
  "$PY" hold_hill.py --probe >"$tmp/probe.log" 2>&1 || fail=1
  grep -q "ROI(nous)=True" "$tmp/probe.log" || { say "  ECHEC: status ne nous voit pas roi"; fail=1; }
  grep -qE "claim: 200" "$tmp/probe.log" || { say "  ECHEC: claim non-200"; fail=1; }
  [ "$fail" -eq 0 ] && say "  OK"

  say "[2/4] tenue 8s avec rival qui reclame toutes les 1.5s"
  ( "$PY" hold_hill.py --run >"$tmp/run.log" 2>&1 & echo $! >"$tmp/run.pid" )
  sleep 8
  if "$PY" - "$tmp/status.json" <<'PY'
import json,sys
d=json.load(open(sys.argv[1]))
assert d['claims']>0, 'aucun claim'
assert d['is_king'] is True, 'ROI=NON au dernier tick'
PY
  then say "  OK (ROI=OUI face au rival)"; else say "  ECHEC: on ne tient pas la colline"; fail=1; fi

  say "[3/4] arret par fichier STOP"
  touch "$tmp/STOP"
  local i; for i in $(seq 1 20); do
    kill -0 "$(cat "$tmp/run.pid")" 2>/dev/null || break; sleep 0.5
  done
  if kill -0 "$(cat "$tmp/run.pid")" 2>/dev/null; then say "  ECHEC: toujours vivant apres STOP"; fail=1
  else say "  OK (arret propre)"; fi

  say "[4/4] verdict du scorer local"
  if curl -s --max-time 3 "http://127.0.0.1:$port/status" | grep -q '"king": "TEAM-US"'; then
    say "  OK (dernier roi = nous)"
  else
    say "  note: dernier roi != nous (course normale) — non bloquant"
  fi

  kill "$mock" 2>/dev/null; wait "$mock" 2>/dev/null
  rm -rf "$tmp"
  echo
  if [ "$fail" -eq 0 ]; then say "SELF-TEST: PASS ✅"; return 0; else say "SELF-TEST: FAIL ❌"; return 1; fi
}

# ---------------------------------------------------------------------- main
case "${1:-start}" in
  start|run) cmd_start ;;
  stop)      cmd_stop ;;
  status)    cmd_status ;;
  logs)      tail -f "$LOG" ;;
  probe)     cmd_probe ;;
  selftest)  cmd_selftest ;;
  _supervise) load_conf; _supervise ;;
  *) sed -n '2,16p' "$0"; exit 1 ;;
esac
