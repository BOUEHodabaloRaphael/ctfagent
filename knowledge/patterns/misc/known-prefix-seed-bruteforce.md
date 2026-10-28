---
doc_kind: pattern
title: "Brute-force a small PRNG seed using the known flag prefix"
category: misc
slug: known-prefix-seed-bruteforce
created: 2026-10-08
---
# Known-prefix seed brute force

**When:** firmware/binary derives output from a PRNG seeded by a short input (e.g. 8 decimal digits) and the capture holding the seed is hard to decode.
**How:** reimplement the LCG in C (check compiler-optimised modulo, e.g. `x mod 2^24-1` via umull magic), loop all seeds, abort early unless first 4 outputs spell `HTB{`/`flag{`. 10^8 seeds ~20s.
**Also:** HTB zips use password `hackthebox`; r2 `pdf @ sym.<fn>` works on non-stripped ARM ELF without a cross toolchain; read constants with `px 4 @ addr`.
Example: [[htb-secret-treasures-flash-lcg]]
