#!/bin/sh
# Point 1: REKit misses the stack canary on STRIPPED dynamic binaries.
cd "$(dirname "$0")"
gcc -O0 -fstack-protector-all -o demo demo.c
cp demo demo_stripped && strip demo_stripped
R=../vendor/REKITV2.py
for b in demo demo_stripped; do
  echo "################ $b ($(file -b $b | grep -o 'not stripped\|stripped'))"
  echo "truth  (readelf -sW): $(readelf -sW $b | grep -c __stack_chk_fail) line(s) with __stack_chk_fail"
  echo "REKit sees (readelf -s): $(readelf -s $b | grep -c stack_chk) line(s) with stack_chk"
  echo "REKit says:"; python3 -I $R $b -p | sed 's/\x1b\[[0-9;]*m//g' | grep -E "Canary"
done
