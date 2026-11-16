#!/bin/bash
# Poll adaptatif : loin de l'echeance -> intervalle large (30s), pres de
# l'echeance (<20s restantes, d'apres le countdown annonce) -> poll serre (1s).
cd /home/kali/ctfagent
set -a; source src/tools/ctf/.env; set +a
while true; do
  out=$(python3 src/tools/ctf/nctf26_watch.py 2>&1)
  echo "$out"
  if echo "$out" | grep -q "NOUVEAUX:"; then
    echo "$out" | sed -n '/NOUVEAUX:/,$p'
  fi
  secs=$(echo "$out" | grep -oP 'Countdown prochain challenge: \K[0-9]+(?= min )' )
  mins=$(echo "$out" | grep -oP 'Countdown prochain challenge: \K[0-9]+(?= min)')
  s=$(echo "$out" | grep -oP '[0-9]+(?= s$)')
  if [ -n "$mins" ] && [ -n "$s" ]; then
    total=$((mins*60 + s))
  else
    total=999
  fi
  if [ "$total" -le 20 ]; then
    sleep 1
  elif [ "$total" -le 60 ]; then
    sleep 5
  else
    sleep $((total - 30))
  fi
done
