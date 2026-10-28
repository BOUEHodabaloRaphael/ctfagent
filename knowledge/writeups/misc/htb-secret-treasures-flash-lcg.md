---
doc_kind: writeup
title: "HTB Secret Treasures - SPI Flash Read via LCG-Scrambled Addresses"
category: misc
slug: htb-secret-treasures-flash-lcg
created: 2026-10-08
status: solved
tags:
  - hardware
  - firmware
  - arm
  - spi-flash
  - w25q128
  - lcg
  - saleae
source: HackTheBox
target: "hw_secret: ARM ELF + 16MB flash dump + Saleae capture"
---
# HTB Secret Treasures

## Challenge Summary
- Files: `embedded_software` (ARM32 ELF, not stripped, wiringPi), `flash_memory_dump.bin` (16 MiB), `input_channel_trace.sal` (Saleae zip: `digital-0.bin`, `meta.json`).
- Archive password: `hackthebox`. Browser download may still be named `*.crdownload` even when complete.

## Firmware logic (radare2, `pdf @ sym.main`)
1. Reads 8 chars from `/dev/ttyS0` (9600 baud), `strtoul` base 10 -> `next_in_seq` (LCG seed).
2. Reads W25Q128 unique ID (SPI cmd `0x4B`) and compares with 8 hardcoded bytes (`d266b42183513 02c`) -> "Identified".
3. 49 iterations: `random_generator()` x3 -> addr = (r1&0xff0000)+(r2&0xff00)+(r3&0xff); `get_secret` does SPI READ (`0x03`) at addr; prints the byte.
4. LCG: `s = s*0x41c64e6d + 0x8042a` (u32), output `s mod 0xFFFFFF` (compiler-optimised udiv by 2^24-1).

## Solve
- Flag = flash bytes at those addresses. Only the seed (typed on UART, in the .sal capture) is missing.
- Intended: decode UART from `digital-0.bin`. Shortcut used: Saleae v1/type100 format was not trivially parseable, so brute-force all 10^8 seeds in C (~20s) keeping those whose output starts with `HTB{`. Seed = 73261522.
- Flag: `HTB{m3M0ry_5cR4Mbl1Ng_4nd_1CG_423_n07_3n0u9h7!$#}`
- Not verified: the unique-ID check (flag was readable without it).

## Reusable
- See pattern `known-prefix-seed-bruteforce`.
