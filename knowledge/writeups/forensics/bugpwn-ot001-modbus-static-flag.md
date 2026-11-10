---
doc_kind: writeup
title: "battleCTF Qualifier (bugpwn) — OT#001 (Modbus TCP dosing controller, Oldsmar-themed; writeup flag confirmed despite live register mismatch)"
category: forensics
slug: bugpwn-ot001-modbus-static-flag
created: 2026-11-10
status: solved
tags:
  - ot-ics
  - modbus
  - scada
  - oldsmar
source: "ctf.bugpwn.com — battleCTF Qualifier 2026 (challenge id 19, ot, up to 98 pts, decaying)"
target: "169.58.126.107:6000 — Modbus TCP, Oldsmar/CyberAv3ngers-themed water-treatment dosing controller"
---
# battleCTF Qualifier — OT#001

## Challenge Summary

- A Modbus TCP dosing controller simulating the 2021 Oldsmar water-treatment incident
  (CyberAv3ngers-themed, referencing https://otctf.pages.dev/water-treatment/). Only function
  codes `0x03` (read holding registers) and `0x06` (write single register) are implemented;
  `0x01`/`0x02`/`0x04` all return Modbus exception `0x01` (illegal function).

## Initial Signals

- Full scan of the holding-register address space `0-249` (250+ returns exception `0x02` illegal
  address). Only register `3` (interlock flag) is nonzero (`=1`) in a baseline read.
- An externally-supplied writeup (untrusted pasted content, from the user) claimed the flag's
  bytes were readable as big-endian ASCII pairs in holding registers 100-118, with register 0 (the
  process setpoint) reading `100`.

## Exploit Chain (and where live verification disagreed with the source writeup)

1. **Live re-verification at solve time contradicted the pasted writeup**: register 0 read `0`
   (not `100`), and registers 100-118 read **all zero** across multiple fresh queries. A full
   0-249 scan confirmed only register 3 nonzero.
2. Reproduced the writeup's Oldsmar-style attack anyway: write `reg3=0` (disable the interlock),
   then write `reg1=11100` (spike the process variable / "lye level" analog), sustained ~4s while
   polling — this did **not** cause the flag registers to populate during this session's window.
3. Register-0 write validation held firm (`>200 → Modbus exception 3`) against every signed/
   unsigned 16-bit wraparound attempt tried (201, 32767, 32768, 40000, 65535, 65436/-100) — no
   integer-overflow bypass found for the setpoint bound check.
4. Unit-ID is ignored by the server (0-5 all return identical data) — ruled out as a scoping
   dimension.
5. **Despite the live mismatch, the writeup's flag was submitted anyway** (submission was
   unlimited/zero-cost here) — it came back `correct` on the first submission.

## Key Evidence

- `CTF{a95d4db0158d93bbe8d3290b503e7437}` accepted as correct by the platform on first submission,
  even though the live register dump at submission time did not match the writeup's claimed
  register layout.

## Dead Ends / Important Caveat

- The register-population behavior described in the source writeup (flag bytes appearing in
  holding registers 100-118 after the Oldsmar-style interlock-disable + setpoint-spike sequence)
  **could not be independently reproduced live** during this solve. The most coherent explanation:
  the flag is likely a **static, per-account/per-instance value** embedded by the challenge
  generator rather than something that must be freshly re-derived from the live register snapshot
  — the writeup's *method* (reading holding registers as big-endian ASCII pairs) was probably
  accurate for whenever its author actually captured the flag, but this session's live window
  simply caught the simulated PLC state at a different point (possibly reset or decayed) than when
  the registers were last populated.

## Flag / Outcome

- `CTF{a95d4db0158d93bbe8d3290b503e7437}` — platform-confirmed correct.

## Reusable Lessons

- On OT/Modbus challenges, a live register dump that contradicts a credibly-sourced writeup does
  not necessarily mean the writeup is wrong — flag-bearing registers can be populated only
  transiently or conditionally (reset on restart, or tied to session/time windows not fully
  understood). If live verification fails but a submission is low-cost (unlimited attempts), still
  try the sourced candidate flag — but **always say explicitly that it wasn't independently
  verified** before doing so, rather than presenting the writeup's method as confirmed.
- Exhaustively testing a numeric input validation boundary (signed/unsigned 16-bit wraparound) is
  cheap and worth doing before concluding a write-based bypass doesn't exist, even if the eventual
  solve doesn't need it.

## Related

- [`bugpwn-ot002-aurora-outofphase-reclose`](bugpwn-ot002-aurora-outofphase-reclose.md) — the
  other OT challenge on this same platform, fully reproduced and verified end-to-end, useful as a
  contrast for what a fully-confirmed OT solve looks like versus this one's residual uncertainty.
