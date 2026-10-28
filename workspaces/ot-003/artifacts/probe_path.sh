#!/bin/bash
export PATH=$PATH:/usr/bin:/bin
BASE="http://169.58.126.107:6002"
dec=2887319554 # 172.25.0.2
for path in "$@"; do
  jar=$(mktemp)
  curl -s -i -m 10 -c "$jar" -X POST "$BASE/login" -d "username=operator&password=St33lW0rks!2024" -o /dev/null
  res=$(curl -s -m 6 -b "$jar" -X POST "$BASE/ops/test-sensor" --data-urlencode "url=http://$dec:4000$path")
  echo "$path -> $res"
  rm -f "$jar"
done
