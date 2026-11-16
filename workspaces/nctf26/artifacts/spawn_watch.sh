#!/bin/bash
# Poll team_instancer spawn for boazak--pagne until a slot frees, log result.
COOKIE=$(cat /tmp/claude-1000/-home-kali-ctfagent/eaffa6fc-a5f0-4cd5-b381-99e664966f16/scratchpad/cookie.txt)
NONCE="fc097c262d82c2685284b5b52075e1d32268d89a2f3ae2df56c4b8e9c7826840"
IP=104.21.67.127
LOG=/home/kali/ctfagent/workspaces/nctf26/artifacts/spawn_pagne.log
for i in $(seq 1 40); do
  ts=$(date -u +%H:%M:%S)
  res=$(curl -sS --resolve arena.ctf.tg:443:$IP --max-time 15 \
    -H "Cookie: $COOKIE" -H "Content-Type: application/json" -H "CSRF-Token: $NONCE" \
    -X POST -d '{"challenge_id": 411}' \
    "https://arena.ctf.tg/plugins/team_instancer/spawn" 2>&1)
  echo "$ts $res" >> "$LOG"
  if echo "$res" | grep -q '"success":true'; then
    echo "$ts SLOT FREED, SPAWNED" >> "$LOG"
    break
  fi
  sleep 60
done
