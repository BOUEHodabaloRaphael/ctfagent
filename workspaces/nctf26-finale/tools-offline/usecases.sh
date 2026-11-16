#!/usr/bin/env bash
# usecases.sh - FILET SLA pour defkit.sh (lu par `./defkit.sh check`)
# But : rejouer les flux LEGITIMES que le checker de l'orga teste. Si UN seul casse
# apres un patch -> defkit dit "rollback du dernier correctif". Code retour != 0 = echec.
#
# Installation sur la box (en root) :
#   cp usecases.sh /root/.defkit/usecases.sh
#   # puis ADAPTER host/port + les flux a la vraie appli AVANT le premier `fix`.
#
# Regle : ne teste QUE des usages benins (ceux que l'orga verifie), jamais tes exploits.
# Chaque bloc doit sortir en erreur (return 1) si le flux legitime ne marche plus.
set -u
HOST="${UC_HOST:-127.0.0.1}"
WEB_PORT="${UC_WEB_PORT:-8080}"
PWN_PORT="${UC_PWN_PORT:-31337}"
BASE="http://$HOST:$WEB_PORT"
rc=0
pass(){ echo "  [usecase OK] $*"; }
fail(){ echo "  [usecase FAIL] $*"; rc=1; }

# --- util : code HTTP attendu -------------------------------------------------
http_code(){ curl -sk -o /dev/null -m 5 -w '%{http_code}' "$@" 2>/dev/null; }
http_body(){ curl -sk -m 5 "$@" 2>/dev/null; }

# =====================================================================
# WEB - juice-todo (Node/Express/EJS/SQLite). ADAPTER aux vrais endpoints.
# =====================================================================

# 1. La home / liste des todos doit repondre 200 (rendu EJS non casse par un patch).
c=$(http_code "$BASE/todos"); case "$c" in 200|302) pass "GET /todos -> $c";; *) fail "GET /todos -> $c (attendu 200/302)";; esac

# 2. Emission de token legitime doit toujours fonctionner (apiRoutes /api/token).
#    NB: on verifie juste que l'endpoint repond et renvoie un JWT, pas qu'on forge admin.
tok=$(http_body -X POST "$BASE/api/token" -H 'Content-Type: application/json' --data '{"user":"guest"}')
if echo "$tok" | grep -qE '"token"|eyJ'; then pass "POST /api/token emet un token"; else fail "POST /api/token n'emet plus de token : $tok"; fi

# 3. Creation d'un todo benin doit marcher (INSERT parametre ne doit pas avoir casse l'ecriture).
c=$(http_code -X POST "$BASE/todos" --data-urlencode 'task=sla-check-benign')
case "$c" in 200|201|302) pass "POST /todos (tache benigne) -> $c";; *) fail "POST /todos -> $c (ecriture cassee ?)";; esac

# 4. Tache vide doit toujours etre rejetee en 400 (regle metier a preserver).
c=$(http_code -X POST "$BASE/todos" --data-urlencode 'task=')
case "$c" in 400) pass "POST /todos tache vide -> 400 (regle metier OK)";; *) fail "POST /todos vide -> $c (attendu 400)";; esac

# =====================================================================
# PWN - pwn-sample-kun (:31337). Le chemin BENIN doit survivre au firewall_filter.py.
# Seul patchable = firewall_filter.py : un patch trop large casse le menu legitime.
# =====================================================================
if command -v nc >/dev/null; then
  # Envoie une commande de menu benigne (ex: afficher le menu / une option sans payload).
  # ADAPTER la sequence a l'appli : ici on verifie juste que le service repond du texte.
  out=$(printf '\n' | timeout 5 nc "$HOST" "$PWN_PORT" 2>/dev/null)
  if [ -n "$out" ]; then pass "pwn :$PWN_PORT repond (service up)"; else fail "pwn :$PWN_PORT ne repond plus (filtre trop strict / service down ?)"; fi
else
  echo "  [usecase skip] nc absent, flux pwn non teste"
fi

# =====================================================================
exit $rc
