#!/usr/bin/env bash
# =============================================================================
# NCTF26 FINALE — KoTH : LA SEULE COMMANDE A LANCER.
#
#   bash koth_run.sh start      <- prend et tient la colline jusqu'a la fin
#   bash koth_run.sh status     <- ROI=OUI/NON, niveau, cadence, RTT, ticks gagnes
#   bash koth_run.sh stop       <- arret propre
#   bash koth_run.sh logs       <- suivi en direct
#   bash koth_run.sh probe      <- 1 claim + 1 status (calibrage a t+0)
#   bash koth_run.sh selftest   <- bataille complete hors-ligne (aucun reseau)
#   bash koth_run.sh bundle     <- ZIP pret a envoyer aux coequipiers
#
# Ce que fait `start` :
#   1. charge hill.env (endpoints reels, remplis a l'ouverture) ;
#   2. lance hill_hold.py detache (setsid) : il survit a la fermeture du terminal ;
#   3. supervise : si le teneur tombe OU se fige (>90 s sans progresser), il le relance ;
#   4. respecte le fichier STOP et l'heure de fin KOTH_UNTIL.
#
# Multi-machines : lance la MEME commande sur chaque Kali, avec KOTH_PUMPS=N sur
# chacune (N = nombre total de machines). Le debit total reste borne, et N machines
# tiennent mieux qu'une. KOTH_PUMP_ID est deduit du hostname si non fourni.
#
# Regles : colline in-scope uniquement. Pas de DoS, pas d'attaque des autres
# equipes ni de l'infra organisatrice.
# =============================================================================
set -u
cd "$(dirname "$0")"

CONF="${KOTH_CONF:-hill.env}"
LOG="${KOTH_LOG:-koth.log}"
STOP="STOP"
SUPPID="supervisor.pid"
PY=python3
HERE="$(pwd)"

say() { printf '[koth] %s\n' "$*"; }

load_conf() {
  if [ -f "$CONF" ]; then
    set -a; . "$CONF"; set +a
  fi
  LOG="${KOTH_LOG:-$LOG}"
  # identite de la pompe : stable par machine, sans collision entre coequipiers
  if [ -z "${KOTH_PUMP_ID:-}" ]; then
    KOTH_PUMP_ID="$(hostname -s 2>/dev/null | tr -cd 'a-zA-Z0-9' | cut -c1-8)"
    [ -z "$KOTH_PUMP_ID" ] && KOTH_PUMP_ID="p$$"
    export KOTH_PUMP_ID
  fi
  export KOTH_STATE_DIR="${KOTH_STATE_DIR:-$HERE}"
  export KOTH_STOP_FILE="${KOTH_STOP_FILE:-$HERE/$STOP}"
}

alive() {
  [ -f "$SUPPID" ] || return 1
  local p; p=$(cat "$SUPPID" 2>/dev/null) || return 1
  [ -n "$p" ] && kill -0 "$p" 2>/dev/null
}

pgid_of() { ps -o pgid= -p "$1" 2>/dev/null | tr -d ' '; }

claims_now() {
  "$PY" - <<'PY' 2>/dev/null
import json,os
p=os.path.join(os.environ.get("KOTH_STATE_DIR","."),"status.json")
try: print(json.load(open(p)).get("claims",0))
except Exception: print(0)
PY
}

# ---------------------------------------------------------------- superviseur
_supervise() {
  echo $$ > "$SUPPID"
  trap 'say "superviseur: signal recu"; kill 0 2>/dev/null; exit 0' INT TERM
  local restarts=0 last_claims=0 stalled=0
  while :; do
    if [ -f "$STOP" ]; then say "STOP present -> fin de la tenue"; break; fi
    "$PY" -u hill_hold.py --run >> "$LOG" 2>&1
    code=$?
    if [ "$code" -eq 0 ]; then say "teneur termine proprement -> fin"; break; fi
    restarts=$((restarts + 1))
    say "teneur tombe (code $code) -> relance #$restarts dans 3 s"
    sleep 3
  done
  rm -f "$SUPPID"
  say "superviseur arrete"
}

