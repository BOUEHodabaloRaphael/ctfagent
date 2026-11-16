#!/usr/bin/env bash
# =====================================================================
# KoTH finale — LANCEUR CLÉ-EN-MAIN (à lancer sur TON terminal et laisser tourner)
#
#   bash run_hold.sh
#
# Tient la colline en continu JUSQU'À LA FIN : watchdog intégré (si le teneur
# tombe, il est relancé), log dans koth.log, statut affiché en direct.
# Pré-requis : l'agent a rempli  hill.env  à l'ouverture (recon de la vraie colline).
# Arrêt : Ctrl+C.
#
# Options :
#   bash run_hold.sh              # utilise ./hill.env
#   bash run_hold.sh autre.env    # config alternative
#   KOTH_THREADS=20 bash run_hold.sh   # surcharge ponctuelle du débit
# =====================================================================
set -u
cd "$(dirname "$0")"

CONF="${1:-hill.env}"
LOG="koth.log"

if [ ! -f "$CONF" ]; then
  echo "[run_hold] ERREUR : config '$CONF' absente."
  echo "           -> l'agent doit la remplir à l'ouverture (cp hill.env.example hill.env puis recon)."
  exit 1
fi

# charge la config (export auto)
set -a; . "./$CONF"; set +a

if [ -z "${KOTH_CLAIM_PATH:-}" ]; then
  echo "[run_hold] ERREUR : KOTH_CLAIM_PATH vide dans $CONF (colline pas encore calibrée)."
  exit 2
fi

echo "[run_hold] démarrage | base=$KOTH_BASE claim=$KOTH_CLAIM_PATH threads=${KOTH_THREADS:-?} | log=$LOG"
echo "[run_hold] calibrage (probe)…"
python3 hold_hill.py --probe 2>&1 | tee -a "$LOG"

# arrêt propre : tue tout le groupe
trap 'echo "[run_hold] arrêt demandé"; kill 0 2>/dev/null; exit 0' INT TERM

echo "[run_hold] tenue en continu (Ctrl+C pour arrêter). Suivi : tail -f $LOG"
# watchdog : relance le teneur s'il s'arrête (crash/réseau), jusqu'à Ctrl+C
while true; do
  python3 hold_hill.py >> "$LOG" 2>&1
  code=$?
  echo "[run_hold] $(date +%H:%M:%S) teneur arrêté (code $code) — relance dans 3s" | tee -a "$LOG"
  sleep 3
done
