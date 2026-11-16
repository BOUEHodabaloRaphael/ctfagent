#!/bin/bash
COOKIE=$(cat /tmp/claude-1000/-home-kali-ctfagent/eaffa6fc-a5f0-4cd5-b381-99e664966f16/scratchpad/cookie.txt)
NONCE="fc097c262d82c2685284b5b52075e1d32268d89a2f3ae2df56c4b8e9c7826840"
IP=104.21.67.127
LOG=/home/kali/ctfagent/workspaces/nctf26/artifacts/spawn_multi.log
TARGETS=(471 411 397 408 416)
for round in $(seq 1 60); do
  for id in "${TARGETS[@]}"; do
    ts=$(date -u +%H:%M:%S)
    res=$(curl -sS --resolve arena.ctf.tg:443:$IP --max-time 15 \
      -H "Cookie: $COOKIE" -H "Content-Type: application/json" -H "CSRF-Token: $NONCE" \
      -X POST -d "{\"challenge_id\": $id}" \
      "https://arena.ctf.tg/plugins/team_instancer/spawn" 2>&1)
    echo "$ts id=$id $res" >> "$LOG"
    if echo "$res" | grep -q '"success":true'; then
      echo "$ts SLOT FREED on id=$id SPAWNED" >> "$LOG"
      exit 0
    fi
    sleep 8
  done
  sleep 40
done