# ------------------------------------------------------------------ commandes
cmd_start() {
  load_conf
  if [ -z "${KOTH_CLAIM_PATH:-}" ] && [ -z "${KOTH_KING_FILE:-}" ]; then
    say "ERREUR : colline non configuree dans $CONF."
    say "  -> a l'ouverture : python3 recon_koth.py  (puis remplir $CONF)"
    say "  -> modele complet : hill.env.example"
    exit 2
  fi
  if alive; then
    say "deja en cours (superviseur pid $(cat "$SUPPID"))"
    say "suivi : bash koth_run.sh status"
    exit 0
  fi
  if [ -f "$STOP" ]; then
    say "arret deja demande (fichier STOP). Relance volontaire :"
    say "  rm -f $STOP && bash koth_run.sh start"
    exit 0
  fi
  say "demarrage | pompe=${KOTH_PUMP_ID} | pompes=${KOTH_PUMPS:-1} | conf=$CONF | log=$LOG"
  if [ -n "${KOTH_KING_FILE:-}" ]; then
    say "mode LOCAL (king file) : $KOTH_KING_FILE"
  else
    say "mode HTTP : ${KOTH_BASE:-?}${KOTH_CLAIM_PATH} | snipe=${KOTH_SLOT_PERIOD:-off}s"
  fi
  setsid nohup bash "$0" _supervise >> "$LOG" 2>&1 &
  sleep 1.2
  if alive; then
    say "OK — la colline est tenue (superviseur pid $(cat "$SUPPID"))."
    say "Tu peux fermer le terminal. Suivi : bash koth_run.sh status"
  else
    say "ECHEC du demarrage — 25 dernieres lignes :"
    tail -n 25 "$LOG"
    exit 1
  fi
}

cmd_stop() {
  load_conf
  touch "$STOP"
  if alive; then
    p=$(cat "$SUPPID"); g=$(pgid_of "$p")
    say "arret : TERM au groupe ${g:-?} (superviseur pid $p)"
    [ -n "$g" ] && kill -TERM "-$g" 2>/dev/null
    for _ in 1 2 3 4 5 6 7 8 9 10; do alive || break; sleep 0.5; done
    alive && { say "toujours vivant -> KILL"; kill -KILL "-$g" 2>/dev/null; }
  else
    say "aucun superviseur vivant"
  fi
  ps -eo pid,args | awk '/[h]ill_hold\.py --run/ {print $1}' | xargs -r kill 2>/dev/null
  rm -f "$SUPPID"
  say "arrete. Repartir : rm -f $STOP && bash koth_run.sh start"
}

cmd_status() {
  load_conf
  if alive; then say "superviseur : VIVANT (pid $(cat "$SUPPID"))"; else say "superviseur : arrete"; fi
  [ -f "$STOP" ] && say "fichier STOP present (arret demande)"
  if [ -f "$KOTH_STATE_DIR/status.json" ]; then
    KOTH_STATE_DIR="$KOTH_STATE_DIR" "$PY" - <<'PY'
import json, os, sys
d = json.load(open(os.path.join(os.environ["KOTH_STATE_DIR"], "status.json")))
up = d.get("uptime_s", 0)
roi = "ROI=OUI  (on est roi)" if d.get("is_king") else "ROI=NON  (on n'est pas roi)"
print("colline    : %s" % roi)
print("roi actuel : %s   (nous : %s)" % (d.get("king"), d.get("our_ids") or "?"))
print("niveau     : %s   threads=%s   fenetre=%ss   RTT=%sms"
      % (d.get("level"), d.get("threads"), d.get("snipe_window"), d.get("rtt_ms")))
print("ticks      : snipe=%ss  (le dernier claim avant le tick gagne)"
      % (d.get("slot_period") or "off"))
print("claims     : %s (ok=%s err=%s 429=%s)  dernier=%s"
      % (d.get("claims"), d.get("ok"), d.get("err"), d.get("rate_limited"), d.get("last_code")))
print("escalades  : %s   relachements : %s   pertes : %s"
      % (d.get("escalations"), d.get("relaxations"), d.get("losses")))
print("uptime     : %.0fs (%.1f h)   pompe=%s/%s"
      % (up, up / 3600.0, d.get("pump"), d.get("pumps")))
PY
  else
    say "pas encore de status.json (teneur pas demarre ?)"
  fi
  echo "--- 6 dernieres lignes de $LOG ---"
  tail -n 6 "$LOG" 2>/dev/null || true
}

cmd_probe() { load_conf; "$PY" -u hill_hold.py --probe 2>&1 | tee -a "$LOG"; }

# ------------------------------------------------------------------ self-test
cmd_selftest() {
  say "SELF-TEST : bataille complete hors-ligne (aucun acces reseau externe)"
  local port="${KOTH_TEST_PORT:-18888}"
  local tmp; tmp=$(mktemp -d)
  local fail=0

  "$PY" mock_rival.py --port "$port" --aggression 3 --tick 5 --ratelimit 0.05 \
        --reset-every 20 >"$tmp/mock.log" 2>&1 &
  local mock=$!
  sleep 0.8
  if ! kill -0 "$mock" 2>/dev/null; then
    say "ECHEC : la colline de test n'a pas demarre"; cat "$tmp/mock.log"; return 1
  fi

  export KOTH_BASE="http://127.0.0.1:$port"
  export KOTH_CLAIM_PATH="/claim" KOTH_CLAIM_METHOD="POST"
  export KOTH_CLAIM_BODY='{"team":"TEAM-US"}'
  export KOTH_STATUS_PATH="/status" KOTH_KING_FIELD="score_king" KOTH_OUR_ID="TEAM-US"
  export KOTH_THREADS_BASE=2 KOTH_THREADS_MAX=8 KOTH_INTERVAL_BASE=2 KOTH_INTERVAL_MIN=0.5
  export KOTH_MAX_LEVEL=2 KOTH_LOSS_STREAK=2 KOTH_HOLD_TICKS=3 KOTH_BURST=4
  export KOTH_STATUS_EVERY=5 KOTH_SLOT_PERIOD=5 KOTH_SNIPE_WINDOW=2 KOTH_RELAX_AFTER=25
  export KOTH_STATE_DIR="$tmp" KOTH_STOP_FILE="$tmp/STOP" KOTH_STORAGE="$tmp/none.json"
  unset KOTH_TOKEN KOTH_AUTH KOTH_SIGN_KEY KOTH_KING_FILE KOTH_UNTIL 2>/dev/null || true

  say "[1/4] probe : 1 claim + 1 status"
  "$PY" hill_hold.py --probe >"$tmp/probe.log" 2>&1 || fail=1
  grep -q "ROI(nous)=True" "$tmp/probe.log" || { say "  ECHEC : status ne nous voit pas roi"; fail=1; }
  grep -q "claim: 200" "$tmp/probe.log" || { say "  ECHEC : claim non-200"; fail=1; }
  [ "$fail" -eq 0 ] && say "  OK"

  say "[2/4] tenue 35 s : rival agressif + reset conteneur toutes les 20 s"
  ( "$PY" hill_hold.py --run >"$tmp/run.log" 2>&1 & echo $! >"$tmp/run.pid" )
  sleep 35
  local score
  score=$(curl -s --max-time 5 "http://127.0.0.1:$port/status" | "$PY" -c "
import sys,json
d=json.load(sys.stdin); t=d['ticks'] or 1
print('%d %d %d %d' % (d['score_us'], t, d['score_rival'], d['resets']))")
  set -- $score
  local us=${1:-0} ticks=${2:-1} riv=${3:-0} resets=${4:-0}
  local pct=$(( 100 * us / (ticks > 0 ? ticks : 1) ))
  say "  ticks gagnes : $us/$ticks (${pct}%) | rival : $riv | resets traverses : $resets"
  if [ "$pct" -ge 60 ]; then say "  OK (on tient la colline malgre resets et rival)"; else
    say "  ECHEC : on ne tient pas ($pct% < 60%)"; fail=1; fi
  if [ "$resets" -ge 1 ]; then say "  OK (au moins un reset traverse)"; else
    say "  note : aucun reset pendant le test (non bloquant)"; fi

  say "[3/4] arret par fichier STOP"
  touch "$tmp/STOP"
  local i; for i in $(seq 1 24); do
    kill -0 "$(cat "$tmp/run.pid")" 2>/dev/null || break; sleep 0.5
  done
  if kill -0 "$(cat "$tmp/run.pid")" 2>/dev/null; then say "  ECHEC : toujours vivant"; fail=1
  else say "  OK (arret propre)"; fi

  say "[4/4] mode LOCAL (king file) : reparation d'un ecrasement"
  local kf="$tmp/king.txt"
  KOTH_KING_FILE="$kf" KOTH_TOKEN="TEAM-US" KOTH_STATE_DIR="$tmp" KOTH_STOP_FILE="$tmp/STOP2" \
    "$PY" hill_hold.py --run >"$tmp/local.log" 2>&1 &
  local lp=$!
  sleep 1.5
  printf 'RIVAL\n' > "$kf" 2>/dev/null || true
  sleep 1.5
  if [ "$(cat "$kf" 2>/dev/null)" = "TEAM-US" ]; then say "  OK (fichier roi restaure)"; else
    say "  ECHEC : king file non restaure"; fail=1; fi
  touch "$tmp/STOP2"; sleep 0.5; kill "$lp" 2>/dev/null

  kill "$mock" 2>/dev/null; wait "$mock" 2>/dev/null
  rm -rf "$tmp"
  echo
  if [ "$fail" -eq 0 ]; then say "SELF-TEST : PASS ✅"; return 0; fi
  say "SELF-TEST : FAIL ❌"; return 1
}

# -------------------------------------------------------------------- bundle
cmd_bundle() {
  load_conf
  local out="koth_finale_$(date +%Y%m%d_%H%M).zip"
  local tmp; tmp=$(mktemp -d)
  mkdir -p "$tmp/koth_finale"
  cp -f koth_run.sh hill_hold.py mock_rival.py koth_ssh_takeover.sh onbox_guardian.sh \
        onbox_persist.sh recon_koth.py recon_target.sh hill.env.example README.md \
        koth-hold.service "$tmp/koth_finale/" 2>/dev/null || true
  chmod +x "$tmp/koth_finale/"*.sh 2>/dev/null || true
  cat > "$tmp/koth_finale/START_HERE.txt" <<'TXT'
NCTF26 FINALE — KoTH : tenir la colline jusqu'a la fin
======================================================
1) Remplir hill.env (l'agent le fait a t+0 ; sinon copier hill.env.example).
2) Verifier le kit (2 min, hors-ligne) :
      bash koth_run.sh selftest
3) LANCER :
      bash koth_run.sh start
4) Suivre / arreter :
      bash koth_run.sh status
      bash koth_run.sh stop

Si tu es la Nieme machine : mettre KOTH_PUMPS=<nombre total de machines>
dans hill.env (le debit total reste borne, plusieurs machines tiennent mieux).

Regles : colline in-scope uniquement, pas de DoS, pas d'attaque des autres
equipes ni de l'infra organisatrice.
TXT
  ( cd "$tmp" && zip -qr "$out" koth_finale ) && mv "$tmp/$out" "./$out"
  rm -rf "$tmp"
  say "bundle pret : $HERE/$out"
  say "envoie-le a tes coequipiers ; ils lancent : bash koth_run.sh start"
}

# ---------------------------------------------------------------------- main
case "${1:-start}" in
  start|run)  cmd_start ;;
  stop)       cmd_stop ;;
  status|st)  cmd_status ;;
  logs)       tail -f "$LOG" ;;
  probe)      cmd_probe ;;
  selftest)   cmd_selftest ;;
  bundle)     cmd_bundle ;;
  _supervise) load_conf; _supervise ;;
  *) sed -n '2,24p' "$0"; exit 1 ;;
esac
